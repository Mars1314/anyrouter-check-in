#!/usr/bin/env python3
"""
FastAPI 后端 API
"""

import asyncio
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import HTMLResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from utils.auto_login import login_anyrouter

# 使用相对导入避免路径问题
if __name__ == '__main__':
	from database import db
	from auth import create_access_token, get_current_user, require_admin
else:
	from web.database import db
	from web.auth import create_access_token, get_current_user, require_admin

app = FastAPI(title='AnyRouter 签到管理系统', version='2.0.0')

# 配置 CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)


# ========== 数据模型 ==========

class LoginRequest(BaseModel):
	username: str
	password: str

class UserCreate(BaseModel):
	username: str
	password: str
	display_name: str
	role: str = 'user'
	expire_date: str | None = None

class UserUpdate(BaseModel):
	display_name: str | None = None
	password: str | None = None
	expire_date: str | None = None
	enabled: bool | None = None

class AccountCreate(BaseModel):
	name: str
	username: str | None = None
	password: str | None = None
	cookies: str | None = None
	api_user: str | None = None
	provider: str = 'anyrouter'


class AccountUpdate(BaseModel):
	name: str | None = None
	password: str | None = None
	cookies: str | None = None
	api_user: str | None = None
	provider: str | None = None
	enabled: bool | None = None


class TestLoginRequest(BaseModel):
	username: str
	password: str


# ========== API 路由 ==========


@app.get('/')
async def read_root():
	"""返回登录页面"""
	html_file = Path(__file__).parent / 'templates' / 'login.html'
	if html_file.exists():
		return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
	return {'message': 'AnyRouter 签到管理系统 API'}


@app.get('/dashboard')
async def dashboard():
	"""返回主页面（需要登录）"""
	html_file = Path(__file__).parent / 'templates' / 'dashboard.html'
	if html_file.exists():
		return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
	# 如果文件不存在，返回旧版主页
	html_file = Path(__file__).parent / 'templates' / 'index.html'
	if html_file.exists():
		return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
	return {'message': 'Dashboard not found'}


@app.get('/users')
async def users_page():
	"""返回用户管理页面（仅管理员）"""
	html_file = Path(__file__).parent / 'templates' / 'users.html'
	if html_file.exists():
		return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
	return {'message': 'Users page not found'}


@app.get('/api/health')
async def health_check():
	"""健康检查"""
	return {'status': 'ok'}


# ========== 用户认证 ==========


@app.post('/api/login')
async def login(request: LoginRequest):
	"""用户登录"""
	try:
		# 验证用户
		user = db.get_user_by_username(request.username)
		if not user:
			raise HTTPException(status_code=401, detail='用户名或密码错误')

		if user['password'] != request.password:
			raise HTTPException(status_code=401, detail='用户名或密码错误')

		if not user.get('enabled'):
			raise HTTPException(status_code=403, detail='账号已被禁用')

		# 检查是否过期
		if db.check_user_expired(user['id']):
			raise HTTPException(status_code=403, detail='账号已过期，请联系管理员')

		# 生成 token
		token = create_access_token(data={'user_id': user['id'], 'username': user['username'], 'role': user['role']})

		return {
			'success': True,
			'data': {'token': token, 'user': {'id': user['id'], 'username': user['username'], 'role': user['role'], 'display_name': user['display_name']}},
		}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/me')
async def get_current_user_info(current_user: dict = Depends(get_current_user)):
	"""获取当前登录用户信息"""
	try:
		user = db.get_user_by_id(current_user['user_id'])
		if not user:
			raise HTTPException(status_code=404, detail='用户不存在')
		return {'success': True, 'data': user}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 用户管理（仅管理员）==========


@app.get('/api/users')
async def get_users(current_user: dict = Depends(require_admin)):
	"""获取所有用户（仅管理员）"""
	try:
		users = db.get_all_users()
		return {'success': True, 'data': users}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/users')
async def create_user(user: UserCreate, current_user: dict = Depends(require_admin)):
	"""创建用户（仅管理员）"""
	try:
		# 检查用户名是否已存在
		existing = db.get_user_by_username(user.username)
		if existing:
			raise HTTPException(status_code=400, detail='用户名已存在')

		user_id = db.add_user(user.username, user.password, user.display_name, user.role, user.expire_date)
		return {'success': True, 'data': {'id': user_id}, 'message': '用户创建成功'}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.put('/api/users/{user_id}')
