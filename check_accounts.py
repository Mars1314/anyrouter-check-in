#!/usr/bin/env python3
"""检查账号配置"""

from web.database import db

print("检查所有账号配置...\n")
accounts = db.get_all_accounts()

for i, account in enumerate(accounts, 1):
    print(f"账号 {i}:")
    print(f"  ID: {account['id']}")
    print(f"  名称: {account['name']}")
    print(f"  Provider: {account['provider']}")
    print(f"  邮箱: {account.get('email', '未配置')}")
    print(f"  认证方式: {account.get('auth_type', 'password')}")
    print()

print(f"总共 {len(accounts)} 个账号")
