#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
数据模型包
"""
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()

# 导入所有模型
from .user import User
from .unicom_account import UnicomAccount
from .device_fingerprint import DeviceFingerprint
from .flow_record import FlowRecord
from .flow_baseline import FlowBaseline
from .monitor_config import MonitorConfig
from .proxy_pool import ProxyPool
from .system_log import SystemLog
from .user_settings import UserSettings

__all__ = [
    'db',
    'User',
    'UnicomAccount',
    'DeviceFingerprint',
    'FlowRecord',
    'MonitorConfig',
    'ProxyPool',
    'SystemLog',
    'UserSettings'
]
