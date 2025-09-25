#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
联通流量监控系统 v3.0 启动脚本
"""
import os
import sys
from app import create_app

def main():
    """主函数"""
    # 创建应用实例（使用环境变量配置）
    app = create_app()
    
    # 启动信息
    print("=" * 80)
    print("🚀 联通流量监控系统 v3.0")
    print("=" * 80)
    print("📍 服务地址: http://localhost:5000")
    print("📱 核心特性:")
    print("   ✅ 多用户支持 - 用户隔离，数据安全")
    print("   ✅ 智能防风控 - 固定设备指纹，IP代理池")
    print("   ✅ 智能缓存 - 10分钟自动刷新，1分钟手动限制")
    print("   ✅ 实时监控 - 用户自定义监控间隔和阈值")
    print("   ✅ H5响应式界面 - 手机电脑都支持")
    print("📊 技术栈:")
    print("   🔧 后端: Flask + SQLAlchemy + JWT + Redis")
    print("   🎨 前端: Vue3 + Element Plus + Tailwind CSS")
    print("   🗄️ 数据库: MySQL")
    print("   📦 部署: Docker + docker-compose")
    print("💡 访问地址:")
    print("   🌐 前端页面: http://localhost:5000")
    print("   📋 API文档: http://localhost:5000/health")
    print("   🔍 健康检查: http://localhost:5000/health")
    print("=" * 80)
    print("🎯 功能页面:")
    print("   1. 首页 - 流量概览、快速查询")
    print("   2. 监控页 - 实时监控、历史趋势")
    print("   3. 配置页 - 账号管理、监控设置")
    print("   4. 个人中心 - 用户信息、Token管理")
    print("=" * 80)
    print("📝 使用说明:")
    print("   1. 注册平台账号并登录")
    print("   2. 添加联通账号（最多5个）")
    print("   3. 在联通APP获取验证码")
    print("   4. 使用验证码完成联通账号认证")
    print("   5. 查询流量信息和设置监控")
    print("=" * 80)
    
    # 获取服务器配置（从环境变量）
    host = os.environ.get('FLASK_HOST', '0.0.0.0')  # 默认绑定所有接口
    port = int(os.environ.get('FLASK_PORT', 5000))
    debug = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'

    print(f"🚀 启动联通流量监控系统 v3.0")
    print(f"📡 监听地址: http://{host}:{port}")
    print(f"🔧 调试模式: {'开启' if debug else '关闭'}")
    print(f"🌍 环境: {app.config.get('ENV', 'unknown')}")

    try:
        app.run(
            host=host,
            port=port,
            debug=debug,
            threaded=True
        )
    except KeyboardInterrupt:
        print("\n👋 系统已停止")
    except Exception as e:
        print(f"\n❌ 启动失败: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
