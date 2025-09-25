#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通流量监控系统 v3.0 主应用
"""
import os
import logging
import json
from flask import Flask
from flask_cors import CORS
from flask_migrate import Migrate
from sqlalchemy import inspect, text

# 导入配置和模型
from .core.config import get_config
from .models import db
from .utils.auth_manager import auth_manager
from .utils.cache_manager import cache_manager

class CustomJSONEncoder(json.JSONEncoder):
    """自定义JSON编码器，确保中文字符正确显示"""
    def __init__(self, **kwargs):
        kwargs.setdefault('ensure_ascii', False)
        super().__init__(**kwargs)

def apply_config_dict(app, config_dict):
    """应用配置字典到Flask应用"""
    # 服务器配置
    server_config = config_dict.get('server', {})
    debug_mode = server_config.get('debug', False)

    # 数据库配置（简化版，直接使用MySQL）
    db_config = config_dict.get('database', {})
    if db_config:
        # 使用远程MySQL数据库
        app.config['SQLALCHEMY_DATABASE_URI'] = (
            f"mysql+pymysql://{db_config.get('username', 'root')}:"
            f"{db_config.get('password', '')}@"
            f"{db_config.get('host', 'localhost')}:"
            f"{db_config.get('port', 3306)}/"
            f"{db_config.get('database', 'unicom_monitor')}"
        )
    else:
        # 默认使用SQLite
        app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///./data/unicom_monitor.db'

    # 安全配置
    security_config = config_dict.get('security', {})
    app.config['SECRET_KEY'] = security_config.get('secret_key', 'unicom-monitor-v3-default-secret')
    app.config['JWT_SECRET_KEY'] = security_config.get('jwt_secret', 'unicom-monitor-v3-default-jwt')

    # Redis缓存配置（简化版）
    cache_config = config_dict.get('cache', {})
    if cache_config and cache_config.get('host'):
        # 使用Redis缓存
        password = cache_config.get('password', '')
        password_part = f":{password}@" if password else ""
        app.config['REDIS_URL'] = (
            f"redis://{password_part}"
            f"{cache_config.get('host', 'localhost')}:"
            f"{cache_config.get('port', 6379)}/"
            f"{cache_config.get('db', 0)}"
        )

    # WxPusher配置
    wxpusher_config = config_dict.get('wxpusher', {})
    if wxpusher_config.get('app_token'):
        app.config['WXPUSHER_APP_TOKEN'] = wxpusher_config['app_token']

    # 其他默认配置
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = debug_mode
    app.config['MAX_UNICOM_ACCOUNTS_PER_USER'] = 5
    app.config['MANUAL_REFRESH_INTERVAL'] = 60
    app.config['AUTO_CACHE_REFRESH_INTERVAL'] = 600
    app.config['FLOW_CACHE_EXPIRE'] = 600

def create_app(config_dict=None):
    """应用工厂函数"""
    app = Flask(__name__)

    # 配置JSON编码，确保中文字符正确显示
    app.config['JSON_AS_ASCII'] = False
    app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
    app.json_encoder = CustomJSONEncoder

    # 加载配置
    if config_dict:
        # 使用传入的配置字典
        apply_config_dict(app, config_dict)
    else:
        # 使用默认配置
        config_name = os.environ.get('FLASK_ENV', 'development')
        config = get_config()
        app.config.from_object(config)

    # 配置日志
    setup_logging(app)

    # 初始化扩展
    init_extensions(app)

    # 注册蓝图
    register_blueprints(app)

    # 注册错误处理
    register_error_handlers(app)

    # 初始化数据库
    with app.app_context():
        try:
            # 检查数据库连接
            db.session.execute(text('SELECT 1'))
            app.logger.info("✅ 数据库连接成功")

            # 检查表是否存在
            inspector = inspect(db.engine)
            existing_tables = inspector.get_table_names()

            if not existing_tables:
                # 数据库为空，创建所有表
                app.logger.info("检测到空数据库，创建所有表...")
                db.create_all()
                app.logger.info("✅ 数据库表创建成功")
            else:
                app.logger.info(f"检测到已存在的表: {existing_tables}")
                # 数据库已有表，跳过创建避免权限问题
                app.logger.info("✅ 数据库表已存在，跳过创建")

            # 轻量自动迁移：为开发阶段补充 monitor_enabled 列
            try:
                if 'unicom_accounts' in existing_tables:
                    columns = [c['name'] for c in inspector.get_columns('unicom_accounts')]
                    if 'monitor_enabled' not in columns:
                        app.logger.info('🔄 自动迁移: 为 unicom_accounts 增加 monitor_enabled 列')
                        db.session.execute(text("ALTER TABLE unicom_accounts ADD COLUMN monitor_enabled TINYINT(1) DEFAULT 0 COMMENT '是否开启监控与通知'"))
                        # 某些数据库不支持 IF NOT EXISTS，这里独立捕获异常
                        try:
                            db.session.execute(text("CREATE INDEX idx_unicom_monitor_enabled ON unicom_accounts (monitor_enabled)"))
                        except Exception as ie2:
                            app.logger.warning(f"创建索引可能已存在: {ie2}")
                        db.session.commit()
                        app.logger.info("✅ 自动迁移完成")
                    else:
                        app.logger.info("✅ monitor_enabled 列已存在，跳过迁移")
            except Exception as ie:
                app.logger.warning(f"自动迁移检查失败或已存在: {ie}")

        except Exception as e:
            app.logger.error(f"❌ 数据库初始化失败: {e}")
            # 不要因为数据库初始化失败就退出应用
            # 让应用继续运行，用户可以通过健康检查接口查看具体错误

    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    #
    from .services.monitor_runner import init_monitor_scheduler
    try:
        init_monitor_scheduler(app)
    except Exception as e:
            """

        app.logger.warning(f"                                                              
            """
            app.logger.warning("初始化调度器失败: %s", e)
















































































































































































































































































































            app.logger.error(f"数据库初始化失败: {e}")

    return app

def setup_logging(app):
    """配置日志"""
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))

    # 创建日志目录
    log_file = app.config.get('LOG_FILE', 'logs/unicom_monitor_v3.log')
    log_dir = os.path.dirname(log_file)
    if log_dir and not os.path.exists(log_dir):
        os.makedirs(log_dir)

    # 配置日志格式
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler()
        ]
    )

    # 设置第三方库日志级别
    logging.getLogger('werkzeug').setLevel(logging.WARNING)
    logging.getLogger('urllib3').setLevel(logging.WARNING)

def init_extensions(app):
    """初始化扩展"""
    # 数据库
    db.init_app(app)

    # 数据库迁移
    migrate = Migrate(app, db)

    # 认证管理器
    auth_manager.init_app(app)

    # 缓存管理器
    cache_manager.init_app(app)

    # CORS - 更灵活的配置
    cors_origins = app.config.get('CORS_ORIGINS', [])

    # 从环境变量添加额外的域名
    extra_origins = os.environ.get('CORS_EXTRA_ORIGINS', '')
    if extra_origins:
        cors_origins.extend(extra_origins.split(','))

    # 如果包含通配符，则允许所有域名
    if '*' in cors_origins:
        cors_origins = True

    CORS(app,
         origins=cors_origins,
         supports_credentials=True,
         allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
         methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS', 'PATCH'],
         expose_headers=['Content-Range', 'X-Content-Range'])

def register_blueprints(app):
    """注册蓝图"""
    from .api import auth_bp, unicom_bp, flow_bp, monitor_bp, admin_bp, notify_bp, settings_bp

    # API蓝图
    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(unicom_bp, url_prefix='/api/unicom')
    app.register_blueprint(flow_bp, url_prefix='/api/flow')
    app.register_blueprint(monitor_bp, url_prefix='/api/monitor')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(notify_bp, url_prefix='/api/notify')
    app.register_blueprint(settings_bp, url_prefix='/api/settings')

    # 主页路由
    @app.route('/')
    def index():
        return {
            'success': True,
            'message': '联通流量监控系统 v3.0',
            'version': '3.0.0',
            'status': 'running'
        }

    # 健康检查
    @app.route('/health')
    def health_check():
        try:
            # 检查数据库连接
            from sqlalchemy import text
            db.session.execute(text('SELECT 1'))

            # 检查Redis连接
            redis_status = cache_manager.ping()

            return {
                'success': True,
                'message': '系统运行正常',
                'database': 'connected',
                'cache': 'connected' if redis_status else 'disconnected'
            }
        except Exception as e:
            app.logger.error(f"健康检查失败: {e}")
            return {
                'success': False,
                'message': '系统异常',
                'error': str(e)
            }, 500

def register_error_handlers(app):
    """注册错误处理"""

    @app.errorhandler(400)
    def bad_request(error):
        return {
            'success': False,
            'message': '请求参数错误',
            'error': str(error)
        }, 400

    @app.errorhandler(401)
    def unauthorized(error):
        return {
            'success': False,
            'message': '未授权访问',
            'error': str(error)
        }, 401

    @app.errorhandler(403)
    def forbidden(error):
        return {
            'success': False,
            'message': '禁止访问',
            'error': str(error)
        }, 403

    @app.errorhandler(404)
    def not_found(error):
        return {
            'success': False,
            'message': '资源不存在',
            'error': str(error)
        }, 404

    @app.errorhandler(429)
    def rate_limit_exceeded(error):
        return {
            'success': False,
            'message': '请求过于频繁，请稍后重试',
            'error': str(error)
        }, 429

    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"内部服务器错误: {error}")
        return {
            'success': False,
            'message': '内部服务器错误',
            'error': str(error)
        }, 500

    @app.errorhandler(Exception)
    def handle_exception(error):
        app.logger.error(f"未处理的异常: {error}")
        return {
            'success': False,
            'message': '系统异常',
            'error': str(error)
        }, 500
