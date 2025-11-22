#!/usr/bin/env python3
"""检查账号 cookies"""

from web.database import db

accounts = db.get_all_accounts()
for account in accounts:
    print(f"账号: {account['name']}")
    print(f"  ID: {account['id']}")
    print(f"  邮箱: {account.get('email', '未配置')}")
    print(f"  认证方式: {account.get('auth_type', 'password')}")
    print(f"  cookies 类型: {type(account.get('cookies'))}")
    print(f"  cookies 值: {repr(account.get('cookies'))}")
    print(f"  api_user: {account.get('api_user')}")
    print()
