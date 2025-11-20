#!/usr/bin/env python3
"""
自动登录模块 - 使用用户名密码自动登录获取 cookies
"""

import asyncio

from playwright.async_api import async_playwright


async def login_anyrouter(username: str, password: str):
	"""使用用户名密码登录 AnyRouter，返回 cookies 和 api_user"""
	print(f'[LOGIN] Starting auto login for {username}')

	async with async_playwright() as p:
		import tempfile

		with tempfile.TemporaryDirectory() as temp_dir:
			context = await p.chromium.launch_persistent_context(
				user_data_dir=temp_dir,
				headless=False,
				user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
				viewport={'width': 1920, 'height': 1080},
				args=[
					'--disable-blink-features=AutomationControlled',
					'--disable-dev-shm-usage',
					'--disable-web-security',
					'--disable-features=VizDisplayCompositor',
					'--no-sandbox',
				],
			)

			page = await context.new_page()

			try:
				# 访问登录页面
				login_url = 'https://anyrouter.top/login'
				print(f'[LOGIN] Navigating to {login_url}')
				await page.goto(login_url, wait_until='networkidle', timeout=30000)

				# 等待页面加载完成
				await page.wait_for_load_state('domcontentloaded')
				await page.wait_for_timeout(2000)

				# 关闭系统公告弹窗（如果有）
				print('[LOGIN] Closing announcement modal if exists')
				try:
					# 查找并点击"关闭公告"或"今日关闭"按钮
					close_buttons = page.locator('button:has-text("关闭公告"), button:has-text("今日关闭"), .semi-modal-close')
					if await close_buttons.count() > 0:
						await close_buttons.first.click()
						await page.wait_for_timeout(500)
						print('[LOGIN] Announcement modal closed')
				except Exception:
					print('[LOGIN] No announcement modal found')

				# 点击"使用 邮箱或用户名 登录"按钮
# 				print('[LOGIN] Clicking email/username login button')
# 				email_login_button = page.locator('button:has-text("使用 邮箱或用户名 登录")').first
# 				await email_login_button.click()
# 				await page.wait_for_timeout(1500)

				# 等待表单出现
# 				print('[LOGIN] Waiting for login form to appear')
# 				await page.wait_for_selector('input#username', timeout=5000)

				# 查找并填写用户名/邮箱（使用 ID 选择器）
				print(f'[LOGIN] Filling username: {username}')
				username_input = page.locator('input#username')
				await username_input.click()
				await username_input.fill(username)
				await page.wait_for_timeout(500)

				# 查找并填写密码（使用 ID 选择器）
				print('[LOGIN] Filling password')
				password_input = page.locator('input#password')
				await password_input.click()
				await password_input.fill(password)
				await page.wait_for_timeout(500)

				# 查找并点击"继续"按钮
				print('[LOGIN] Clicking submit button')
				submit_button = page.locator('button[type="submit"]:has-text("继续")').first
				await submit_button.click()

				# 等待登录完成（等待跳转或特定元素出现）
				print('[LOGIN] Waiting for login to complete...')
				try:
					# 等待跳转到首页或出现登录后的元素
					await page.wait_for_url('**/panel/**', timeout=10000)
					print('[LOGIN] Login successful, redirected to panel')
				except Exception:
					# 如果没有跳转，等待一下看是否有错误提示
					await page.wait_for_timeout(3000)

					# 检查是否有错误提示
					error_selectors = [
						'text="用户名或密码错误"',
						'text="登录失败"',
						'text="账号不存在"',
						'.error',
						'.alert-danger',
					]
					for selector in error_selectors:
						try:
							error_element = page.locator(selector).first
							if await error_element.is_visible(timeout=1000):
								error_text = await error_element.text_content()
								print(f'[FAILED] Login failed: {error_text}')
								await context.close()
								return None
						except Exception:
							continue

				# 获取所有 cookies
				cookies = await page.context.cookies()
				print(f'[LOGIN] Got {len(cookies)} cookies')

				# 提取 session cookie
				session_cookie = None
				waf_cookies = {}
				for cookie in cookies:
					if cookie.get('name') == 'session':
						session_cookie = cookie.get('value')
					if cookie.get('name') in ['acw_tc', 'cdn_sec_tc', 'acw_sc__v2']:
						waf_cookies[cookie.get('name')] = cookie.get('value')

				if not session_cookie:
					print('[FAILED] Session cookie not found')
					await context.close()
					return None

				print(f'[LOGIN] Session cookie obtained: {session_cookie[:20]}...')

				# 获取 api_user (从请求头中获取)
				# 等待任意 API 请求，从请求头中提取 new-api-user
				api_user = None

				async def handle_request(request):
					nonlocal api_user
					if '/api/' in request.url:
						headers = request.headers
						if 'new-api-user' in headers:
							api_user = headers['new-api-user']
							print(f'[LOGIN] Found api_user: {api_user}')

				page.on('request', handle_request)

				# 访问用户信息页面触发 API 请求
				try:
					await page.goto('https://anyrouter.top/panel/profile', wait_until='networkidle', timeout=10000)
					await page.wait_for_timeout(2000)
				except Exception:
					pass

				if not api_user:
					# 尝试直接从 localStorage 或页面元素获取
					try:
						api_user = await page.evaluate('() => localStorage.getItem("userId") || localStorage.getItem("user_id")')
					except Exception:
						pass

				if not api_user:
					print('[FAILED] Could not obtain api_user')
					await context.close()
					return None

				print(f'[SUCCESS] Login successful! api_user: {api_user}')

				await context.close()

				return {
					'cookies': {'session': session_cookie, **waf_cookies},
					'api_user': api_user,
					'success': True,
				}

			except Exception as e:
				print(f'[FAILED] Login error: {e}')
				await context.close()
				return None


async def test_login(username: str, password: str):
	"""测试登录功能"""
	result = await login_anyrouter(username, password)
	if result and result.get('success'):
		print('\n✅ Login test successful!')
		print(f'Cookies: {result["cookies"]}')
		print(f'API User: {result["api_user"]}')
		return True
	else:
		print('\n❌ Login test failed!')
		return False


if __name__ == '__main__':
	import sys

	if len(sys.argv) < 3:
		print('Usage: python auto_login.py <username> <password>')
		sys.exit(1)

	username = sys.argv[1]
	password = sys.argv[2]

	asyncio.run(test_login(username, password))
