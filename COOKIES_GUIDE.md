# 获取 Cookies 和 API User 指南

如果你无法提供账号密码，可以手动从浏览器中提取 Cookies 和 API User。

## 方法一：使用浏览器开发者工具（推荐）

### 步骤 1: 登录 AnyRouter

1. 打开浏览器访问 https://anyrouter.top
2. 使用你的账号密码正常登录

### 步骤 2: 打开开发者工具

- **Chrome/Edge**: 按 `F12` 或 `Ctrl+Shift+I`
- **Firefox**: 按 `F12`
- **Safari**: 按 `Command+Option+I`

### 步骤 3: 获取 Cookies

1. 点击开发者工具中的 **Application** 或 **存储** 标签
2. 在左侧找到 **Cookies** → **https://anyrouter.top**
3. 找到以下重要的 cookies（复制其值）：
   - `session` - **必需**，这是最重要的认证 cookie
   - `acw_tc` - 可选，WAF 防护相关
   - `cdn_sec_tc` - 可选，CDN 安全相关
   - `acw_sc__v2` - 可选，WAF 防护相关

4. 将这些 cookies 组织成 JSON 格式：

```json
{
  "session": "这里填写 session cookie 的值",
  "acw_tc": "这里填写 acw_tc 的值（如果有）",
  "cdn_sec_tc": "这里填写 cdn_sec_tc 的值（如果有）",
  "acw_sc__v2": "这里填写 acw_sc__v2 的值（如果有）"
}
```

**最简单的情况（只要 session）：**
```json
{
  "session": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9..."
}
```

### 步骤 4: 获取 API User

1. 在开发者工具中切换到 **Network** 或 **网络** 标签
2. 刷新页面或访问 https://anyrouter.top/panel/profile
3. 在网络请求列表中找到任意一个发送到 `/api/` 的请求
4. 点击该请求，查看 **请求头**（Request Headers）
5. 找到 `new-api-user` 这个请求头，复制它的值

示例：
```
new-api-user: abc123def456
```

那么 API User 就是：`abc123def456`

## 方法二：使用浏览器控制台快速提取

### 获取 Cookies（一键复制）

1. 登录 https://anyrouter.top 后，按 `F12` 打开开发者工具
2. 切换到 **Console** 或 **控制台** 标签
3. 粘贴以下代码并按回车：

```javascript
// 提取所有 cookies 并转换为 JSON 格式
(() => {
  const cookies = document.cookie.split('; ').reduce((acc, cookie) => {
    const [name, value] = cookie.split('=');
    if (['session', 'acw_tc', 'cdn_sec_tc', 'acw_sc__v2'].includes(name)) {
      acc[name] = value;
    }
    return acc;
  }, {});

  const json = JSON.stringify(cookies, null, 2);
  console.log('复制下面的 JSON:');
  console.log(json);

  // 尝试自动复制到剪贴板
  navigator.clipboard.writeText(json).then(() => {
    console.log('✅ 已自动复制到剪贴板！');
  }).catch(() => {
    console.log('⚠️ 请手动复制上面的 JSON');
  });
})();
```

### 获取 API User（一键复制）

1. 访问 https://anyrouter.top/panel/profile
2. 在控制台粘贴以下代码：

```javascript
// 监听下一个 API 请求并提取 new-api-user
(() => {
  const observer = new PerformanceObserver((list) => {
    for (const entry of list.getEntries()) {
      if (entry.name.includes('/api/')) {
        fetch(entry.name, { method: 'HEAD' })
          .then(response => response.headers.get('new-api-user'))
          .catch(() => {
            // 从 localStorage 获取
            const userId = localStorage.getItem('userId') || localStorage.getItem('user_id');
            if (userId) {
              console.log('API User:', userId);
              navigator.clipboard.writeText(userId);
              console.log('✅ 已复制到剪贴板！');
            }
          });
        observer.disconnect();
      }
    }
  });
  observer.observe({ entryTypes: ['resource'] });
  console.log('正在等待 API 请求...');
  console.log('你也可以直接从 Network 标签的请求头中查看 new-api-user');
})();
```

或者更简单的方式，直接从 localStorage 获取：

```javascript
console.log('API User:', localStorage.getItem('userId') || localStorage.getItem('user_id'));
```

## 方法三：使用抓包工具（高级）

如果你熟悉抓包工具，可以使用：
- **Charles Proxy**
- **Fiddler**
- **Wireshark**

抓取登录后的请求，从中提取 cookies 和请求头中的 `new-api-user`。

## 常见问题

### Q: Cookies 会过期吗？

A: 会的。session cookie 通常会在一段时间后过期（具体时间取决于 AnyRouter 的设置）。如果签到失败，可能需要重新获取 cookies。

### Q: 为什么推荐使用密码认证？

A: 密码认证方式会自动处理 cookies 过期的问题，每次签到时都会重新登录获取新的 cookies，更加稳定和方便。

### Q: API User 是什么？

A: 这是 AnyRouter 用来标识用户身份的 ID，通常在登录后的 API 请求头中携带。

### Q: 我只找到了 session cookie，没有其他的 cookies 怎么办？

A: 没关系！只有 `session` cookie 就足够了，其他的 cookies 是可选的。

## 添加账号示例

完成上述步骤后，在 Web 界面添加账号时：

1. 点击「添加账号」
2. 选择认证方式：**Cookies + API User**
3. 填写：
   - **账号名称**: 例如 "我的主账号"
   - **Cookies**: 粘贴你获取的 JSON（格式如上）
   - **API User**: 粘贴你获取的 API User ID
   - **平台**: 选择 AnyRouter

4. 点击保存

## 安全提示

- **不要分享你的 cookies** - 它们相当于你的登录凭证
- **不要在公共电脑上获取 cookies**
- **定期更新 cookies** - 如果发现签到失败，可能需要重新获取
- **建议使用密码认证方式** - 更安全且自动化程度更高
