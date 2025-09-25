#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控配置API
"""
from flask import Blueprint, request, jsonify, current_app
from ..models import db, UnicomAccount, MonitorConfig
from ..utils.auth_manager import login_required
from datetime import datetime

monitor_bp = Blueprint('monitor', __name__)

@monitor_bp.route('/configs', methods=['GET'])
@login_required
def get_monitor_configs(current_user):
    """获取用户的所有监控配置"""
    try:
        # 获取用户的所有联通账号
        accounts = UnicomAccount.query.filter_by(
            user_id=current_user.id,
            status=1
        ).all()
        
        if not accounts:
            return jsonify({
                'success': True,
                'data': []
            })
        
        configs = []
        for account in accounts:
            # 获取监控配置
            monitor_config = MonitorConfig.query.filter_by(
                unicom_account_id=account.id,
                status=1
            ).first()
            
            config_data = {
                'account_id': account.id,
                'phone': account.phone,
                'phone_alias': account.phone_alias,
                'auth_status': account.auth_status,
                'is_auth_valid': account.is_auth_valid(),
                'monitor_enabled': False,
                'threshold_low': 1.0,
                'threshold_jump': 0.5,
                'notification_enabled': False,
                'created_at': None,
                'updated_at': None
            }
            
            if monitor_config:
                config_data.update({
                    'monitor_enabled': monitor_config.enabled,
                    'threshold_low': float(monitor_config.threshold_low or 1.0),
                    'threshold_jump': float(monitor_config.threshold_jump or 0.5),
                    'notification_enabled': monitor_config.notification_enabled,
                    'created_at': monitor_config.created_at.isoformat() if monitor_config.created_at else None,
                    'updated_at': monitor_config.updated_at.isoformat() if monitor_config.updated_at else None
                })
            
            configs.append(config_data)
        
        return jsonify({
            'success': True,
            'data': configs
        })
        
    except Exception as e:
        current_app.logger.error(f"获取监控配置失败: {e}")
        return jsonify({'success': False, 'message': '获取监控配置失败'}), 500

@monitor_bp.route('/configs/<int:account_id>', methods=['GET'])
@login_required
def get_monitor_config(current_user, account_id):
    """获取指定账号的监控配置"""
    try:
        # 验证账号权限
        account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()
        
        if not account:
            return jsonify({'success': False, 'message': '账号不存在'}), 404
        
        # 获取监控配置
        monitor_config = MonitorConfig.query.filter_by(
            unicom_account_id=account_id,
            status=1
        ).first()
        
        config_data = {
            'account_id': account.id,
            'phone': account.phone,
            'phone_alias': account.phone_alias,
            'auth_status': account.auth_status,
            'is_auth_valid': account.is_auth_valid(),
            'monitor_enabled': False,
            'threshold_low': 1.0,
            'threshold_jump': 0.5,
            'notification_enabled': False
        }
        
        if monitor_config:
            config_data.update({
                'monitor_enabled': monitor_config.enabled,
                'threshold_low': float(monitor_config.threshold_low or 1.0),
                'threshold_jump': float(monitor_config.threshold_jump or 0.5),
                'notification_enabled': monitor_config.notification_enabled
            })
        
        return jsonify({
            'success': True,
            'data': config_data
        })
        
    except Exception as e:
        current_app.logger.error(f"获取监控配置失败: {e}")
        return jsonify({'success': False, 'message': '获取监控配置失败'}), 500

@monitor_bp.route('/configs/<int:account_id>', methods=['POST', 'PUT'])
@login_required
def save_monitor_config(current_user, account_id):
    """保存监控配置"""
    try:
        # 验证账号权限
        account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()
        
        if not account:
            return jsonify({'success': False, 'message': '账号不存在'}), 404
        
        data = request.get_json() or {}
        
        # 查找或创建监控配置
        monitor_config = MonitorConfig.query.filter_by(
            unicom_account_id=account_id,
            status=1
        ).first()
        
        if not monitor_config:
            monitor_config = MonitorConfig(
                unicom_account_id=account_id,
                user_id=current_user.id
            )
            db.session.add(monitor_config)
        
        # 更新配置
        monitor_config.enabled = data.get('monitor_enabled', False)
        monitor_config.threshold_low = float(data.get('threshold_low', 1.0))
        monitor_config.threshold_jump = float(data.get('threshold_jump', 0.5))
        monitor_config.notification_enabled = data.get('notification_enabled', False)
        from ..utils.timezone_helper import get_db_time
        monitor_config.updated_at = get_db_time()
        
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': '监控配置保存成功',
            'data': {
                'monitor_enabled': monitor_config.enabled,
                'threshold_low': float(monitor_config.threshold_low),
                'threshold_jump': float(monitor_config.threshold_jump),
                'notification_enabled': monitor_config.notification_enabled
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"保存监控配置失败: {e}")
        return jsonify({'success': False, 'message': '保存监控配置失败'}), 500

@monitor_bp.route('/configs/<int:account_id>/toggle', methods=['POST'])
@login_required
def toggle_monitor(current_user, account_id):
    """切换监控状态"""
    try:
        # 验证账号权限
        account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()
        
        if not account:
            return jsonify({'success': False, 'message': '账号不存在'}), 404
        
        # 查找或创建监控配置
        monitor_config = MonitorConfig.query.filter_by(
            unicom_account_id=account_id,
            status=1
        ).first()
        
        if not monitor_config:
            monitor_config = MonitorConfig(
                unicom_account_id=account_id,
                user_id=current_user.id,
                enabled=True
            )
            db.session.add(monitor_config)
        else:
            monitor_config.enabled = not monitor_config.enabled
        
        monitor_config.updated_at = get_db_time()
        db.session.commit()
        
        return jsonify({
            'success': True,
            'message': f'监控已{"开启" if monitor_config.enabled else "关闭"}',
            'data': {
                'monitor_enabled': monitor_config.enabled
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"切换监控状态失败: {e}")
        return jsonify({'success': False, 'message': '切换监控状态失败'}), 500

@monitor_bp.route('/status', methods=['GET'])
@login_required
def get_monitor_status(current_user):
    """获取监控状态概览"""
    try:
        # 获取用户的所有联通账号
        accounts = UnicomAccount.query.filter_by(
            user_id=current_user.id,
            status=1
        ).all()
        
        total_accounts = len(accounts)
        monitoring_accounts = 0
        
        for account in accounts:
            monitor_config = MonitorConfig.query.filter_by(
                unicom_account_id=account.id,
                status=1,
                enabled=True
            ).first()
            if monitor_config:
                monitoring_accounts += 1
        
        return jsonify({
            'success': True,
            'data': {
                'total_accounts': total_accounts,
                'monitoring_accounts': monitoring_accounts,
                'monitoring_rate': round(monitoring_accounts / total_accounts * 100, 1) if total_accounts > 0 else 0
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取监控状态失败: {e}")
        return jsonify({'success': False, 'message': '获取监控状态失败'}), 500
