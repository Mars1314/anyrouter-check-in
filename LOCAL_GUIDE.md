# 本地开发和使用指南

## 目录

- [环境要求](#环境要求)
- [本地开发启动](#本地开发启动)
- [使用说明](#使用说明)
- [测试功能](#测试功能)
- [常见问题](#常见问题)
- [开发调试](#开发调试)

## 环境要求

- **Python**: 3.11 或更高版本
- **操作系统**: Windows / Linux / macOS
- **内存**: 至少 2GB 可用内存（Playwright 需要）
- **磁盘**: 至少 1GB 可用空间（浏览器下载）

## 本地开发启动

### 步骤 1：克隆项目

```bash
git clone https://github.com/your/anyrouter-check-in.git
cd anyrouter-check-in
```

### 步骤 2：安装依赖

**安装 UV 包管理器：**

```bash
# Windows (PowerShell)
pip install uv

# Linux / macOS
pip3 install uv
```

**安装项目依赖：**

```bash
# 安装所有依赖（包括 Web 服务相关依赖）
uv sync

# 如果出现问题，可以手动安装
uv pip install httpx[http2] playwright python-dotenv fastapi uvicorn[standard] apscheduler cryptography
```

**安装 Playwright 浏览器：**

```bash
# 仅安装 Chromium（推荐）
uv run playwright install chromium

# 如果遇到依赖问题，使用以下命令
uv run playwright install chromium --with-deps
```

### 步骤 3：创建必要的目录

```bash
# Windows (PowerShell)
New-Item -ItemType Directory -Force -Path data, logs

# Linux / macOS
mkdir -p data logs
```

### 步骤 4：启动服务

您有两种启动方式：

#### 方式一：完整启动（Web + 定时任务）

需要打开**两个终端窗口**：

**终端 1 - 启动 Web 服务：**
```bash
uv run python web/api.py
```

看到以下输出表示成功：
```
🚀 Starting AnyRouter 签到管理系统...
📝 访问地址: http://localhost:8080
INFO:     Started server process [xxxxx]
INFO:     Uvicorn running on http://0.0.0.0:8080
```

**终端 2 - 启动定时任务调度器：**
```bash
uv run python web/scheduler.py
```

看到以下输出表示成功：
```
🚀 定时任务调度器已启动
📅 签到任务将每 6 小时执行一次
```

#### 方式二：仅启动 Web 服务（用于测试）

如果只想测试 Web 界面和手动签到，不需要自动定时任务：

```bash
uv run python web/api.py
```

### 步骤 5：访问管理界面

打开浏览器访问：**http://localhost:8080**

您应该能看到管理界面，包含：
- 统计卡片（总账号数、今日签到等）
- 添加账号按钮
- 账号列表
- 签到日志

## 使用说明

### 添加账号

1. 点击页面顶部的 **"➕ 添加账号"** 按钮
2. 在弹出的对话框中填写信息：
   - **账号名称**：自定义名称，方便识别（例如：主账号、备用账号）
   - **用户名/邮箱**：登录 AnyRouter 的邮箱地址
   - **密码**：登录密码
   - **平台**：选择 AnyRouter（默认）
3. **（推荐）点击 "🧪 测试登录" 按钮**
   - 系统会自动启动浏览器登录验证
   - 成功后会提示 "登录测试成功！"
   - 失败会显示具体错误信息
4. 点击 **"💾 保存"** 按钮

### 编辑账号

1. 在账号列表中找到要编辑的账号
2. 点击 **"编辑"** 按钮
3. 修改账号名称或密码（密码留空表示不修改）
4. 点击 **"💾 保存"**

### 禁用/启用账号

- 点击账号行的 **"禁用"** 按钮：暂停该账号的自动签到
- 点击 **"启用"** 按钮：恢复自动签到
- 禁用的账号不会被定时任务处理

### 手动签到

**单个账号签到：**
1. 点击账号行的 **"签到"** 按钮
2. 等待处理（会自动登录并签到）
3. 查看结果提示

**全部账号签到：**
1. 点击顶部的 **"🔄 全部签到"** 按钮
2. 确认操作
3. 等待所有账号处理完成
4. 查看签到结果统计

### 查看余额

1. 点击账号的 **"查看余额"** 按钮
2. 弹窗显示当前余额和已使用额度

### 查看签到日志

页面底部自动显示最近 50 条签到记录，包括：
- 账号名称
- 成功/失败状态
- 错误信息（如果有）
- 签到时间

### 刷新数据

点击顶部的 **"🔃 刷新数据"** 按钮，重新加载所有数据。

## 测试功能

### 测试自动登录模块

单独测试自动登录功能，验证账号是否可以正常登录：

```bash
uv run python utils/auto_login.py 你的邮箱 你的密码
```

**示例：**
```bash
uv run python utils/auto_login.py test@example.com mypassword123
```

**成功输出示例：**
```
[LOGIN] Starting auto login for test@example.com
[LOGIN] Navigating to https://anyrouter.top/login
[LOGIN] Filling username: test@example.com
[LOGIN] Filling password
[LOGIN] Clicking login button
[LOGIN] Waiting for login to complete...
[LOGIN] Login successful, redirected to panel
[LOGIN] Got 8 cookies
[LOGIN] Session cookie obtained: abc123session...
[LOGIN] Found api_user: 12345
[SUCCESS] Login successful! api_user: 12345

✅ Login test successful!
Cookies: {'session': 'abc123...', 'acw_tc': '...', ...}
API User: 12345
```

### 测试数据库功能

测试数据库创建和基本操作：

```bash
uv run python web/database.py
```

**成功输出示例：**
```
Testing database...
✅ Added account with ID: 1
✅ Retrieved account: 测试账号 (test@example.com)
✅ Added checkin log
✅ Added balance record
✅ Statistics: {...}
✅ Deleted test account

✅ All database tests passed!
```

### 测试签到任务

测试完整的自动签到流程（不启动定时器）：

```bash
uv run python web/scheduler.py test
```

这会：
1. 读取数据库中所有启用的账号
2. 依次自动登录并签到
3. 记录日志和余额
4. 显示签到结果

**注意**：运行前需要先在 Web 界面添加账号。

### 测试 API 接口

启动 Web 服务后，访问 API 文档：

- **Swagger UI**: http://localhost:8080/docs
- **ReDoc**: http://localhost:8080/redoc

可以在这里测试所有 API 接口。

## 常见问题

### 1. 端口被占用

**问题**：启动时提示 `Address already in use` 或 `port 8080 is already in use`

**解决方案 A - 修改端口：**

编辑 `web/api.py`，找到最后一行：
```python
uvicorn.run(app, host='0.0.0.0', port=8080)
```

改为其他端口：
```python
uvicorn.run(app, host='0.0.0.0', port=8888)
```

**解决方案 B - 停止占用端口的进程：**

```bash
# Windows
netstat -ano | findstr :8080
taskkill /PID <进程ID> /F

# Linux / macOS
lsof -i :8080
kill -9 <进程ID>
```

### 2. Playwright 浏览器未安装

**问题**：运行时提示 `Executable doesn't exist` 或找不到浏览器

**解决方案：**
```bash
# 重新安装浏览器
uv run playwright install chromium --with-deps

# 如果网络问题，可以设置镜像
set PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/  # Windows
export PLAYWRIGHT_DOWNLOAD_HOST=https://npmmirror.com/mirrors/playwright/  # Linux/macOS
uv run playwright install chromium
```

### 3. 数据库权限问题

**问题**：提示无法创建或写入数据库文件

**解决方案：**
```bash
# 确保 data 目录存在且有写权限
mkdir -p data
chmod 755 data  # Linux/macOS

# Windows 下检查文件夹权限，确保当前用户有写权限
```

### 4. 登录测试失败

**问题**：点击"测试登录"失败，显示错误

**可能原因和解决方案：**

A. **用户名或密码错误**
   - 检查输入是否正确
   - 尝试在浏览器中手动登录验证

B. **网络连接问题**
   - 检查是否能访问 https://anyrouter.top
   - 检查防火墙或代理设置

C. **Playwright 问题**
   - 查看终端输出的详细错误
   - 尝试重新安装 Playwright

D. **AnyRouter 网站变化**
   - 网站可能更新了登录页面
   - 查看日志中的具体错误信息

### 5. 模块导入错误

**问题**：提示 `ModuleNotFoundError` 或 `ImportError`

**解决方案：**
```bash
# 重新安装依赖
uv sync

# 或手动安装缺失的包
uv pip install <package_name>
```

### 6. 签到失败

**问题**：手动签到或自动签到失败

**检查步骤：**

1. 查看签到日志中的错误信息
2. 尝试"测试登录"验证账号是否有效
3. 检查终端输出的详细日志
4. 确认账号状态为"已启用"

### 7. 定时任务不执行

**问题**：自动签到没有按时执行

**解决方案：**

1. 确认调度器正在运行：
   ```bash
   # 查看调度器输出
   # 应该看到类似输出：
   # 🚀 定时任务调度器已启动
   # 📅 签到任务将每 6 小时执行一次
   ```

2. 检查是否有启用的账号：
   - 在 Web 界面确认账号状态为"已启用"

3. 手动触发测试：
   ```bash
   uv run python web/scheduler.py test
   ```

## 开发调试

### 启用调试模式

**API 服务调试：**

编辑 `web/api.py`，添加调试参数：
```python
if __name__ == '__main__':
    import uvicorn
    uvicorn.run(app, host='0.0.0.0', port=8080, reload=True, log_level='debug')
```

`reload=True` 会在代码修改后自动重启服务。

### 查看详细日志

**方式一：终端输出**

直接查看终端输出，所有日志都会打印到控制台。

**方式二：重定向到文件**

```bash
# Windows (PowerShell)
uv run python web/api.py > logs/api.log 2>&1

# Linux / macOS
uv run python web/api.py > logs/api.log 2>&1 &
```

### 数据库管理

**查看数据库内容：**

```bash
# 安装 sqlite3 命令行工具（如果没有）
# Windows: 下载 https://www.sqlite.org/download.html
# Linux: sudo apt install sqlite3
# macOS: brew install sqlite3

# 打开数据库
sqlite3 data/checkin.db

# 查看所有表
.tables

# 查看账号
SELECT * FROM accounts;

# 查看签到日志
SELECT * FROM checkin_logs ORDER BY created_at DESC LIMIT 10;

# 查看余额历史
SELECT * FROM balance_history ORDER BY created_at DESC LIMIT 10;

# 退出
.quit
```

**备份数据库：**

```bash
# 简单复制
cp data/checkin.db data/checkin.db.backup

# 或使用 sqlite3 导出
sqlite3 data/checkin.db ".backup data/checkin.db.backup"
```

**重置数据库：**

```bash
# 停止所有服务
# 删除数据库文件
rm -f data/checkin.db data/secret.key

# 重新启动服务，会自动创建新数据库
```

### 修改签到时间

编辑 `web/scheduler.py`，找到以下行：

```python
scheduler.add_job(auto_checkin_task, CronTrigger(hour='*/6'), ...)
```

修改为你想要的时间：

```python
# 每天固定时间执行（例如：每天 09:00 和 21:00）
CronTrigger(hour='9,21', minute='0')

# 每 4 小时执行一次
CronTrigger(hour='*/4')

# 每小时执行一次
CronTrigger(hour='*')

# 每天 08:00 执行
CronTrigger(hour='8', minute='0')
```

### 前端开发

前端代码在 `web/templates/index.html`，使用了 CDN 加载的库：
- Vue.js 3
- Tailwind CSS
- Axios
- Chart.js

修改前端代码后，刷新浏览器即可看到效果（无需重启服务）。

### API 测试工具

推荐使用以下工具测试 API：

- **内置文档**: http://localhost:8080/docs
- **Postman**: 导入 API 进行测试
- **curl**: 命令行测试

**示例：获取账号列表**
```bash
curl http://localhost:8080/api/accounts
```

**示例：添加账号**
```bash
curl -X POST http://localhost:8080/api/accounts \
  -H "Content-Type: application/json" \
  -d '{"name":"测试","username":"test@example.com","password":"pwd123","provider":"anyrouter"}'
```

## 配置通知（可选）

如果想在签到失败时收到通知，创建 `.env` 文件：

```bash
# 创建 .env 文件
touch .env
```

在 `.env` 文件中添加配置：

```env
# 邮件通知
EMAIL_USER=your@email.com
EMAIL_PASS=your_password_or_app_key
EMAIL_TO=receiver@email.com
CUSTOM_SMTP_SERVER=smtp.gmail.com  # 可选，默认自动检测

# 钉钉机器人
DINGDING_WEBHOOK=https://oapi.dingtalk.com/robot/send?access_token=xxx

# 飞书机器人
FEISHU_WEBHOOK=https://open.feishu.cn/open-apis/bot/v2/hook/xxx

# 企业微信机器人
WEIXIN_WEBHOOK=https://qyapi.weixin.qq.com/cgi-bin/webhook/send?key=xxx

# PushPlus
PUSHPLUS_TOKEN=your_pushplus_token

# Server酱
SERVERPUSHKEY=your_server_push_key

# Telegram Bot
TELEGRAM_BOT_TOKEN=your_telegram_bot_token
TELEGRAM_CHAT_ID=your_telegram_chat_id
```

重启服务后生效。

## 性能优化建议

### 减少浏览器启动时间

Playwright 启动浏览器比较耗时，如果账号多，可以考虑：

1. 使用更快的服务器或电脑
2. 为 Playwright 配置更少的启动参数
3. 考虑使用更轻量的登录方式（如果 API 支持）

### 数据库优化

如果账号和日志很多，可以定期清理旧日志：

```sql
-- 删除 30 天前的签到日志
DELETE FROM checkin_logs WHERE created_at < datetime('now', '-30 days');

-- 删除 90 天前的余额历史
DELETE FROM balance_history WHERE created_at < datetime('now', '-90 days');
```

可以创建定时任务自动执行。

## 安全建议

1. **不要暴露到公网**：本地开发只在 localhost 访问
2. **定期备份数据**：备份 `data/` 目录
3. **保护密钥文件**：`data/secret.key` 是加密密钥，不要泄露
4. **使用强密码**：设置 AnyRouter 账号的强密码
5. **及时更新**：定期 `git pull` 获取最新代码

## 从 GitHub Actions 迁移

如果您之前使用 GitHub Actions 版本，想迁移到本地：

1. 启动本地服务
2. 在 Web 界面手动添加账号（使用用户名密码）
3. 测试签到功能正常
4. 可以保留 GitHub Actions 作为备份，或者删除

## 故障排查流程

遇到问题时，按以下顺序检查：

1. **查看终端输出**：是否有错误信息
2. **检查服务状态**：Web 服务和调度器是否都在运行
3. **测试登录功能**：单独运行 `auto_login.py` 测试
4. **查看数据库**：确认账号已正确保存
5. **查看日志表**：检查签到日志中的错误信息
6. **网络连接**：确认能访问 AnyRouter 网站
7. **提交 Issue**：如果无法解决，在 GitHub 提交详细问题

## 获取帮助

- **GitHub Issues**: https://github.com/your/anyrouter-check-in/issues
- **查看文档**: README_SERVER.md, QUICKSTART_SERVER.md
- **查看示例**: IMPLEMENTATION.md

---

祝你使用愉快！🎉