async def update_user(user_id: int, user: UserUpdate, current_user: dict = Depends(require_admin)):
	"""更新用户（仅管理员）"""
	try:
		# 检查用户是否存在
		existing = db.get_user_by_id(user_id)
		if not existing:
			raise HTTPException(status_code=404, detail='用户不存在')

		db.update_user(user_id, display_name=user.display_name, password=user.password, expire_date=user.expire_date, enabled=user.enabled)
		return {'success': True, 'message': '用户更新成功'}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/users/{user_id}')
async def delete_user(user_id: int, current_user: dict = Depends(require_admin)):
	"""删除用户（仅管理员）"""
	try:
		# 不能删除自己
		if user_id == current_user['user_id']:
			raise HTTPException(status_code=400, detail='不能删除自己')

		# 检查用户是否存在
		existing = db.get_user_by_id(user_id)
		if not existing:
			raise HTTPException(status_code=404, detail='用户不存在')

		db.delete_user(user_id)
		return {'success': True, 'message': '用户删除成功'}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 账号管理 ==========


@app.get('/api/accounts')
async def get_accounts(current_user: dict = Depends(get_current_user)):
	"""获取账号列表 - 管理员看所有，普通用户只看自己的"""
	try:
		# 管理员可以看所有账号，普通用户只能看自己的
		if current_user['role'] == 'admin':
			accounts = db.get_all_accounts()
		else:
			accounts = db.get_all_accounts(user_id=current_user['user_id'])

		# 不返回密码，并附加最新余额信息
		for account in accounts:
			account.pop('password', None)
			account.pop('cookies', None)
			# 获取最新余额
			balance = db.get_latest_balance(account['id'])
			account['balance'] = balance
		return {'success': True, 'data': accounts}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/accounts/{account_id}')
async def get_account(account_id: int, include_sensitive: bool = False, current_user: dict = Depends(get_current_user)):
	"""获取单个账号详情"""
	try:
		account = db.get_account(account_id)
		if not account:
			raise HTTPException(status_code=404, detail='账号不存在')

		# 权限检查：普通用户只能访问自己的账号
		if current_user['role'] != 'admin' and account['user_id'] != current_user['user_id']:
			raise HTTPException(status_code=403, detail='无权访问此账号')

		# 如果不需要敏感信息，则移除密码和cookies
		if not include_sensitive:
			account.pop('password', None)
			account.pop('cookies', None)

		# 获取最新余额
		latest_balance = db.get_latest_balance(account_id)

		return {'success': True, 'data': {'account': account, 'balance': latest_balance}}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/accounts')
async def create_account(account: AccountCreate, current_user: dict = Depends(get_current_user)):
	"""添加新账号 - 支持两种认证方式"""
	try:
		# 验证：必须提供用户名密码 或 cookies+api_user
		has_password_auth = account.username and account.password
		has_cookies_auth = account.cookies and account.api_user

		if not has_password_auth and not has_cookies_auth:
			raise HTTPException(
				status_code=400,
				detail='请提供用户名密码或 Cookies+API User'
			)

		# 调用数据库添加账号，关联到当前用户
		account_id = db.add_account(
			user_id=current_user['user_id'],
			name=account.name,
			username=account.username,
			password=account.password,
			cookies=account.cookies,
			api_user=account.api_user,
			provider=account.provider
		)

		auth_type = '密码认证' if has_password_auth else 'Cookies认证'
		return {
			'success': True,
			'data': {'id': account_id, 'auth_type': auth_type},
			'message': f'账号添加成功 ({auth_type})'
		}
	except HTTPException:
		raise
	except Exception as e:
		if 'UNIQUE constraint failed' in str(e):
			raise HTTPException(status_code=400, detail='用户名已存在')
		raise HTTPException(status_code=500, detail=str(e))


