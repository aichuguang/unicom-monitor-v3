#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
认证管理器
"""
from flask import request, jsonify, current_app
from flask_jwt_extended import JWTManager, create_access_token, create_refresh_token, jwt_required, get_jwt_identity, get_jwt
from functools import wraps
import re
from datetime import datetime, timedelta

class AuthManager:
    """认证管理器"""
    
    def __init__(self, app=None):
        self.jwt = JWTManager()
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        self.jwt.init_app(app)
        
        # JWT错误处理
        @self.jwt.expired_token_loader
        def expired_token_callback(jwt_header, jwt_payload):
            return jsonify({
                'success': False,
                'message': '令牌已过期，请重新登录',
                'code': 'TOKEN_EXPIRED'
            }), 401
        
        @self.jwt.invalid_token_loader
        def invalid_token_callback(error):
            current_app.logger.error(f"JWT token无效: {error}")
            return jsonify({
                'success': False,
                'message': '无效的令牌',
                'code': 'TOKEN_INVALID'
            }), 401
        
        @self.jwt.unauthorized_loader
        def missing_token_callback(error):
            current_app.logger.error(f"JWT token缺失: {error}")
            return jsonify({
                'success': False,
                'message': '缺少访问令牌',
                'code': 'TOKEN_MISSING'
            }), 401
        
        @self.jwt.revoked_token_loader
        def revoked_token_callback(jwt_header, jwt_payload):
            return jsonify({
                'success': False,
                'message': '令牌已被撤销',
                'code': 'TOKEN_REVOKED'
            }), 401
    
    @staticmethod
    def validate_username(username):
        """验证用户名"""
        if not username or len(username) < 3 or len(username) > 50:
            return False, "用户名长度必须在3-50个字符之间"
        
        if not re.match(r'^[a-zA-Z0-9_]+$', username):
            return False, "用户名只能包含字母、数字和下划线"
        
        return True, ""
    
    @staticmethod
    def validate_password(password):
        """验证密码"""
        if not password or len(password) < 6:
            return False, "密码长度不能少于6个字符"
        
        if len(password) > 128:
            return False, "密码长度不能超过128个字符"
        
        # 检查密码复杂度
        has_letter = re.search(r'[a-zA-Z]', password)
        has_digit = re.search(r'\d', password)
        
        if not (has_letter and has_digit):
            return False, "密码必须包含字母和数字"
        
        return True, ""
    
    @staticmethod
    def validate_email(email):
        """验证邮箱"""
        if not email:
            return True, ""  # 邮箱可选
        
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        if not re.match(email_pattern, email):
            return False, "邮箱格式不正确"
        
        return True, ""
    
    @staticmethod
    def validate_phone(phone):
        """验证手机号"""
        if not phone:
            return False, "手机号不能为空"
        
        if not re.match(r'^1[3-9]\d{9}$', phone):
            return False, "手机号格式不正确"
        
        return True, ""
    
    @staticmethod
    def register_user(username, password, email=None, nickname=None):
        """用户注册"""
        from ..models import db, User, SystemLog
        
        try:
            # 验证输入
            valid, msg = AuthManager.validate_username(username)
            if not valid:
                return {'success': False, 'message': msg}
            
            valid, msg = AuthManager.validate_password(password)
            if not valid:
                return {'success': False, 'message': msg}
            
            if email:
                valid, msg = AuthManager.validate_email(email)
                if not valid:
                    return {'success': False, 'message': msg}
            
            # 检查用户名是否已存在
            if User.query.filter_by(username=username).first():
                return {'success': False, 'message': '用户名已存在'}
            
            # 检查邮箱是否已存在
            if email and User.query.filter_by(email=email).first():
                return {'success': False, 'message': '邮箱已被注册'}
            
            # 创建用户
            user = User(
                username=username,
                email=email,
                nickname=nickname or username
            )
            user.set_password(password)
            
            db.session.add(user)
            db.session.commit()
            
            # 记录日志
            SystemLog.log_action(
                action='user_register',
                description=f'用户 {username} 注册成功',
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                module='auth'
            )
            
            return {
                'success': True,
                'message': '注册成功',
                'data': user.to_dict()
            }
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"用户注册失败: {e}")
            return {'success': False, 'message': '注册失败，请稍后重试'}
    
    @staticmethod
    def login_user(username, password):
        """用户登录"""
        from ..models import db, User, SystemLog
        
        try:
            # 查找用户
            user = User.query.filter_by(username=username, status=1).first()
            
            if not user or not user.check_password(password):
                # 记录登录失败日志
                SystemLog.log_action(
                    action='user_login_failed',
                    description=f'用户 {username} 登录失败：用户名或密码错误',
                    ip_address=request.remote_addr,
                    user_agent=request.headers.get('User-Agent'),
                    result=0,
                    module='auth'
                )
                return {'success': False, 'message': '用户名或密码错误'}
            
            # 更新最后登录时间
            user.update_last_login()
            
            # 生成JWT令牌 (确保identity是字符串)
            access_token = create_access_token(identity=str(user.id))
            refresh_token = create_refresh_token(identity=str(user.id))
            
            # 记录登录成功日志
            SystemLog.log_action(
                action='user_login',
                description=f'用户 {username} 登录成功',
                user_id=user.id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                module='auth'
            )
            
            return {
                'success': True,
                'message': '登录成功',
                'data': {
                    'user': user.to_dict(),
                    'access_token': access_token,
                    'refresh_token': refresh_token
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"用户登录失败: {e}")
            return {'success': False, 'message': '登录失败，请稍后重试'}
    
    @staticmethod
    def refresh_token():
        """刷新访问令牌"""
        from ..models import User
        
        try:
            current_user_id = get_jwt_identity()
            # 确保user_id是整数类型
            user_id = int(current_user_id) if current_user_id else None
            user = User.query.get(user_id) if user_id else None
            
            if not user or user.status != 1:
                return {'success': False, 'message': '用户不存在或已被禁用'}
            
            # 生成新的访问令牌 (确保identity是字符串)
            new_access_token = create_access_token(identity=str(user.id))
            
            return {
                'success': True,
                'message': '令牌刷新成功',
                'data': {
                    'access_token': new_access_token
                }
            }
            
        except Exception as e:
            current_app.logger.error(f"令牌刷新失败: {e}")
            return {'success': False, 'message': '令牌刷新失败'}

def login_required(f):
    """登录装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        from ..models import User
        
        try:
            current_user_id = get_jwt_identity()
            # 确保user_id是整数类型
            user_id = int(current_user_id) if current_user_id else None
            current_user = User.query.get(user_id) if user_id else None
            
            if not current_user or current_user.status != 1:
                return jsonify({
                    'success': False,
                    'message': '用户不存在或已被禁用'
                }), 401
            
            return f(current_user, *args, **kwargs)
            
        except Exception as e:
            current_app.logger.error(f"认证检查失败: {e}")
            return jsonify({
                'success': False,
                'message': '认证失败'
            }), 401
    
    return decorated_function

def admin_required(f):
    """管理员权限装饰器"""
    @wraps(f)
    @jwt_required()
    def decorated_function(*args, **kwargs):
        try:
            from ..models.user import User

            # 获取当前用户ID
            current_user_id = get_jwt_identity()
            if not current_user_id:
                return jsonify({
                    'success': False,
                    'message': '用户未登录'
                }), 401

            # 查询用户信息 (确保user_id是整数类型)
            user_id = int(current_user_id)
            user = User.query.get(user_id)
            if not user:
                return jsonify({
                    'success': False,
                    'message': '用户不存在'
                }), 401

            # 检查管理员权限
            if not user.is_admin:
                return jsonify({
                    'success': False,
                    'message': '需要管理员权限'
                }), 403

            return f(*args, **kwargs)

        except Exception as e:
            current_app.logger.error(f"管理员权限检查失败: {e}")
            return jsonify({
                'success': False,
                'message': '权限检查失败'
            }), 500

    return decorated_function

# 创建全局实例
auth_manager = AuthManager()
