#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查邮箱配置"""

import sys
import os
from dotenv import load_dotenv

sys.stdout.reconfigure(encoding='utf-8')
load_dotenv()

print("=" * 60)
print("检查环境变量配置")
print("=" * 60)

# 检查邮箱配置
email_user = os.getenv('EMAIL_USER', '')
email_pass = os.getenv('EMAIL_PASS', '')

print(f"\n[邮箱发送配置]")
print(f"EMAIL_USER: {email_user if email_user else '❌ 未配置'}")
print(f"EMAIL_PASS: {'✅ 已配置' if email_pass else '❌ 未配置'}")

if not email_user or not email_pass:
    print("\n⚠️  警告: EMAIL_USER 或 EMAIL_PASS 未配置，无法发送邮件！")
    sys.exit(1)

# 检查账号配置
accounts_str = os.getenv('ANYROUTER_ACCOUNTS', '')
if not accounts_str:
    print("\n❌ 错误: ANYROUTER_ACCOUNTS 未配置")
    sys.exit(1)

import json
try:
    accounts = json.loads(accounts_str)
    print(f"\n[账号配置]")
    print(f"找到 {len(accounts)} 个账号配置\n")

    for i, account in enumerate(accounts, 1):
        print(f"账号 {i}:")
        print(f"  - name: {account.get('name', '未设置')}")
        print(f"  - provider: {account.get('provider', 'anyrouter')}")
        print(f"  - email: {account.get('email', '❌ 未配置')}")

        if not account.get('email'):
            print(f"  ⚠️  警告: 该账号未配置 email 字段，不会收到单独的签到通知邮件！")
        print()

    # 检查是否所有账号都配置了 email
    accounts_with_email = [acc for acc in accounts if acc.get('email')]
    accounts_without_email = [acc for acc in accounts if not acc.get('email')]

    print("=" * 60)
    print("配置总结")
    print("=" * 60)
    print(f"✅ 配置了邮箱的账号: {len(accounts_with_email)}/{len(accounts)}")
    print(f"❌ 未配置邮箱的账号: {len(accounts_without_email)}/{len(accounts)}")

    if accounts_without_email:
        print(f"\n⚠️  警告: 以下账号不会收到单独的签到邮件:")
        for acc in accounts_without_email:
            print(f"  - {acc.get('name', '未命名账号')}")

        print("\n💡 解决方法:")
        print("在 ANYROUTER_ACCOUNTS 环境变量中为每个账号添加 email 字段，例如:")
        print('[{"name":"账号1","cookies":{"session":"xxx"},"api_user":"12345","email":"your@email.com"}]')
    else:
        print("\n✅ 所有账号都已配置邮箱，签到后会收到邮件通知！")

except json.JSONDecodeError as e:
    print(f"\n❌ 错误: ANYROUTER_ACCOUNTS 格式不正确: {e}")
    sys.exit(1)
