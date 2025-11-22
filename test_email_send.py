#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""测试邮件发送"""

import sys
from utils.notify import NotificationKit
from datetime import datetime

sys.stdout.reconfigure(encoding='utf-8')

print("初始化 NotificationKit...")
notify = NotificationKit()

print(f"email_user: {notify.email_user}")
print(f"email_pass: {'已配置' if notify.email_pass else '未配置'}")
print(f"smtp_server: {notify.smtp_server}")

print("\n发送测试邮件到 1344096385@qq.com...")

try:
    notify.send_email_to(
        '1344096385@qq.com',
        'AnyRouter 签到测试',
        f'''这是一封测试邮件

测试时间: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

如果收到此邮件，说明邮件功能正常！
''',
        msg_type='text'
    )
    print("[OK] 邮件发送成功！")
except Exception as e:
    print(f"[FAIL] 邮件发送失败: {e}")
    import traceback
    traceback.print_exc()
