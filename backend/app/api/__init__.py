#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
API蓝图包
"""

from .auth import auth_bp
from .unicom import unicom_bp
from .flow import flow_bp
from .monitor import monitor_bp
from .admin import admin_bp
from .notify import notify_bp
from .settings import settings_bp

__all__ = [
    'auth_bp',
    'unicom_bp',
    'flow_bp',
    'monitor_bp',
    'admin_bp',
    'notify_bp',
    'settings_bp'
]
