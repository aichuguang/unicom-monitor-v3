#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通API接口类 - 基于原项目优化
集成设备指纹生成器，支持代理和缓存
"""
import requests
import time
import json
import base64
import logging
import random
from datetime import datetime
from Crypto.PublicKey import RSA
from Crypto.Cipher import PKCS1_v1_5
from flask import current_app

from ..core.config import Config
from .device_generator import device_generator
from .cache_manager import cache_manager

logger = logging.getLogger(__name__)

class UnicomAPI:
    """联通API处理类"""

    def __init__(self):
        self.session = requests.Session()
        self.public_key = Config.UNICOM_PUBLIC_KEY

        # 设置请求超时
        self.session.timeout = 30

        # 设置重试策略
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry

        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

    def rsa_encrypt(self, text):
        """RSA加密"""
        try:
            key = RSA.import_key(self.public_key)
            cipher = PKCS1_v1_5.new(key)
            encrypted = cipher.encrypt(text.encode('utf-8'))
            return base64.b64encode(encrypted).decode('utf-8')
        except Exception as e:
            logger.error(f"RSA加密失败: {e}")
            return None

    def _get_proxy_config(self, device_fingerprint):
        """获取代理配置"""
        if device_fingerprint and device_fingerprint.proxy:
            return device_fingerprint.get_proxy_config()
        return None

    def _extract_cookies(self, response):
        """从响应中提取Cookie"""
        cookies = []

        # 使用requests的原生方法获取所有cookies
        for cookie in response.cookies:
            cookies.append(f"{cookie.name}={cookie.value}")

        # 备用方法：解析Set-Cookie头
        if not cookies:
            logger.info("尝试从headers解析Cookie")
            set_cookies = []

            # 获取所有Set-Cookie头
            if hasattr(response.headers, 'get_list'):
                set_cookies = response.headers.get_list('Set-Cookie')
            else:
                for header_name, header_value in response.headers.items():
                    if header_name.lower() == 'set-cookie':
                        set_cookies.append(header_value)

            logger.info(f"找到Set-Cookie头数量: {len(set_cookies)}")

            # 解析每个Set-Cookie
            for cookie_header in set_cookies:
                cookie_part = cookie_header.split(';')[0].strip()
                if '=' in cookie_part:
                    cookies.append(cookie_part)
                    logger.info(f"提取Cookie: {cookie_part}")

        cookie_string = '; '.join(cookies)
        logger.info(f"最终Cookie: {cookie_string}")
        logger.info(f"Cookie数量: {len(cookies)}")

        return cookie_string

    def sms_login(self, unicom_account, sms_code):
        """验证码登录"""
        start_time = time.time()

        try:
            logger.info(f"开始验证码登录: {unicom_account.phone}")

            # RSA加密手机号和验证码
            encrypted_phone = self.rsa_encrypt(unicom_account.phone)
            encrypted_sms_code = self.rsa_encrypt(sms_code)

            if not encrypted_phone or not encrypted_sms_code:
                return {"success": False, "message": "加密失败，请检查输入"}

            # 获取设备指纹
            device_fingerprint = unicom_account.device_fingerprint
            if not device_fingerprint:
                return {"success": False, "message": "设备指纹未初始化"}

            # 获取代理配置
            proxies = self._get_proxy_config(device_fingerprint)

            # 构建登录参数 (使用随机AppID)
            post_data = device_fingerprint.generate_login_params(
                encrypted_phone,
                encrypted_sms_code,
                unicom_account.get_effective_app_id() or device_generator.generate_random_app_id()
            )
            # 指定为短信验证码登录样式，避免被判为密码登录
            post_data['loginStyle'] = '2'


            # 设置请求头
            headers = device_fingerprint.generate_request_headers()

            # 随机延迟避免风控
            time.sleep(random.uniform(0.5, 2.0))

            # 打印详细的请求参数
            logger.info(f"请求URL: https://m.client.10010.com/mobileService/radomLogin.htm")
            logger.info(f"请求头: {headers}")
            logger.info(f"POST数据: {post_data}")
            logger.info(f"加密后的手机号: {encrypted_phone}")
            logger.info(f"加密后的验证码: {encrypted_sms_code}")

            # 发送登录请求
            response = self.session.post(
                'https://m.client.10010.com/mobileService/radomLogin.htm',
                data=post_data,
                headers=headers,
                proxies=proxies,
                timeout=30
            )

            query_time = time.time() - start_time
            logger.info(f"登录请求完成，耗时: {query_time:.3f}秒，状态码: {response.status_code}")

            # 解析响应
            try:
                result = response.json()
                logger.info(f"登录响应: {result}")

                if result.get('code') == '0':
                    # 登录成功，提取认证信息
                    cookies_string = self._extract_cookies(response)

                    auth_data = {
                        'phone': unicom_account.phone,
                        'token_online': result.get('token_online'),
                        'ecs_token': result.get('ecs_token'),
                        'appId': result.get('appId'),
                        'cookies': cookies_string,
                        'loginTime': int(time.time()),
                        'loginMethod': 'sms',
                        'query_time': query_time
                    }

                    return {
                        "success": True,
                        "message": "验证码登录成功",
                        "data": auth_data
                    }
                else:
                    error_msg = result.get('desmobile') or result.get('dsc') or '登录失败'
                    error_code = result.get('code')

                    # 检查是否是风控错误
                    if error_code == 'ECS99999':
                        logger.warning(f"遇到风控: {result}")
                        return {
                            "success": False,
                            "message": f"账号安全验证: {error_msg}",
                            "code": error_code,
                            "risk_info": result
                        }

                    return {
                        "success": False,
                        "message": error_msg,
                        "code": error_code
                    }

            except json.JSONDecodeError as e:
                logger.error(f"登录响应解析失败: {e}, 响应内容: {response.text}")
                return {"success": False, "message": "服务器响应格式错误"}

        except requests.exceptions.RequestException as e:
            logger.error(f"网络请求失败: {e}")
            return {"success": False, "message": f"网络请求失败: {str(e)}"}
        except Exception as e:
            logger.error(f"验证码登录异常: {e}")
            return {"success": False, "message": f"登录处理失败: {str(e)}"}

    def token_refresh(self, unicom_account):
        """Token刷新登录"""
        start_time = time.time()

        try:
            logger.info(f"开始Token刷新: {unicom_account.phone}")

            if not unicom_account.token_online or not unicom_account.get_effective_app_id():
                return {"success": False, "message": "缺少Token或AppID信息"}

            # 随机延迟避免风控
            time.sleep(random.uniform(0.5, 2.0))

            # 获取设备指纹
            device_fingerprint = unicom_account.device_fingerprint
            if not device_fingerprint:
                return {"success": False, "message": "设备指纹未初始化"}

            # 获取代理配置
            proxies = self._get_proxy_config(device_fingerprint)

            # 加密手机号
            encrypted_phone = self.rsa_encrypt(unicom_account.phone)
            if not encrypted_phone:
                return {"success": False, "message": "手机号加密失败"}

            # 使用固定的密码加密数据（从成功的抓包获取）
            encrypted_password = "QsKVUpKoYExian%2Fi1qghiW6ZZrMTf5sBUYrK10sjsiKq1XgURNEvQrNasndJRW9TF4VXU1zkbfQDy5jXGQojCqHxkTUt8qNdEzUQClnSw1kHomQVPRsb%2FmDRZ96pG6rwbIi%2FlKbhoq0k2LALZaTLphRVE4j78T1XSaO%2Ba7bo5OA%3D"

            # 构建刷新参数
            post_data = device_fingerprint.generate_login_params(
                encrypted_phone,
                encrypted_password,
                unicom_account.get_effective_app_id()
            )

            # 获取请求头
            headers = device_fingerprint.generate_request_headers()

            # 发送刷新请求 (Token刷新使用login.htm)
            response = self.session.post(
                'https://m.client.10010.com/mobileService/login.htm',
                data=post_data,
                headers=headers,
                proxies=proxies,
                timeout=30
            )

            query_time = time.time() - start_time
            logger.info(f"Token刷新完成，耗时: {query_time:.3f}秒，状态码: {response.status_code}")
            logger.info(f"刷新响应: {response.text}")

            try:
                result = response.json()

                if result.get('code') == '0':
                    # 刷新成功
                    cookies_string = self._extract_cookies(response)

                    auth_data = {
                        'phone': unicom_account.phone,
                        'token_online': result.get('token_online') or unicom_account.token_online,
                        'ecs_token': result.get('ecs_token'),
                        'appId': result.get('appId') or unicom_account.get_effective_app_id(),
                        'cookies': cookies_string,
                        'loginTime': int(time.time()),
                        'loginMethod': 'token_refresh',
                        'query_time': query_time
                    }

                    return {
                        "success": True,
                        "message": "Token刷新成功",
                        "data": auth_data
                    }
                else:
                    error_msg = result.get('dsc') or '刷新失败'
                    error_code = result.get('code')

                    # 检查是否是风控错误
                    if error_code == 'ECS99999':
                        logger.warning(f"Token刷新遇到风控: {result}")
                        return {
                            "success": False,
                            "message": f"账号安全验证: {error_msg}",
                            "code": error_code,
                            "risk_info": result
                        }

                    return {
                        "success": False,
                        "message": f"Token刷新失败: {error_msg}",
                        "code": error_code
                    }

            except json.JSONDecodeError:
                logger.error(f"Token刷新响应不是JSON格式: {response.text}")
                return {"success": False, "message": "刷新响应格式错误"}

        except Exception as e:
            logger.error(f"Token刷新异常: {e}")
            return {"success": False, "message": f"Token刷新失败: {str(e)}"}

    def query_flow(self, unicom_account, use_cache=True, user_id=None):
        """查询流量信息"""
        start_time = time.time()

        try:
            logger.info(f"开始查询流量: {unicom_account.phone}")

            # 检查缓存
            if use_cache:
                cached_data = cache_manager.get_flow_cache(unicom_account.id)
                if cached_data and cache_manager.is_flow_cache_valid(unicom_account.id):
                    logger.info(f"使用缓存数据: {unicom_account.phone}")
                    # 为缓存数据添加当前查询时间
                    from .timezone_helper import now, format_local
                    current_time = now()
                    cache_flow_data = cached_data['data'].copy() if cached_data['data'] else {}
                    if cache_flow_data:
                        cache_flow_data['query_time_local'] = format_local(current_time)
                        cache_flow_data['query_time_iso'] = current_time.isoformat()

                    return {
                        "success": True,
                        "message": "流量查询成功(缓存)",
                        "data": cache_flow_data,
                        "is_cached": True,
                        "cached_at": cached_data.get('cached_at')
                    }

            # 检查认证信息
            if not unicom_account.is_auth_valid():
                return {"success": False, "message": "认证信息无效，请重新登录"}

            # 构建Cookie字符串
            cookies_dict = unicom_account.get_cookies_dict()
            if not cookies_dict:
                return {"success": False, "message": "缺少认证信息，请重新登录"}

            # 转换为Cookie字符串
            if isinstance(cookies_dict, dict):
                cookies = '; '.join([f"{k}={v}" for k, v in cookies_dict.items()])
            else:
                cookies = str(cookies_dict)

            logger.info(f"使用Cookie查询 (片段数: {len(cookies.split(';')) if cookies else 0})")

            # 获取设备指纹
            device_fingerprint = unicom_account.device_fingerprint
            if not device_fingerprint:
                return {"success": False, "message": "设备指纹未初始化"}

            # 获取代理配置
            proxies = self._get_proxy_config(device_fingerprint)

            # 设置请求头
            headers = device_fingerprint.generate_request_headers()
            headers['Cookie'] = cookies

            # 发送流量查询请求
            response = self.session.post(
                'https://m.client.10010.com/servicequerybusiness/operationservice/queryOcsPackageFlowLeftContentRevisedInJune',
                headers=headers,
                proxies=proxies,
                timeout=30
            )

            query_time = time.time() - start_time
            logger.info(f"流量查询完成，耗时: {query_time:.3f}秒，状态码: {response.status_code}")

            response_text = response.text.strip()
            logger.info(f"流量查询响应: {response_text}")

            # 检查数字错误码
            if response_text.isdigit():
                if response_text == '999999':
                    return {
                        "success": False,
                        "message": "认证失效，需要重新登录",
                        "code": "999999",
                        "auth_error": True
                    }
                elif response_text == '999998':
                    return {
                        "success": False,
                        "message": "Cookie失效，需要重新认证",
                        "code": "999998",
                        "auth_error": True
                    }
                else:
                    return {
                        "success": False,
                        "message": f"查询失败，错误码: {response_text}",
                        "code": response_text
                    }

            # 解析JSON响应
            try:
                result = response.json()

                if result.get('code') == '0000':
                    # 查询成功，缓存结果
                    if use_cache:
                        cache_manager.set_flow_cache(unicom_account.id, result, user_id=user_id)

                    return {
                        "success": True,
                        "message": "流量查询成功",
                        "data": result,
                        "is_cached": False,
                        "query_time": query_time
                    }
                else:
                    error_code = result.get('code')
                    error_msg = result.get('dsc', '流量查询失败')

                    # 检查是否是非联通用户错误
                    if error_code == 'ECS000047':
                        return {
                            "success": False,
                            "message": "此功能只针对联通号码开放，请确认您使用的是联通手机号码",
                            "code": error_code,
                            "user_error": True,  # 标记为用户错误，不是系统错误
                            "raw_response": response_text
                        }

                    # 检查是否是认证相关错误
                    auth_error_codes = ['999999', '999998', 'AUTH_FAILED', 'LOGIN_REQUIRED']
                    if error_code in auth_error_codes or '登录' in error_msg or '认证' in error_msg:
                        return {
                            "success": False,
                            "message": f"认证失效: {error_msg}",
                            "code": error_code,
                            "auth_error": True,
                            "raw_response": response_text
                        }
                    else:
                        return {
                            "success": False,
                            "message": f"流量查询失败: {error_msg}",
                            "code": error_code,
                            "raw_response": response_text
                        }

            except json.JSONDecodeError:
                if response_text == '999999':
                    return {
                        "success": False,
                        "message": "认证失效，需要重新登录",
                        "code": "999999",
                        "auth_error": True
                    }
                elif response_text == '999998':
                    return {
                        "success": False,
                        "message": "Cookie失效，需要重新认证",
                        "code": "999998",
                        "auth_error": True
                    }
                else:
                    return {
                        "success": False,
                        "message": f"响应格式错误: {response_text}",
                        "raw_response": response_text
                    }

        except Exception as e:
            logger.error(f"流量查询异常: {e}")
            return {"success": False, "message": f"流量查询失败: {str(e)}"}

# 创建全局实例
unicom_api = UnicomAPI()
