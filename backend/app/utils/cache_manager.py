#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
缓存管理器
"""
import redis
import json
import pickle
from datetime import datetime, timedelta
from flask import current_app

class CacheManager:
    """缓存管理器"""

    def __init__(self, app=None):
        self.redis_client = None
        self.memory_cache = {}  # 内存缓存作为fallback
        if app is not None:
            self.init_app(app)
    
    def init_app(self, app):
        """初始化应用"""
        try:
            redis_url = app.config.get('REDIS_URL')
            redis_host = app.config.get('REDIS_HOST', 'localhost')
            redis_port = app.config.get('REDIS_PORT', 6379)
            redis_password = app.config.get('REDIS_PASSWORD')

            if redis_url:
                self.redis_client = redis.from_url(redis_url, decode_responses=False)
            else:
                self.redis_client = redis.Redis(
                    host=redis_host,
                    port=redis_port,
                    db=app.config.get('REDIS_DB', 0),
                    password=redis_password,
                    decode_responses=False
                )

            # 测试连接
            self.redis_client.ping()
            app.logger.info(f"Redis连接成功: {redis_host}:{redis_port}")

        except Exception as e:
            app.logger.warning(f"Redis连接失败: {e}")
            self.redis_client = None
    
    def ping(self):
        """检查Redis连接"""
        try:
            if self.redis_client:
                return self.redis_client.ping()
            return False
        except Exception:
            return False
    
    def is_available(self):
        """检查缓存是否可用"""
        return True  # 总是可用，因为有内存缓存fallback

    def set(self, key, value, expire=None):
        """设置缓存"""
        try:
            if self.redis_client:
                # 使用Redis缓存
                if isinstance(value, (dict, list)):
                    serialized_value = json.dumps(value, ensure_ascii=False)
                else:
                    serialized_value = pickle.dumps(value)

                if expire:
                    return self.redis_client.setex(key, expire, serialized_value)
                else:
                    return self.redis_client.set(key, serialized_value)
            else:
                # 使用内存缓存
                expire_time = None
                if expire:
                    from .timezone_helper import now
                    expire_time = now() + timedelta(seconds=expire)

                self.memory_cache[key] = {
                    'value': value,
                    'expire_time': expire_time
                }
                return True

        except Exception as e:
            current_app.logger.error(f"设置缓存失败: {e}")
            # 降级到内存缓存
            try:
                expire_time = None
                if expire:
                    from .timezone_helper import now
                    expire_time = now() + timedelta(seconds=expire)

                self.memory_cache[key] = {
                    'value': value,
                    'expire_time': expire_time
                }
                return True
            except:
                return False

    def get(self, key):
        """获取缓存"""
        try:
            if self.redis_client:
                # 从Redis获取
                value = self.redis_client.get(key)
                if value is None:
                    return None

                # 尝试JSON反序列化
                try:
                    return json.loads(value.decode('utf-8'))
                except (json.JSONDecodeError, UnicodeDecodeError):
                    # 如果JSON反序列化失败，尝试pickle
                    try:
                        return pickle.loads(value)
                    except:
                        return value.decode('utf-8') if isinstance(value, bytes) else value
            else:
                # 从内存缓存获取
                cache_item = self.memory_cache.get(key)
                if cache_item is None:
                    return None

                # 检查是否过期
                if cache_item['expire_time']:
                    from .timezone_helper import now
                    if now() > cache_item['expire_time']:
                        del self.memory_cache[key]
                        return None

                return cache_item['value']

        except Exception as e:
            current_app.logger.error(f"获取缓存失败: {e}")
            return None
    
    def delete(self, key):
        """删除缓存"""
        try:
            if self.redis_client:
                return self.redis_client.delete(key)
            else:
                # 从内存缓存删除
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
        except Exception as e:
            current_app.logger.error(f"删除缓存失败: {e}")
            # 降级到内存缓存
            try:
                if key in self.memory_cache:
                    del self.memory_cache[key]
                    return True
                return False
            except:
                return False

    def exists(self, key):
        """检查缓存是否存在"""
        try:
            if self.redis_client:
                return self.redis_client.exists(key)
            else:
                # 检查内存缓存
                cache_item = self.memory_cache.get(key)
                if cache_item is None:
                    return False

                # 检查是否过期
                if cache_item['expire_time']:
                    from .timezone_helper import now
                    if now() > cache_item['expire_time']:
                        del self.memory_cache[key]
                        return False

                return True
        except Exception as e:
            current_app.logger.error(f"检查缓存存在性失败: {e}")
            return False
    
    def expire(self, key, seconds):
        """设置缓存过期时间"""
        if not self.is_available():
            return False
        
        try:
            return self.redis_client.expire(key, seconds)
        except Exception as e:
            current_app.logger.error(f"设置缓存过期时间失败: {e}")
            return False
    
    def ttl(self, key):
        """获取缓存剩余时间"""
        if not self.is_available():
            return -1
        
        try:
            return self.redis_client.ttl(key)
        except Exception as e:
            current_app.logger.error(f"获取缓存剩余时间失败: {e}")
            return -1
    
    def keys(self, pattern='*'):
        """获取匹配的键"""
        if not self.is_available():
            return []
        
        try:
            keys = self.redis_client.keys(pattern)
            return [key.decode('utf-8') if isinstance(key, bytes) else key for key in keys]
        except Exception as e:
            current_app.logger.error(f"获取键列表失败: {e}")
            return []
    
    def clear_pattern(self, pattern):
        """清除匹配模式的缓存"""
        if not self.is_available():
            return 0
        
        try:
            keys = self.redis_client.keys(pattern)
            if keys:
                return self.redis_client.delete(*keys)
            return 0
        except Exception as e:
            current_app.logger.error(f"清除模式缓存失败: {e}")
            return 0
    
    # 流量缓存相关方法
    def get_flow_cache_key(self, unicom_account_id):
        """获取流量缓存键"""
        return f"flow_data:{unicom_account_id}"
    
    def set_flow_cache(self, unicom_account_id, flow_data, expire=None, user_id=None):
        """设置流量缓存"""
        if expire is None:
            # 优先使用用户设置的缓存时间
            if user_id:
                try:
                    from ..models.user_settings import UserSettings
                    user_settings = UserSettings.get_or_create(user_id)
                    settings_dict = user_settings.to_dict()
                    cache_ttl_minutes = settings_dict.get('cache', {}).get('cacheTtlMinutes', 10)
                    expire = cache_ttl_minutes * 60  # 转换为秒
                    current_app.logger.info(f"使用用户缓存设置: {cache_ttl_minutes}分钟 ({expire}秒)")
                except Exception as e:
                    current_app.logger.warning(f"获取用户缓存设置失败，使用默认值: {e}")
                    expire = current_app.config.get('FLOW_CACHE_EXPIRE', 600)
            else:
                expire = current_app.config.get('FLOW_CACHE_EXPIRE', 600)  # 默认10分钟

        cache_key = self.get_flow_cache_key(unicom_account_id)

        # 添加缓存时间戳
        from .timezone_helper import now as timezone_now
        current_time = timezone_now()
        cache_data = {
            'data': flow_data,
            'cached_at': current_time.isoformat(),
            'expires_at': (current_time + timedelta(seconds=expire)).isoformat()
        }

        return self.set(cache_key, cache_data, expire)
    
    def get_flow_cache(self, unicom_account_id):
        """获取流量缓存"""
        cache_key = self.get_flow_cache_key(unicom_account_id)
        return self.get(cache_key)
    
    def delete_flow_cache(self, unicom_account_id):
        """删除流量缓存"""
        cache_key = self.get_flow_cache_key(unicom_account_id)
        return self.delete(cache_key)
    
    def is_flow_cache_valid(self, unicom_account_id):
        """检查流量缓存是否有效"""
        cache_data = self.get_flow_cache(unicom_account_id)
        if not cache_data:
            return False
        
        try:
            from .timezone_helper import parse_datetime, now
            expires_at = parse_datetime(cache_data.get('expires_at', ''))
            if expires_at:
                return now() < expires_at
            return False
        except:
            return False
    
    # 频率限制相关方法
    def get_rate_limit_key(self, user_id, action):
        """获取频率限制键"""
        return f"rate_limit:{user_id}:{action}"
    
    def check_rate_limit(self, user_id, action, limit_seconds):
        """检查频率限制"""
        rate_key = self.get_rate_limit_key(user_id, action)
        
        if self.exists(rate_key):
            remaining_time = self.ttl(rate_key)
            return False, remaining_time
        
        # 设置频率限制
        from .timezone_helper import now
        self.set(rate_key, now().isoformat(), limit_seconds)
        return True, 0
    
    def clear_rate_limit(self, user_id, action):
        """清除频率限制"""
        rate_key = self.get_rate_limit_key(user_id, action)
        return self.delete(rate_key)
    
    # 监控缓存相关方法
    def get_monitor_cache_key(self, unicom_account_id):
        """获取监控缓存键"""
        return f"monitor_status:{unicom_account_id}"
    
    def set_monitor_status(self, unicom_account_id, status_data, expire=3600):
        """设置监控状态"""
        cache_key = self.get_monitor_cache_key(unicom_account_id)
        return self.set(cache_key, status_data, expire)
    
    def get_monitor_status(self, unicom_account_id):
        """获取监控状态"""
        cache_key = self.get_monitor_cache_key(unicom_account_id)
        return self.get(cache_key)

    def can_manual_refresh(self, unicom_account_id, user_id=None):
        """检查是否可以手动刷新"""
        try:
            # 获取上次手动刷新时间
            cache_key = f"manual_refresh:{unicom_account_id}"
            last_refresh = self.get(cache_key)

            if not last_refresh:
                return True

            # 获取用户的刷新冷却配置
            interval = 60  # 默认60秒
            if user_id:
                try:
                    from ..models.user_settings import UserSettings
                    user_settings = UserSettings.get_or_create(user_id)
                    settings_dict = user_settings.to_dict()
                    interval = settings_dict.get('cache', {}).get('refreshCooldownSeconds', 60)
                except Exception as e:
                    current_app.logger.warning(f"获取用户刷新配置失败，使用默认值: {e}")
                    interval = current_app.config.get('MANUAL_REFRESH_INTERVAL', 60)
            else:
                interval = current_app.config.get('MANUAL_REFRESH_INTERVAL', 60)

            # 检查是否超过限制间隔
            from .timezone_helper import parse_datetime, now
            from datetime import timedelta
            last_time = parse_datetime(last_refresh)
            if last_time:
                return now() > last_time + timedelta(seconds=interval)
            return True
        except Exception as e:
            current_app.logger.error(f"检查手动刷新限制失败: {e}")
            return True  # 出错时允许刷新

    def set_manual_refresh_time(self, unicom_account_id, user_id=None):
        """设置手动刷新时间"""
        try:
            from datetime import datetime
            cache_key = f"manual_refresh:{unicom_account_id}"

            # 获取用户的刷新冷却配置
            interval = 60  # 默认60秒
            if user_id:
                try:
                    from ..models.user_settings import UserSettings
                    user_settings = UserSettings.get_or_create(user_id)
                    settings_dict = user_settings.to_dict()
                    interval = settings_dict.get('cache', {}).get('refreshCooldownSeconds', 60)
                except Exception as e:
                    current_app.logger.warning(f"获取用户刷新配置失败，使用默认值: {e}")
                    interval = current_app.config.get('MANUAL_REFRESH_INTERVAL', 60)
            else:
                interval = current_app.config.get('MANUAL_REFRESH_INTERVAL', 60)

            from .timezone_helper import now
            self.set(cache_key, now().isoformat(), expire=interval)
        except Exception as e:
            current_app.logger.error(f"设置手动刷新时间失败: {e}")

# 创建全局实例
cache_manager = CacheManager()
