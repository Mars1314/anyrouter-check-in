# 双认证模式说明

系统现在支持两种账号认证方式，满足不同用户的需求。

## 两种认证方式对比

| 特性 | 密码认证 | Cookies 认证 |
|------|----------|--------------|
| **便利性** | ⭐⭐⭐⭐⭐ 最方便 | ⭐⭐⭐ 需要手动获取 |
| **自动化** | ✅ 完全自动 | ❌ 手动操作 |
| **安全性** | ⭐⭐⭐⭐ 密码加密存储 | ⭐⭐⭐⭐ Cookies 加密存储 |
| **稳定性** | ⭐⭐⭐⭐⭐ 自动刷新 | ⭐⭐⭐ Cookie 可能过期 |
| **适用场景** | 可以提供账号密码 | 无法提供账号密码 |
| **推荐程度** | ⭐⭐⭐⭐⭐ **强烈推荐** | ⭐⭐⭐ 备选方案 |

## 方式一：密码认证（推荐）

### 工作原理

1. 你提供账号的用户名和密码
2. 系统使用 Playwright 自动打开浏览器登录
3. 自动获取登录后的 Cookies 和 API User
4. 每次签到前自动重新登录，确保 Cookies 始终有效

### 优点

- ✅ **完全自动化** - 设置一次，永久使用
- ✅ **不会过期** - 每次自动重新登录
- ✅ **无需手动操作** - 系统自动处理一切
- ✅ **测试功能** - 可以在添加前测试登录

### 缺点

- ⚠️ 需要提供账号密码（已加密存储）
- ⚠️ 依赖浏览器自动化（需要 Playwright）

### 使用步骤

1. 点击「添加账号」
2. 选择认证方式：**用户名密码**（默认）
3. 填写：
   - 账号名称：例如 "我的主账号"
   - 用户名/邮箱：你的 AnyRouter 账号
   - 密码：你的 AnyRouter 密码
   - 平台：选择 AnyRouter
4. （可选）点击「测试登录」验证账号密码是否正确
5. 点击「保存」

### 示例

```
账号名称: 我的主账号
用户名/邮箱: user@example.com
密码: your_password
平台: AnyRouter
```

## 方式二：Cookies 认证（备选）

### 工作原理

1. 你手动登录 AnyRouter 网站
2. 从浏览器开发者工具提取 Cookies 和 API User
3. 将这些信息保存到系统
4. 系统使用这些 Cookies 进行签到

### 优点

- ✅ **不需要提供密码** - 适合共享账号的场景
- ✅ **立即可用** - 无需等待自动登录
- ✅ **隐私保护** - 不保存账号密码

### 缺点

- ⚠️ **需要手动获取** - 第一次配置较复杂
- ⚠️ **可能过期** - Cookies 有效期有限，过期需重新获取
- ⚠️ **无法自动刷新** - Cookie 过期后签到会失败

### 使用步骤

详细步骤请参考 [COOKIES_GUIDE.md](./COOKIES_GUIDE.md)

简要步骤：

1. 登录 https://anyrouter.top
2. 按 F12 打开开发者工具
3. 从 Application → Cookies 中获取 session cookie
4. 从 Network 请求头中获取 new-api-user
5. 在添加账号时选择「Cookies + API User」
6. 填写获取的信息

### 示例

```json
Cookies:
{
  "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "acw_tc": "abc123..."
}

API User: user_123456
```

## 技术实现

### 数据库设计

账号表增加了以下字段：

```sql
CREATE TABLE accounts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT NOT NULL,

    -- 密码认证字段
    username TEXT,
    password TEXT,  -- 加密存储

    -- Cookies 认证字段
    cookies TEXT,   -- 加密存储
    api_user TEXT,

    -- 认证类型标识
    auth_type TEXT DEFAULT 'password',  -- 'password' 或 'cookies'

    provider TEXT DEFAULT 'anyrouter',
    enabled INTEGER DEFAULT 1,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

### 签到流程

#### 密码认证流程

```python
# 1. 获取账号信息（包含加密的密码）
account = db.get_account(account_id)

# 2. 自动登录
login_result = await login_anyrouter(account['username'], account['password'])
cookies = login_result['cookies']
api_user = login_result['api_user']

# 3. 使用获取的 cookies 签到
await check_in_account(cookies, api_user)
```

#### Cookies 认证流程

```python
# 1. 获取账号信息（包含加密的 cookies）
account = db.get_account(account_id)

# 2. 直接使用保存的 cookies
cookies = json.loads(account['cookies'])
api_user = account['api_user']

# 3. 使用 cookies 签到
await check_in_account(cookies, api_user)
```

### 安全性

- ✅ 密码使用 Fernet 对称加密存储
- ✅ Cookies 使用 Fernet 对称加密存储
- ✅ 加密密钥独立存储在 `data/secret.key`
- ✅ 数据库文件独立存储在 `data/checkin.db`
- ✅ 支持环境变量配置路径

## 迁移指南

### 从旧版本升级

如果你之前使用的是旧版本（只支持密码认证），升级后：

1. **无需任何操作** - 旧账号会自动标记为 `password` 认证类型
2. **继续正常使用** - 所有功能保持兼容
3. **可以添加新类型** - 可以添加使用 Cookies 认证的新账号

数据库迁移会自动执行：

```python
# 检查并添加新字段（用于数据库升级）
try:
    cursor.execute("SELECT cookies FROM accounts LIMIT 1")
except Exception:
    # 字段不存在，添加新字段
    cursor.execute("ALTER TABLE accounts ADD COLUMN cookies TEXT")
    cursor.execute("ALTER TABLE accounts ADD COLUMN api_user TEXT")
    cursor.execute("ALTER TABLE accounts ADD COLUMN auth_type TEXT DEFAULT 'password'")
```

## 常见问题

### Q: 应该选择哪种认证方式？

A: **强烈推荐密码认证**，除非你：
- 无法提供账号密码（比如别人分享给你的账号）
- 不想保存密码
- 只是临时使用

### Q: 密码存储安全吗？

A: 是的，密码使用 Fernet 加密存储，加密密钥独立保存，即使数据库泄露也无法解密。

### Q: Cookies 会过期吗？

A: 会的。通常几天到几周不等（取决于 AnyRouter 的设置）。密码认证不存在这个问题。

### Q: 能否混合使用两种认证方式？

A: 可以！你可以为不同账号使用不同的认证方式，系统会自动识别并处理。

### Q: 如何知道 Cookies 是否过期？

A: 如果签到失败且日志显示「认证失败」或「未授权」，可能是 Cookie 过期了。你需要重新获取 Cookies 或改用密码认证。

### Q: 能否从 Cookies 认证切换到密码认证？

A: 暂不支持。建议删除旧账号，重新添加并选择密码认证。

## 推荐配置

### 个人用户（有密码）

```
✅ 使用：密码认证
理由：完全自动化，永不过期
```

### 共享账号（无密码）

```
✅ 使用：Cookies 认证
理由：不需要密码，保护隐私
注意：定期更新 Cookies
```

### 企业/团队（多账号）

```
✅ 主要账号：密码认证
✅ 临时账号：Cookies 认证
理由：主力账号稳定，临时账号灵活
```

## 技术支持

如有问题，请查看：
- [COOKIES_GUIDE.md](./COOKIES_GUIDE.md) - Cookies 获取详细指南
- [LOCAL_GUIDE.md](./LOCAL_GUIDE.md) - 本地开发指南
- [README.md](./README.md) - 项目总体说明

或提交 Issue 到 GitHub 仓库。
