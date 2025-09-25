#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
系统日志模型
"""
from datetime import datetime
import json
from . import db
from ..utils.timezone_helper import get_db_time, from_db_time

class SystemLog(db.Model):
    """系统日志模型"""
    __tablename__ = 'system_logs'
    
    id = db.Column(db.Integer, primary_key=True)
    
    # 关联信息
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True, index=True)
    unicom_account_id = db.Column(db.Integer, db.ForeignKey('unicom_accounts.id'), nullable=True, index=True)
    
    # 操作信息
    action = db.Column(db.String(50), nullable=False, index=True, comment='操作类型')
    description = db.Column(db.Text, comment='操作描述')
    module = db.Column(db.String(30), comment='模块名称')
    
    # 请求信息
    ip_address = db.Column(db.String(45), comment='IP地址(支持IPv6)')
    user_agent = db.Column(db.Text, comment='用户代理')
    request_method = db.Column(db.String(10), comment='请求方法')
    request_url = db.Column(db.String(255), comment='请求URL')
    request_params = db.Column(db.Text, comment='请求参数')
    
    # 结果信息
    result = db.Column(db.SmallInteger, default=1, comment='操作结果: 1-成功, 0-失败')
    error_code = db.Column(db.String(20), comment='错误代码')
    error_message = db.Column(db.Text, comment='错误信息')
    response_time = db.Column(db.Float, comment='响应时间(秒)')
    
    # 额外数据
    extra_data = db.Column(db.JSON, comment='额外数据')
    
    # 日志级别
    level = db.Column(db.String(10), default='INFO', comment='日志级别: DEBUG, INFO, WARN, ERROR')
    
    # 时间
    created_at = db.Column(db.DateTime, default=get_db_time, index=True)
    
    # 索引
    __table_args__ = (
        db.Index('idx_action_result_time', 'action', 'result', 'created_at'),
        db.Index('idx_user_action_time', 'user_id', 'action', 'created_at'),
        db.Index('idx_level_time', 'level', 'created_at'),
    )
    
    @staticmethod
    def log_action(action, description=None, user_id=None, unicom_account_id=None, 
                   result=1, error_code=None, error_message=None, 
                   ip_address=None, user_agent=None, request_method=None, 
                   request_url=None, request_params=None, response_time=None,
                   extra_data=None, level='INFO', module=None):
        """记录操作日志"""
        try:
            log = SystemLog(
                user_id=user_id,
                unicom_account_id=unicom_account_id,
                action=action,
                description=description,
                module=module,
                ip_address=ip_address,
                user_agent=user_agent,
                request_method=request_method,
                request_url=request_url,
                request_params=request_params,
                result=result,
                error_code=error_code,
                error_message=error_message,
                response_time=response_time,
                extra_data=extra_data,
                level=level
            )
            db.session.add(log)
            db.session.commit()
            return log
        except Exception as e:
            db.session.rollback()
            print(f"记录日志失败: {e}")
            return None
    
    @staticmethod
    def log_login(user_id, success=True, ip_address=None, user_agent=None, error_msg=None):
        """记录登录日志"""
        return SystemLog.log_action(
            action='user_login',
            description=f'用户登录{"成功" if success else "失败"}',
            user_id=user_id,
            result=1 if success else 0,
            error_message=error_msg,
            ip_address=ip_address,
            user_agent=user_agent,
            module='auth'
        )
    
    @staticmethod
    def log_unicom_login(user_id, unicom_account_id, phone, method, success=True, error_msg=None):
        """记录联通账号登录日志"""
        return SystemLog.log_action(
            action='unicom_login',
            description=f'联通账号 {phone} {method}登录{"成功" if success else "失败"}',
            user_id=user_id,
            unicom_account_id=unicom_account_id,
            result=1 if success else 0,
            error_message=error_msg,
            module='unicom'
        )
    
    @staticmethod
    def log_flow_query(user_id, unicom_account_id, phone, success=True, query_time=None, error_msg=None, is_cached=False):
        """记录流量查询日志"""
        return SystemLog.log_action(
            action='flow_query',
            description=f'查询联通账号 {phone} 流量{"成功" if success else "失败"}{"(缓存)" if is_cached else ""}',
            user_id=user_id,
            unicom_account_id=unicom_account_id,
            result=1 if success else 0,
            error_message=error_msg,
            response_time=query_time,
            extra_data={'is_cached': is_cached},
            module='flow'
        )
    
    @staticmethod
    def log_monitor_check(user_id, unicom_account_id, phone, success=True, data_change=None, error_msg=None):
        """记录监控检查日志"""
        return SystemLog.log_action(
            action='monitor_check',
            description=f'监控检查联通账号 {phone}{"成功" if success else "失败"}',
            user_id=user_id,
            unicom_account_id=unicom_account_id,
            result=1 if success else 0,
            error_message=error_msg,
            extra_data={'data_change': data_change} if data_change else None,
            module='monitor'
        )
    
    @staticmethod
    def log_api_request(action, user_id=None, ip_address=None, user_agent=None, 
                       request_method=None, request_url=None, request_params=None,
                       success=True, response_time=None, error_msg=None):
        """记录API请求日志"""
        return SystemLog.log_action(
            action=action,
            user_id=user_id,
            ip_address=ip_address,
            user_agent=user_agent,
            request_method=request_method,
            request_url=request_url,
            request_params=request_params,
            result=1 if success else 0,
            error_message=error_msg,
            response_time=response_time,
            module='api'
        )
    
    def get_extra_data_dict(self):
        """获取额外数据字典"""
        if not self.extra_data:
            return {}
        try:
            return json.loads(self.extra_data) if isinstance(self.extra_data, str) else self.extra_data
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'user_id': self.user_id,
            'unicom_account_id': self.unicom_account_id,
            'action': self.action,
            'description': self.description,
            'module': self.module,
            'ip_address': self.ip_address,
            'user_agent': self.user_agent,
            'request_method': self.request_method,
            'request_url': self.request_url,
            'request_params': self.request_params,
            'result': self.result,
            'error_code': self.error_code,
            'error_message': self.error_message,
            'response_time': self.response_time,
            'extra_data': self.get_extra_data_dict(),
            'level': self.level,
            'created_at': from_db_time(self.created_at).isoformat() if self.created_at else None
        }
    
    def __repr__(self):
        return f'<SystemLog {self.action} {self.result}>'
