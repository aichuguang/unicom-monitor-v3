# 🚀 联通流量监控系统 v3.0

一个现代化的联通流量监控系统，支持多用户、实时监控、智能缓存等功能。

## ✨ 主要特性

- 🔐 **多用户支持** - 用户隔离，数据安全
- 🛡️ **智能防风控** - 固定设备指纹，IP代理池
- ⚡ **智能缓存** - 10分钟自动刷新，1分钟手动限制
- 📊 **实时监控** - 用户自定义监控间隔和阈值
- 📱 **响应式界面** - 完美适配手机和电脑

## 🎯 技术栈

- **前端**: Vue 3 + Element Plus + Tailwind CSS
- **后端**: Flask + SQLAlchemy + JWT + Redis
- **数据库**: MySQL + Redis

## ⚙️ 环境配置

系统使用 `.env` 文件进行配置，只需要配置必要参数：

```bash
FLASK_ENV=production
SECRET_KEY=unicom-monitor-v3
DEBUG=false

# 数据库配置
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=unicom
MYSQL_PASSWORD=AHwJzT362STAYy4E
MYSQL_DATABASE=unicom

# Redis配置
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=redis_PdvfA

# JWT配置
JWT_SECRET_KEY=unicom-monitor-v3

# 日志配置
LOG_LEVEL=INFO
LOG_FILE=logs/unicom_monitor_v3.log

# WxPusher配置
WXPUSHER_APP_TOKEN=AT_Zub4kGlArW4rffsdfrEGdJhIdtnm0Mga

# 监控调度器开关
ENABLE_SCHEDULER=false

# 业务配置（系统默认值，一般无需修改）
MAX_UNICOM_ACCOUNTS_PER_USER=5
MIN_MONITOR_INTERVAL=180
MAX_MONITOR_INTERVAL=3600
MANUAL_REFRESH_INTERVAL=60
AUTO_CACHE_REFRESH_INTERVAL=600
FLOW_CACHE_EXPIRE=600
```

## 🚀 快速开始

### 传统部署方式（推荐）

```bash
# 1. 克隆项目
git clone <repository-url>
cd unicom-monitor-v3

# 2. 前端构建
cd frontend
npm install
npm run build

# 3. 后端部署
cd ../backend
pip install -r requirements.txt

# 4. 环境配置
cp .env.example .env
nano .env  # 修改数据库和Redis连接信息

# 5. 启动后端
python run.py

# 6. 配置Nginx反向代理（见下方配置）
```

## 📖 使用说明

### 1. 注册和登录
- 访问系统首页
- 注册新账号或使用现有账号登录

### 2. 添加联通账号
- 进入配置页面
- 添加联通手机号
- 获取并输入验证码完成认证

### 3. 查询流量
- 在首页点击查询按钮
- 查看流量使用情况和变化趋势

### 4. 设置监控
- 配置监控阈值和通知方式
- 开启自动监控功能

## 🔧 Nginx 配置

创建 Nginx 配置文件 

```nginx
server {
    listen 80;
    server_name your-domain.com;  # 替换为你的域名或IP

    # 前端静态文件
    location / {
        root /path/to/unicom-monitor-v3/frontend/dist;
        try_files $uri $uri/ /index.html;
        index index.html;
    }

    # 后端API代理
    location /api/ {
        proxy_pass http://127.0.0.1:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态资源缓存
    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        root /path/to/unicom-monitor-v3/frontend/dist;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
```



## 🔧 管理命令

```bash
# 启动后端服务
cd backend && python run.py

# 查看后端日志
tail -f logs/unicom_monitor_v3.log


```

## 📁 项目结构

```
unicom-monitor-v3/
├── frontend/           # 前端代码 (Vue 3 + Element Plus)
│   ├── src/           # 源码目录
│   ├── dist/          # 构建输出目录
│   └── package.json   # 前端依赖
├── backend/           # 后端代码 (Flask + SQLAlchemy)
│   ├── app/           # 应用核心代码
│   ├── run.py         # 启动文件
│   ├── .env.example   # 环境配置模板
│   └── requirements.txt # 后端依赖
├── data/              # 数据目录
└── logs/              # 日志目录
```

## 🐛 故障排查

### 常见问题

1. **前端构建失败**
   ```bash
   cd frontend
   npm install --registry https://registry.npmmirror.com
   npm run build
   ```

2. **后端启动失败**
   ```bash
   cd backend
   pip install -r requirements.txt -i https://pypi.tuna.tsinghua.edu.cn/simple
   python run.py
   ```

3. **数据库连接失败**
   ```bash
   telnet 127.0.0.1 3306
   ```

4. **环境配置错误**
   ```bash
   # 检查.env文件格式
   cat backend/.env
   ```

5. **Nginx配置问题**
   ```bash
   sudo nginx -t
   sudo systemctl status nginx
   ```

## 📚 文档

- [项目说明.md](项目说明.md) - 详细项目说明

## 🔒 安全建议

1. **修改默认密钥**: 编辑 `.env` 中的安全配置
2. **使用HTTPS**: 生产环境建议配置SSL证书
3. **限制访问**: 配置防火墙和访问控制

## 📊 系统要求

- **操作系统**: Linux（推荐）
- **Node.js**: 18.x+
- **Python**: 3.9+
- **Nginx**: 1.18+
- **MySQL**: 8.0+ 或 SQLite
- **Redis**: 6.0+（可选）
- **内存**: 最低 512MB，推荐 1GB+
- **存储**: 最低 1GB 可用空间

## 🚀 生产环境部署建议

### 1. 使用进程管理器

推荐使用 PM2 或 systemd 管理后端进程：

```bash
# 使用PM2
npm install -g pm2
cd backend
pm2 start run.py --name unicom-monitor --interpreter python3

# 或使用systemd
sudo nano /etc/systemd/system/unicom-monitor.service
```

### 2. 设置开机自启

```bash
# PM2开机自启
pm2 startup
pm2 save

# systemd开机自启
sudo systemctl enable unicom-monitor
sudo systemctl enable nginx
```

### 3. 日志轮转

```bash
# 配置logrotate
sudo nano /etc/logrotate.d/unicom-monitor
```

---

**联通流量监控系统 v3.0** - 简化配置，传统部署！

🌟 如果这个项目对您有帮助，请给个 Star 支持一下！

## 📝 部署总结

1. **前端**: `npm run build` 构建静态文件
2. **后端**: `python run.py` 启动Flask服务
3. **代理**: Nginx反向代理，统一访问入口
4. **配置**: 一个 `.env` 文件搞定所有配置

简单、稳定、易维护！🎉
