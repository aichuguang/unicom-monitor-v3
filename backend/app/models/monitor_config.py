#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控配置模型
"""
from datetime import datetime
import json
from . import db

class MonitorConfig(db.Model):
    """监控配置模型"""
    __tablename__ = 'monitor_configs'
    
    id = db.Column(db.Integer, primary_key=True)
    unicom_account_id = db.Column(db.Integer, db.ForeignKey('unicom_accounts.id'), nullable=False, unique=True)
    
    # 监控开关
    is_enabled = db.Column(db.Boolean, default=False, comment='是否启用监控')
    
    # 监控间隔 (秒)
    check_interval = db.Column(db.Integer, default=600, comment='检查间隔(秒), 最小180秒, 最大3600秒')
    
    # 流量变化阈值
    change_threshold_mb = db.Column(db.Integer, default=50, comment='流量变化阈值(MB)')
    
    # 通知设置
    notification_enabled = db.Column(db.Boolean, default=False, comment='是否启用通知')
    notification_methods = db.Column(db.JSON, comment='通知方式配置')
    
    # 监控时间段
    monitor_start_time = db.Column(db.Time, comment='监控开始时间')
    monitor_end_time = db.Column(db.Time, comment='监控结束时间')
    monitor_days = db.Column(db.String(20), default='1,2,3,4,5,6,7', comment='监控日期(1-7代表周一到周日)')
    
    # 监控状态
    last_check_at = db.Column(db.DateTime, comment='最后检查时间')
    last_notification_at = db.Column(db.DateTime, comment='最后通知时间')
    check_count = db.Column(db.Integer, default=0, comment='检查次数')
    notification_count = db.Column(db.Integer, default=0, comment='通知次数')
    
    # 错误信息
    last_error = db.Column(db.Text, comment='最后错误信息')
    error_count = db.Column(db.Integer, default=0, comment='错误次数')
    
    # 状态和时间
    status = db.Column(db.SmallInteger, default=1, comment='状态: 1-正常, 0-禁用')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def is_in_monitor_time(self):
        """检查当前是否在监控时间段内"""
        if not self.monitor_start_time or not self.monitor_end_time:
            return True  # 如果没有设置时间段，默认全天监控

        from ..utils.timezone_helper import now
        current_dt = now()
        current_time = current_dt.time()
        current_weekday = str(current_dt.weekday() + 1)  # 1-7代表周一到周日
        
        # 检查是否在监控日期内
        if self.monitor_days and current_weekday not in self.monitor_days.split(','):
            return False
            
        # 检查是否在监控时间段内
        if self.monitor_start_time <= self.monitor_end_time:
            # 同一天内的时间段
            return self.monitor_start_time <= current_time <= self.monitor_end_time
        else:
            # 跨天的时间段
            return current_time >= self.monitor_start_time or current_time <= self.monitor_end_time
    
    def should_check_now(self):
        """检查是否应该现在进行监控"""
        if not self.is_enabled or not self.is_in_monitor_time():
            return False
            
        if not self.last_check_at:
            return True
            
        # 检查间隔
        from ..utils.timezone_helper import get_db_time
        time_diff = get_db_time() - self.last_check_at
        return time_diff.total_seconds() >= self.check_interval
    
    def should_notify(self, data_change_mb):
        """检查是否应该发送通知"""
        if not self.notification_enabled:
            return False
            
        # 检查变化阈值
        if abs(data_change_mb) < self.change_threshold_mb:
            return False
            
        # 检查通知间隔 (至少间隔5分钟)
        if self.last_notification_at:
            from ..utils.timezone_helper import get_db_time
            time_diff = get_db_time() - self.last_notification_at
            if time_diff.total_seconds() < 300:  # 5分钟
                return False
                
        return True
    
    def update_check_info(self, success=True, error_msg=None):
        """更新检查信息"""
        from ..utils.timezone_helper import get_db_time
        self.last_check_at = get_db_time()
        self.check_count += 1

        if success:
            self.error_count = 0
            self.last_error = None
        else:
            self.error_count += 1
            self.last_error = error_msg

        db.session.commit()

    def update_notification_info(self):
        """更新通知信息"""
        from ..utils.timezone_helper import get_db_time
        self.last_notification_at = get_db_time()
        self.notification_count += 1
        db.session.commit()
    
    def get_notification_config(self):
        """获取通知配置"""
        if not self.notification_methods:
            return {}
            
        try:
            return json.loads(self.notification_methods) if isinstance(self.notification_methods, str) else self.notification_methods
        except (json.JSONDecodeError, TypeError):
            return {}
    
    def set_notification_config(self, config):
        """设置通知配置"""
        if isinstance(config, dict):
            self.notification_methods = json.dumps(config)
        else:
            self.notification_methods = config
    
    def validate_interval(self):
        """验证监控间隔"""
        from ..core.config import Config
        if self.check_interval < Config.MIN_MONITOR_INTERVAL:
            self.check_interval = Config.MIN_MONITOR_INTERVAL
        elif self.check_interval > Config.MAX_MONITOR_INTERVAL:
            self.check_interval = Config.MAX_MONITOR_INTERVAL
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'is_enabled': self.is_enabled,
            'check_interval': self.check_interval,
            'change_threshold_mb': self.change_threshold_mb,
            'notification_enabled': self.notification_enabled,
            'notification_config': self.get_notification_config(),
            'monitor_start_time': self.monitor_start_time.strftime('%H:%M') if self.monitor_start_time else None,
            'monitor_end_time': self.monitor_end_time.strftime('%H:%M') if self.monitor_end_time else None,
            'monitor_days': self.monitor_days,
            'last_check_at': self.last_check_at.isoformat() if self.last_check_at else None,
            'last_notification_at': self.last_notification_at.isoformat() if self.last_notification_at else None,
            'check_count': self.check_count,
            'notification_count': self.notification_count,
            'last_error': self.last_error,
            'error_count': self.error_count,
            'status': self.status,
            'is_in_monitor_time': self.is_in_monitor_time(),
            'should_check_now': self.should_check_now()
        }
    
    def __repr__(self):
        return f'<MonitorConfig {self.unicom_account_id} enabled={self.is_enabled}>'
