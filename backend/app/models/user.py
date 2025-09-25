#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
用户模型
"""
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from . import db
from ..utils.timezone_helper import get_db_time, from_db_time

class User(db.Model):
    """用户模型"""
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False, index=True)
    email = db.Column(db.String(100), unique=True, nullable=True, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    nickname = db.Column(db.String(50))
    avatar_url = db.Column(db.String(255))
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1-正常, 0-禁用')
    created_at = db.Column(db.DateTime, default=get_db_time)
    updated_at = db.Column(db.DateTime, default=get_db_time, onupdate=get_db_time)
    last_login_at = db.Column(db.DateTime)
    
    # 关联关系
    unicom_accounts = db.relationship('UnicomAccount', backref='user', lazy='dynamic', cascade='all, delete-orphan')
    system_logs = db.relationship('SystemLog', backref='user', lazy='dynamic')
    
    def set_password(self, password):
        """设置密码"""
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """验证密码"""
        return check_password_hash(self.password_hash, password)
    
    def update_last_login(self):
        """更新最后登录时间"""
        self.last_login_at = get_db_time()
        db.session.commit()
    
    def get_unicom_account_count(self):
        """获取联通账号数量"""
        return self.unicom_accounts.filter_by(status=1).count()
    
    def can_add_unicom_account(self):
        """是否可以添加联通账号"""
        from ..core.config import Config
        return self.get_unicom_account_count() < Config.MAX_UNICOM_ACCOUNTS_PER_USER
    
    def to_dict(self, include_sensitive=False):
        """转换为字典"""
        data = {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'nickname': self.nickname,
            'avatar_url': self.avatar_url,
            'status': self.status,
            'unicom_account_count': self.get_unicom_account_count(),
            'created_at': from_db_time(self.created_at).isoformat() if self.created_at else None,
            'last_login_at': from_db_time(self.last_login_at).isoformat() if self.last_login_at else None
        }
        
        if include_sensitive:
            data['password_hash'] = self.password_hash
            
        return data
    
    def __repr__(self):
        return f'<User {self.username}>'
