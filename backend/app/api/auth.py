#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证API蓝图
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import jwt_required, get_jwt_identity

from ..utils.auth_manager import AuthManager, login_required
from ..models import db, User, SystemLog

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/register', methods=['POST'])
def register():
    """用户注册"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        email = data.get('email', '').strip() or None
        nickname = data.get('nickname', '').strip() or None
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        result = AuthManager.register_user(username, password, email, nickname)
        status_code = 200 if result['success'] else 400
        
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'message': '注册失败，请稍后重试'}), 500

@auth_bp.route('/login', methods=['POST'])
def login():
    """用户登录"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'success': False, 'message': '用户名和密码不能为空'}), 400
        
        result = AuthManager.login_user(username, password)
        status_code = 200 if result['success'] else 401
        
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'message': '登录失败，请稍后重试'}), 500

@auth_bp.route('/refresh', methods=['POST'])
@jwt_required(refresh=True)
def refresh():
    """刷新访问令牌"""
    try:
        result = AuthManager.refresh_token()
        status_code = 200 if result['success'] else 401
        
        return jsonify(result), status_code
        
    except Exception as e:
        return jsonify({'success': False, 'message': '令牌刷新失败'}), 500

@auth_bp.route('/me', methods=['GET'])
@login_required
def get_user_info(current_user):
    """获取当前用户信息"""
    try:
        return jsonify({
            'success': True,
            'data': current_user.to_dict()
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': '获取用户信息失败'}), 500

@auth_bp.route('/me', methods=['PUT'])
@login_required
def update_user_info(current_user):
    """更新用户信息"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        # 可更新的字段
        nickname = data.get('nickname', '').strip()
        email = data.get('email', '').strip() or None
        avatar_url = data.get('avatar_url', '').strip() or None
        
        # 验证邮箱
        if email:
            valid, msg = AuthManager.validate_email(email)
            if not valid:
                return jsonify({'success': False, 'message': msg}), 400
            
            # 检查邮箱是否被其他用户使用
            existing_user = User.query.filter(User.email == email, User.id != current_user.id).first()
            if existing_user:
                return jsonify({'success': False, 'message': '邮箱已被其他用户使用'}), 400
        
        # 更新用户信息
        if nickname:
            current_user.nickname = nickname
        if email is not None:
            current_user.email = email
        if avatar_url is not None:
            current_user.avatar_url = avatar_url
        
        db.session.commit()
        
        # 记录日志
        SystemLog.log_action(
            action='user_update',
            description=f'用户 {current_user.username} 更新个人信息',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='auth'
        )
        
        return jsonify({
            'success': True,
            'message': '用户信息更新成功',
            'data': current_user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '更新用户信息失败'}), 500

@auth_bp.route('/change-password', methods=['POST'])
@login_required
def change_password(current_user):
    """修改密码"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'success': False, 'message': '旧密码和新密码不能为空'}), 400
        
        # 验证旧密码
        if not current_user.check_password(old_password):
            return jsonify({'success': False, 'message': '旧密码错误'}), 400
        
        # 验证新密码
        valid, msg = AuthManager.validate_password(new_password)
        if not valid:
            return jsonify({'success': False, 'message': msg}), 400
        
        # 检查新密码是否与旧密码相同
        if current_user.check_password(new_password):
            return jsonify({'success': False, 'message': '新密码不能与旧密码相同'}), 400
        
        # 更新密码
        current_user.set_password(new_password)
        db.session.commit()
        
        # 记录日志
        SystemLog.log_action(
            action='password_change',
            description=f'用户 {current_user.username} 修改密码',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='auth'
        )
        
        return jsonify({
            'success': True,
            'message': '密码修改成功'
        })
        
    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': '修改密码失败'}), 500

@auth_bp.route('/logout', methods=['POST'])
@login_required
def logout(current_user):
    """用户登出"""
    try:
        # 记录登出日志
        SystemLog.log_action(
            action='user_logout',
            description=f'用户 {current_user.username} 登出',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='auth'
        )
        
        return jsonify({
            'success': True,
            'message': '登出成功'
        })
        
    except Exception as e:
        return jsonify({'success': False, 'message': '登出失败'}), 500

@auth_bp.route('/delete-account', methods=['DELETE'])
@login_required
def delete_account(current_user):
    """注销账号 - 彻底删除用户及所有相关数据"""
    try:
        from ..models import UnicomAccount, FlowRecord, FlowBaseline, MonitorConfig, UserSettings, DeviceFingerprint

        user_id = current_user.id
        username = current_user.username

        # 记录注销日志
        SystemLog.log_action(
            action='user_delete_account',
            description=f'用户 {username} 注销账号',
            user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='auth'
        )

        # 删除用户相关的所有数据
        # 1. 删除联通账号相关数据
        unicom_accounts = UnicomAccount.query.filter_by(user_id=user_id).all()
        for account in unicom_accounts:
            # 删除流量记录
            FlowRecord.query.filter_by(unicom_account_id=account.id).delete()
            # 删除流量基准
            FlowBaseline.query.filter_by(unicom_account_id=account.id).delete()
            # 删除监控配置
            MonitorConfig.query.filter_by(unicom_account_id=account.id).delete()
            # 删除设备指纹
            DeviceFingerprint.query.filter_by(unicom_account_id=account.id).delete()

        # 2. 删除联通账号
        UnicomAccount.query.filter_by(user_id=user_id).delete()

        # 3. 删除用户设置
        UserSettings.query.filter_by(user_id=user_id).delete()

        # 4. 删除用户相关的系统日志（可选，保留用于审计）
        # SystemLog.query.filter_by(user_id=user_id).delete()

        # 5. 最后删除用户本身
        db.session.delete(current_user)

        # 提交所有删除操作
        db.session.commit()

        return jsonify({
            'success': True,
            'message': '账号已成功注销，所有数据已删除'
        })

    except Exception as e:
        db.session.rollback()
        return jsonify({'success': False, 'message': f'注销账号失败: {str(e)}'}), 500
