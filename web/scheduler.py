#!/usr/bin/env python3
"""
定时任务调度器 - 自动执行签到任务
"""

import asyncio
import sys
from datetime import datetime
from pathlib import Path

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from checkin import check_in_account
from utils.auto_login import login_anyrouter
from utils.config import AccountConfig, AppConfig
from utils.notify import notify

# 使用相对导入避免路径问题
if __name__ == '__main__':
    from database import db
else:
    from web.database import db


async def auto_checkin_task():
	"""自动签到任务"""
	print(f'\n[SCHEDULER] 开始执行自动签到任务 - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}')

	# 获取所有启用的账号
	accounts = db.get_all_accounts(enabled_only=True)
	if not accounts:
		print('[SCHEDULER] 没有启用的账号，跳过签到任务')
		return

	print(f'[SCHEDULER] 找到 {len(accounts)} 个启用的账号')

	app_config = AppConfig.load_from_env()
	success_count = 0
	failed_accounts = []

	for account in accounts:
		try:
			print(f'\n[SCHEDULER] 处理账号: {account["name"]}')

			# 根据认证类型获取 cookies 和 api_user
			if account.get('auth_type') == 'password':
				# 密码认证：自动登录获取 cookies
				print(f'[SCHEDULER] 正在登录账号: {account["name"]} (密码认证)')
				login_result = await login_anyrouter(account['username'], account['password'])

				if not login_result or not login_result.get('success'):
					error_msg = '自动登录失败'
					print(f'[SCHEDULER] ❌ {account["name"]}: {error_msg}')
					db.add_checkin_log(account['id'], False, error_msg)
					failed_accounts.append({'name': account['name'], 'error': error_msg})
					continue

				print(f'[SCHEDULER] ✅ {account["name"]}: 登录成功，开始签到')
				cookies = login_result['cookies']
				api_user = login_result['api_user']
			else:
				# Cookies认证：直接使用保存的 cookies 和 api_user
				print(f'[SCHEDULER] 使用已保存的 Cookies: {account["name"]} (Cookies认证)')
				import json
				cookies = json.loads(account['cookies']) if isinstance(account['cookies'], str) else account['cookies']
				api_user = account['api_user']

			# 构造账号配置
			account_config = AccountConfig(
				cookies=cookies,
				api_user=api_user,
				provider=account['provider'],
				name=account['name'],
			)

			# 执行签到
			success, user_info = await check_in_account(account_config, 0, app_config)

			# 记录日志
			if success:
				success_count += 1
				message = '签到成功'
				print(f'[SCHEDULER] ✅ {account["name"]}: 签到成功')
			else:
				message = '签到失败'
				print(f'[SCHEDULER] ❌ {account["name"]}: 签到失败')
				failed_accounts.append({'name': account['name'], 'error': message})

			db.add_checkin_log(account['id'], success, message)

			# 记录余额
			if user_info and user_info.get('success'):
				db.add_balance_record(account['id'], user_info['quota'], user_info['used_quota'])
				print(f'[SCHEDULER] 💰 {account["name"]}: 余额 ${user_info["quota"]}, 已使用 ${user_info["used_quota"]}')

		except Exception as e:
			error_msg = f'签到异常: {str(e)[:100]}'
			print(f'[SCHEDULER] ❌ {account["name"]}: {error_msg}')
			db.add_checkin_log(account['id'], False, error_msg)
			failed_accounts.append({'name': account['name'], 'error': error_msg})

	# 发送通知
	total_count = len(accounts)
	print(f'\n[SCHEDULER] 签到任务完成: {success_count}/{total_count} 成功')

	# 只在有失败时发送通知
	if failed_accounts:
		notification_content = f'''
[时间] {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}

[统计] 签到结果:
✅ 成功: {success_count}/{total_count}
❌ 失败: {len(failed_accounts)}/{total_count}

[失败账号]:
'''
		for account in failed_accounts:
			notification_content += f'\n❌ {account["name"]}: {account["error"]}'

		try:
			notify.push_message('AnyRouter 自动签到提醒', notification_content, msg_type='text')
			print('[SCHEDULER] 📧 通知已发送')
		except Exception as e:
			print(f'[SCHEDULER] ⚠️ 发送通知失败: {e}')


def start_scheduler():
	"""启动定时任务调度器"""
	scheduler = AsyncIOScheduler()

	# 每 6 小时执行一次签到任务（与 GitHub Actions 保持一致）
	scheduler.add_job(auto_checkin_task, CronTrigger(hour='*/6'), id='auto_checkin', name='自动签到任务')

	# 启动调度器
	scheduler.start()
	print('🚀 定时任务调度器已启动')
	print('📅 签到任务将每 6 小时执行一次')

	return scheduler


async def test_checkin_task():
	"""测试签到任务"""
	print('🧪 测试签到任务...\n')
	await auto_checkin_task()
	print('\n✅ 测试完成')


if __name__ == '__main__':
	# 可以运行测试
	if len(sys.argv) > 1 and sys.argv[1] == 'test':
		asyncio.run(test_checkin_task())
	else:
		# 正常模式：启动调度器并保持运行
		scheduler = start_scheduler()

		try:
			# 保持程序运行
			asyncio.get_event_loop().run_forever()
		except (KeyboardInterrupt, SystemExit):
			print('\n⚠️ 调度器正在关闭...')
			scheduler.shutdown()
			print('✅ 调度器已停止')
