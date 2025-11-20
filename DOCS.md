# 📚 文档导航

欢迎使用 AnyRouter 签到管理系统！根据您的需求选择相应的文档：

## 🎯 我想要...

### → 快速开始（5分钟）
**你有服务器或想本地测试**
- 📄 [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md) - Docker 一键部署
- 📄 [LOCAL_GUIDE.md](LOCAL_GUIDE.md) - 本地开发和测试

**你没有服务器，想用免费的 GitHub Actions**
- 📄 [README.md](README.md) - 查看"GitHub Actions 版"部分

### → 深入了解

**完整部署指南**
- 📄 [README_SERVER.md](README_SERVER.md) - 服务器版完整文档
  - 部署方式对比
  - 详细安装步骤
  - 配置通知
  - 安全建议
  - 故障排查

**技术架构**
- 📄 [IMPLEMENTATION.md](IMPLEMENTATION.md) - 系统实现说明
  - 功能清单
  - 架构图
  - 工作流程
  - 技术栈
  - 文件说明

**快速参考**
- 📄 [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 速查手册
  - 常用命令
  - API 接口
  - 故障排查
  - 性能参考

**开发指南**
- 📄 [CLAUDE.md](CLAUDE.md) - Claude Code 开发指南
  - 项目架构
  - 开发命令
  - 配置说明

## 📖 文档分类

### 入门文档

| 文档 | 适合人群 | 内容 |
|------|----------|------|
| [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md) | 新用户 | 5分钟快速部署 |
| [LOCAL_GUIDE.md](LOCAL_GUIDE.md) | 开发者 | 本地开发详细说明 |
| [README.md](README.md) | 所有用户 | 项目介绍和 GitHub Actions 版 |

### 进阶文档

| 文档 | 适合人群 | 内容 |
|------|----------|------|
| [README_SERVER.md](README_SERVER.md) | 运维人员 | 完整部署和维护 |
| [IMPLEMENTATION.md](IMPLEMENTATION.md) | 开发者 | 技术实现细节 |
| [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | 所有用户 | 命令速查 |

### 开发文档

| 文档 | 适合人群 | 内容 |
|------|----------|------|
| [CLAUDE.md](CLAUDE.md) | Claude Code 用户 | AI 辅助开发指南 |

## 🗺️ 使用场景导航

### 场景 1：我是新用户，想快速体验

1. 看 → [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md)
2. 执行 → `docker-compose up -d`
3. 访问 → http://localhost:8080
4. 添加账号 → 输入用户名密码

### 场景 2：我想在本地开发和调试

1. 看 → [LOCAL_GUIDE.md](LOCAL_GUIDE.md)
2. 执行 → `uv sync` + `uv run python web/api.py`
3. 查看 → [QUICK_REFERENCE.md](QUICK_REFERENCE.md) 获取常用命令

### 场景 3：我要部署到生产服务器

1. 看 → [README_SERVER.md](README_SERVER.md)
2. 关注 → 安全建议、备份策略
3. 配置 → Nginx 反向代理、HTTPS

### 场景 4：我想了解技术实现

1. 看 → [IMPLEMENTATION.md](IMPLEMENTATION.md)
2. 了解 → 架构设计、工作流程
3. 查看 → 源代码注释

### 场景 5：我遇到问题了

1. 看 → [LOCAL_GUIDE.md](LOCAL_GUIDE.md#常见问题)
2. 看 → [README_SERVER.md](README_SERVER.md#故障排除)
3. 查 → [QUICK_REFERENCE.md](QUICK_REFERENCE.md#故障排查)
4. 找不到解决方案 → [提交 Issue](https://github.com/your/anyrouter-check-in/issues)

### 场景 6：我没有服务器

1. 看 → [README.md](README.md#使用方法github-actions-版)
2. 使用 → GitHub Actions 免费方案

## 📝 文档详细介绍

### [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md)
**5分钟快速开始指南**

最简洁的入门文档，适合想快速体验的用户。

**包含：**
- ✅ 5步骤部署流程
- ✅ 功能演示
- ✅ 常用命令
- ✅ 通知配置
- ✅ 安全建议

**不包含：**
- ❌ 详细原理说明
- ❌ 复杂配置选项
- ❌ 深入的故障排查

---

### [LOCAL_GUIDE.md](LOCAL_GUIDE.md)
**本地开发和使用指南**

最详细的本地使用文档，适合开发者和想深入了解的用户。

**包含：**
- ✅ 环境要求
- ✅ 详细安装步骤
- ✅ 启动方式对比
- ✅ 完整功能说明
- ✅ 测试方法
- ✅ 常见问题解答
- ✅ 开发调试技巧
- ✅ 数据库管理
- ✅ 配置优化

**适合：**
- 本地开发测试
- 学习源码
- 自定义修改

---

### [README_SERVER.md](README_SERVER.md)
**服务器部署完整指南**

生产环境部署的完整文档。

**包含：**
- ✅ 功能特性介绍
- ✅ 快速开始
- ✅ 使用说明
- ✅ 通知配置
- ✅ 数据管理
- ✅ 维护操作
- ✅ 安全建议
- ✅ 故障排查
- ✅ 常见问题

**适合：**
- 服务器部署
- 生产环境
- 运维人员

---

### [IMPLEMENTATION.md](IMPLEMENTATION.md)
**系统实现总结**

技术实现的详细说明。

**包含：**
- ✅ 已完成功能清单
- ✅ 系统架构图
- ✅ 核心工作流程
- ✅ 技术栈说明
- ✅ 文件清单
- ✅ 使用场景
- ✅ 优化建议
- ✅ 版本对比

**适合：**
- 开发者
- 想了解实现原理
- 准备二次开发

---

### [QUICK_REFERENCE.md](QUICK_REFERENCE.md)
**快速参考手册**

命令和操作的速查表。

**包含：**
- ✅ 启动命令
- ✅ 测试命令
- ✅ Web 操作
- ✅ API 接口
- ✅ 目录结构
- ✅ 环境变量
- ✅ 故障排查
- ✅ 性能参考

**适合：**
- 快速查找命令
- 日常操作参考
- 问题快速定位

---

### [README.md](README.md)
**项目主文档**

项目总览和 GitHub Actions 版本说明。

**包含：**
- ✅ 项目介绍
- ✅ 功能特性
- ✅ 两种使用方式对比
- ✅ GitHub Actions 详细配置
- ✅ 通知配置
- ✅ 故障排除

**适合：**
- 项目概览
- GitHub Actions 用户
- 首次接触项目

---

### [CLAUDE.md](CLAUDE.md)
**Claude Code 开发指南**

为 Claude Code 提供的项目架构说明。

**包含：**
- ✅ 项目概览
- ✅ 开发命令
- ✅ 架构说明
- ✅ 配置方案
- ✅ 测试说明

**适合：**
- 使用 Claude Code 开发
- AI 辅助开发

## 💡 建议阅读顺序

### 新用户推荐路径：
1. [README.md](README.md) - 了解项目
2. [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md) - 快速部署
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 日常使用

### 开发者推荐路径：
1. [README.md](README.md) - 项目介绍
2. [IMPLEMENTATION.md](IMPLEMENTATION.md) - 技术架构
3. [LOCAL_GUIDE.md](LOCAL_GUIDE.md) - 本地开发
4. [CLAUDE.md](CLAUDE.md) - 开发规范

### 运维人员推荐路径：
1. [README.md](README.md) - 项目介绍
2. [README_SERVER.md](README_SERVER.md) - 部署指南
3. [QUICK_REFERENCE.md](QUICK_REFERENCE.md) - 运维命令

## 🔍 快速查找

**我想找...**

| 想找的内容 | 查看文档 | 章节 |
|-----------|---------|------|
| 安装步骤 | [LOCAL_GUIDE.md](LOCAL_GUIDE.md) | 本地开发启动 |
| Docker 部署 | [QUICKSTART_SERVER.md](QUICKSTART_SERVER.md) | 5分钟部署 |
| API 接口 | [QUICK_REFERENCE.md](QUICK_REFERENCE.md) | API 接口 |
| 故障排查 | [LOCAL_GUIDE.md](LOCAL_GUIDE.md) | 常见问题 |
| 配置通知 | [README_SERVER.md](README_SERVER.md) | 通知配置 |
| 架构说明 | [IMPLEMENTATION.md](IMPLEMENTATION.md) | 系统架构 |
| 测试方法 | [LOCAL_GUIDE.md](LOCAL_GUIDE.md) | 测试功能 |
| 备份数据 | [README_SERVER.md](README_SERVER.md) | 数据管理 |
| 修改端口 | [LOCAL_GUIDE.md](LOCAL_GUIDE.md) | 端口被占用 |
| 安全建议 | [README_SERVER.md](README_SERVER.md) | 安全建议 |

## 📞 获取帮助

**文档没有解决你的问题？**

1. 🔍 搜索 [已有 Issue](https://github.com/your/anyrouter-check-in/issues)
2. 💬 提交 [新 Issue](https://github.com/your/anyrouter-check-in/issues/new)
3. 📧 联系维护者

**提问时请提供：**
- 使用的文档和步骤
- 完整的错误信息
- 系统环境（操作系统、Python 版本）
- 相关日志

## 🎉 开始使用

**准备好了吗？选择你的起点：**

- 🚀 [快速开始 →](QUICKSTART_SERVER.md)
- 💻 [本地开发 →](LOCAL_GUIDE.md)
- 📖 [完整文档 →](README_SERVER.md)
- 🧠 [技术实现 →](IMPLEMENTATION.md)

---

**祝你使用愉快！** 🎊
