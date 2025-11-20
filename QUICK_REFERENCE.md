# 快速参考

## 本地启动（开发/测试）

### 1. 安装依赖
```bash
uv sync
uv run playwright install chromium
```

### 2. 启动服务

**方式 A：仅 Web 界面（推荐用于测试）**
```bash
uv run python web/api.py
```
访问：http://localhost:8080

**方式 B：Web + 自动签到（完整功能）**

打开两个终端：

**终端 1：**
```bash
uv run python web/api.py
```

**终端 2：**
```bash
uv run python web/scheduler.py
```

## 服务器部署（生产环境）

### Docker 部署（推荐）
```bash
docker-compose up -d              # 启动
docker-compose logs -f            # 查看日志
docker-compose restart            # 重启
docker-compose down               # 停止
```

### 直接运行
```bash
nohup python web/api.py > logs/api.log 2>&1 &
nohup python web/scheduler.py > logs/scheduler.log 2>&1 &
```

## 常用测试命令

### 测试自动登录
```bash
uv run python utils/auto_login.py 你的邮箱 你的密码
```

### 测试数据库
```bash
uv run python web/database.py
```

### 测试签到任务
```bash
uv run python web/scheduler.py test
```

## Web 界面操作

| 功能 | 操作 |
|------|------|
| 添加账号 | 点击"➕ 添加账号" → 填写用户名密码 → 保存 |
| 测试登录 | 添加账号时点击"🧪 测试登录" |
| 手动签到 | 点击账号行的"签到"按钮 |
| 全部签到 | 点击顶部"🔄 全部签到" |
| 禁用账号 | 点击"禁用"按钮 |
| 查看余额 | 点击"查看余额" |
| 查看日志 | 页面底部自动显示 |

## API 接口

访问 http://localhost:8080/docs 查看完整 API 文档

### 常用接口

| 功能 | 方法 | 路径 |
|------|------|------|
| 获取账号列表 | GET | /api/accounts |
| 添加账号 | POST | /api/accounts |
| 更新账号 | PUT | /api/accounts/{id} |
| 删除账号 | DELETE | /api/accounts/{id} |
| 手动签到 | POST | /api/checkin/{id} |
| 全部签到 | POST | /api/checkin-all |
| 获取日志 | GET | /api/logs |
| 获取统计 | GET | /api/statistics |
| 测试登录 | POST | /api/test-login |

## 目录结构

```
anyrouter-check-in/
├── web/                    # 新增：Web 管理系统
│   ├── api.py             # FastAPI 后端
│   ├── database.py        # 数据库模块
│   ├── scheduler.py       # 定时任务
│   └── templates/
│       └── index.html     # Web 界面
├── utils/
│   ├── auto_login.py      # 新增：自动登录
│   ├── config.py          # 配置管理
│   └── notify.py          # 通知系统
├── checkin.py             # 签到核心逻辑
├── data/                  # 数据目录（自动创建）
│   ├── checkin.db         # SQLite 数据库
│   └── secret.key         # 加密密钥
├── Dockerfile
├── docker-compose.yml
└── README.md
```

## 数据文件

| 文件 | 说明 | 是否需要备份 |
|------|------|-------------|
| data/checkin.db | 账号、日志、余额数据 | ✅ 需要 |
| data/secret.key | 密码加密密钥 | ✅ 需要 |
| logs/*.log | 运行日志 | ❌ 可选 |

## 环境变量（通知配置）

创建 `.env` 文件：

```env
# 邮件
EMAIL_USER=your@email.com
EMAIL_PASS=your_password
EMAIL_TO=receiver@email.com

# 钉钉
DINGDING_WEBHOOK=https://oapi.dingtalk.com/...

# 飞书
FEISHU_WEBHOOK=https://open.feishu.cn/...

# 企业微信
WEIXIN_WEBHOOK=https://qyapi.weixin.qq.com/...

# Telegram
TELEGRAM_BOT_TOKEN=your_token
TELEGRAM_CHAT_ID=your_chat_id

# PushPlus
PUSHPLUS_TOKEN=your_token

# Server酱
SERVERPUSHKEY=your_key
```

## 故障排查

| 问题 | 解决方案 |
|------|---------|
| 端口被占用 | 修改 `web/api.py` 中的端口号 |
| 浏览器未安装 | `uv run playwright install chromium --with-deps` |
| 登录失败 | 检查用户名密码，查看终端日志 |
| 数据库错误 | 检查 `data/` 目录权限 |
| 签到不执行 | 确认调度器已启动，账号已启用 |

## 端口说明

| 端口 | 服务 | 说明 |
|------|------|------|
| 8080 | Web 界面 | 默认端口，可修改 |

## 性能参考

| 操作 | 耗时 |
|------|------|
| 自动登录 | ~5-10秒 |
| 签到请求 | ~1-2秒 |
| 单账号总计 | ~8-15秒 |

## 版本对比

| 功能 | GitHub Actions | 服务器版 |
|------|----------------|----------|
| 配置难度 | ⭐⭐⭐ | ⭐ |
| 管理便捷 | ⭐ | ⭐⭐⭐⭐⭐ |
| 需要服务器 | ❌ | ✅ |
| 完全免费 | ✅ | ❌ |
| 实时查看 | ❌ | ✅ |

## 安全建议

✅ 密码加密存储
✅ 本地数据库
✅ 定期备份
⚠️ 不要暴露到公网
⚠️ 使用强密码
⚠️ 保护密钥文件

## 获取帮助

📖 [本地开发指南](LOCAL_GUIDE.md) - 详细的本地使用说明
📖 [服务器部署指南](README_SERVER.md) - 完整的服务器部署文档
📖 [快速开始](QUICKSTART_SERVER.md) - 5分钟入门指南
📖 [实现说明](IMPLEMENTATION.md) - 技术架构详解

🐛 遇到问题？[提交 Issue](https://github.com/your/anyrouter-check-in/issues)
