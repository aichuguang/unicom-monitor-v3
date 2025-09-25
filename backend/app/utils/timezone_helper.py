#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
时区处理工具类
统一处理项目中的时区问题，确保时间显示正确
"""
import os
from datetime import datetime, timezone, timedelta
from typing import Optional, Union
import pytz

class TimezoneHelper:
    """时区处理助手类"""
    
    # 默认时区为中国标准时间 (UTC+8)
    DEFAULT_TIMEZONE = 'Asia/Shanghai'
    
    @classmethod
    def get_timezone(cls) -> pytz.BaseTzInfo:
        """获取当前配置的时区"""
        tz_name = os.environ.get('TIMEZONE', cls.DEFAULT_TIMEZONE)
        try:
            return pytz.timezone(tz_name)
        except pytz.UnknownTimeZoneError:
            # 如果时区名称无效，使用默认时区
            return pytz.timezone(cls.DEFAULT_TIMEZONE)
    
    @classmethod
    def now(cls) -> datetime:
        """获取当前本地时间（带时区信息）"""
        tz = cls.get_timezone()
        return datetime.now(tz)
    
    @classmethod
    def utcnow(cls) -> datetime:
        """获取当前UTC时间（带时区信息）"""
        return datetime.now(timezone.utc)
    
    @classmethod
    def to_local(cls, dt: Union[datetime, str, None]) -> Optional[datetime]:
        """将时间转换为本地时区"""
        if dt is None:
            return None
            
        # 如果是字符串，先解析为datetime
        if isinstance(dt, str):
            dt = cls.parse_datetime(dt)
            if dt is None:
                return None
        
        # 如果没有时区信息，假设为UTC时间
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        # 转换为本地时区
        local_tz = cls.get_timezone()
        return dt.astimezone(local_tz)
    
    @classmethod
    def to_utc(cls, dt: Union[datetime, str, None]) -> Optional[datetime]:
        """将时间转换为UTC时区"""
        if dt is None:
            return None
            
        # 如果是字符串，先解析为datetime
        if isinstance(dt, str):
            dt = cls.parse_datetime(dt)
            if dt is None:
                return None
        
        # 如果没有时区信息，假设为本地时间
        if dt.tzinfo is None:
            local_tz = cls.get_timezone()
            dt = local_tz.localize(dt)
        
        # 转换为UTC时区
        return dt.astimezone(timezone.utc)
    
    @classmethod
    def parse_datetime(cls, dt_str: str) -> Optional[datetime]:
        """解析时间字符串为datetime对象"""
        if not dt_str:
            return None
            
        # 常见的时间格式
        formats = [
            '%Y-%m-%dT%H:%M:%S.%fZ',      # ISO格式带微秒和Z
            '%Y-%m-%dT%H:%M:%SZ',         # ISO格式带Z
            '%Y-%m-%dT%H:%M:%S.%f',       # ISO格式带微秒
            '%Y-%m-%dT%H:%M:%S',          # ISO格式
            '%Y-%m-%d %H:%M:%S.%f',       # 空格分隔带微秒
            '%Y-%m-%d %H:%M:%S',          # 空格分隔
            '%Y-%m-%d',                   # 仅日期
        ]
        
        for fmt in formats:
            try:
                dt = datetime.strptime(dt_str.strip(), fmt)
                # 如果格式包含Z，表示UTC时间
                if fmt.endswith('Z'):
                    dt = dt.replace(tzinfo=timezone.utc)
                return dt
            except ValueError:
                continue
        
        # 如果所有格式都失败，尝试使用dateutil解析
        try:
            from dateutil import parser
            return parser.parse(dt_str)
        except Exception:
            return None
    
    @classmethod
    def format_local(cls, dt: Union[datetime, str, None], fmt: str = '%Y年%m月%d日%H:%M') -> str:
        """格式化时间为本地时区字符串"""
        if dt is None:
            return '未知'
            
        local_dt = cls.to_local(dt)
        if local_dt is None:
            return '未知'
            
        return local_dt.strftime(fmt)
    
    @classmethod
    def format_relative(cls, dt: Union[datetime, str, None]) -> str:
        """格式化为相对时间（如：3分钟前）"""
        if dt is None:
            return '未知'
            
        local_dt = cls.to_local(dt)
        if local_dt is None:
            return '未知'
            
        now = cls.now()
        diff = now - local_dt
        
        if diff.total_seconds() < 60:
            return '刚刚'
        elif diff.total_seconds() < 3600:
            minutes = int(diff.total_seconds() / 60)
            return f'{minutes}分钟前'
        elif diff.total_seconds() < 86400:
            hours = int(diff.total_seconds() / 3600)
            return f'{hours}小时前'
        elif diff.days < 7:
            return f'{diff.days}天前'
        else:
            return cls.format_local(local_dt, '%m月%d日')
    
    @classmethod
    def get_db_time(cls) -> datetime:
        """获取用于数据库存储的时间（统一使用UTC）"""
        return cls.utcnow()
    
    @classmethod
    def from_db_time(cls, dt: Union[datetime, str, None]) -> Optional[datetime]:
        """从数据库时间转换为本地时间"""
        if dt is None:
            return None
            
        # 数据库时间统一按UTC处理
        if isinstance(dt, str):
            dt = cls.parse_datetime(dt)
            if dt is None:
                return None
        
        # 如果没有时区信息，假设为UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)
        
        return cls.to_local(dt)

# 创建全局实例
tz = TimezoneHelper()

# 便捷函数
def now() -> datetime:
    """获取当前本地时间"""
    return tz.now()

def utcnow() -> datetime:
    """获取当前UTC时间"""
    return tz.utcnow()

def to_local(dt: Union[datetime, str, None]) -> Optional[datetime]:
    """转换为本地时间"""
    return tz.to_local(dt)

def format_local(dt: Union[datetime, str, None], fmt: str = '%Y年%m月%d日%H:%M') -> str:
    """格式化为本地时间字符串"""
    return tz.format_local(dt, fmt)

def format_relative(dt: Union[datetime, str, None]) -> str:
    """格式化为相对时间"""
    return tz.format_relative(dt)

def get_db_time() -> datetime:
    """获取数据库时间"""
    return tz.get_db_time()

def from_db_time(dt: Union[datetime, str, None]) -> Optional[datetime]:
    """从数据库时间转换"""
    return tz.from_db_time(dt)

def parse_datetime(dt_str: str) -> Optional[datetime]:
    """解析时间字符串"""
    return tz.parse_datetime(dt_str)
