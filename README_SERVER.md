# AnyRouter 签到管理系统 - 服务器部署指南

## 系统简介

这是一个完整的 Web 管理系统，支持：
- ✅ 用户名密码自动登录（无需手动获取 cookies）
- ✅ Web 界面管理多个账号
- ✅ 自动定时签到（每 6 小时）
- ✅ 签到历史和余额追踪
- ✅ 多种通知方式
- ✅ Docker 一键部署

## 快速开始

### 方式一：Docker Compose 部署（推荐）

#### 1. 克隆项目

```bash
git clone https://github.com/your/anyrouter-check-in.git
cd anyrouter-check-in
```

#### 2. 配置环境变量（可选）

如果需要通知功能，创建 `.env` 文件：

```bash
# 邮件通知
EMAIL_USER=your@email.com
EMAIL_PASS=your_password
EMAIL_TO=receiver@email.com

# 钉钉机器人
DINGDING_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx

# 飞书机器人
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# 企业微信机器人
WEIXIN_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# PushPlus
PUSHPLUS_TOKEN=your_token

# Server酱
SERVERPUSHKEY=your_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_bot_token
TELEGRAM_CHAT_ID=your_chat_id
```

#### 3. 启动服务

```bash
docker-compose up -d
```

#### 4. 访问管理界面

打开浏览器访问：`http://your-server-ip:8080`

#### 5. 添加账号

在 Web 界面中：
1. 点击"添加账号"
2. 输入账号名称、用户名（邮箱）、密码
3. 可以先点击"测试登录"验证
4. 点击"保存"

完成！系统会每 6 小时自动签到。

### 方式二：直接运行（不使用 Docker）

#### 1. 安装依赖

```bash
# 安装 UV
pip install uv

# 安装项目依赖
uv sync

# 安装额外依赖
uv pip install fastapi uvicorn[standard] apscheduler cryptography

# 安装 Playwright 浏览器
uv run playwright install chromium
```

#### 2. 创建数据目录

```bash
mkdir -p data
```

#### 3. 启动服务

**启动 Web 服务：**
```bash
python web/api.py
```

**启动定时任务（另一个终端）：**
```bash
python web/scheduler.py
```

或者使用后台运行：
```bash
nohup python web/api.py > logs/api.log 2>&1 &
nohup python web/scheduler.py > logs/scheduler.log 2>&1 &
```

#### 4. 访问管理界面

打开浏览器访问：`http://localhost:8080`

## 使用说明

### 账号管理

**添加账号：**
1. 点击"➕ 添加账号"按钮
2. 填写账号信息：
   - 账号名称：自定义，方便识别
   - 用户名/邮箱：登录 AnyRouter 的用户名
   - 密码：登录密码
   - 平台：选择 AnyRouter 或 AgentRouter
3. 点击"🧪 测试登录"验证账号（推荐）
4. 点击"💾 保存"

**编辑账号：**
- 点击账号行的"编辑"按钮
- 修改账号名称或密码
- 密码留空表示不修改

**禁用/启用账号：**
- 点击"禁用"按钮暂停该账号的自动签到
- 禁用的账号不会被定时任务处理

**删除账号：**
- 点击"删除"按钮
- 确认后会删除账号及其所有历史记录

### 签到操作

**手动签到：**
- 单个账号：点击账号行的"签到"按钮
- 全部账号：点击顶部的"🔄 全部签到"按钮

**自动签到：**
- 系统会每 6 小时自动对所有启用的账号进行签到
- 执行时间：00:00、06:00、12:00、18:00

### 查看信息

**统计卡片：**
- 总账号数：所有账号数量
- 已启用账号：正在自动签到的账号数
- 今日签到成功：今天成功签到的次数
- 总余额：所有账号的余额总和

**签到日志：**
- 显示最近 50 条签到记录
- 包含账号名称、成功/失败状态、时间

**余额查看：**
- 点击账号的"查看余额"按钮
- 显示当前余额和已使用额度

## 通知配置

系统支持在签到失败时发送通知。配置方式：

