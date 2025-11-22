#!/usr/bin/env python3
"""测试数据库配置读取"""

from web.database import db

print("测试读取系统配置...")
configs = db.get_all_configs()
print(f"所有配置: {configs}")

email_user = db.get_config('email_user')
email_pass = db.get_config('email_pass')
smtp_server = db.get_config('custom_smtp_server')

print(f"\nemail_user: {email_user}")
print(f"email_pass: {email_pass}")
print(f"custom_smtp_server: {smtp_server}")

print("\n测试 NotificationKit...")
from utils.notify import NotificationKit
notify = NotificationKit()

print(f"notify.email_user: {notify.email_user}")
print(f"notify.email_pass: {notify.email_pass}")
print(f"notify.smtp_server: {notify.smtp_server}")
