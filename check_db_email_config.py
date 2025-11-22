#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""检查数据库中的邮箱配置"""

import sys

sys.stdout.reconfigure(encoding='utf-8')

try:
    from web.database import db

    print("=" * 60)
    print("检查数据库中的邮箱配置")
    print("=" * 60)

    email_user = db.get_config('email_user')
    email_pass = db.get_config('email_pass')
    smtp_server = db.get_config('custom_smtp_server')

    print(f"\n[邮箱发送配置]")
    print(f"email_user: {email_user if email_user else '❌ 未配置'}")
    print(f"email_pass: {'✅ 已配置' if email_pass else '❌ 未配置'}")
    print(f"custom_smtp_server: {smtp_server if smtp_server else '未配置（将使用默认）'}")

    if not email_user or not email_pass:
        print("\n⚠️  警告: 数据库中未配置邮箱发送信息！")
        print("\n💡 解决方法:")
        print("1. 在 Web 界面的设置页面中配置邮箱信息")
        print("2. 或者手动插入配置到数据库:")
        print("   INSERT INTO config (key, value) VALUES ('email_user', '2310030579@qq.com');")
        print("   INSERT INTO config (key, value) VALUES ('email_pass', 'ygjcwvybxdkodiii');")
        print("   INSERT INTO config (key, value) VALUES ('custom_smtp_server', 'smtp.qq.com');")
    else:
        print("\n✅ 邮箱配置完整，可以正常发送邮件")

    print("\n" + "=" * 60)
    print("账号配置")
    print("=" * 60)

    accounts = db.get_all_accounts()
    if not accounts:
        print("❌ 数据库中没有账号")
    else:
        print(f"\n找到 {len(accounts)} 个账号:\n")
        for acc in accounts:
            print(f"账号: {acc['username']}")
            print(f"  邮箱: {acc.get('email', '❌ 未配置')}")
            if not acc.get('email'):
                print(f"  ⚠️  该账号不会收到单独的签到邮件通知")
            print()

except Exception as e:
    print(f"❌ 错误: {e}")
    import traceback
    traceback.print_exc()
