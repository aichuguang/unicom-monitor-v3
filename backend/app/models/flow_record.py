#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流量记录模型
"""
from datetime import datetime
import json
from . import db
from ..utils.timezone_helper import get_db_time

class FlowRecord(db.Model):
    """流量查询记录模型"""
    __tablename__ = 'flow_records'
    
    id = db.Column(db.Integer, primary_key=True)
    unicom_account_id = db.Column(db.Integer, db.ForeignKey('unicom_accounts.id'), nullable=False, index=True)
    
    # 查询信息
    query_type = db.Column(db.String(20), default='manual', comment='查询类型: manual-手动, auto-自动, monitor-监控')
    query_source = db.Column(db.String(20), default='web', comment='查询来源: web-网页, api-接口, task-任务')
    
    # 流量数据
    total_data = db.Column(db.String(50), comment='总流量')
    used_data = db.Column(db.String(50), comment='已用流量')
    remain_data = db.Column(db.String(50), comment='剩余流量')
    free_data = db.Column(db.String(50), comment='免费流量')
    package_name = db.Column(db.String(100), comment='套餐名称')
    end_date = db.Column(db.String(20), comment='结束日期')
    
    # 对比数据 - 与上次查询的对比
    last_used_data = db.Column(db.String(50), comment='上次已用流量')
    last_free_data = db.Column(db.String(50), comment='上次免费流量')
    last_total_data = db.Column(db.String(50), comment='上次总流量')
    data_change = db.Column(db.String(50), comment='流量变化量')
    
    # 原始响应
    raw_response = db.Column(db.Text, comment='原始响应数据')
    
    # 查询状态
    query_status = db.Column(db.SmallInteger, default=1, comment='查询状态: 1-成功, 0-失败')
    error_message = db.Column(db.Text, comment='错误信息')
    query_time = db.Column(db.Numeric(5, 3), comment='查询耗时(秒)')
    
    # 缓存标识
    is_cached = db.Column(db.Boolean, default=False, comment='是否来自缓存')
    cache_key = db.Column(db.String(100), comment='缓存键')
    
    # 时间
    created_at = db.Column(db.DateTime, default=get_db_time, index=True)
    
    # 索引
    __table_args__ = (
        db.Index('idx_account_status_time', 'unicom_account_id', 'query_status', 'created_at'),
        db.Index('idx_query_type_time', 'query_type', 'created_at'),
    )
    
    def calculate_data_change(self, last_record=None):
        """计算流量变化"""
        if not last_record:
            return None
            
        try:
            current_used = float(self.used_data or 0)
            last_used = float(last_record.used_data or 0)
            change = current_used - last_used
            
            if change > 0:
                self.data_change = f"+{change:.2f}MB"
            elif change < 0:
                self.data_change = f"{change:.2f}MB"
            else:
                self.data_change = "0MB"
                
            return change
        except (ValueError, TypeError):
            return None
    
    def get_flow_summary(self):
        """获取流量摘要"""
        try:
            if self.raw_response:
                raw_data = json.loads(self.raw_response)
                return {
                    'total': self.total_data,
                    'used': self.used_data,
                    'remain': self.remain_data,
                    'free': self.free_data,
                    'package': self.package_name,
                    'end_date': self.end_date,
                    'change': self.data_change,
                    'raw_data': raw_data
                }
        except (json.JSONDecodeError, TypeError):
            pass
            
        return {
            'total': self.total_data,
            'used': self.used_data,
            'remain': self.remain_data,
            'free': self.free_data,
            'package': self.package_name,
            'end_date': self.end_date,
            'change': self.data_change
        }
    
    def is_significant_change(self, threshold_mb=10):
        """判断是否为显著变化"""
        if not self.data_change:
            return False
            
        try:
            # 提取数字部分
            change_str = self.data_change.replace('MB', '').replace('+', '')
            change_value = abs(float(change_str))
            return change_value >= threshold_mb
        except (ValueError, TypeError):
            return False
    
    def to_dict(self):
        """转换为字典"""
        from ..utils.timezone_helper import from_db_time
        return {
            'id': self.id,
            'query_type': self.query_type,
            'query_source': self.query_source,
            'total_data': self.total_data,
            'used_data': self.used_data,
            'remain_data': self.remain_data,
            'free_data': self.free_data,
            'package_name': self.package_name,
            'end_date': self.end_date,
            'last_used_data': self.last_used_data,
            'last_free_data': self.last_free_data,
            'last_total_data': self.last_total_data,
            'data_change': self.data_change,
            'query_status': self.query_status,
            'error_message': self.error_message,
            'query_time': float(self.query_time) if self.query_time else None,
            'is_cached': self.is_cached,
            'created_at': from_db_time(self.created_at).isoformat() if self.created_at else None,
            'flow_summary': self.get_flow_summary()
        }
    
    def __repr__(self):
        return f'<FlowRecord {self.unicom_account_id} {self.used_data}>'
