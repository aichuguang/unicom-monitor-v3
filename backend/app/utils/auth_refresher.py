#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通账号认证自动刷新工具
"""
import logging
from flask import current_app
from ..models import db

logger = logging.getLogger(__name__)

class AuthRefresher:
    """联通账号认证自动刷新器"""
    
    @staticmethod
    def auto_refresh_if_needed(unicom_account, unicom_api_instance):
        """
        自动刷新认证（如果需要）
        
        Args:
            unicom_account: 联通账号对象
            unicom_api_instance: 联通API实例
            
        Returns:
            tuple: (是否成功, 错误信息)
        """
        try:
            # 检查基本认证信息
            if not unicom_account.is_auth_valid():
                logger.warning(f"账号 {unicom_account.phone} 缺少认证信息，需要重新认证")
                return False, "账号缺少认证信息，请重新认证"
            
            # 尝试token刷新
            logger.info(f"尝试刷新账号 {unicom_account.phone} 的认证信息")
            refresh_result = unicom_api_instance.token_refresh(unicom_account)
            
            if refresh_result['success']:
                # 刷新成功，更新账号信息
                auth_data = refresh_result['data']
                
                # 更新认证信息（优先使用刷新返回的数据）
                unicom_account.app_id = auth_data.get('appId', unicom_account.app_id)
                unicom_account.token_online = auth_data.get('token_online', unicom_account.token_online)

                # ecs_token和cookies必须更新（如果返回了的话）
                if auth_data.get('ecs_token'):
                    unicom_account.ecs_token = auth_data['ecs_token']
                if auth_data.get('cookies'):
                    unicom_account.cookies = auth_data['cookies']

                logger.info(f"更新认证信息 - AppID: {unicom_account.app_id}, "
                           f"Token: {unicom_account.token_online[:20] if unicom_account.token_online else 'None'}..., "
                           f"ECS Token: {'已更新' if auth_data.get('ecs_token') else '未变更'}, "
                           f"Cookies: {'已更新' if auth_data.get('cookies') else '未变更'}")
                
                unicom_account.auth_status = 1
                unicom_account.update_refresh_info()
                
                try:
                    db.session.commit()
                    logger.info(f"账号 {unicom_account.phone} 认证刷新成功")
                    return True, "认证刷新成功"
                except Exception as e:
                    logger.error(f"保存刷新后的认证信息失败: {e}")
                    db.session.rollback()
                    return False, f"保存认证信息失败: {str(e)}"
            else:
                # 刷新失败
                error_msg = refresh_result.get('message', '未知错误')
                logger.warning(f"账号 {unicom_account.phone} 认证刷新失败: {error_msg}")
                
                # 标记认证失效
                unicom_account.auth_status = 0
                try:
                    db.session.commit()
                except Exception as e:
                    logger.error(f"更新认证状态失败: {e}")
                    db.session.rollback()
                
                return False, f"认证刷新失败: {error_msg}"
                
        except Exception as e:
            logger.error(f"认证刷新过程异常: {e}")
            return False, f"认证刷新异常: {str(e)}"
    
    @staticmethod
    def handle_auth_error(unicom_account, unicom_api_instance, original_operation=None):
        """
        处理认证错误，尝试自动刷新后重试
        
        Args:
            unicom_account: 联通账号对象
            unicom_api_instance: 联通API实例
            original_operation: 原始操作函数（可选，用于重试）
            
        Returns:
            dict: 处理结果
        """
        logger.info(f"处理账号 {unicom_account.phone} 的认证错误")
        
        # 尝试自动刷新
        refresh_success, refresh_msg = AuthRefresher.auto_refresh_if_needed(
            unicom_account, unicom_api_instance
        )
        
        if refresh_success:
            # 刷新成功，如果有原始操作则重试
            if original_operation:
                try:
                    logger.info(f"认证刷新成功，重试原始操作")
                    return original_operation()
                except Exception as e:
                    logger.error(f"重试原始操作失败: {e}")
                    return {
                        'success': False,
                        'message': f'认证刷新成功但重试操作失败: {str(e)}'
                    }
            else:
                return {
                    'success': True,
                    'message': '认证刷新成功'
                }
        else:
            # 刷新失败，需要重新认证
            return {
                'success': False,
                'message': f'认证已失效且自动刷新失败，请重新认证账号',
                'need_reauth': True,
                'refresh_error': refresh_msg
            }
    
    @staticmethod
    def is_auth_error(result):
        """
        判断是否是认证错误

        Args:
            result: API调用结果

        Returns:
            bool: 是否是认证错误
        """
        if not isinstance(result, dict):
            return False

        # 直接检查auth_error标识
        if result.get('auth_error'):
            return True

        # 检查常见的认证错误标识
        error_codes = ['999999', '999998', '1', 'AUTH_FAILED', 'TOKEN_EXPIRED', 'INVALID_TOKEN', 'LOGIN_REQUIRED']
        error_messages = ['认证失败', '认证失效', '登录失效', 'token过期', '请重新登录', '身份验证失败', '需要重新登录', '别处登录', '在别处登录']

        # 检查错误码
        if result.get('code') in error_codes:
            return True

        # 检查错误信息
        message = result.get('message', '')
        for error_msg in error_messages:
            if error_msg in message:
                return True

        return False
