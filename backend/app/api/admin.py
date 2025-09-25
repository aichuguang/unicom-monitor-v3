#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
管理员API蓝图
"""
from flask import Blueprint, request, jsonify, current_app
from datetime import datetime, timedelta
from sqlalchemy import func

from ..utils.auth_manager import login_required, admin_required
from ..utils.cache_manager import cache_manager
from ..models import db, User, UnicomAccount, FlowRecord, SystemLog, ProxyPool

admin_bp = Blueprint('admin', __name__)

@admin_bp.route('/dashboard', methods=['GET'])
@admin_required
def get_dashboard_stats(current_user):
    """获取管理员仪表板统计数据"""
    try:
        # 用户统计
        from ..utils.timezone_helper import now, get_db_time
        current_time = now()
        today_start = get_db_time().replace(hour=0, minute=0, second=0, microsecond=0)

        total_users = User.query.filter_by(status=1).count()
        new_users_today = User.query.filter(
            User.status == 1,
            User.created_at >= today_start
        ).count()

        # 联通账号统计
        total_accounts = UnicomAccount.query.filter_by(status=1).count()
        active_accounts = UnicomAccount.query.filter_by(status=1, auth_status=1).count()

        # 流量查询统计
        week_start = today_start - timedelta(days=7)
        queries_today = FlowRecord.query.filter(
            FlowRecord.created_at >= today_start
        ).count()

        queries_this_week = FlowRecord.query.filter(
            FlowRecord.created_at >= week_start
        ).count()

        # 系统日志统计
        logs_today = SystemLog.query.filter(
            SystemLog.created_at >= today_start
        ).count()
        
        # 代理池统计
        total_proxies = ProxyPool.query.count()
        active_proxies = ProxyPool.query.filter_by(status=1).count()
        
        return jsonify({
            'success': True,
            'data': {
                'users': {
                    'total': total_users,
                    'new_today': new_users_today
                },
                'accounts': {
                    'total': total_accounts,
                    'active': active_accounts,
                    'inactive': total_accounts - active_accounts
                },
                'queries': {
                    'today': queries_today,
                    'this_week': queries_this_week
                },
                'logs': {
                    'today': logs_today
                },
                'proxies': {
                    'total': total_proxies,
                    'active': active_proxies,
                    'inactive': total_proxies - active_proxies
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取仪表板统计异常: {e}")
        return jsonify({'success': False, 'message': '获取统计数据失败'}), 500

@admin_bp.route('/users', methods=['GET'])
@admin_required
def get_users(current_user):
    """获取用户列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        search = request.args.get('search', '').strip()
        
        query = User.query
        
        if search:
            query = query.filter(
                db.or_(
                    User.username.contains(search),
                    User.email.contains(search),
                    User.nickname.contains(search)
                )
            )
        
        pagination = query.order_by(User.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        users = []
        for user in pagination.items:
            user_data = user.to_dict()
            # 添加统计信息
            user_data['unicom_accounts_count'] = UnicomAccount.query.filter_by(
                user_id=user.id, status=1
            ).count()
            users.append(user_data)
        
        return jsonify({
            'success': True,
            'data': {
                'users': users,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取用户列表异常: {e}")
        return jsonify({'success': False, 'message': '获取用户列表失败'}), 500

@admin_bp.route('/users/<int:user_id>/status', methods=['PUT'])
@admin_required
def update_user_status(current_user, user_id):
    """更新用户状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        status = data.get('status')
        if status not in [0, 1]:
            return jsonify({'success': False, 'message': '状态值无效'}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'success': False, 'message': '用户不存在'}), 404
        
        if user.id == current_user.id:
            return jsonify({'success': False, 'message': '不能修改自己的状态'}), 400
        
        user.status = status
        db.session.commit()
        
        # 记录操作日志
        SystemLog.log_action(
            action='user_status_update',
            description=f'{"启用" if status else "禁用"}用户 {user.username}',
            user_id=current_user.id,
            target_user_id=user_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='admin'
        )
        
        return jsonify({
            'success': True,
            'message': f'用户状态已{"启用" if status else "禁用"}',
            'data': user.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新用户状态异常: {e}")
        return jsonify({'success': False, 'message': '更新用户状态失败'}), 500

@admin_bp.route('/logs', methods=['GET'])
@admin_required
def get_system_logs(current_user):
    """获取系统日志"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 50, type=int), 200)
        action = request.args.get('action', '').strip()
        module = request.args.get('module', '').strip()
        user_id = request.args.get('user_id', type=int)
        days = request.args.get('days', 7, type=int)
        
        query = SystemLog.query
        
        # 时间过滤
        if days > 0:
            from ..utils.timezone_helper import get_db_time
            start_date = get_db_time() - timedelta(days=days)
            query = query.filter(SystemLog.created_at >= start_date)
        
        # 动作过滤
        if action:
            query = query.filter(SystemLog.action.contains(action))
        
        # 模块过滤
        if module:
            query = query.filter(SystemLog.module == module)
        
        # 用户过滤
        if user_id:
            query = query.filter(SystemLog.user_id == user_id)
        
        pagination = query.order_by(SystemLog.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        logs = [log.to_dict() for log in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'logs': logs,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取系统日志异常: {e}")
        return jsonify({'success': False, 'message': '获取系统日志失败'}), 500

@admin_bp.route('/proxies', methods=['GET'])
@admin_required
def get_proxies(current_user):
    """获取代理池列表"""
    try:
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        status = request.args.get('status', type=int)
        
        query = ProxyPool.query
        
        if status is not None:
            query = query.filter(ProxyPool.status == status)
        
        pagination = query.order_by(ProxyPool.created_at.desc()).paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        proxies = [proxy.to_dict() for proxy in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'proxies': proxies,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取代理池列表异常: {e}")
        return jsonify({'success': False, 'message': '获取代理池列表失败'}), 500

@admin_bp.route('/proxies', methods=['POST'])
@admin_required
def add_proxy(current_user):
    """添加代理"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        host = data.get('host', '').strip()
        port = data.get('port', type=int)
        username = data.get('username', '').strip() or None
        password = data.get('password', '').strip() or None
        proxy_type = data.get('proxy_type', 'http').strip()
        
        if not host or not port:
            return jsonify({'success': False, 'message': '代理地址和端口不能为空'}), 400
        
        # 检查是否已存在
        existing_proxy = ProxyPool.query.filter_by(host=host, port=port).first()
        if existing_proxy:
            return jsonify({'success': False, 'message': '代理已存在'}), 400
        
        proxy = ProxyPool(
            host=host,
            port=port,
            username=username,
            password=password,
            proxy_type=proxy_type,
            status=1
        )
        
        db.session.add(proxy)
        db.session.commit()
        
        # 记录操作日志
        SystemLog.log_action(
            action='proxy_add',
            description=f'添加代理 {host}:{port}',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='admin'
        )
        
        return jsonify({
            'success': True,
            'message': '代理添加成功',
            'data': proxy.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"添加代理异常: {e}")
        return jsonify({'success': False, 'message': '添加代理失败'}), 500

@admin_bp.route('/proxies/<int:proxy_id>/status', methods=['PUT'])
@admin_required
def update_proxy_status(current_user, proxy_id):
    """更新代理状态"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({'success': False, 'message': '请求数据不能为空'}), 400
        
        status = data.get('status')
        if status not in [0, 1]:
            return jsonify({'success': False, 'message': '状态值无效'}), 400
        
        proxy = ProxyPool.query.get(proxy_id)
        if not proxy:
            return jsonify({'success': False, 'message': '代理不存在'}), 404
        
        proxy.status = status
        db.session.commit()
        
        # 记录操作日志
        SystemLog.log_action(
            action='proxy_status_update',
            description=f'{"启用" if status else "禁用"}代理 {proxy.host}:{proxy.port}',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='admin'
        )
        
        return jsonify({
            'success': True,
            'message': f'代理状态已{"启用" if status else "禁用"}',
            'data': proxy.to_dict()
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"更新代理状态异常: {e}")
        return jsonify({'success': False, 'message': '更新代理状态失败'}), 500

@admin_bp.route('/cache/clear', methods=['POST'])
@admin_required
def clear_cache(current_user):
    """清理缓存"""
    try:
        data = request.get_json() or {}
        cache_type = data.get('cache_type', 'all')
        
        if cache_type == 'all':
            cache_manager.clear_all()
            message = '所有缓存已清理'
        elif cache_type == 'flow':
            cache_manager.clear_pattern('flow:*')
            message = '流量缓存已清理'
        elif cache_type == 'auth':
            cache_manager.clear_pattern('auth:*')
            message = '认证缓存已清理'
        elif cache_type == 'monitor':
            cache_manager.clear_pattern('monitor:*')
            message = '监控缓存已清理'
        else:
            return jsonify({'success': False, 'message': '无效的缓存类型'}), 400
        
        # 记录操作日志
        SystemLog.log_action(
            action='cache_clear',
            description=f'清理缓存: {cache_type}',
            user_id=current_user.id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='admin'
        )
        
        return jsonify({
            'success': True,
            'message': message
        })
        
    except Exception as e:
        current_app.logger.error(f"清理缓存异常: {e}")
        return jsonify({'success': False, 'message': '清理缓存失败'}), 500
