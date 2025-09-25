#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
设备指纹生成器 - 基于原项目优化
为每个手机号生成固定的设备信息，确保一致性防风控
"""
import random
import string
import hashlib
import time
from typing import Dict, Any

class DeviceGenerator:
    """设备指纹生成器"""
    
    # 设备品牌和型号映射
    DEVICE_DATA = {
        'HUAWEI': {
            'models': ['P50 Pro', 'Mate 50', 'nova 10', 'P40 Pro', 'Mate 40 Pro', 'nova 9', 'P30 Pro'],
            'os_versions': ['android12', 'android13', 'android11'],
            'builds': ['HARMONYOS3.0.0', 'EMUI12.0.0', 'EMUI11.0.0']
        },
        'XIAOMI': {
            'models': ['MI 13 Pro', 'Redmi K60', 'MI 12', 'Redmi Note 12', 'POCO F4', 'MI 11', 'Redmi K50'],
            'os_versions': ['android13', 'android12', 'android11'],
            'builds': ['MIUI14.0.1', 'MIUI13.0.5', 'MIUI12.5.8']
        },
        'OPPO': {
            'models': ['Find X6', 'Reno 9', 'A98', 'K10x', 'Find N2', 'Reno 8', 'A96'],
            'os_versions': ['android13', 'android12', 'android11'],
            'builds': ['ColorOS13.1', 'ColorOS12.1', 'ColorOS11.3']
        },
        'VIVO': {
            'models': ['X90 Pro', 'S17', 'iQOO 11', 'Y78+', 'X Fold2', 'S16', 'iQOO 9'],
            'os_versions': ['android13', 'android12', 'android11'],
            'builds': ['OriginOS3.0', 'OriginOS Ocean', 'FuntouchOS12']
        },
        'SAMSUNG': {
            'models': ['Galaxy S23', 'Galaxy A54', 'Galaxy Note20', 'Galaxy Z Fold4', 'Galaxy S22', 'Galaxy A73'],
            'os_versions': ['android13', 'android12', 'android11'],
            'builds': ['OneUI5.1', 'OneUI4.1', 'OneUI3.1']
        },
        'ONEPLUS': {
            'models': ['11 Pro', 'Nord CE 3', 'Ace 2', '10T', '9RT', '10 Pro'],
            'os_versions': ['android13', 'android12', 'android11'],
            'builds': ['OxygenOS13.1', 'OxygenOS12.1', 'ColorOS13.1']
        }
    }
    
    APP_VERSIONS = ['12.0601', '12.0701', '12.0801', '11.9901', '12.0501', '11.9801']
    
    @classmethod
    def generate_device_fingerprint(cls, phone: str) -> Dict[str, Any]:
        """
        为指定手机号生成固定的设备指纹
        使用手机号作为种子，确保每次生成的设备信息都相同
        """
        # 使用手机号作为随机种子，确保固定性
        random.seed(phone)
        
        # 选择设备品牌
        brand = random.choice(list(cls.DEVICE_DATA.keys()))
        brand_data = cls.DEVICE_DATA[brand]
        
        # 选择设备型号和系统信息
        model = random.choice(brand_data['models'])
        os_version = random.choice(brand_data['os_versions'])
        build = random.choice(brand_data['builds'])
        app_version = random.choice(cls.APP_VERSIONS)
        
        # 生成设备ID (基于手机号的MD5)
        device_id = cls._generate_device_id(phone)
        android_id = cls._generate_android_id(phone)
        unique_identifier = cls._generate_unique_identifier(phone)
        
        # 生成IP地址
        ip_address = cls._generate_ip_address(phone)
        
        # 生成时间戳
        timestamp = str(int(time.time() * 1000))
        
        # 生成User-Agent
        user_agent = cls._generate_user_agent(brand, model, os_version, app_version)
        
        # 重置随机种子
        random.seed()
        
        return {
            'device_brand': brand,
            'device_model': model,
            'device_os': os_version,
            'build_version': build,
            'app_version': app_version,
            'device_id': device_id,
            'android_id': android_id,
            'unique_identifier': unique_identifier,
            'push_platform': '1',
            'ip_address': ip_address,
            'timestamp': timestamp,
            'user_agent': user_agent
        }
    
    @classmethod
    def _generate_device_id(cls, phone: str) -> str:
        """生成设备ID"""
        # 基于手机号生成32位设备ID
        hash_obj = hashlib.md5(f"device_{phone}".encode())
        return hash_obj.hexdigest()
    
    @classmethod
    def _generate_android_id(cls, phone: str) -> str:
        """生成Android ID"""
        # 基于手机号生成16位Android ID
        hash_obj = hashlib.md5(f"android_{phone}".encode())
        return hash_obj.hexdigest()[:16]
    
    @classmethod
    def _generate_unique_identifier(cls, phone: str) -> str:
        """生成唯一标识符"""
        # 基于手机号生成唯一标识符
        hash_obj = hashlib.sha256(f"unique_{phone}".encode())
        return hash_obj.hexdigest()[:32]
    
    @classmethod
    def _generate_ip_address(cls, phone: str) -> str:
        """生成IP地址"""
        # 基于手机号生成固定的内网IP
        random.seed(phone)
        ip = f"192.168.{random.randint(1, 254)}.{random.randint(1, 254)}"
        random.seed()
        return ip
    
    @classmethod
    def _generate_user_agent(cls, brand: str, model: str, os_version: str, app_version: str) -> str:
        """生成User-Agent"""
        # 构建真实的User-Agent字符串
        android_version = os_version.replace('android', '')
        
        user_agent = (
            f"Mozilla/5.0 (Linux; Android {android_version}; {model}) "
            f"AppleWebKit/537.36 (KHTML, like Gecko) "
            f"Version/4.0 Chrome/91.0.4472.120 Mobile Safari/537.36 "
            f"unicom{{version:{app_version},desmobile:android}}"
        )
        
        return user_agent
    
    @classmethod
    def generate_request_params(cls, phone: str, encrypted_phone: str, encrypted_password: str, app_id: str) -> Dict[str, str]:
        """生成登录请求参数"""
        device_info = cls.generate_device_fingerprint(phone)
        
        return {
            'isFirstInstall': '1',
            'deviceId': device_info['device_id'],
            'pushPlatform': device_info['push_platform'],
            'password': encrypted_password,
            'pip': device_info['ip_address'],
            'appId': app_id,
            'voiceoff_flag': '1',
            'simOperator': '5,cmcc,460,01,cn@5,--,460,01,cn',
            'androidId': device_info['android_id'],
            'uniqueIdentifier': device_info['unique_identifier'],
            'timestamp': device_info['timestamp'],
            'yw_code': '',
            'loginStyle': '0',
            'deviceOS': device_info['device_os'],
            'mobile': encrypted_phone,
            'netWay': '',
            'deviceCode': device_info['device_id'],
            'isRemberPwd': 'true',
            'version': f"android@{device_info['app_version']}",
            'platformToken': 'v2-CRvjk3iX6vY96Dn6_EbWozerG6nJ206KIXJSJ7C9ttZs6tKcYH3tAw4O-g',
            'keyVersion': '',
            'provinceChanel': 'general',
            'voice_code': '',
            'deviceModel': device_info['device_model'],
            'deviceBrand': device_info['device_brand']
        }
    
    @classmethod
    def get_headers(cls, phone: str) -> Dict[str, str]:
        """获取请求头"""
        device_info = cls.generate_device_fingerprint(phone)
        
        return {
            'Content-Type': 'application/x-www-form-urlencoded',
            'User-Agent': device_info['user_agent'],
            'Origin': 'https://img.client.10010.com',
            'Referer': 'https://img.client.10010.com/',
            'X-Tingyun-Id': '4gA5HRiCw8g;c=2;r=919396103;u=20b0f1f663580aaa777224278bdec44b99c5aeb3d91d35d3c4ea1032bc583bbafd96ea06fcd7cc412b1b5c1ee52c63af::BD4E4C616020FB61',
            'X-Tingyun': 'c=A|wD9JNk4GH8w;'
        }
    
    @classmethod
    def generate_random_app_id(cls) -> str:
        """生成随机AppID（64位小写十六进制）"""
        # 按常见规范使用十六进制字符，避免超出服务端校验规则
        return ''.join(random.choices('0123456789abcdef', k=64))

    @classmethod
    def create_device_fingerprint_for_account(cls, unicom_account):
        """为联通账号创建设备指纹记录"""
        from ..models import db, DeviceFingerprint, ProxyPool

        # 生成设备信息
        device_info = cls.generate_device_fingerprint(unicom_account.phone)

        # 随机分配代理（如果有可用代理）
        proxy = ProxyPool.get_random_proxy()

        # 创建设备指纹记录
        device_fingerprint = DeviceFingerprint(
            unicom_account_id=unicom_account.id,
            device_id=device_info['device_id'],
            android_id=device_info['android_id'],
            device_brand=device_info['device_brand'],
            device_model=device_info['device_model'],
            device_os=device_info['device_os'],
            app_version=device_info['app_version'],
            push_platform=device_info['push_platform'],
            unique_identifier=device_info['unique_identifier'],
            user_agent=device_info['user_agent'],
            ip_address=device_info['ip_address'],
            proxy_id=proxy.id if proxy else None,
            timestamp=device_info['timestamp']
        )

        db.session.add(device_fingerprint)
        return device_fingerprint

# 创建全局实例
device_generator = DeviceGenerator()