### Docker 部署

在 `docker-compose.yml` 中添加环境变量，或创建 `.env` 文件。

### 直接运行

创建 `.env` 文件，或设置系统环境变量。

### 通知触发条件

- ❌ 任何账号签到失败
- 仅失败时通知，避免频繁打扰

## 数据管理

### 数据存储位置

所有数据存储在 `data/` 目录：
- `data/checkin.db`：SQLite 数据库（账号、日志、余额历史）
- `data/secret.key`：加密密钥（用于加密存储密码）

### 备份数据

```bash
# 停止服务
docker-compose down

# 备份数据目录
tar -czf anyrouter-data-backup-$(date +%Y%m%d).tar.gz data/

# 重启服务
docker-compose up -d
```

### 恢复数据

```bash
# 停止服务
docker-compose down

# 解压备份
tar -xzf anyrouter-data-backup-YYYYMMDD.tar.gz

# 重启服务
docker-compose up -d
```

## 维护操作

### 查看日志

**Docker 部署：**
```bash
# 查看实时日志
docker-compose logs -f

# 查看最近 100 行
docker-compose logs --tail=100
```

**直接运行：**
```bash
# 查看 API 日志
tail -f logs/api.log

# 查看调度器日志
tail -f logs/scheduler.log
```

### 重启服务

**Docker 部署：**
```bash
docker-compose restart
```

**直接运行：**
```bash
# 停止进程
pkill -f "python web/api.py"
pkill -f "python web/scheduler.py"

# 重新启动
nohup python web/api.py > logs/api.log 2>&1 &
nohup python web/scheduler.py > logs/scheduler.log 2>&1 &
```

### 更新系统

```bash
# 拉取最新代码
git pull

# 重新构建并启动
docker-compose down
docker-compose build
docker-compose up -d
```

## 安全建议

1. **修改端口**：在 `docker-compose.yml` 中将 `8080:8080` 改为其他端口
2. **启用防火墙**：只允许可信 IP 访问
3. **使用反向代理**：通过 Nginx 添加 HTTPS 和访问控制
4. **定期备份**：设置定时任务自动备份数据库

### Nginx 反向代理示例

```nginx
server {
    listen 80;
    server_name your-domain.com;

    location / {
        proxy_pass http://127.0.0.1:8080;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

## 故障排查

### 1. 无法访问 Web 界面

检查服务是否运行：
```bash
docker-compose ps
# 或
ps aux | grep python
```

检查端口是否被占用：
```bash
netstat -tulpn | grep 8080
```

### 2. 登录测试失败

- 检查用户名和密码是否正确
- 确认 Playwright 浏览器已安装
- 查看日志获取详细错误信息

### 3. 自动签到不执行

检查调度器是否运行：
```bash
docker-compose logs | grep SCHEDULER
```

手动测试签到任务：
```bash
docker-compose exec anyrouter-checkin python web/scheduler.py test
```

### 4. 数据库锁定错误

这通常是并发访问导致的：
```bash
# 停止服务
docker-compose down

# 删除锁文件（如果存在）
rm -f data/checkin.db-journal

# 重启服务
docker-compose up -d
```

## 常见问题

**Q: 密码存储安全吗？**
A: 密码使用 Fernet 对称加密存储在本地数据库中，密钥文件 `data/secret.key` 需妥善保管。

**Q: 可以同时运行 GitHub Actions 版本吗？**
A: 可以，但建议只使用一种方式，避免重复签到。

**Q: 支持其他平台吗？**
A: 当前专注于 AnyRouter，其他 NewAPI/OneAPI 平台需要根据实际情况调整代码。

**Q: 如何修改签到时间？**
A: 编辑 `web/scheduler.py`，修改 `CronTrigger(hour='*/6')` 中的时间表达式。

## 技术支持

遇到问题请：
1. 查看日志获取详细错误信息
2. 在 GitHub 提交 Issue
3. 提供日志和错误截图

## 许可证

本项目仅供学习研究使用，使用前请确保遵守相关网站的使用条款。
