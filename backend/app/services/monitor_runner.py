#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
监控调度器（APScheduler）
- 读取用户监控配置与账号开关
- 定时查询已启用账号流量
- 根据规则判断并通过 NotificationService 发送通知
注意：默认不自动启用，需设置环境变量 ENABLE_SCHEDULER=true
"""
from __future__ import annotations
import math
import os
import socket
import time
from datetime import datetime, timedelta
from typing import Dict, Any, Optional, Tuple

from apscheduler.schedulers.background import BackgroundScheduler
from flask import current_app

from ..models import db
from ..models.user import User
from ..models.user_settings import UserSettings
from ..models.unicom_account import UnicomAccount
from ..models.flow_record import FlowRecord
from ..utils.cache_manager import cache_manager
from ..utils.unicom_api import unicom_api
from ..utils.timezone_helper import now, format_local
from .notification_service import NotificationService

_scheduler: Optional[BackgroundScheduler] = None

# ---------------------- 工具函数 ----------------------

def _parse_mb(value) -> Optional[float]:
    """将带单位的字符串转为 MB 浮点数（不合法返回None）"""
    if value is None:
        return None
    try:
        if isinstance(value, (int, float)):
            return float(value)
        s = str(value).strip().upper()
        if not s:
            return None
        if s.endswith('GB'):
            return float(s[:-2].strip()) * 1024
        if s.endswith('MB'):
            return float(s[:-2].strip())
        # 纯数字默认MB
        return float(s)
    except Exception:
        return None


def _extract_flow_by_type(raw_data: Dict[str, Any]) -> Dict[str, float]:
    """从联通原始响应中提取各类总量/剩余/已用（粗粒度）
    返回：{
        'total_all_mb', 'remain_all_mb', 'used_all_mb',
        'general_total_mb', 'general_remain_mb', 'used_general_mb',
        'special_total_mb', 'special_remain_mb', 'used_free_mb'
    }
    """
    result = {
        'total_all_mb': None,
        'remain_all_mb': None,
        'used_all_mb': None,
        'general_total_mb': None,
        'general_remain_mb': None,
        'used_general_mb': None,
        'special_total_mb': None,
        'special_remain_mb': None,
        'used_free_mb': None,
    }
    try:
        data = raw_data or {}
        result['total_all_mb'] = _parse_mb(data.get('sum'))
        result['remain_all_mb'] = _parse_mb(data.get('canUseFlowAll'))
        result['used_all_mb'] = _parse_mb(data.get('allUserFlow'))

        # 从flowSumList中提取通用和专用流量的使用量
        flow_sum_list = data.get('flowSumList') or []
        for item in flow_sum_list:
            flow_type = str(item.get('flowtype', '')).strip()
            used_value = _parse_mb(item.get('xusedvalue'))
            if flow_type == '1':  # 通用流量
                result['used_general_mb'] = used_value
            elif flow_type == '2':  # 专用流量
                result['used_free_mb'] = used_value

        # 资源维度
        def walk_resources(arr):
            gt_total = 0.0
            gt_remain = 0.0
            sp_total = 0.0
            sp_remain = 0.0
            for it in arr or []:
                # 资源明细有时在 it['details']
                details = it.get('details') if isinstance(it, dict) else None
                if isinstance(details, list) and details:
                    for d in details:
                        ftype = str(d.get('flowType') or d.get('type') or '').strip()
                        total_mb = _parse_mb(d.get('total'))
                        remain_mb = _parse_mb(d.get('remain'))
                        if ftype == '1':  # 通用
                            if total_mb: gt_total += total_mb
                            if remain_mb is not None: gt_remain += max(0.0, remain_mb)
                        if ftype == '2':  # 免流/专用
                            if total_mb: sp_total += total_mb
                            if remain_mb is not None: sp_remain += max(0.0, remain_mb)
            return gt_total, gt_remain, sp_total, sp_remain

        resources = data.get('resources') if isinstance(data.get('resources'), list) else []
        gt_total1, gt_remain1, sp_total1, sp_remain1 = walk_resources(resources)
        # 某些返回还在 TwResources
        tw = data.get('TwResources') if isinstance(data.get('TwResources'), list) else []
        gt_total2, gt_remain2, sp_total2, sp_remain2 = walk_resources(tw)

        g_total = (gt_total1 + gt_total2) or None
        g_remain = (gt_remain1 + gt_remain2) or None
        s_total = (sp_total1 + sp_total2) or None
        s_remain = (sp_remain1 + sp_remain2) or None

        if g_total:
            result['general_total_mb'] = g_total
        if g_remain is not None:
            result['general_remain_mb'] = g_remain
        if s_total:
            result['special_total_mb'] = s_total
        if s_remain is not None:
            result['special_remain_mb'] = s_remain
    except Exception:
        pass
    return result


def _now_ts() -> int:
    return int(time.time())


# ---------------------- 规则判断 ----------------------

def _should_run_user(user_id: int, freq_seconds: int) -> bool:
    key = f"monitor:last_scan:{user_id}"
    last_ts = cache_manager.get(key)
    now = _now_ts()
    if isinstance(last_ts, dict):
        last_val = last_ts.get('ts')
    else:
        last_val = last_ts
    try:
        last_val = int(last_val)
    except Exception:
        last_val = None
    if (not last_val) or (now - last_val >= max(60, int(freq_seconds))):
        cache_manager.set(key, {'ts': now}, expire=freq_seconds)
        return True
    return False


def _get_settings(user_id: int) -> Dict[str, Any]:
    us = UserSettings.get_or_create(user_id)
    return us.to_dict()


def _format_change_mb(change_mb: float) -> str:
    if change_mb is None:
        return '0MB'
    return f"{change_mb:+.2f}MB"


def _calc_jump_buckets(baseline_used_mb: float, current_used_mb: float, threshold_mb: float) -> Tuple[int, float]:
    """返回跨越的桶数和新的基线值推进量"""
    if baseline_used_mb is None or current_used_mb is None or threshold_mb <= 0:
        return 0, 0.0
    delta = current_used_mb - baseline_used_mb
    if delta < threshold_mb:
        return 0, 0.0
    k = int(math.floor(delta / threshold_mb))
    advance = k * threshold_mb
    return k, advance


# ---------------------- 通知发送 ----------------------

def _send_notifications(user_settings: Dict[str, Any], title: str, content: str) -> Dict[str, Any]:
    svc = NotificationService(current_app.config)
    noti = (user_settings.get('notifications') or {}) if isinstance(user_settings.get('notifications'), dict) else {}
    results = {}
    enabled_channels = []

    # 统计启用的通知渠道
    for channel, cfg in noti.items():
        if isinstance(cfg, dict) and cfg.get('enabled'):
            enabled_channels.append(channel)

    if not enabled_channels:
        print(f"[通知] 未配置任何通知渠道")
        return results

    print(f"[通知] 开始发送通知，启用渠道: {', '.join(enabled_channels)}")
    print(f"[通知] 标题: {title}")

    for channel, cfg in noti.items():
        if isinstance(cfg, dict) and cfg.get('enabled'):
            try:
                print(f"[通知] 发送 {channel} 通知...")
                res = svc.send(channel, cfg, title, content)
                results[channel] = res
                if res.get('success'):
                    print(f"[通知] {channel} - 发送成功")
                else:
                    print(f"[通知] {channel} - 发送失败: {res.get('message', '未知错误')}")
            except Exception as e:
                error_msg = f'send error: {e}'
                results[channel] = {'success': False, 'message': error_msg}
                print(f"[通知] {channel} - 发送异常: {error_msg}")

    # 汇总结果
    success_count = sum(1 for r in results.values() if r.get('success'))
    total_count = len(results)
    print(f"[通知] 发送完成: {success_count}/{total_count} 成功")

    return results


# ---------------------- 主执行逻辑 ----------------------

def _process_account(user: User, account: UnicomAccount, settings: Dict[str, Any]):
    alerts = settings.get('alerts') or {}
    # 通知节奏=监控频率；不使用独立的最小通知间隔

    # 查询流量（不使用缓存）
    print(f"[监控] 账号 {account.phone} - 开始查询流量数据")
    q = unicom_api.query_flow(account, use_cache=False, user_id=account.user_id)
    if not q.get('success'):
        print(f"[监控] 账号 {account.phone} - 查询失败: {q.get('message')}")
        current_app.logger.info(f"[monitor] 查询失败 {account.phone}: {q.get('message')}")
        return
    raw = q.get('data') or {}
    print(f"[监控] 账号 {account.phone} - 查询成功，开始分析数据")

    # 保存 FlowRecord 基础摘要（尽量复用已有字段）
    fr = FlowRecord(
        unicom_account_id=account.id,
        query_type='monitor',
        query_source='task',
        query_status=1,
        is_cached=bool(q.get('is_cached')),
        query_time=q.get('query_time')
    )
    try:
        # 一些常见字段（允许为空）
        fr.total_data = str(raw.get('sum') or '')
        fr.remain_data = str(raw.get('canUseFlowAll') or '')
        fr.used_data = str(raw.get('allUserFlow') or '')
        fr.package_name = str(raw.get('packageName') or '')
        fr.end_date = str(raw.get('endDate') or '')
        import json
        fr.raw_response = json.dumps(raw, ensure_ascii=False)

        # 取上一条记录计算变化
        last = account.flow_records.filter_by(query_status=1).order_by(FlowRecord.created_at.desc()).first()
        if last:
            fr.last_used_data = last.used_data
            fr.last_free_data = last.free_data
            fr.last_total_data = last.total_data
            fr.calculate_data_change(last)
        db.session.add(fr)
        db.session.commit()
    except Exception as e:
        current_app.logger.warning(f"[monitor] 保存FlowRecord失败: {e}")
        db.session.rollback()

    # 解析数据结构化
    metrics = _extract_flow_by_type(raw)

    # -------- 低余量（只通知一次，按配置版本） --------
    low_cfg = alerts.get('low') or {}
    for tname in ['general', 'special']:
        tcfg = low_cfg.get(tname) or {}
        if not tcfg.get('enabled'):
            continue
        # 剩余 & 总量
        if tname == 'general':
            remain_mb = metrics.get('general_remain_mb') if metrics.get('general_remain_mb') is not None else metrics.get('remain_all_mb')
            total_mb = metrics.get('general_total_mb') if metrics.get('general_total_mb') else metrics.get('total_all_mb')
        else:
            remain_mb = metrics.get('special_remain_mb')
            total_mb = metrics.get('special_total_mb')
        if remain_mb is None or total_mb is None or total_mb <= 0:
            continue
        mode = (tcfg.get('mode') or 'percent').lower()
        val = float(tcfg.get('value') or 0)
        hit = False
        if mode == 'percent':
            percent = (remain_mb / total_mb) * 100.0
            hit = percent <= val
        else:  # 'gb'
            hit = remain_mb <= (val * 1024.0)
        if not hit:
            continue
        # 基于“只通知一次”的逻辑（与配置版本绑定）
        # 使用阈值作为去重标识，确保同一阈值只通知一次
        threshold_key = f"{mode}_{val}"
        dedupe_key = f"alert_once:{account.user_id}:{account.id}:low:{tname}:{threshold_key}"
        if cache_manager.exists(dedupe_key):
            continue
        # 发通知
        title = "低余量提醒"
        current_time = now()
        content = (
            f"账号：{account.phone}\n"
            f"通用流量剩余 {remain_mb/1024:.2f}GB/共{total_mb/1024:.2f}GB\n"
            f"时间：{format_local(current_time)}"
        )
        _send_notifications(settings, title, content)
        cache_manager.set(dedupe_key, 1, expire=60*60*24*7)  # 7天兜底；账期切换会自然重置

    # -------- 跳点（只检测通用流量变化） --------
    jump_cfg = alerts.get('jump') or {}
    for tname in ['general']:  # 只检测通用跳点
        tcfg = jump_cfg.get(tname) or {}
        if not tcfg.get('enabled'):
            continue
        threshold_mb = float(tcfg.get('thresholdMB') or 0)
        if threshold_mb <= 0:
            continue
        # 基线存储（基于“上次通知后的已用量”）
        base_key = f"jump_base:{account.user_id}:{account.id}:{tname}"
        base = cache_manager.get(base_key) or {}
        baseline_used_mb = base.get('baseline_used_mb')
        # 当前已用（优先按通用/专用解析，其次总已用）
        current_used_mb = None
        used_all_mb = _parse_mb(metrics.get('used_all_mb')) if metrics.get('used_all_mb') is not None else None
        # 这里由于原始返回对通用/专用已用拆分不稳定，先用总已用代替，保证“每累计NMB就发”
        # 跳点只检测通用流量变化
        current_used_mb = _parse_mb(metrics.get('used_general_mb')) if metrics.get('used_general_mb') is not None else None
        if current_used_mb is None:
            print(f"[跳点] 账号 {account.phone} - 无法获取通用流量数据，跳过")
            continue

        # 初始化基线：第一次不发，只建立基线
        if baseline_used_mb is None:
            print(f"[跳点] 账号 {account.phone} {tname} - 初始化基线: {current_used_mb:.2f}MB")
            cache_manager.set(base_key, {'baseline_used_mb': current_used_mb}, expire=30*24*3600)
            continue

        print(f"[跳点] 账号 {account.phone} {tname} - 基线: {baseline_used_mb:.2f}MB, 当前: {current_used_mb:.2f}MB, 阈值: {threshold_mb:.0f}MB")
        buckets, advance = _calc_jump_buckets(baseline_used_mb, current_used_mb, threshold_mb)
        print(f"[跳点] 账号 {account.phone} {tname} - 跨越桶数: {buckets}, 推进量: {advance:.2f}MB")

        if buckets <= 0:
            print(f"[跳点] 账号 {account.phone} {tname} - 未达到阈值，跳过")
            continue

        # 发送一条合并通知
        print(f"[跳点] 账号 {account.phone} {tname} - 触发通知！跨越 {buckets} 档，累计增加 {buckets * threshold_mb:.0f}MB")
        title = "用量跳点提醒"
        current_time = now()

        # 获取专用流量数据
        used_special_mb = metrics.get('used_special_mb', 0) or 0

        content = (
            f"账号：{account.phone}\n\n"
            f"基线已用通用流量：{baseline_used_mb:.2f}MB\n"
            f"当前已用通用流量：{current_used_mb:.2f}MB\n"
            f"当前已用专用流量：{used_special_mb:.2f}MB\n"
            f"最近跳点增加{buckets * threshold_mb:.0f}MB，阈值{threshold_mb:.0f}MB，共跨{buckets}档\n"
            f"时间：{format_local(current_time)}\n"
            f"提示：请注意流量使用哦~"
        )
        # 如果跨度大于10档，增加免流提醒
        if buckets > 10:
            content += "\n最近流量跳点过大，快看看免流开关是否打开或者免流是否失效！"
        _send_notifications(settings, title, content)
        # 推进基线
        new_base = baseline_used_mb + advance
        print(f"[跳点] 账号 {account.phone} {tname} - 基线推进: {baseline_used_mb:.2f}MB -> {new_base:.2f}MB")
        cache_manager.set(base_key, {'baseline_used_mb': new_base}, expire=30*24*3600)


# ---------------------- 定时任务 ----------------------

def monitor_tick():
    """监控定时任务"""
    from flask import current_app
    # 获取应用实例（在调度器初始化时设置）
    app = getattr(monitor_tick, '_app', None)
    if not app:
        print("[ERROR] 监控任务：应用上下文未设置")
        return

    with app.app_context():
        try:
            from ..utils.timezone_helper import now, format_local
            print(f"[监控] 开始执行监控任务 - {format_local(now())}")

            # 仅扫描启用了监控开关的账号所属用户
            user_ids = [uid for (uid,) in db.session.query(User.id).all()]
            print(f"[监控] 发现 {len(user_ids)} 个用户")

            settings_cache: Dict[int, Dict[str, Any]] = {}
            active_users = 0

            for uid in user_ids:
                settings = settings_cache.get(uid)
                if not settings:
                    settings = _get_settings(uid)
                    settings_cache[uid] = settings
                freq = int((settings.get('monitor') or {}).get('frequencySeconds') or current_app.config.get('MIN_MONITOR_INTERVAL', 180))

                if not _should_run_user(uid, freq):
                    continue

                active_users += 1
                print(f"[监控] 用户 {uid} - 监控频率: {freq}秒")

                # 扫描该用户账号
                accounts = UnicomAccount.query.filter_by(user_id=uid, status=1, monitor_enabled=True).all()
                print(f"[监控] 用户 {uid} - 发现 {len(accounts)} 个启用监控的账号")
                for acc in accounts:
                    if not acc.is_auth_valid():
                        print(f"[监控] 账号 {acc.phone} - 认证已过期，跳过")
                        continue
                    try:
                        print(f"[监控] 开始处理账号 {acc.phone}")
                        _process_account(User.query.get(uid), acc, settings)
                        print(f"[监控] 账号 {acc.phone} - 处理完成")
                    except Exception as e:
                        print(f"[监控] 账号 {acc.phone} - 处理失败: {e}")
                        current_app.logger.error(f"[monitor] 处理账号失败 {acc.phone}: {e}")

            if active_users == 0:
                print("[监控] 没有需要监控的用户")
            else:
                print(f"[监控] 本轮监控完成，处理了 {active_users} 个用户")

        except Exception as e:
            print(f"[监控] 监控任务异常: {e}")
            current_app.logger.error(f"[monitor] tick 异常: {e}")


# ---------------------- 初始化 ----------------------

def init_monitor_scheduler(app):
    global _scheduler
    if _scheduler is not None:
        return _scheduler
    if not app.config.get('ENABLE_SCHEDULER'):
        app.logger.info('监控调度器未启用（ENABLE_SCHEDULER=false）')
        return None

    _scheduler = BackgroundScheduler(timezone='Asia/Shanghai')

    # 将应用实例绑定到监控任务函数上，供调度器线程使用
    monitor_tick._app = app

    # 每30秒tick一次，由内部根据每个用户配置的 frequencySeconds 判定是否执行
    _scheduler.add_job(monitor_tick, 'interval', seconds=30, id='monitor_tick', max_instances=1, coalesce=True)

    # 尝试使用Redis获取一个“实例锁”，避免多进程重复启动（简单保护）
    try:
        lock_key = 'scheduler:instance_lock'
        ident = f"{socket.gethostname()}:{os.getpid()}"
        if cache_manager.redis_client:
            ok = cache_manager.redis_client.set(lock_key, ident, nx=True, ex=120)
            if not ok:
                app.logger.warning('已有调度实例在运行，当前进程不再启动调度器')
                return None
    except Exception:
        # 无Redis时直接启动，适合开发环境
        pass

    _scheduler.start()
    app.logger.info('监控调度器已启动（interval=30s）')
    return _scheduler

