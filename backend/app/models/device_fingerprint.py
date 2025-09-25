#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备指纹模型
"""
from datetime import datetime
from . import db
from ..utils.timezone_helper import get_db_time

class DeviceFingerprint(db.Model):
    """设备指纹模型 - 每个联通账号固定设备信息"""
    __tablename__ = 'device_fingerprints'
    
    id = db.Column(db.Integer, primary_key=True)
    unicom_account_id = db.Column(db.Integer, db.ForeignKey('unicom_accounts.id'), nullable=False, unique=True)
    
    # 设备基本信息
    device_id = db.Column(db.String(64), nullable=False, comment='设备ID')
    android_id = db.Column(db.String(32), nullable=False, comment='Android ID')
    device_brand = db.Column(db.String(20), nullable=False, comment='设备品牌')
    device_model = db.Column(db.String(50), nullable=False, comment='设备型号')
    device_os = db.Column(db.String(20), nullable=False, comment='操作系统版本')
    
    # 应用信息
    app_version = db.Column(db.String(20), nullable=False, comment='应用版本')
    push_platform = db.Column(db.String(20), nullable=False, comment='推送平台')
    unique_identifier = db.Column(db.String(64), nullable=False, comment='唯一标识符')
    
    # 网络信息
    user_agent = db.Column(db.Text, comment='用户代理')
    ip_address = db.Column(db.String(15), comment='IP地址')
    
    # 代理信息
    proxy_id = db.Column(db.Integer, db.ForeignKey('proxy_pools.id'), nullable=True, comment='绑定的代理ID')
    
    # 时间戳
    timestamp = db.Column(db.String(13), nullable=False, comment='时间戳')
    
    # 状态和时间
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1-正常, 0-禁用')
    created_at = db.Column(db.DateTime, default=lambda: get_db_time())
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 关联关系
    proxy = db.relationship('ProxyPool', backref='device_fingerprints')
    
    def generate_request_headers(self):
        """生成请求头"""
        return {
            'User-Agent': self.user_agent,
            'Content-Type': 'application/x-www-form-urlencoded',
            'Origin': 'https://img.client.10010.com',
            'Referer': 'https://img.client.10010.com/',
            'X-Tingyun-Id': '4gA5HRiCw8g;c=2;r=919396103;u=20b0f1f663580aaa777224278bdec44b99c5aeb3d91d35d3c4ea1032bc583bbafd96ea06fcd7cc412b1b5c1ee52c63af::BD4E4C616020FB61',
            'X-Tingyun': 'c=A|wD9JNk4GH8w;'
        }
    
    def generate_login_params(self, encrypted_phone, encrypted_password_or_sms, app_id):
        """生成登录参数"""
        return {
            'isFirstInstall': '1',
            'simCount': '1',
            'yw_code': '',
            'deviceOS': self.device_os,
            'mobile': encrypted_phone,
            'netWay': '',
            'deviceCode': self.device_id,
            'isRemberPwd': 'true',
            'version': f"android@{self.app_version}",
            'deviceId': self.device_id,
            'pushPlatform': self.push_platform,
            'password': encrypted_password_or_sms,
            'platformToken': 'v2-CRvjk3iX6vY96Dn6_EbWozerG6nJ206KIXJSJ7C9ttZs6tKcYH3tAw4O-g',
            'keyVersion': '',
            'pip': self.ip_address,
            'provinceChanel': 'general',
            'appId': app_id,
            'simOperator': '5,cmcc,460,01,cn@5,--,460,01,cn',
            'deviceModel': self.device_model,
            'androidId': self.android_id,
            'deviceBrand': self.device_brand,
            'uniqueIdentifier': self.unique_identifier,
            'timestamp': self.timestamp,
            'voiceoff_flag': '1',
            'loginStyle': '0',
            'voice_code': ''
        }
    
    def get_proxy_config(self):
        """获取代理配置"""
        if self.proxy and self.proxy.status == 1:
            return {
                'http': f'{self.proxy.proxy_type}://{self.proxy.proxy_host}:{self.proxy.proxy_port}',
                'https': f'{self.proxy.proxy_type}://{self.proxy.proxy_host}:{self.proxy.proxy_port}'
            }
        return None
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'device_brand': self.device_brand,
            'device_model': self.device_model,
            'device_os': self.device_os,
            'app_version': self.app_version,
            'device_id': self.device_id,
            'android_id': self.android_id,
            'unique_identifier': self.unique_identifier,
            'ip_address': self.ip_address,
            'proxy_info': self.proxy.to_dict() if self.proxy else None,
            'status': self.status,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<DeviceFingerprint {self.device_brand} {self.device_model}>'
