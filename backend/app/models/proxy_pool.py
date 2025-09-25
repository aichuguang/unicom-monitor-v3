#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
代理池模型
"""
from datetime import datetime
from . import db
from ..utils.timezone_helper import get_db_time

class ProxyPool(db.Model):
    """代理池模型"""
    __tablename__ = 'proxy_pools'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 代理信息
    proxy_host = db.Column(db.String(100), nullable=False, comment='代理主机')
    proxy_port = db.Column(db.Integer, nullable=False, comment='代理端口')
    proxy_type = db.Column(db.String(10), default='http', comment='代理类型: http, https, socks5')
    proxy_username = db.Column(db.String(50), comment='代理用户名')
    proxy_password = db.Column(db.String(100), comment='代理密码')
    
    # 代理属性
    country = db.Column(db.String(50), comment='国家')
    region = db.Column(db.String(50), comment='地区')
    city = db.Column(db.String(50), comment='城市')
    isp = db.Column(db.String(50), comment='运营商')
    
    # 质量指标
    response_time = db.Column(db.Float, comment='响应时间(秒)')
    success_rate = db.Column(db.Float, default=0.0, comment='成功率(0-1)')
    total_requests = db.Column(db.Integer, default=0, comment='总请求次数')
    success_requests = db.Column(db.Integer, default=0, comment='成功请求次数')
    
    # 状态信息
    last_check_at = db.Column(db.DateTime, comment='最后检查时间')
    last_success_at = db.Column(db.DateTime, comment='最后成功时间')
    last_error = db.Column(db.Text, comment='最后错误信息')
    
    # 使用统计
    usage_count = db.Column(db.Integer, default=0, comment='使用次数')
    last_used_at = db.Column(db.DateTime, comment='最后使用时间')
    
    # 状态和优先级
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1-可用, 0-禁用, -1-失效')
    priority = db.Column(db.Integer, default=0, comment='优先级(数字越大优先级越高)')
    
    # 时间
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # 索引
    __table_args__ = (
        db.Index('idx_status_priority', 'status', 'priority'),
        db.Index('idx_success_rate', 'success_rate'),
        db.UniqueConstraint('proxy_host', 'proxy_port', name='uk_proxy_host_port'),
    )
    
    def get_proxy_url(self):
        """获取代理URL"""
        if self.proxy_username and self.proxy_password:
            return f'{self.proxy_type}://{self.proxy_username}:{self.proxy_password}@{self.proxy_host}:{self.proxy_port}'
        else:
            return f'{self.proxy_type}://{self.proxy_host}:{self.proxy_port}'
    
    def get_proxy_dict(self):
        """获取代理字典格式"""
        proxy_url = self.get_proxy_url()
        return {
            'http': proxy_url,
            'https': proxy_url
        }
    
    def update_stats(self, success=True, response_time=None, error_msg=None):
        """更新统计信息"""
        self.total_requests += 1
        self.last_check_at = get_db_time()

        if success:
            self.success_requests += 1
            self.last_success_at = get_db_time()
            self.last_error = None
            if response_time is not None:
                self.response_time = response_time
        else:
            self.last_error = error_msg
            
        # 计算成功率
        if self.total_requests > 0:
            self.success_rate = self.success_requests / self.total_requests
            
        # 根据成功率调整状态
        if self.success_rate < 0.3 and self.total_requests >= 10:
            self.status = -1  # 标记为失效
        elif self.success_rate >= 0.7:
            self.status = 1   # 标记为可用
            
        db.session.commit()
    
    def mark_used(self):
        """标记为已使用"""
        self.usage_count += 1
        self.last_used_at = get_db_time()
        db.session.commit()
    
    def is_available(self):
        """检查是否可用"""
        if self.status != 1:
            return False
            
        # 检查最近是否有成功记录
        if self.last_success_at:
            time_diff = get_db_time() - self.last_success_at
            # 如果超过24小时没有成功记录，认为不可用
            if time_diff.total_seconds() > 86400:
                return False
                
        return True
    
    def get_location_info(self):
        """获取位置信息"""
        location_parts = []
        if self.country:
            location_parts.append(self.country)
        if self.region:
            location_parts.append(self.region)
        if self.city:
            location_parts.append(self.city)
        return ' - '.join(location_parts) if location_parts else '未知'
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'proxy_host': self.proxy_host,
            'proxy_port': self.proxy_port,
            'proxy_type': self.proxy_type,
            'country': self.country,
            'region': self.region,
            'city': self.city,
            'isp': self.isp,
            'location_info': self.get_location_info(),
            'response_time': self.response_time,
            'success_rate': round(self.success_rate * 100, 2) if self.success_rate else 0,
            'total_requests': self.total_requests,
            'success_requests': self.success_requests,
            'usage_count': self.usage_count,
            'last_check_at': self.last_check_at.isoformat() if self.last_check_at else None,
            'last_success_at': self.last_success_at.isoformat() if self.last_success_at else None,
            'last_used_at': self.last_used_at.isoformat() if self.last_used_at else None,
            'last_error': self.last_error,
            'status': self.status,
            'priority': self.priority,
            'is_available': self.is_available(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    @classmethod
    def get_available_proxy(cls):
        """获取可用的代理"""
        return cls.query.filter_by(status=1).order_by(
            cls.priority.desc(),
            cls.success_rate.desc(),
            cls.usage_count.asc()
        ).first()
    
    @classmethod
    def get_random_proxy(cls):
        """获取随机代理"""
        import random
        available_proxies = cls.query.filter_by(status=1).all()
        return random.choice(available_proxies) if available_proxies else None
    
    def __repr__(self):
        return f'<ProxyPool {self.proxy_host}:{self.proxy_port}>'
