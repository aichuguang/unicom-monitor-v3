#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户设置模型：存储用户级全局设置（含缓存配置）
"""
from datetime import datetime
from . import db
from sqlalchemy.dialects.mysql import JSON as MySQLJSON

try:
    JSONType = MySQLJSON
except Exception:  # sqlite fallback
    from sqlalchemy import JSON as JSONType  # type: ignore

DEFAULT_SETTINGS = {
    "cache": {
        "refreshCooldownSeconds": 60,  # 手动刷新冷却（秒）
        "cacheTtlMinutes": 10          # 缓存有效期（分钟）
    },
    "monitor": {
        "frequencySeconds": 300  # 扫描频率（秒）
    },
    "alerts": {
        "low": {
            "general": {"enabled": True,  "mode": "gb", "value": 1},   # 通用：低于1GB提醒（只提醒一次）
            "special": {"enabled": True, "mode": "gb", "value": 1}    # 免流：默认开启，低于1GB提醒
        },
        "jump": {
            "general": {"enabled": True,  "thresholdMB": 3},  # 通用：累计每3MB跳点一次
            "special": {"enabled": True,  "thresholdMB": 3}   # 免流：累计每3MB跳点一次
        }
    },
    "notifications": {
        "wxpusher":   {"enabled": False, "uids": ""},
        "bark":       {"enabled": False, "server": "https://api.day.app", "device_keys": "", "group": "", "sound": "", "isArchive": True},
        "email":      {"enabled": False, "smtp_server": "", "smtp_port": 465, "username": "", "password": "", "to_emails": ""},
        "wechat":     {"enabled": False, "webhook_url": ""},
        "wechat_app": {"enabled": False, "corpid": "", "corpsecret": "", "agentid": None, "touser": "@all"},
        "dingtalk":   {"enabled": False, "webhook_url": "", "secret": ""},
        "wechat_call": {"enabled": False, "api_url": "", "robot_id": "", "target_wxid": "", "server_id": "", "token": ""},
        "webhook":    {"enabled": False, "method": "POST", "url": "", "headers": "", "params": "", "body": ""}
    },
    "display": {
        "showCharts": True,
        "compactMode": False
    }
}

class UserSettings(db.Model):
    __tablename__ = 'user_settings'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True, index=True)
    settings = db.Column(JSONType, nullable=True)

    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('user_settings', uselist=False))

    def to_dict(self):
        data = (self.settings or {}) if isinstance(self.settings, dict) else {}
        # 合并默认值（浅合并 + 针对若干节点进行一层深合并）
        merged = {**DEFAULT_SETTINGS, **data}
        # 一层深合并的节点
        for key in ['cache', 'monitor', 'alerts', 'notifications', 'display']:
            default_part = DEFAULT_SETTINGS.get(key, {})
            user_part = data.get(key, {}) if isinstance(data.get(key, {}), dict) else {}
            merged[key] = {**default_part, **user_part}
        return merged

    @staticmethod
    def get_or_create(user_id: int):
        obj = UserSettings.query.filter_by(user_id=user_id).first()
        if not obj:
            obj = UserSettings(user_id=user_id, settings=DEFAULT_SETTINGS.copy())
            db.session.add(obj)
            db.session.commit()
        return obj

