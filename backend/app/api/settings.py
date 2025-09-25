#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户全局设置API（缓存配置等）
"""
from flask import Blueprint, request, jsonify, current_app
from ..utils.auth_manager import login_required
from ..models import db, UserSettings
from ..utils.cache_manager import cache_manager

settings_bp = Blueprint('settings', __name__)


# 统一解析 settings 字段为 dict（兼容 JSON 字符串/None）
import json

def _as_dict(val):
    if isinstance(val, dict):
        return val
    try:
        return json.loads(val) if isinstance(val, str) and val else {}
    except Exception:
        return {}

@settings_bp.route('/cache', methods=['GET'])
@login_required
def get_cache_settings(current_user):
    try:
        us = UserSettings.get_or_create(current_user.id)
        # 返回原始已保存值，避免默认值合并造成的“看起来没变化”
        settings_dict = _as_dict(us.settings)
        raw = settings_dict.get('cache', {})
        current_app.logger.info(f"[settings] cache get uid={current_user.id} us.settings={us.settings} raw={raw}")
        return jsonify({ 'success': True, 'data': raw })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'获取缓存设置失败: {e}' }), 500

@settings_bp.route('/cache', methods=['POST'])
@login_required
def save_cache_settings(current_user):
    try:
        payload = request.get_json(silent=True) or {}

        us = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not us:
            us = UserSettings(user_id=current_user.id, settings={})
            db.session.add(us)
        # merge
        settings = _as_dict(us.settings)
        cache_cfg = settings.get('cache', {}) if isinstance(settings.get('cache'), dict) else {}
        # 仅更新传入的键，未传入的不覆盖
        if 'refreshCooldownSeconds' in payload:
            try:
                # 手动刷新冷却：30秒~3600秒（1小时）
                val = int(payload.get('refreshCooldownSeconds'))
                cache_cfg['refreshCooldownSeconds'] = max(30, min(3600, val))
            except Exception:
                pass
        if 'cacheTtlMinutes' in payload:
            try:
                # 缓存TTL：5分钟~1440分钟（24小时）
                val = int(payload.get('cacheTtlMinutes'))
                cache_cfg['cacheTtlMinutes'] = max(5, min(1440, val))
            except Exception:
                pass
        settings['cache'] = cache_cfg
        us.settings = settings
        # 强制标记字段为已修改，确保SQLAlchemy检测到变化
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(us, 'settings')
        db.session.commit()

        # 
        current_app.logger.info(f"[settings] cache saved uid={current_user.id} payload={payload} stored={cache_cfg}")
        return jsonify({ 'success': True, 'data': cache_cfg })
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'message': f'保存缓存设置失败: {e}' }), 500



@settings_bp.route('/monitor', methods=['GET'])
@login_required
def get_monitor_settings(current_user):
    try:
        us = UserSettings.get_or_create(current_user.id)
        settings_dict = _as_dict(us.settings)
        raw = settings_dict.get('monitor', {})
        current_app.logger.info(f"[settings] monitor get uid={current_user.id} us.settings={us.settings} raw={raw}")
        return jsonify({ 'success': True, 'data': raw })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'获取监控设置失败: {e}' }), 500

@settings_bp.route('/monitor', methods=['POST'])
@login_required
def save_monitor_settings(current_user):
    try:
        payload = request.get_json(silent=True) or {}
        us = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not us:
            us = UserSettings(user_id=current_user.id, settings={})
            db.session.add(us)
        settings = _as_dict(us.settings)
        mon = settings.get('monitor', {}) if isinstance(settings.get('monitor'), dict) else {}
        # 校验频率
        min_iv = int(current_app.config.get('MIN_MONITOR_INTERVAL', 180))
        max_iv = int(current_app.config.get('MAX_MONITOR_INTERVAL', 3600))
        if 'frequencySeconds' in payload:
            try:
                val = int(payload.get('frequencySeconds'))
                mon['frequencySeconds'] = max(min_iv, min(max_iv, val))
            except Exception:
                pass
        if 'notificationMinIntervalMinutes' in payload:
            try:
                val = int(payload.get('notificationMinIntervalMinutes'))
                mon['notificationMinIntervalMinutes'] = max(1, val)
            except Exception:
                pass
        settings['monitor'] = mon
        us.settings = settings
        # 强制标记字段为已修改，确保SQLAlchemy检测到变化
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(us, 'settings')
        db.session.commit()
        current_app.logger.info(f"[settings] monitor saved uid={current_user.id} payload={payload} stored={mon}")
        return jsonify({ 'success': True, 'data': mon })
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'message': f'保存监控设置失败: {e}' }), 500

@settings_bp.route('/alerts', methods=['GET'])
@login_required
def get_alerts_settings(current_user):
    try:
        us = UserSettings.get_or_create(current_user.id)
        settings_dict = _as_dict(us.settings)
        raw = settings_dict.get('alerts', {})
        current_app.logger.info(f"[settings] alerts get uid={current_user.id} us.settings={us.settings} raw={raw}")
        return jsonify({ 'success': True, 'data': raw })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'获取告警设置失败: {e}' }), 500

@settings_bp.route('/alerts', methods=['POST'])
@login_required
def save_alerts_settings(current_user):
    try:
        payload = request.get_json(silent=True) or {}
        us = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not us:
            us = UserSettings(user_id=current_user.id, settings={})
            db.session.add(us)
        settings = _as_dict(us.settings)
        alerts = settings.get('alerts', {}) if isinstance(settings.get('alerts'), dict) else {}
        # 浅合并 low/jump
        for key in ['low', 'jump']:
            part = payload.get(key)
            if isinstance(part, dict):
                base = alerts.get(key) if isinstance(alerts.get(key), dict) else {}
                base.update(part)
                alerts[key] = base
        settings['alerts'] = alerts
        us.settings = settings
        # 强制标记字段为已修改，确保SQLAlchemy检测到变化
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(us, 'settings')
        db.session.commit()
        current_app.logger.info(f"[settings] alerts saved uid={current_user.id} payload={payload} stored={alerts}")
        return jsonify({ 'success': True, 'data': alerts })
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'message': f'保存告警设置失败: {e}' }), 500

@settings_bp.route('/alerts/clear', methods=['POST'])
@login_required
def clear_alert_states(current_user):
    """清空当前用户的告警状态（低余量一次性标记、跳点基线）
    可选参数：accountId, types=['low','jump']
    """
    try:
        payload = request.get_json(silent=True) or {}
        account_id = payload.get('accountId')
        types = payload.get('types') or ['low', 'jump']
        if not isinstance(types, list):
            types = ['low', 'jump']

        uid = current_user.id
        deleted = 0

        # 低余量：alert_once:*（包含配置版本后缀，使用通配符）
        if 'low' in types:
            if account_id:
                pattern = f"alert_once:{uid}:{int(account_id)}:low:*:*"
                deleted += cache_manager.clear_pattern(pattern)
            else:
                pattern = f"alert_once:{uid}:*:low:*:*"
                deleted += cache_manager.clear_pattern(pattern)

        # 跳点：jump_base:uid:account:{general|special}
        if 'jump' in types:
            if account_id:
                pattern = f"jump_base:{uid}:{int(account_id)}:*"
                deleted += cache_manager.clear_pattern(pattern)
            else:
                pattern = f"jump_base:{uid}:*:*"
                deleted += cache_manager.clear_pattern(pattern)

        return jsonify({ 'success': True, 'data': { 'deleted': int(deleted) } })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'清空告警状态失败: {e}' }), 500


@settings_bp.route('/notifications', methods=['GET'])
@login_required
def get_notifications_settings(current_user):
    try:
        us = UserSettings.get_or_create(current_user.id)
        raw = (us.settings or {}).get('notifications', {}) if isinstance(us.settings, dict) else {}
        current_app.logger.info(f"[settings] notifications get uid={current_user.id} raw={raw}")
        return jsonify({ 'success': True, 'data': raw })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'获取通知设置失败: {e}' }), 500

@settings_bp.route('/notifications', methods=['POST'])
@login_required
def save_notifications_settings(current_user):
    try:
        payload = request.get_json(silent=True) or {}
        us = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not us:
            us = UserSettings(user_id=current_user.id, settings={})
            db.session.add(us)
        settings = us.settings or {}
        noti = settings.get('notifications') if isinstance(settings.get('notifications'), dict) else {}
        if isinstance(payload, dict):
            for ch, cfg in payload.items():
                if isinstance(cfg, dict):
                    base = noti.get(ch) if isinstance(noti.get(ch), dict) else {}
                    base.update(cfg)
                    noti[ch] = base
        settings['notifications'] = noti
        us.settings = settings
        # 强制标记字段为已修改，确保SQLAlchemy检测到变化
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(us, 'settings')
        db.session.commit()
        current_app.logger.info(f"[settings] notifications saved uid={current_user.id} payload={payload} stored={noti}")
        return jsonify({ 'success': True, 'data': noti })
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'message': f'保存通知设置失败: {e}' }), 500

@settings_bp.route('/display', methods=['GET'])
@login_required
def get_display_settings(current_user):
    try:
        us = UserSettings.get_or_create(current_user.id)
        raw = (us.settings or {}).get('display', {}) if isinstance(us.settings, dict) else {}
        current_app.logger.info(f"[settings] display get uid={current_user.id} raw={raw}")
        return jsonify({ 'success': True, 'data': raw })
    except Exception as e:
        return jsonify({ 'success': False, 'message': f'获取展示设置失败: {e}' }), 500

@settings_bp.route('/display', methods=['POST'])
@login_required
def save_display_settings(current_user):
    try:
        payload = request.get_json(silent=True) or {}
        us = UserSettings.query.filter_by(user_id=current_user.id).first()
        if not us:
            us = UserSettings(user_id=current_user.id, settings={})
            db.session.add(us)
        settings = us.settings or {}
        display = settings.get('display') if isinstance(settings.get('display'), dict) else {}
        if isinstance(payload, dict):
            display.update(payload)
        settings['display'] = display
        us.settings = settings
        # 强制标记字段为已修改，确保SQLAlchemy检测到变化
        from sqlalchemy.orm.attributes import flag_modified
        flag_modified(us, 'settings')
        db.session.commit()
        current_app.logger.info(f"[settings] display saved uid={current_user.id} payload={payload} stored={display}")
        return jsonify({ 'success': True, 'data': display })
    except Exception as e:
        db.session.rollback()
        return jsonify({ 'success': False, 'message': f'保存展示设置失败: {e}' }), 500
