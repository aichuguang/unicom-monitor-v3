#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流量基准模型
"""
from datetime import datetime
import json
from . import db
from ..utils.timezone_helper import get_db_time, from_db_time

class FlowBaseline(db.Model):
    """流量统计基准模型"""
    __tablename__ = 'flow_baselines'
    
    id = db.Column(db.Integer, primary_key=True)
    unicom_account_id = db.Column(db.Integer, db.ForeignKey('unicom_accounts.id'), nullable=False, index=True)
    
    # 基准时间
    baseline_time = db.Column(db.DateTime, nullable=False, index=True)
    
    # 基准流量数据
    baseline_used_data = db.Column(db.String(50), comment='基准已用流量(MB)')
    baseline_free_data = db.Column(db.String(50), comment='基准专属流量(MB)')
    baseline_total_data = db.Column(db.String(50), comment='基准总流量(MB)')
    baseline_general_data = db.Column(db.String(50), comment='基准通用流量(MB)')
    
    # 基准时的原始数据
    baseline_raw_data = db.Column(db.Text, comment='基准时的完整流量数据JSON')
    
    # 重置信息
    reset_reason = db.Column(db.String(100), default='manual', comment='重置原因')
    reset_note = db.Column(db.String(255), comment='重置备注')
    
    # 时间戳
    created_at = db.Column(db.DateTime, default=get_db_time, index=True)
    updated_at = db.Column(db.DateTime, default=get_db_time, onupdate=get_db_time)
    
    # 索引
    __table_args__ = (
        db.Index('idx_account_baseline_time', 'unicom_account_id', 'baseline_time'),
        db.Index('idx_account_created', 'unicom_account_id', 'created_at'),
    )
    
    @classmethod
    def get_latest_baseline(cls, unicom_account_id):
        """获取指定账号的最新基准"""
        return cls.query.filter_by(
            unicom_account_id=unicom_account_id
        ).order_by(cls.baseline_time.desc()).first()
    
    @classmethod
    def create_baseline(cls, unicom_account_id, flow_data, reason='manual', note=None):
        """创建新的流量基准"""
        # 解析流量数据
        general_used = 0
        free_used = 0
        
        if flow_data.get('flowSumList'):
            for item in flow_data['flowSumList']:
                if item.get('flowtype') == '1':  # 通用流量
                    general_used = float(item.get('xusedvalue', 0))
                elif item.get('flowtype') == '2':  # 专属流量
                    free_used = float(item.get('xusedvalue', 0))
        
        total_used = float(flow_data.get('allUserFlow', 0))
        
        baseline = cls(
            unicom_account_id=unicom_account_id,
            baseline_time=get_db_time(),
            baseline_used_data=str(total_used),
            baseline_free_data=str(free_used),
            baseline_general_data=str(general_used),
            baseline_total_data=str(total_used),  # 这里可以根据需要调整
            baseline_raw_data=json.dumps(flow_data, ensure_ascii=False),
            reset_reason=reason,
            reset_note=note
        )
        
        db.session.add(baseline)
        db.session.commit()
        
        return baseline
    
    def calculate_changes(self, current_flow_data):
        """计算相对于此基准的流量变化"""
        # 解析当前流量数据
        current_general = 0
        current_free = 0
        
        if current_flow_data.get('flowSumList'):
            for item in current_flow_data['flowSumList']:
                if item.get('flowtype') == '1':  # 通用流量
                    current_general = float(item.get('xusedvalue', 0))
                elif item.get('flowtype') == '2':  # 专属流量
                    current_free = float(item.get('xusedvalue', 0))
        
        current_total = float(current_flow_data.get('allUserFlow', 0))
        
        # 计算变化
        baseline_general = float(self.baseline_general_data or 0)
        baseline_free = float(self.baseline_free_data or 0)
        baseline_total = float(self.baseline_used_data or 0)
        
        changes = {
            'general_change': current_general - baseline_general,
            'free_change': current_free - baseline_free,
            'total_change': current_total - baseline_total,
            'baseline_time': from_db_time(self.baseline_time).isoformat() if self.baseline_time else None,
            'baseline_data': {
                'general': baseline_general,
                'free': baseline_free,
                'total': baseline_total
            },
            'current_data': {
                'general': current_general,
                'free': current_free,
                'total': current_total
            }
        }
        
        return changes
    
    def to_dict(self):
        """转换为字典"""
        return {
            'id': self.id,
            'unicom_account_id': self.unicom_account_id,
            'baseline_time': from_db_time(self.baseline_time).isoformat() if self.baseline_time else None,
            'baseline_used_data': self.baseline_used_data,
            'baseline_free_data': self.baseline_free_data,
            'baseline_total_data': self.baseline_total_data,
            'baseline_general_data': self.baseline_general_data,
            'reset_reason': self.reset_reason,
            'reset_note': self.reset_note,
            'created_at': from_db_time(self.created_at).isoformat() if self.created_at else None,
            'updated_at': from_db_time(self.updated_at).isoformat() if self.updated_at else None
        }
    
    def __repr__(self):
        return f'<FlowBaseline {self.unicom_account_id} {self.baseline_time}>'
