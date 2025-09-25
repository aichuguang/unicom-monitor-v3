#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
应用配置文件
"""
import os
from datetime import timedelta
from dotenv import load_dotenv
from pathlib import Path

# 加载环境变量（同时尝试项目根目录默认 .env 与 backend/.env）
load_dotenv()  # 默认当前工作目录
BASE_DIR = Path(__file__).resolve().parents[2]  # backend 目录
load_dotenv(BASE_DIR / '.env')  # 明确加载 backend/.env

class Config:
    """基础配置"""

    # 应用配置
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'unicom-monitor-v3-secret-key-2025'
    DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

    # 数据库配置
    MYSQL_HOST = os.environ.get('MYSQL_HOST') or '127.0.0.1
    MYSQL_PORT = int(os.environ.get('MYSQL_PORT') or 3306)
    MYSQL_USER = os.environ.get('MYSQL_USER') or 'chinaunicom'
    MYSQL_PASSWORD = os.environ.get('MYSQL_PASSWORD') or 'tkYKDbpz6MSdSAaF'
    MYSQL_DATABASE = os.environ.get('MYSQL_DATABASE') or 'chinaunicom'

    # 构建数据库连接URI
    SQLALCHEMY_DATABASE_URI = f'mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DATABASE}?charset=utf8mb4'
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        'pool_recycle': 3600,
        'pool_pre_ping': True,
        'pool_size': 10,
        'max_overflow': 20
    }

    # Redis配置
    REDIS_HOST = os.environ.get('REDIS_HOST') or '127.0.0.1
    REDIS_PORT = int(os.environ.get('REDIS_PORT') or 6379)
    REDIS_DB = int(os.environ.get('REDIS_DB') or 0)
    REDIS_PASSWORD = os.environ.get('REDIS_PASSWORD') or 'redis_PDkScA'
    REDIS_URL = f'redis://:{REDIS_PASSWORD}@{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}' if REDIS_PASSWORD else f'redis://{REDIS_HOST}:{REDIS_PORT}/{REDIS_DB}'

    # JWT配置
    JWT_SECRET_KEY = SECRET_KEY
    JWT_ACCESS_TOKEN_EXPIRES = timedelta(hours=24)
    JWT_REFRESH_TOKEN_EXPIRES = timedelta(days=30)

    # 联通API配置
    UNICOM_PUBLIC_KEY = """-----BEGIN PUBLIC KEY-----
MIGfMA0GCSqGSIb3DQEBAQUAA4GNADCBiQKBgQDc+CZK9bBA9IU+gZUOc6FUGu7y
O9WpTNB0PzmgFBh96Mg1WrovD1oqZ+eIF4LjvxKXGOdI79JRdve9NPhQo07+uqGQ
gE4imwNnRx7PFtCRryiIEcUoavuNtuRVoBAm6qdB0SrctgaqGfLgKvZHOnwTjyNq
jBUxzMeQlEC2czEMSwIDAQAB
-----END PUBLIC KEY-----"""

    # 业务配置
    MAX_UNICOM_ACCOUNTS_PER_USER = 5  # 每个用户最多联通账号数量
    MIN_MONITOR_INTERVAL = 60   # 最小监控间隔(秒) - 1分钟
    MAX_MONITOR_INTERVAL = 7200 # 最大监控间隔(秒) - 2小时
    MANUAL_REFRESH_INTERVAL = 60  # 手动刷新间隔(秒) - 1分钟
    AUTO_CACHE_REFRESH_INTERVAL = 600  # 自动缓存刷新间隔(秒) - 10分钟


    # 调度配置
    ENABLE_SCHEDULER = os.environ.get('ENABLE_SCHEDULER', 'false').lower() == 'true'
    NOTIFICATION_MIN_INTERVAL_DEFAULT = int(os.environ.get('NOTIFICATION_MIN_INTERVAL', 600))

    # 缓存配置
    FLOW_CACHE_EXPIRE = 600  # 流量缓存过期时间(秒) - 10分钟

    # 日志配置
    LOG_LEVEL = os.environ.get('LOG_LEVEL', 'INFO')
    LOG_FILE = os.environ.get('LOG_FILE', 'logs/unicom_monitor_v3.log')

    # CORS配置
    CORS_ORIGINS = [
        'http://localhost:3000',
        'http://localhost:5173',
        'http://localhost:8080',
        'http://127.0.0.1:3000',
        'http://127.0.0.1:5173',
        'http://127.0.0.1:8080',
    ]

    # 代理配置
    ENABLE_PROXY = os.environ.get('ENABLE_PROXY', 'False').lower() == 'true'
    PROXY_POOL_SIZE = int(os.environ.get('PROXY_POOL_SIZE', 10))

    # 第三方通知配置
    WXPUSHER_APP_TOKEN = os.environ.get('WXPUSHER_APP_TOKEN', '')

class DevelopmentConfig(Config):
    """开发环境配置"""
    DEBUG = True
    TESTING = False

class ProductionConfig(Config):
    """生产环境配置"""
    DEBUG = False
    TESTING = False

class TestingConfig(Config):
    """测试环境配置"""
    DEBUG = True
    TESTING = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'

# 配置字典
config_dict = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'testing': TestingConfig,
    'default': DevelopmentConfig
}

def get_config():
    """获取当前配置"""
    env = os.environ.get('FLASK_ENV', 'development')
    return config_dict.get(env, DevelopmentConfig)
