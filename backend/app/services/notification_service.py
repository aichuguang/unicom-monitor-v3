#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
NotificationService: 统一通知发送服务
支持: Email SMTP, 企业微信机器人(Webhook), 钉钉(Webhook), 自定义 Webhook,
Bark(iOS), WxPusher(文本)、微信电话(自定义API)

说明：
- 提供最小可用的发送能力，参数从调用方传入
- WxPusher 的 appToken 从应用配置读取（环境变量 WXPUSHER_APP_TOKEN）
"""
from __future__ import annotations
import smtplib
from email.mime.text import MIMEText
from email.header import Header
from typing import Dict, Any, List, Optional
import requests

class NotificationService:
    def __init__(self, app_config):
        self.config = app_config
        self.timeout = 10

    # ---------------- Email ----------------
    def send_email(self, settings: Dict[str, Any], subject: str, content: str) -> Dict[str, Any]:
        """
        settings: { smtp_server, smtp_port, username, password, to_emails }
        to_emails 可以是以逗号/换行分隔的字符串或列表
        """
        smtp_server = settings.get('smtp_server')
        smtp_port = int(settings.get('smtp_port') or 25)
        username = settings.get('username')
        password = settings.get('password')
        to_emails = settings.get('to_emails') or ''
        if isinstance(to_emails, str):
            tos = [x.strip() for x in to_emails.replace('\n', ',').split(',') if x.strip()]
        else:
            tos = list(to_emails or [])
        if not smtp_server or not username or not password or not tos:
            return { 'success': False, 'message': '邮件参数不完整' }

        msg = MIMEText(content, 'plain', 'utf-8')
        msg['Subject'] = Header(subject, 'utf-8')
        msg['From'] = username
        msg['To'] = ','.join(tos)

        try:
            # 兼容 465(SSL)/ 587(TLS)/ 25
            if smtp_port == 465:
                server = smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=self.timeout)
            else:
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=self.timeout)
                if smtp_port in (587,):
                    server.starttls()
            server.login(username, password)
            server.sendmail(username, tos, msg.as_string())
            server.quit()
            return { 'success': True }
        except Exception as e:
            return { 'success': False, 'message': f'发送邮件失败: {e}' }

    # ------------- 企业微信机器人 -------------
    def send_wechat_robot(self, settings: Dict[str, Any], content: str) -> Dict[str, Any]:
        url = settings.get('webhook_url')
        if not url:
            return { 'success': False, 'message': 'Webhook URL 未配置' }
        try:
            resp = requests.post(url, json={ 'msgtype': 'text', 'text': { 'content': content } }, timeout=self.timeout)
            ok = resp.status_code == 200
            return { 'success': ok, 'status': resp.status_code, 'data': resp.text }
        except Exception as e:
            return { 'success': False, 'message': f'企业微信发送失败: {e}' }

    # ----------------- 钉钉 ------------------
    def send_dingtalk(self, settings: Dict[str, Any], content: str) -> Dict[str, Any]:
        url = settings.get('webhook_url')
        # 简化：未实现加签，可后续扩展。若提供 secret，可提示忽略。
        if not url:
            return { 'success': False, 'message': 'Webhook URL 未配置' }
        try:
            resp = requests.post(url, json={ 'msgtype': 'text', 'text': { 'content': content } }, timeout=self.timeout)
            ok = resp.status_code == 200
            return { 'success': ok, 'status': resp.status_code, 'data': resp.text }
        except Exception as e:
            return { 'success': False, 'message': f'钉钉发送失败: {e}' }

    # ------------- 自定义 Webhook -------------
    def send_custom_webhook(self, settings: Dict[str, Any]) -> Dict[str, Any]:
        method = (settings.get('method') or 'POST').upper()
        url = settings.get('url')
        headers = settings.get('headers')
        params = settings.get('params')
        body = settings.get('body')
        if not url:
            return { 'success': False, 'message': 'URL 未配置' }
        try:
            # headers/params/body 可为字符串(JSON)或已解析对象
            import json
            if isinstance(headers, str) and headers.strip():
                headers = json.loads(headers)
            if isinstance(params, str) and params.strip():
                params = json.loads(params)
            if isinstance(body, str) and body.strip():
                body = json.loads(body)
            func = requests.post if method == 'POST' else requests.get
            resp = func(url, headers=headers, params=params, json=body, timeout=self.timeout)
            ok = 200 <= resp.status_code < 300
            return { 'success': ok, 'status': resp.status_code, 'data': resp.text }
        except Exception as e:
            return { 'success': False, 'message': f'Webhook 发送失败: {e}' }

    # ----------------- Bark ------------------
    def send_bark(self, settings: Dict[str, Any], title: str, content: str) -> Dict[str, Any]:
        server = (settings.get('server') or 'https://api.day.app').rstrip('/')
        device_keys = settings.get('device_keys') or ''
        group = settings.get('group')
        sound = settings.get('sound')
        is_archive = settings.get('isArchive', True)
        keys: List[str] = []
        if isinstance(device_keys, str):
            keys = [x.strip() for x in device_keys.replace('\n', ',').split(',') if x.strip()]
        else:
            keys = list(device_keys or [])
        if not keys:
            return { 'success': False, 'message': 'Bark Device Key 未配置' }
        try:
            results = []
            params = {}
            if group: params['group'] = group
            if sound: params['sound'] = sound
            if is_archive is not None: params['isArchive'] = '1' if is_archive else '0'
            for key in keys:
                url = f"{server}/{key}/{title}/{content}"
                resp = requests.get(url, params=params, timeout=self.timeout)
                results.append({ 'key': key, 'status': resp.status_code, 'data': resp.text })
            ok = all(200 <= r['status'] < 300 for r in results)
            return { 'success': ok, 'results': results }
        except Exception as e:
            return { 'success': False, 'message': f'Bark 发送失败: {e}' }

    # --------------- WxPusher ----------------
    def send_wxpusher_text(self, uids: List[str], content: str) -> Dict[str, Any]:
        app_token = (self.config.get('WXPUSHER_APP_TOKEN') or '').strip()
        if not app_token:
            return { 'success': False, 'message': 'WXPUSHER_APP_TOKEN 未配置' }
        uids = [u for u in (uids or []) if u]
        if not uids:
            return { 'success': False, 'message': 'UID 列表为空' }
        try:
            resp = requests.post('https://wxpusher.zjiecode.com/api/send/message', json={
                'appToken': app_token,
                'content': content,
                'contentType': 1,
                'uids': uids
            }, timeout=self.timeout)
            rj = resp.json()
            ok = rj.get('success') or (rj.get('code') == 1000)
            return { 'success': bool(ok), 'raw': rj }
        except Exception as e:
            return { 'success': False, 'message': f'WxPusher 发送失败: {e}' }

    # -------------- 企业微信应用 --------------
    def send_wechat_app(self, settings: Dict[str, Any], content: str) -> Dict[str, Any]:
        corpid = settings.get('corpid')
        corpsecret = settings.get('corpsecret')
        agentid = settings.get('agentid')
        touser = settings.get('touser', '@all')

        if not all([corpid, corpsecret, agentid]):
            return { 'success': False, 'message': '企业微信应用参数不完整' }

        try:
            # 1. 获取access_token
            token_resp = requests.get(
                'https://qyapi.weixin.qq.com/cgi-bin/gettoken',
                params={'corpid': corpid, 'corpsecret': corpsecret},
                timeout=self.timeout
            )
            token_data = token_resp.json()
            if token_data.get('errcode') != 0:
                return { 'success': False, 'message': f'获取access_token失败: {token_data.get("errmsg")}' }

            access_token = token_data.get('access_token')

            # 2. 发送消息
            send_resp = requests.post(
                f'https://qyapi.weixin.qq.com/cgi-bin/message/send?access_token={access_token}',
                json={
                    'touser': touser,
                    'msgtype': 'text',
                    'agentid': agentid,
                    'text': {'content': content}
                },
                timeout=self.timeout
            )
            send_data = send_resp.json()
            ok = send_data.get('errcode') == 0
            return { 'success': ok, 'status': send_resp.status_code, 'data': send_data }
        except Exception as e:
            return { 'success': False, 'message': f'企业微信应用发送失败: {e}' }

    # -------------- 微信电话 -----------------
    def send_wechat_call(self, settings: Dict[str, Any], content: str) -> Dict[str, Any]:
        api_url = settings.get('api_url')
        token = settings.get('token', '').strip()

        if not api_url:
            return { 'success': False, 'message': '微信电话 API 地址未配置' }
        if not token:
            return { 'success': False, 'message': '微信电话 Token 未配置' }

        # 自动添加 Bearer 前缀（如果用户没有添加的话）
        if not token.startswith('Bearer '):
            token = f'Bearer {token}'

        payload = {
            'robotid': settings.get('robot_id'),
            'target_wxid': settings.get('target_wxid'),
            'server_id': settings.get('server_id'),
            'token': token,
            'text': content,
        }
        try:
            resp = requests.post(api_url, json=payload, timeout=self.timeout)
            ok = 200 <= resp.status_code < 300
            return { 'success': ok, 'status': resp.status_code, 'data': resp.text }
        except Exception as e:
            return { 'success': False, 'message': f'微信电话发送失败: {e}' }

    # --------------- 统一入口 ----------------
    def send(self, channel: str, settings: Dict[str, Any], title: str, content: str) -> Dict[str, Any]:
        channel = (channel or '').lower()
        if channel == 'email':
            return self.send_email(settings, title, content)
        if channel == 'wechat':
            return self.send_wechat_robot(settings, content)
        if channel == 'wechat_app':
            return self.send_wechat_app(settings, content)
        if channel == 'dingtalk':
            return self.send_dingtalk(settings, content)
        if channel == 'webhook':
            return self.send_custom_webhook(settings)
        if channel == 'bark':
            return self.send_bark(settings, title, content)
        if channel == 'wxpusher':
            # settings 里取 uids 字符串
            uids_val = settings.get('uids') or ''
            if isinstance(uids_val, str):
                uids = [x.strip() for x in uids_val.replace('\n', ',').split(',') if x.strip()]
            else:
                uids = list(uids_val or [])
            return self.send_wxpusher_text(uids, content)
        if channel == 'wechat_call':
            return self.send_wechat_call(settings, content)
        return { 'success': False, 'message': f'不支持的通知渠道: {channel}' }