@app.put('/api/accounts/{account_id}')
async def update_account(account_id: int, account: AccountUpdate, current_user: dict = Depends(get_current_user)):
	"""更新账号信息 - 支持两种认证方式"""
	try:
		# 检查账号是否存在
		existing = db.get_account(account_id)
		if not existing:
			raise HTTPException(status_code=404, detail='账号不存在')

		# 权限检查：普通用户只能修改自己的账号
		if current_user['role'] != 'admin' and existing['user_id'] != current_user['user_id']:
			raise HTTPException(status_code=403, detail='无权修改此账号')

		db.update_account(
			account_id,
			name=account.name,
			password=account.password,
			cookies=account.cookies,
			api_user=account.api_user,
			provider=account.provider,
			enabled=account.enabled
		)
		return {'success': True, 'message': '账号更新成功'}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/accounts/{account_id}')
async def delete_account(account_id: int, current_user: dict = Depends(get_current_user)):
	"""删除账号"""
	try:
		# 检查账号是否存在
		existing = db.get_account(account_id)
		if not existing:
			raise HTTPException(status_code=404, detail='账号不存在')

		# 权限检查：普通用户只能删除自己的账号
		if current_user['role'] != 'admin' and existing['user_id'] != current_user['user_id']:
			raise HTTPException(status_code=403, detail='无权删除此账号')

		db.delete_account(account_id)
		return {'success': True, 'message': '账号删除成功'}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 登录测试 ==========


@app.post('/api/test-login')
async def test_login(request: TestLoginRequest):
	"""测试登录功能"""
	try:
		result = await login_anyrouter(request.username, request.password)
		if result and result.get('success'):
			return {
				'success': True,
				'message': '登录测试成功',
				'data': {'api_user': result['api_user'], 'has_cookies': bool(result['cookies'])},
			}
		else:
			raise HTTPException(status_code=400, detail='登录失败，请检查用户名和密码')
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=f'登录测试出错: {str(e)}')


# ========== 签到日志 ==========


@app.get('/api/logs')
async def get_logs(account_id: int | None = None, limit: int = 100, current_user: dict = Depends(get_current_user)):
	"""获取签到日志 - 管理员看所有，普通用户只看自己的"""
	try:
		# 管理员可以看所有日志，普通用户只能看自己的
		if current_user['role'] == 'admin':
			logs = db.get_checkin_logs(account_id=account_id, limit=limit)
		else:
			logs = db.get_checkin_logs(account_id=account_id, user_id=current_user['user_id'], limit=limit)

		return {'success': True, 'data': logs}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 余额历史 ==========


@app.get('/api/balance/{account_id}')
async def get_balance_history(account_id: int, limit: int = 30, current_user: dict = Depends(get_current_user)):
	"""获取余额历史"""
	try:
		# 权限检查
		account = db.get_account(account_id)
		if not account:
			raise HTTPException(status_code=404, detail='账号不存在')

		if current_user['role'] != 'admin' and account['user_id'] != current_user['user_id']:
			raise HTTPException(status_code=403, detail='无权查看此账号的余额历史')

		history = db.get_balance_history(account_id, limit=limit)
		return {'success': True, 'data': history}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 统计信息 ==========


@app.get('/api/statistics')
async def get_statistics(current_user: dict = Depends(get_current_user)):
	"""获取统计信息 - 管理员看所有，普通用户只看自己的"""
	try:
		# 管理员可以看所有统计，普通用户只能看自己的
		if current_user['role'] == 'admin':
			stats = db.get_statistics()
		else:
			stats = db.get_statistics(user_id=current_user['user_id'])

		return {'success': True, 'data': stats}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 手动签到 ==========


