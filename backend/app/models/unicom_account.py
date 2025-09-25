#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通账号模型
"""
from datetime import datetime, timedelta
import json
from . import db
from ..utils.timezone_helper import get_db_time, from_db_time

class UnicomAccount(db.Model):
    """联通账号模型"""
    __tablename__ = 'unicom_accounts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, index=True)
    phone = db.Column(db.String(11), nullable=False, index=True)
    phone_alias = db.Column(db.String(50), comment='手机号别名')

    # 认证信息
    token_online = db.Column(db.Text, comment='在线令牌')
    app_id = db.Column(db.Text, comment='应用ID')
    ecs_token = db.Column(db.Text, comment='ECS令牌')
    cookies = db.Column(db.Text, comment='Cookie信息')

    # 登录方式和状态
    login_method = db.Column(db.String(20), default='sms', comment='登录方式: sms, token')
    auth_status = db.Column(db.SmallInteger, default=1, comment='认证状态: 1-有效, 0-失效')
    expires_at = db.Column(db.DateTime, comment='认证过期时间')
    last_refresh_at = db.Column(db.DateTime, comment='最后刷新时间')
    refresh_count = db.Column(db.Integer, default=0, comment='刷新次数')

    # 抓包获取的AppID
    custom_app_id = db.Column(db.Text, comment='从联通APP抓包获取的AppID')
    use_custom_app_id = db.Column(db.Boolean, default=False, comment='是否使用抓包获取的AppID')

    # 监控与通知开关（账号维度）
    monitor_enabled = db.Column(db.Boolean, default=False, index=True, comment='是否开启监控与通知')

    # 状态和时间
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1-正常, 0-删除')
    created_at = db.Column(db.DateTime, default=get_db_time)
    updated_at = db.Column(db.DateTime, default=get_db_time, onupdate=get_db_time)

    # 唯一约束
    __table_args__ = (
        db.UniqueConstraint('user_id', 'phone', name='uk_user_phone'),
        db.Index('idx_phone_status', 'phone', 'status'),
    )
    
    # 关联关系
    device_fingerprint = db.relationship('DeviceFingerprint', backref='unicom_account', uselist=False, cascade='all, delete-orphan')
    flow_records = db.relationship('FlowRecord', backref='unicom_account', lazy='dynamic', cascade='all, delete-orphan')
    monitor_config = db.relationship('MonitorConfig', backref='unicom_account', uselist=False, cascade='all, delete-orphan')
    
    def get_display_name(self):
        """获取显示名称"""
        return self.phone_alias or f"{self.phone[:3]}****{self.phone[-4:]}"
    
    def is_auth_valid(self):
        """检查认证是否有效（仅检查基本信息，不检查过期时间）"""
        if self.auth_status != 1:
            return False

        # 检查是否有必要的认证信息
        return bool(self.cookies or (self.token_online and self.app_id))
    
    def set_expires_at(self, hours=24):
        """设置过期时间（仅用于记录，实际过期由联通服务器决定）"""
        self.expires_at = get_db_time() + timedelta(hours=hours)
    
    def update_refresh_info(self):
        """更新刷新信息"""
        self.last_refresh_at = get_db_time()
        self.refresh_count += 1
        self.set_expires_at()
    
    def get_effective_app_id(self):
        """获取有效的AppID"""
        if self.use_custom_app_id and self.custom_app_id:
            return self.custom_app_id
        return self.app_id
    
    def get_latest_flow_data(self):
        """获取最新流量数据"""
        from .flow_record import FlowRecord
        latest_record = self.flow_records.filter_by(query_status=1).order_by(FlowRecord.created_at.desc()).first()
        return latest_record.to_dict() if latest_record else None
    
    def get_cookies_dict(self):
        """获取Cookie字典"""
        if not self.cookies:
            return {}
        try:
            if isinstance(self.cookies, str):
                # 如果是字符串格式的cookie，解析为字典
                cookie_dict = {}
                for item in self.cookies.split(';'):
                    if '=' in item:
                        key, value = item.strip().split('=', 1)
                        cookie_dict[key] = value
                return cookie_dict
            else:
                return json.loads(self.cookies)
        except (json.JSONDecodeError, ValueError):
            return {}
    
    def set_cookies_from_dict(self, cookie_dict):
        """从字典设置Cookie"""
        if isinstance(cookie_dict, dict):
            self.cookies = json.dumps(cookie_dict)
        else:
            self.cookies = str(cookie_dict)
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'phone': self.phone,
            'phone_alias': self.phone_alias,
            'display_name': self.get_display_name(),
            'login_method': self.login_method,
            'auth_status': self.auth_status,
            'is_auth_valid': self.is_auth_valid(),
            'expires_at': from_db_time(self.expires_at).isoformat() if self.expires_at else None,
            'last_refresh_at': from_db_time(self.last_refresh_at).isoformat() if self.last_refresh_at else None,
            'refresh_count': self.refresh_count,
            'use_custom_app_id': self.use_custom_app_id,
            'monitor_enabled': bool(self.monitor_enabled),
            'status': self.status,
            'created_at': from_db_time(self.created_at).isoformat() if self.created_at else None,
            'device_info': self.device_fingerprint.to_dict() if self.device_fingerprint else None,
            'latest_flow': self.get_latest_flow_data(),
            'monitor_config': self.monitor_config.to_dict() if self.monitor_config else None
        }

        if include_sensitive:
            data.update({
                'token_online': self.token_online,
                'app_id': self.app_id,
                'ecs_token': self.ecs_token,
                'custom_app_id': self.custom_app_id,
                'effective_app_id': self.get_effective_app_id()
            })

        return data
    
    def __repr__(self):
        return f'<UnicomAccount {self.phone}>'
