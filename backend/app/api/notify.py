#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
通知（Notifications）相关API
- WxPusher: 生成参数二维码、查询扫码UID
- 预留：回调接收（可选）
- Test: 各渠道测试发送
"""
from flask import Blueprint, current_app, request, jsonify
import requests
from ..services.notification_service import NotificationService

notify_bp = Blueprint('notify', __name__)

WXPUSHER_BASE = 'https://wxpusher.zjiecode.com'


def _get_wxpusher_token():
    token = getattr(current_app.config, 'WXPUSHER_APP_TOKEN', None) or current_app.config.get('WXPUSHER_APP_TOKEN')
    if token:
        token = str(token).strip()
    if not token:
        current_app.logger.warning('WXPUSHER_APP_TOKEN 未配置，无法调用WxPusher接口')
    return token


@notify_bp.route('/wxpusher/qrcode', methods=['POST'])
def wxpusher_create_qrcode():
    """创建WxPusher参数二维码
    body = { extra, validTime }
    返回: { success, code, url, expireTime, raw }
    """
    token = _get_wxpusher_token()
    if not token:
        return { 'success': False, 'message': 'WXPUSHER_APP_TOKEN 未配置' }, 400

    data = request.get_json(silent=True) or {}
    extra = data.get('extra') or 'bind_uid'
    valid_time = int(data.get('validTime') or 600)
    # WxPusher: 默认30分钟，最长30天；这里做下边界保护
    valid_time = max(60, min(valid_time, 30*24*3600))

    try:
        resp = requests.post(f'{WXPUSHER_BASE}/api/fun/create/qrcode', json={
            'appToken': token,
            'extra': extra,
            'validTime': valid_time
        }, timeout=10)
        rj = resp.json()
        if not rj.get('success'):
            return { 'success': False, 'message': rj.get('msg') or '创建二维码失败', 'raw': rj }, 400
        data = rj.get('data') or {}
        # 兼容不同字段名
        code = data.get('code') or data.get('qrCode') or data.get('qrcode')
        url = data.get('url') or data.get('shortUrl') or data.get('qrUrl')
        return { 'success': True, 'code': code, 'url': url, 'expireTime': data.get('expireTime'), 'raw': data }
    except Exception as e:
        current_app.logger.error(f'创建WxPusher二维码失败: {e}')
        return { 'success': False, 'message': '请求WxPusher失败' }, 500


@notify_bp.route('/wxpusher/scan-result', methods=['GET'])
def wxpusher_scan_result():
    """查询扫码用户UID（轮询）
    请求: ?code=xxx
    返回: { success, uids: [..], raw }
    """
    code = request.args.get('code')
    if not code:
        return { 'success': False, 'message': '缺少code参数' }, 400
    try:
        resp = requests.get(f'{WXPUSHER_BASE}/api/fun/scan-qrcode-uid', params={'code': code}, timeout=10)
        rj = resp.json()
        if not rj.get('success'):
            return { 'success': False, 'message': rj.get('msg') or '查询失败', 'raw': rj }, 400
        data = rj.get('data')
        # 文档示例返回为单个uid或对象，这里做兼容
        uids = []
        if isinstance(data, dict):
            uid = data.get('uid') or data.get('UID')
            if uid:
                uids = [uid]
        elif isinstance(data, list):
            for it in data:
                if isinstance(it, dict) and (it.get('uid') or it.get('UID')):
                    uids.append(it.get('uid') or it.get('UID'))
                elif isinstance(it, str):
                    uids.append(it)
        elif isinstance(data, str):
            uids = [data]
        return { 'success': True, 'uids': uids, 'raw': rj }
    except Exception as e:
        current_app.logger.error(f'查询WxPusher扫码UID失败: {e}')
        return { 'success': False, 'message': '请求WxPusher失败' }, 500


@notify_bp.route('/wxpusher/callback', methods=['POST'])
def wxpusher_callback():
    """可选：接收WxPusher回调（关注/上行/付费等）
    这里只做记录并回OK，便于后续扩展。
    """
    payload = request.get_json(silent=True) or {}
    current_app.logger.info(f'WxPusher回调: {payload}')

@notify_bp.route('/send-test', methods=['POST'])
def send_test_notification():
    """通用测试发送接口
    请求JSON: { channel, settings, title, content }
    """
    data = request.get_json(silent=True) or {}
    channel = data.get('channel')
    settings = data.get('settings') or {}
    title = (data.get('title') or '测试通知').strip()
    content = (data.get('content') or '这是一条测试通知').strip()

    if not channel:
        return jsonify({ 'success': False, 'message': '缺少channel参数' }), 400

    svc = NotificationService(current_app.config)
    try:
        result = svc.send(channel, settings, title, content)
        status = 200 if result.get('success') else 400
        return jsonify({ 'success': result.get('success', False), 'data': result }), status
    except Exception as e:
        current_app.logger.error(f'测试通知发送失败: {e}')
        return jsonify({ 'success': False, 'message': '测试通知发送异常' }), 500

    return { 'success': True }

