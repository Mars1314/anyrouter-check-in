#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""从数据库导出账号配置到环境变量格式"""

import sys
import json

sys.stdout.reconfigure(encoding='utf-8')

try:
    from web.database import db

    print("正在从数据库读取账号配置...")

    accounts = db.get_all_accounts()

    if not accounts:
        print("❌ 数据库中没有账号配置")
        sys.exit(1)

    print(f"找到 {len(accounts)} 个账号\n")

    # 构建环境变量格式的配置
    env_accounts = []

    for account in accounts:
        account_dict = {
            "name": account['username'],
            "provider": account['provider'],
            "api_user": account['api_user'],
            "email": account.get('email', '')
        }

        # 根据认证方式添加 cookies
        if account['auth_type'] == 'cookies':
            account_dict['cookies'] = json.loads(account['cookies'])
        elif account['auth_type'] == 'password':
            # 如果是密码认证，需要先登录获取 cookies
            print(f"⚠️  警告: 账号 {account['username']} 使用密码认证")
            print(f"   在 GitHub Actions 中运行时，需要使用 cookies 认证方式")
            print(f"   请在 Web 界面中切换到 cookies 认证模式\n")
            continue

        env_accounts.append(account_dict)

        print(f"账号: {account['username']}")
        print(f"  Provider: {account['provider']}")
        print(f"  Email: {account.get('email', '❌ 未配置')}")
        if not account.get('email'):
            print(f"  ⚠️  警告: 该账号未配置邮箱，不会收到单独的签到邮件！")
        print()

    if not env_accounts:
        print("❌ 没有可导出的账号（所有账号都使用密码认证）")
        sys.exit(1)

    # 生成环境变量格式（单行 JSON）
    env_json = json.dumps(env_accounts, ensure_ascii=False, separators=(',', ':'))

    print("=" * 60)
    print("导出的配置（复制以下内容到 .env 文件或 GitHub Secrets）")
    print("=" * 60)
    print(f"\nANYROUTER_ACCOUNTS={env_json}\n")

    print("=" * 60)
    print("配置说明")
    print("=" * 60)
    print("1. 本地测试: 将上面的配置复制到 .env 文件中")
    print("2. GitHub Actions: 在 GitHub 仓库的 Settings > Secrets 中")
    print("   添加名为 ANYROUTER_ACCOUNTS 的 secret，值为上面的 JSON")
    print("3. 确保每个账号都配置了 email 字段，否则不会收到邮件通知")

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)