@app.post('/api/checkin/{account_id}')
async def manual_checkin(account_id: int, current_user: dict = Depends(get_current_user)):
	"""手动触发单个账号签到"""
	try:
		# 获取账号信息
		account = db.get_account(account_id)
		if not account:
			raise HTTPException(status_code=404, detail='账号不存在')

		# 权限检查：普通用户只能签到自己的账号
		if current_user['role'] != 'admin' and account['user_id'] != current_user['user_id']:
			raise HTTPException(status_code=403, detail='无权操作此账号')

		if not account.get('enabled'):
			raise HTTPException(status_code=400, detail='账号已禁用')

		# 检查用户是否过期
		if db.check_user_expired(account['user_id']):
			raise HTTPException(status_code=403, detail='用户已过期，无法签到')

		# 执行签到逻辑（导入原有的签到函数）
		from checkin import check_in_account
		from utils.config import AccountConfig, AppConfig

		# 根据认证类型获取 cookies 和 api_user
		import json
		cookies = None
		api_user = None
		need_login = False

		if account.get('auth_type') == 'password':
			# 密码认证：优先使用已保存的 cookies，失效时才重新登录
			if account.get('cookies') and account.get('api_user'):
				# 尝试使用已保存的 cookies
				try:
					cookies = json.loads(account['cookies']) if isinstance(account['cookies'], str) else account['cookies']
					api_user = account['api_user']
				except:
					need_login = True
			else:
				# 第一次登录，没有保存的 cookies
				need_login = True
		else:
			# Cookies认证：直接使用保存的 cookies 和 api_user
			cookies = json.loads(account['cookies']) if isinstance(account['cookies'], str) else account['cookies']
			api_user = account['api_user']

		# 构造账号配置
		account_config = AccountConfig(
			cookies=cookies, api_user=api_user, provider=account['provider'], name=account['name']
		)

		app_config = AppConfig.load_from_env()

		# 执行签到
		success, user_info = await check_in_account(account_config, 0, app_config)

		# 如果签到失败且是密码认证，可能是 cookies 过期，尝试重新登录
		if not success and account.get('auth_type') == 'password' and not need_login:
			print(f'[API] Cookies 可能已过期，尝试重新登录账号: {account["name"]}')
			need_login = True

		# 需要登录的情况：重新登录并保存 cookies
		if need_login:
			login_result = await login_anyrouter(account['username'], account['password'])
			if not login_result or not login_result.get('success'):
				db.add_checkin_log(account_id, False, '自动登录失败')
				raise HTTPException(status_code=400, detail='自动登录失败')

			cookies = login_result['cookies']
			api_user = login_result['api_user']

			# 保存新的 cookies 和 api_user 到数据库
			db.update_account(
				account_id,
				cookies=json.dumps(cookies) if isinstance(cookies, dict) else cookies,
				api_user=api_user
			)
			print(f'[API] 已更新账号 {account["name"]} 的 cookies 和 api_user')

			# 使用新的 cookies 重新签到
			account_config = AccountConfig(
				cookies=cookies, api_user=api_user, provider=account['provider'], name=account['name']
			)
			success, user_info = await check_in_account(account_config, 0, app_config)

		# 记录日志
		message = '签到成功' if success else '签到失败'
		db.add_checkin_log(account_id, success, message)

		# 记录余额
		if user_info and user_info.get('success'):
			db.add_balance_record(account_id, user_info['quota'], user_info['used_quota'])

		if success:
			return {'success': True, 'message': '签到成功', 'data': user_info}
		else:
			raise HTTPException(status_code=400, detail='签到失败')

	except HTTPException:
		raise
	except Exception as e:
		db.add_checkin_log(account_id, False, f'签到异常: {str(e)[:100]}')
		raise HTTPException(status_code=500, detail=f'签到出错: {str(e)}')


@app.post('/api/checkin-all')
async def checkin_all(current_user: dict = Depends(get_current_user)):
	"""手动触发所有账号签到 - 管理员签到所有账号，普通用户签到自己的账号"""
	try:
		# 管理员签到所有账号，普通用户只签到自己的
		if current_user['role'] == 'admin':
			accounts = db.get_all_accounts(enabled_only=True)
		else:
			accounts = db.get_all_accounts(user_id=current_user['user_id'], enabled_only=True)

		# 过滤掉过期用户的账号
		valid_accounts = [acc for acc in accounts if not db.check_user_expired(acc['user_id'])]

		results = []

		for account in valid_accounts:
			try:
				# 调用单个账号签到
				result = await manual_checkin(account['id'], current_user)
				results.append({'account_id': account['id'], 'name': account['name'], 'success': True})
			except Exception as e:
				results.append({'account_id': account['id'], 'name': account['name'], 'success': False, 'error': str(e)})

		success_count = sum(1 for r in results if r['success'])
		return {
			'success': True,
			'message': f'签到完成: {success_count}/{len(results)} 成功',
			'data': {'results': results, 'success_count': success_count, 'total_count': len(results)},
		}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


if __name__ == '__main__':
	import uvicorn

	print('[INFO] Starting AnyRouter Check-in System...')
	print('[INFO] Visit: http://localhost:8080')
	uvicorn.run(app, host='0.0.0.0', port=8080)
