#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通账号管理API蓝图
"""
from flask import Blueprint, request, jsonify, current_app
import re

from ..utils.auth_manager import login_required
from ..utils.unicom_api import unicom_api
from ..utils.device_generator import device_generator
from ..utils.cache_manager import cache_manager
from ..models import db, UnicomAccount, DeviceFingerprint, SystemLog

unicom_bp = Blueprint('unicom', __name__)

@unicom_bp.route('/accounts', methods=['GET'])
@login_required
def get_accounts(current_user):
    """获取用户的联通账号列表"""
    try:
        accounts = UnicomAccount.query.filter_by(
            user_id=current_user.id,
            status=1
        ).order_by(UnicomAccount.created_at.desc()).all()

        return jsonify({
            'success': True,
            'data': [account.to_dict() for account in accounts]
        })

    except Exception as e:
        current_app.logger.error(f"获取联通账号列表异常: {e}")
        return jsonify({'success': False, 'message': '获取账号列表失败'}), 500

@unicom_bp.route('/accounts/<int:account_id>', methods=['GET'])
@login_required
def get_account_detail(current_user, account_id):
    """获取单个联通账号详情（含敏感字段）"""
    try:
        account = UnicomAccount.query.filter_by(id=account_id, user_id=current_user.id).first()
        if not account or account.status != 1:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404
        return jsonify({'success': True, 'data': account.to_dict(include_sensitive=True)})
    except Exception as e:
        current_app.logger.error(f"获取联通账号详情异常: {e}")
        return jsonify({'success': False, 'message': '获取账号详情失败'}), 500


@unicom_bp.route('/accounts', methods=['POST'])
@login_required
def add_account(current_user):
    """添加联通账号"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400

        phone = data.get('phone', '').strip()
        phone_alias = data.get('phone_alias', '').strip() or None
        # 可选：抓包AppID相关字段（用于后续登录或偏好）
        custom_app_id = (data.get('custom_app_id', '') or '').strip() or None
        use_custom_app_id = bool(data.get('use_custom_app_id', False))

        # 验证必填字段
        if not phone:
            return jsonify({'success': False, 'message': '手机号不能为空'}), 400

        # 验证手机号格式
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return jsonify({'success': False, 'message': '手机号格式不正确'}), 400

        # 检查是否超过限制
        if not current_user.can_add_unicom_account():
            return jsonify({
                'success': False,
                'message': f'每个用户最多只能添加{current_app.config["MAX_UNICOM_ACCOUNTS_PER_USER"]}个联通账号'
            }), 400

        # 检查手机号是否已存在（不区分状态，避免唯一索引冲突）
        existing_any = UnicomAccount.query.filter_by(
            user_id=current_user.id,
            phone=phone
        ).first()
        if existing_any:
            if existing_any.status == 1:
                return jsonify({'success': False, 'message': '该手机号已存在，无需重复添加'}), 400
            # 复用已存在但被禁用/删除的记录，恢复为正常状态
            existing_any.status = 1
            existing_any.phone_alias = phone_alias
            # 若请求中携带AppID偏好，同步恢复
            existing_any.custom_app_id = custom_app_id
            existing_any.use_custom_app_id = use_custom_app_id and bool(custom_app_id)
            existing_any.auth_status = 0  # 仍未认证
            db.session.flush()
            # 确保存在设备指纹
            if not existing_any.device_fingerprint:
                device_generator.create_device_fingerprint_for_account(existing_any)
            db.session.commit()
            SystemLog.log_action(
                action='unicom_account_restore',
                description=f'恢复联通账号 {phone}',
                user_id=current_user.id,
                unicom_account_id=existing_any.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                module='unicom'
            )
            return jsonify({
                'success': True,
                'message': '联通账号已恢复',
                'data': existing_any.to_dict()
            })

        # 创建联通账号记录
        unicom_account = UnicomAccount(
            user_id=current_user.id,
            phone=phone,
            phone_alias=phone_alias,
            auth_status=0,  # 初始状态为未认证
            custom_app_id=custom_app_id,
            use_custom_app_id=use_custom_app_id and bool(custom_app_id)
        )
        db.session.add(unicom_account)
        db.session.flush()  # 获取ID

        # 生成设备指纹
        device_fingerprint = device_generator.create_device_fingerprint_for_account(unicom_account)
        db.session.commit()

        # 记录操作日志
        SystemLog.log_action(
            action='unicom_account_add',
            description=f'添加联通账号 {phone}',
            user_id=current_user.id,
            unicom_account_id=unicom_account.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='unicom'
        )

        return jsonify({
            'success': True,
            'message': '联通账号添加成功',
            'data': unicom_account.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加联通账号异常: {e}")
        return jsonify({'success': False, 'message': '添加联通账号失败'}), 500

@unicom_bp.route('/accounts/<int:account_id>', methods=['PUT'])
@login_required
def update_account(current_user, account_id):
    """更新联通账号信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400

        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()

        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404

        # 可更新的字段
        phone_alias = data.get('phone_alias', '').strip() or None
        custom_app_id = data.get('custom_app_id', '').strip() or None
        use_custom_app_id = data.get('use_custom_app_id', False)

        # 更新信息
        unicom_account.phone_alias = phone_alias
        unicom_account.custom_app_id = custom_app_id
        unicom_account.use_custom_app_id = use_custom_app_id and bool(custom_app_id)

        db.session.commit()

        # 记录操作日志
        SystemLog.log_action(
            action='unicom_account_update',
            description=f'更新联通账号 {unicom_account.phone} 信息',
            user_id=current_user.id,
            unicom_account_id=account_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='unicom'
        )

        return jsonify({
            'success': True,
            'message': '联通账号信息更新成功',
            'data': unicom_account.to_dict()
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新联通账号异常: {e}")
        return jsonify({'success': False, 'message': '更新联通账号失败'}), 500

@unicom_bp.route('/accounts/<int:account_id>', methods=['DELETE'])
@login_required
def delete_account(current_user, account_id):
    """删除联通账号"""
    try:
        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()

        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404

        # 软删除（设置状态为0）
        unicom_account.status = 0
        db.session.commit()

        # 清除相关缓存
        cache_manager.delete_flow_cache(account_id)
        cache_manager.clear_pattern(f"*:{account_id}:*")

        # 记录操作日志
        SystemLog.log_action(
            action='unicom_account_delete',
            description=f'删除联通账号 {unicom_account.phone}',
            user_id=current_user.id,
            unicom_account_id=account_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='unicom'
        )

        return jsonify({
            'success': True,
            'message': '联通账号删除成功'
        })

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"删除联通账号异常: {e}")
        return jsonify({'success': False, 'message': '删除联通账号失败'}), 500

@unicom_bp.route('/accounts/<int:account_id>/login/sms', methods=['POST'])
@login_required
def sms_login(current_user, account_id):
    """联通账号验证码登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400

        sms_code = data.get('sms_code', '').strip()
        custom_app_id = data.get('custom_app_id', '').strip()

        if not sms_code:
            return jsonify({'success': False, 'message': '验证码不能为空'}), 400
        if not custom_app_id:
            return jsonify({'success': False, 'message': 'AppID不能为空'}), 400

        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()

        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404

        # 更新AppID
        unicom_account.custom_app_id = custom_app_id
        unicom_account.use_custom_app_id = True

        # 调用联通API登录
        result = unicom_api.sms_login(unicom_account, sms_code)

        if result['success']:
            # 保存认证信息
            auth_data = result['data']

            unicom_account.app_id = auth_data.get('appId')
            unicom_account.token_online = auth_data.get('token_online')
            unicom_account.ecs_token = auth_data.get('ecs_token')
            unicom_account.cookies = auth_data.get('cookies')
            unicom_account.login_method = 'sms'
            unicom_account.auth_status = 1
            unicom_account.set_expires_at(hours=current_app.config.get('TOKEN_EXPIRE_HOURS', 24))

            db.session.commit()

            # 记录操作日志
            SystemLog.log_unicom_login(
                user_id=current_user.id,
                unicom_account_id=account_id,
                phone=unicom_account.phone,
                method='验证码',
                success=True
            )

            return jsonify({
                'success': True,
                'message': '验证码登录成功',
                'data': {
                    'account_info': unicom_account.to_dict(include_sensitive=True),
                    'auth_info': auth_data
                }
            })
        else:
            # 记录登录失败
            SystemLog.log_unicom_login(
                user_id=current_user.id,
                unicom_account_id=account_id,
                phone=unicom_account.phone,
                method='验证码',
                success=False,
                error_msg=result.get('message')
            )

            return jsonify(result), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"验证码登录异常: {e}")
        return jsonify({'success': False, 'message': '验证码登录失败'}), 500

@unicom_bp.route('/accounts/<int:account_id>/login/token', methods=['POST'])
@login_required
def token_login(current_user, account_id):
    """联通账号Token登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400

        token_online = data.get('token_online', '').strip()
        app_id = data.get('app_id', '').strip()

        if not token_online:
            return jsonify({'success': False, 'message': 'Token Online不能为空'}), 400
        if not app_id:
            return jsonify({'success': False, 'message': 'App ID不能为空'}), 400

        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()

        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404

        # 更新Token信息
        unicom_account.token_online = token_online
        unicom_account.app_id = app_id
        unicom_account.login_method = 'token'

        # 调用联通API进行token登录
        result = unicom_api.token_login(unicom_account)

        if result['success']:
            # 保存认证信息
            auth_data = result['data']

            unicom_account.app_id = auth_data.get('appId')
            unicom_account.token_online = auth_data.get('token_online')
            unicom_account.ecs_token = auth_data.get('ecs_token')
            unicom_account.cookies = auth_data.get('cookies')
            unicom_account.auth_status = 1
            unicom_account.set_expires_at(hours=current_app.config.get('TOKEN_EXPIRE_HOURS', 24))

            db.session.commit()

            # 记录操作日志
            SystemLog.log_unicom_login(
                user_id=current_user.id,
                unicom_account_id=account_id,
                phone=unicom_account.phone,
                method='Token',
                success=True
            )

            return jsonify({
                'success': True,
                'message': 'Token登录成功',
                'data': {
                    'account_info': unicom_account.to_dict(include_sensitive=True),
                    'auth_info': auth_data
                }
            })
        else:
            # 记录登录失败
            SystemLog.log_unicom_login(
                user_id=current_user.id,
                unicom_account_id=account_id,
                phone=unicom_account.phone,
                method='Token',
                success=False,
                error_msg=result.get('message')
            )

            return jsonify(result), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Token登录异常: {e}")
        return jsonify({'success': False, 'message': 'Token登录失败'}), 500

@unicom_bp.route('/accounts/<int:account_id>/refresh', methods=['POST'])
@login_required
def refresh_auth(current_user, account_id):
    """刷新联通账号认证"""
    try:
        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()

        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404

        if not unicom_account.token_online or not unicom_account.get_effective_app_id():
            return jsonify({'success': False, 'message': '缺少Token或AppID信息，请重新登录'}), 400

        # 调用联通API刷新
        result = unicom_api.token_refresh(unicom_account)

        if result['success']:
            # 保存认证信息
            auth_data = result['data']

            unicom_account.app_id = auth_data.get('appId')
            unicom_account.token_online = auth_data.get('token_online')
            unicom_account.ecs_token = auth_data.get('ecs_token')
            unicom_account.cookies = auth_data.get('cookies')
            unicom_account.auth_status = 1
            unicom_account.update_refresh_info()

            db.session.commit()

            # 清除流量缓存
            cache_manager.delete_flow_cache(account_id)

            return jsonify({
                'success': True,
                'message': '认证刷新成功',
                'data': unicom_account.to_dict(include_sensitive=True)
            })
        else:
            # 刷新失败，返回详细错误信息
            error_msg = result.get('message', '认证刷新失败')
            error_code = result.get('code')
            need_reauth = result.get('need_reauth', False)

            # 记录刷新失败日志
            SystemLog.log_action(
                action='refresh_auth_failed',
                description=f'刷新认证失败 {unicom_account.phone}: {error_msg}',
                user_id=current_user.id,
                unicom_account_id=account_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                module='unicom'
            )

            return jsonify({
                'success': False,
                'message': error_msg,
                'code': error_code,
                'need_reauth': need_reauth
            }), 400

    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"刷新认证异常: {e}")
        return jsonify({'success': False, 'message': '刷新认证失败'}), 500


@unicom_bp.route('/accounts/<int:account_id>/monitor-toggle', methods=['POST'])
@login_required
def toggle_monitor(current_user, account_id):
    """切换账号监控与通知开关"""
    try:
        data = request.get_json(silent=True) or {}
        enabled = bool(data.get('enabled'))

        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id
        ).first()
        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404

        if unicom_account.status != 1:
            return jsonify({'success': False, 'message': '账号已被删除或禁用'}), 400

        # 可选校验：未认证有效时不允许开启
        if enabled and not unicom_account.is_auth_valid():
            return jsonify({'success': False, 'message': '账号未认证或已过期，无法开启监控'}), 400

        unicom_account.monitor_enabled = enabled
        db.session.commit()

        SystemLog.log_action(
            action='unicom_account_monitor_toggle',
            description=f'切换监控开关为 {"开启" if enabled else "关闭"} - {unicom_account.phone}',
            user_id=current_user.id,
            unicom_account_id=account_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='unicom'
        )

        return jsonify({'success': True, 'data': {'monitor_enabled': bool(unicom_account.monitor_enabled)}})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"切换监控开关异常: {e}")
        return jsonify({'success': False, 'message': '切换监控开关失败'}), 500
