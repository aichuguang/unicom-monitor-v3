#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
流量查询API蓝图
"""
from flask import Blueprint, request, jsonify, current_app, session
from datetime import datetime, timedelta
import time
import json
import logging

from ..utils.auth_manager import login_required
from ..utils.unicom_api import unicom_api
from ..utils.cache_manager import cache_manager
from ..models import db, UnicomAccount, FlowRecord, FlowBaseline, SystemLog, User

flow_bp = Blueprint('flow', __name__)
logger = logging.getLogger(__name__)

@flow_bp.route('/query/<int:account_id>', methods=['GET'])
@login_required
def query_flow(current_user, account_id):
    """查询指定账号的流量信息"""
    try:
        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()
        
        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404
        
        # 检查基本认证信息
        if not unicom_account.is_auth_valid():
            return jsonify({
                'success': False,
                'message': '账号缺少认证信息，请重新认证',
                'need_refresh': True
            }), 401
        
        # 检查手动刷新频率限制
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        force_refresh = request.args.get('force_refresh', 'false').lower() == 'true'

        if force_refresh and not cache_manager.can_manual_refresh(account_id, current_user.id):
            # 获取用户的刷新冷却配置来显示准确的等待时间
            try:
                from ..models.user_settings import UserSettings
                user_settings = UserSettings.get_or_create(current_user.id)
                settings_dict = user_settings.to_dict()
                cooldown_seconds = settings_dict.get('cache', {}).get('refreshCooldownSeconds', 60)
            except Exception:
                cooldown_seconds = current_app.config.get('MANUAL_REFRESH_INTERVAL', 60)

            return jsonify({
                'success': False,
                'message': f'手动刷新限制：{cooldown_seconds}秒内只能刷新1次',
                'code': 'RATE_LIMITED'
            }), 429

        # 如果强制刷新，则不使用缓存
        if force_refresh:
            use_cache = False
            cache_manager.set_manual_refresh_time(account_id, current_user.id)
        
        # 调用联通API查询
        result = unicom_api.query_flow(unicom_account, use_cache=use_cache, user_id=current_user.id)

        # 如果是认证错误，尝试自动刷新后重试
        from ..utils.auth_refresher import AuthRefresher
        if not result['success'] and AuthRefresher.is_auth_error(result):
            logger.info(f"检测到认证错误，尝试自动刷新账号 {unicom_account.phone} 的认证")

            # 定义重试操作
            def retry_query():
                return unicom_api.query_flow(unicom_account, use_cache=use_cache, user_id=current_user.id)

            # 处理认证错误（自动刷新并重试）
            auth_result = AuthRefresher.handle_auth_error(
                unicom_account, unicom_api, retry_query
            )

            if not auth_result['success']:
                # 自动刷新失败，返回错误
                return jsonify({
                    'success': False,
                    'message': auth_result['message'],
                    'need_refresh': auth_result.get('need_reauth', False)
                }), 401
            else:
                # 自动刷新成功，使用重试结果
                result = auth_result if 'data' in auth_result else retry_query()
        
        if result['success']:
            # 获取上次查询记录用于对比（排除当前可能正在创建的记录）
            last_record = FlowRecord.query.filter_by(
                unicom_account_id=account_id
            ).order_by(FlowRecord.created_at.desc()).first()

            from ..utils.timezone_helper import from_db_time
            last_record_time = from_db_time(last_record.created_at) if last_record else None
            logger.info(f"查询对比数据 - 账号ID: {account_id}, 上次记录: {last_record.id if last_record else None}, 创建时间: {last_record_time}")

            # 保存流量记录
            flow_data = result['data']

            # 解析流量信息
            flow_info = _parse_flow_data(flow_data)

            # 创建流量记录（使用新的解析结果）
            flow_record = FlowRecord(
                unicom_account_id=account_id,
                total_data=flow_info.get('total_flow', '0'),
                used_data=flow_info.get('used_flow', '0'),  # 使用总已用流量
                remain_data=flow_info.get('remaining_flow', '0'),
                free_data=flow_info.get('used_special', '0'),  # 专属流量使用量
                package_name=flow_info.get('package_name', ''),
                # 新增分类流量字段
                used_general=flow_info.get('used_general', '0'),
                used_special=flow_info.get('used_special', '0'),
                used_other=flow_info.get('used_other', '0'),
                remain_general=flow_info.get('remain_general', '0'),
                remain_special=flow_info.get('remain_special', '0'),
                remain_other=flow_info.get('remain_other', '0'),
                raw_response=json.dumps(flow_data, ensure_ascii=False, separators=(',', ':')) if flow_data else None,
                is_cached=result.get('is_cached', False),
                query_time=result.get('query_time', 0),
                # 记录上次查询的数据用于对比
                last_used_data=last_record.used_data if last_record else None,
                last_free_data=last_record.free_data if last_record else None,
                last_total_data=last_record.total_data if last_record else None
            )

            # 计算流量变化
            if last_record:
                change = flow_record.calculate_data_change(last_record)
                logger.info(f"流量变化计算 - 当前: {flow_record.used_data}, 上次: {last_record.used_data}, 变化: {change}, 变化文本: {flow_record.data_change}")
            else:
                logger.info("没有上次记录，无法计算变化")

            db.session.add(flow_record)
            db.session.commit()

            # 获取基准数据并计算基准变化
            baseline = FlowBaseline.get_latest_baseline(account_id)
            baseline_changes = None

            if baseline:
                baseline_changes = baseline.calculate_changes(flow_data)
                from ..utils.timezone_helper import from_db_time
                baseline_local_time = from_db_time(baseline.baseline_time)
                logger.info(f"基准变化计算 - 基准时间: {baseline_local_time}, 变化: {baseline_changes}")
            else:
                # 首次查询，自动创建基准
                baseline = FlowBaseline.create_baseline(
                    unicom_account_id=account_id,
                    flow_data=flow_data,
                    reason='auto',
                    note='首次查询自动创建基准'
                )
                # 首次创建基准时，变化量应该为0
                baseline_changes = {
                    'general_change': 0.0,
                    'free_change': 0.0,
                    'total_change': 0.0,
                    'baseline_time': baseline.baseline_time.isoformat(),
                    'baseline_data': {
                        'general': float(baseline.baseline_general_data or 0),
                        'free': float(baseline.baseline_free_data or 0),
                        'total': float(baseline.baseline_used_data or 0)
                    },
                    'current_data': {
                        'general': float(baseline.baseline_general_data or 0),
                        'free': float(baseline.baseline_free_data or 0),
                        'total': float(baseline.baseline_used_data or 0)
                    }
                }
                logger.info(f"首次查询创建基准 - 基准ID: {baseline.id}, 所有变化设为0")

            # 记录查询日志
            SystemLog.log_action(
                action='flow_query',
                description=f'查询流量 {unicom_account.phone} ({"缓存" if result.get("is_cached") else "实时"})',
                user_id=current_user.id,
                unicom_account_id=account_id,
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent'),
                module='flow'
            )
            
            # 添加正确的查询时间到raw_data
            from ..utils.timezone_helper import now, format_local
            current_time = now()
            if flow_data:
                flow_data['query_time_local'] = format_local(current_time)
                flow_data['query_time_iso'] = current_time.isoformat()

            return jsonify({
                'success': True,
                'message': '流量查询成功',
                'data': {
                    'account_info': {
                        'id': unicom_account.id,
                        'phone': unicom_account.phone,
                        'phone_alias': unicom_account.phone_alias
                    },
                    'flow_info': flow_info,
                    'raw_data': flow_data,
                    'is_cached': result.get('is_cached', False),
                    'cached_at': result.get('cached_at'),
                    'query_time': result.get('query_time', 0),
                    'record_id': flow_record.id,
                    # 添加对比数据
                    'comparison': {
                        'last_used_data': flow_record.last_used_data,
                        'last_free_data': flow_record.last_free_data,
                        'last_total_data': flow_record.last_total_data,
                        'data_change': flow_record.data_change,
                        'last_query_time': from_db_time(last_record.created_at).isoformat() if last_record else None,
                        'has_previous_data': last_record is not None
                    },
                    # 添加基准变化数据
                    'baseline_changes': baseline_changes,
                    # 新增分类流量数据供前端使用
                    'flow_summary': {
                        'used_general': flow_info.get('used_general', '0'),
                        'used_special': flow_info.get('used_special', '0'),
                        'used_other': flow_info.get('used_other', '0'),
                        'remain_general': flow_info.get('remain_general', '0'),
                        'remain_special': flow_info.get('remain_special', '0'),
                        'remain_other': flow_info.get('remain_other', '0'),
                        'extra_packages': flow_info.get('extra_packages', [])
                    }
                }
            })

            # 记录对比数据日志
            comparison_data = {
                'last_used_data': flow_record.last_used_data,
                'last_free_data': flow_record.last_free_data,
                'data_change': flow_record.data_change,
                'has_previous_data': last_record is not None
            }
            logger.info(f"返回对比数据: {comparison_data}")
        else:
            # 检查是否需要刷新认证
            if result.get('need_refresh') or result.get('code') == '999999':
                return jsonify({
                    'success': False,
                    'message': '认证已过期，请刷新认证或重新登录',
                    'need_refresh': True,
                    'code': result.get('code')
                }), 401
            
            return jsonify(result), 400
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"查询流量异常: {e}")
        return jsonify({'success': False, 'message': '查询流量失败'}), 500

@flow_bp.route('/query-all', methods=['GET'])
@login_required
def query_all_flows(current_user):
    """查询用户所有账号的流量信息"""
    try:
        # 获取用户所有有效的联通账号
        accounts = UnicomAccount.query.filter_by(
            user_id=current_user.id,
            status=1
        ).all()
        
        if not accounts:
            return jsonify({
                'success': True,
                'message': '暂无联通账号',
                'data': []
            })
        
        results = []
        use_cache = request.args.get('use_cache', 'true').lower() == 'true'
        
        for account in accounts:
            try:
                # 检查认证状态
                if not account.is_auth_valid():
                    results.append({
                        'account_id': account.id,
                        'phone': account.phone,
                        'phone_alias': account.phone_alias,
                        'success': False,
                        'message': '认证已过期',
                        'need_refresh': True
                    })
                    continue
                
                # 查询流量
                result = unicom_api.query_flow(account, use_cache=use_cache, user_id=current_user.id)
                
                if result['success']:
                    # 获取上次查询记录用于对比
                    last_record = FlowRecord.query.filter_by(
                        unicom_account_id=account.id
                    ).order_by(FlowRecord.created_at.desc()).first()

                    flow_data = result['data']
                    flow_info = _parse_flow_data(flow_data)

                    # 创建流量记录（使用新的解析结果）
                    flow_record = FlowRecord(
                        unicom_account_id=account.id,
                        total_data=flow_info.get('total_flow', '0'),
                        used_data=flow_info.get('used_flow', '0'),  # 使用总已用流量
                        remain_data=flow_info.get('remaining_flow', '0'),
                        free_data=flow_info.get('used_special', '0'),  # 专属流量使用量
                        package_name=flow_info.get('package_name', ''),
                        # 新增分类流量字段
                        used_general=flow_info.get('used_general', '0'),
                        used_special=flow_info.get('used_special', '0'),
                        used_other=flow_info.get('used_other', '0'),
                        remain_general=flow_info.get('remain_general', '0'),
                        remain_special=flow_info.get('remain_special', '0'),
                        remain_other=flow_info.get('remain_other', '0'),
                        raw_response=json.dumps(flow_data, ensure_ascii=False, separators=(',', ':')) if flow_data else None,
                        is_cached=result.get('is_cached', False),
                        query_time=result.get('query_time', 0),
                        # 记录上次查询的数据用于对比
                        last_used_data=last_record.used_data if last_record else None,
                        last_free_data=last_record.free_data if last_record else None,
                        last_total_data=last_record.total_data if last_record else None
                    )

                    # 计算流量变化
                    if last_record:
                        flow_record.calculate_data_change(last_record)

                    db.session.add(flow_record)
                    
                    results.append({
                        'account_id': account.id,
                        'phone': account.phone,
                        'phone_alias': account.phone_alias,
                        'success': True,
                        'flow_info': flow_info,
                        'is_cached': result.get('is_cached', False),
                        'cached_at': result.get('cached_at'),
                        'query_time': result.get('query_time', 0),
                        'record_id': flow_record.id,
                        # 添加对比数据
                        'comparison': {
                            'last_used_data': flow_record.last_used_data,
                            'last_free_data': flow_record.last_free_data,
                            'last_total_data': flow_record.last_total_data,
                            'data_change': flow_record.data_change,
                            'last_query_time': last_record.created_at.isoformat() if last_record else None,
                            'has_previous_data': last_record is not None
                        }
                    })
                else:
                    results.append({
                        'account_id': account.id,
                        'phone': account.phone,
                        'phone_alias': account.phone_alias,
                        'success': False,
                        'message': result.get('message'),
                        'need_refresh': result.get('need_refresh', False),
                        'code': result.get('code')
                    })
                    
            except Exception as e:
                current_app.logger.error(f"查询账号 {account.phone} 流量异常: {e}")
                results.append({
                    'account_id': account.id,
                    'phone': account.phone,
                    'phone_alias': account.phone_alias,
                    'success': False,
                    'message': f'查询失败: {str(e)}'
                })
        
        db.session.commit()
        
        # 统计结果
        success_count = sum(1 for r in results if r['success'])
        total_count = len(results)
        
        return jsonify({
            'success': True,
            'message': f'批量查询完成，成功 {success_count}/{total_count}',
            'data': results,
            'summary': {
                'total_count': total_count,
                'success_count': success_count,
                'failed_count': total_count - success_count
            }
        })
        
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"批量查询流量异常: {e}")
        return jsonify({'success': False, 'message': '批量查询流量失败'}), 500

@flow_bp.route('/history/<int:account_id>', methods=['GET'])
@login_required
def get_flow_history(current_user, account_id):
    """获取指定账号的流量历史记录"""
    try:
        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()
        
        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404
        
        # 获取查询参数
        page = request.args.get('page', 1, type=int)
        per_page = min(request.args.get('per_page', 20, type=int), 100)
        days = request.args.get('days', 7, type=int)
        
        # 计算时间范围
        from ..utils.timezone_helper import get_db_time
        end_date = get_db_time()
        start_date = end_date - timedelta(days=days)
        
        # 查询流量记录
        query = FlowRecord.query.filter(
            FlowRecord.unicom_account_id == account_id,
            FlowRecord.created_at >= start_date
        ).order_by(FlowRecord.created_at.desc())
        
        pagination = query.paginate(
            page=page,
            per_page=per_page,
            error_out=False
        )
        
        records = [record.to_dict() for record in pagination.items]
        
        return jsonify({
            'success': True,
            'data': {
                'records': records,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total': pagination.total,
                    'pages': pagination.pages,
                    'has_prev': pagination.has_prev,
                    'has_next': pagination.has_next
                },
                'account_info': {
                    'id': unicom_account.id,
                    'phone': unicom_account.phone,
                    'phone_alias': unicom_account.phone_alias
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取流量历史异常: {e}")
        return jsonify({'success': False, 'message': '获取流量历史失败'}), 500

@flow_bp.route('/statistics/<int:account_id>', methods=['GET'])
@login_required
def get_flow_statistics(current_user, account_id):
    """获取指定账号的流量统计信息"""
    try:
        # 查找账号
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id,
            status=1
        ).first()
        
        if not unicom_account:
            return jsonify({'success': False, 'message': '联通账号不存在'}), 404
        
        # 获取查询参数
        days = request.args.get('days', 30, type=int)
        
        # 计算时间范围
        from ..utils.timezone_helper import get_db_time
        end_date = get_db_time()
        start_date = end_date - timedelta(days=days)
        
        # 查询统计数据
        records = FlowRecord.query.filter(
            FlowRecord.unicom_account_id == account_id,
            FlowRecord.created_at >= start_date
        ).order_by(FlowRecord.created_at.asc()).all()
        
        if not records:
            return jsonify({
                'success': True,
                'data': {
                    'account_info': {
                        'id': unicom_account.id,
                        'phone': unicom_account.phone,
                        'phone_alias': unicom_account.phone_alias
                    },
                    'statistics': {
                        'total_queries': 0,
                        'avg_usage_percentage': 0,
                        'max_usage_percentage': 0,
                        'min_usage_percentage': 0,
                        'trend_data': []
                    }
                }
            })
        
        # 计算统计信息
        total_queries = len(records)
        usage_percentages = [r.usage_percentage for r in records if r.usage_percentage is not None]
        
        avg_usage = sum(usage_percentages) / len(usage_percentages) if usage_percentages else 0
        max_usage = max(usage_percentages) if usage_percentages else 0
        min_usage = min(usage_percentages) if usage_percentages else 0
        
        # 生成趋势数据（按天聚合）
        trend_data = []
        current_date = start_date.date()
        
        while current_date <= end_date.date():
            day_records = [r for r in records if r.created_at.date() == current_date]
            
            if day_records:
                # 取当天最后一条记录
                latest_record = max(day_records, key=lambda x: x.created_at)
                trend_data.append({
                    'date': current_date.isoformat(),
                    'total_flow': latest_record.total_flow,
                    'used_flow': latest_record.used_flow,
                    'remaining_flow': latest_record.remaining_flow,
                    'usage_percentage': latest_record.usage_percentage,
                    'query_count': len(day_records)
                })
            
            current_date += timedelta(days=1)
        
        return jsonify({
            'success': True,
            'data': {
                'account_info': {
                    'id': unicom_account.id,
                    'phone': unicom_account.phone,
                    'phone_alias': unicom_account.phone_alias
                },
                'statistics': {
                    'total_queries': total_queries,
                    'avg_usage_percentage': round(avg_usage, 2),
                    'max_usage_percentage': round(max_usage, 2),
                    'min_usage_percentage': round(min_usage, 2),
                    'trend_data': trend_data,
                    'date_range': {
                        'start_date': start_date.date().isoformat(),
                        'end_date': end_date.date().isoformat(),
                        'days': days
                    }
                }
            }
        })
        
    except Exception as e:
        current_app.logger.error(f"获取流量统计异常: {e}")
        return jsonify({'success': False, 'message': '获取流量统计失败'}), 500

def _parse_flow_data(flow_data):
    """解析流量数据 - 兼容所有联通API响应格式"""
    try:
        # 根据联通API响应格式解析
        if not flow_data:
            return {
                'total_flow': '0',
                'used_flow': '0',
                'remaining_flow': '0',
                'usage_percentage': 0,
                'flow_packages': [],
                'extra_packages': [],
                'package_name': '',
                'used_general': '0',
                'used_special': '0',
                'used_other': '0',
                'remain_general': '0',
                'remain_special': '0',
                'remain_other': '0'
            }

        # 基础流量信息
        total_flow = flow_data.get('sum', '0')  # 总流量
        used_flow = flow_data.get('allUserFlow', '0')  # 已用流量

        # 剩余流量：优先canUseFlowAll，备选canUseValueAll
        remaining_flow = flow_data.get('canUseFlowAll') or flow_data.get('canUseValueAll', '0')

        # 套餐名称：优先packageName，备选从unshared中提取
        package_name = flow_data.get('packageName', '')

        # 从flowSumList提取分类使用量和剩余量
        used_general = '0'
        used_special = '0'
        used_other = '0'
        remain_general = '0'
        remain_special = '0'
        remain_other = '0'

        flow_sum_list = flow_data.get('flowSumList', [])
        for item in flow_sum_list:
            flow_type = str(item.get('flowtype', '')).strip()
            used_value = str(item.get('xusedvalue', '0'))
            remain_value = str(item.get('xcanusevalue', '0'))

            if flow_type == '1':  # 通用流量
                used_general = used_value
                remain_general = remain_value
            elif flow_type == '2':  # 专用流量
                used_special = used_value
                remain_special = remain_value
            elif flow_type == '3':  # 其他流量
                used_other = used_value
                remain_other = remain_value

        # 解析流量包详情
        flow_packages = []
        extra_packages = []

        # 方法1：从resources提取流量包
        resources = flow_data.get('resources', [])
        if resources:
            for resource in resources:
                if resource.get('type') == 'flow' and resource.get('details'):
                    for detail in resource['details']:
                        # 处理无限量流量包（total为0或空的情况）
                        total_value = detail.get('total', '0')
                        used_value = detail.get('use', '0')
                        remain_value = detail.get('remain', '0')

                        # 识别无限量流量包
                        is_unlimited = False
                        try:
                            # 情况1: total为0或空，且有使用量
                            if (not total_value or float(total_value) == 0) and used_value and float(used_value) > 0:
                                is_unlimited = True
                            # 情况2: remain为负数或异常大的情况（可能是无限量）
                            elif remain_value and float(remain_value) < 0:
                                is_unlimited = True
                        except (ValueError, TypeError):
                            pass

                        package_info = {
                            'name': detail.get('addUpItemName') or detail.get('feePolicyName', '流量包'),
                            'total': total_value if not is_unlimited else 'unlimited',
                            'used': used_value,
                            'remaining': remain_value if not is_unlimited else 'unlimited',
                            'unit': 'MB',
                            'type': detail.get('flowType', '1'),
                            'end_date': detail.get('endDate', ''),
                            'used_percent': detail.get('usedPercent', '0'),
                            'source': 'resources',
                            'is_unlimited': is_unlimited
                        }
                        flow_packages.append(package_info)

                        # 如果没有套餐名称，从主要流量包中提取
                        if not package_name and detail.get('feePolicyName'):
                            package_name = detail['feePolicyName']

        # 方法2：从unshared提取流量包（如果resources为空或无详情）
        if not flow_packages:
            unshared = flow_data.get('unshared', [])
            for item in unshared:
                if item.get('type') == 'unsharedFlowList' and item.get('details'):
                    for detail in item['details']:
                        # 处理无限量流量包（total为0或空的情况）
                        total_value = detail.get('total', '0')
                        used_value = detail.get('use', '0')
                        remain_value = detail.get('remain', '0')

                        # 识别无限量流量包
                        is_unlimited = False
                        try:
                            # 情况1: total为0或空，且有使用量
                            if (not total_value or float(total_value) == 0) and used_value and float(used_value) > 0:
                                is_unlimited = True
                            # 情况2: remain为负数或异常大的情况（可能是无限量）
                            elif remain_value and float(remain_value) < 0:
                                is_unlimited = True
                        except (ValueError, TypeError):
                            pass

                        package_info = {
                            'name': detail.get('addUpItemName') or detail.get('feePolicyName', '流量包'),
                            'total': total_value if not is_unlimited else 'unlimited',
                            'used': used_value,
                            'remaining': remain_value if not is_unlimited else 'unlimited',
                            'unit': 'MB',
                            'type': detail.get('flowType', '1'),
                            'end_date': detail.get('endDate', ''),
                            'used_percent': detail.get('usedPercent', '0'),
                            'source': 'unshared',
                            'is_unlimited': is_unlimited
                        }
                        flow_packages.append(package_info)

                        # 提取套餐名称（优先主套餐）
                        if not package_name and detail.get('feePolicyName'):
                            if '大王卡' in detail['feePolicyName'] or detail.get('flowType') == '2':
                                package_name = detail['feePolicyName']

        # 解析套外流量包 (TwResources)
        tw_resources = flow_data.get('TwResources', [])
        for tw_resource in tw_resources:
            if tw_resource.get('type') == 'flow' and tw_resource.get('details'):
                for detail in tw_resource['details']:
                    # 处理无限量流量包（total为0或空的情况）
                    total_value = detail.get('total', '0')
                    used_value = detail.get('use', '0')
                    remain_value = detail.get('remain', '0')

                    # 识别无限量流量包的多种情况
                    is_unlimited = False
                    try:
                        # 情况1: total为0或空，且有使用量
                        if (not total_value or float(total_value) == 0) and used_value and float(used_value) > 0:
                            is_unlimited = True
                        # 情况2: 包名包含"专享"、"免费"、"大王卡"等关键词，且没有明确总量
                        elif detail.get('addUpItemName') and any(keyword in detail.get('addUpItemName', '') for keyword in ['专享', '免费', '大王卡', '定向']):
                            if not total_value or float(total_value) == 0:
                                is_unlimited = True
                        # 情况3: remain为负数或异常大的情况（可能是无限量）
                        elif remain_value and float(remain_value) < 0:
                            is_unlimited = True
                    except (ValueError, TypeError):
                        pass

                    extra_info = {
                        'name': detail.get('addUpItemName', '套外流量包'),
                        'total': total_value if not is_unlimited else 'unlimited',
                        'used': used_value,
                        'remaining': remain_value if not is_unlimited else 'unlimited',
                        'unit': 'MB',
                        'type': detail.get('flowType', '1'),
                        'used_percent': detail.get('usedPercent', '0'),
                        'is_extra': True,
                        'is_unlimited': is_unlimited,
                        'source': 'TwResources'
                    }
                    extra_packages.append(extra_info)

        # 计算使用百分比
        try:
            usage_percentage = float(flow_data.get('sumPercent', 0))
        except (ValueError, AttributeError):
            try:
                total_num = float(str(total_flow).replace('MB', '').replace('GB', '').replace(',', ''))
                used_num = float(str(used_flow).replace('MB', '').replace('GB', '').replace(',', ''))
                usage_percentage = (used_num / total_num * 100) if total_num > 0 else 0
            except (ValueError, AttributeError):
                usage_percentage = 0

        return {
            'total_flow': total_flow,
            'used_flow': used_flow,
            'remaining_flow': remaining_flow,
            'usage_percentage': round(usage_percentage, 2),
            'flow_packages': flow_packages,
            'extra_packages': extra_packages,
            'package_name': package_name,
            'used_general': used_general,
            'used_special': used_special,
            'used_other': used_other,
            'remain_general': remain_general,
            'remain_special': remain_special,
            'remain_other': remain_other
        }

    except Exception as e:
        current_app.logger.error(f"解析流量数据异常: {e}")
        return {
            'total_flow': '0',
            'used_flow': '0',
            'remaining_flow': '0',
            'usage_percentage': 0,
            'flow_packages': [],
            'extra_packages': [],
            'package_name': '',
            'used_general': '0',
            'used_special': '0',
            'used_other': '0',
            'remain_general': '0',
            'remain_special': '0',
            'remain_other': '0'
        }

def _parse_flow_value(value_str):
    """解析流量值（MB）"""
    try:
        if isinstance(value_str, (int, float)):
            return float(value_str)
        
        if isinstance(value_str, str):
            # 移除单位和空格
            value_str = value_str.replace('MB', '').replace('GB', '').replace('KB', '').strip()
            return float(value_str) if value_str else 0
        
        return 0
    except:
        return 0


@flow_bp.route('/reset-baseline/<int:account_id>', methods=['POST'])
@login_required
def reset_flow_baseline(current_user, account_id):
    """重置流量统计基准"""
    try:

        # 验证账号权限
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id
        ).first()

        if not unicom_account:
            return jsonify({
                'success': False,
                'message': '账号不存在或无权限'
            }), 404

        # 获取请求参数
        data = request.get_json() or {}
        note = data.get('note', '手动重置统计基准')

        # 先查询当前流量数据
        from ..utils.unicom_api import unicom_api

        # 强制实时查询获取最新数据（不使用缓存）
        result = unicom_api.query_flow(unicom_account, use_cache=False, user_id=current_user.id)

        if not result['success']:
            return jsonify({
                'success': False,
                'message': f'获取流量数据失败: {result.get("message", "未知错误")}'
            }), 500

        flow_data = result['data']

        # 创建新的基准
        baseline = FlowBaseline.create_baseline(
            unicom_account_id=account_id,
            flow_data=flow_data,
            reason='manual',
            note=note
        )

        # 记录操作日志
        SystemLog.log_action(
            action='reset_baseline',
            description=f'重置流量统计基准 {unicom_account.phone}',
            user_id=current_user.id,
            unicom_account_id=account_id,
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent'),
            module='flow'
        )

        logger.info(f"用户 {current_user.username} 重置了账号 {unicom_account.phone} 的流量基准")

        return jsonify({
            'success': True,
            'message': '统计基准重置成功',
            'data': {
                'baseline': baseline.to_dict(),
                'current_flow_data': flow_data
            }
        })

    except Exception as e:
        logger.error(f"重置流量基准失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'重置失败: {str(e)}'
        }), 500


@flow_bp.route('/baseline-history/<int:account_id>', methods=['GET'])
@login_required
def get_baseline_history(account_id):
    """获取基准历史记录"""
    try:
        current_user = User.query.get(session.get('user_id'))

        # 验证账号权限
        unicom_account = UnicomAccount.query.filter_by(
            id=account_id,
            user_id=current_user.id
        ).first()

        if not unicom_account:
            return jsonify({
                'success': False,
                'message': '账号不存在或无权限'
            }), 404

        # 获取分页参数
        page = request.args.get('page', 1, type=int)
        limit = request.args.get('limit', 20, type=int)

        # 查询基准历史
        baselines = FlowBaseline.query.filter_by(
            unicom_account_id=account_id
        ).order_by(FlowBaseline.baseline_time.desc()).paginate(
            page=page, per_page=limit, error_out=False
        )

        return jsonify({
            'success': True,
            'data': {
                'total': baselines.total,
                'page': page,
                'limit': limit,
                'baselines': [baseline.to_dict() for baseline in baselines.items]
            }
        })

    except Exception as e:
        logger.error(f"获取基准历史失败: {str(e)}")
        return jsonify({
            'success': False,
            'message': f'获取历史失败: {str(e)}'
        }), 500
