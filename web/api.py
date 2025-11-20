#!/usr/bin/env python3
"""
FastAPI 后端 API
"""

import asyncio
import sys
from pathlib import Path

from fastapi import FastAPI, HTTPException
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
else:
    from web.database import db

app = FastAPI(title='AnyRouter 签到管理系统', version='1.0.0')

# 配置 CORS
app.add_middleware(
	CORSMiddleware,
	allow_origins=['*'],
	allow_credentials=True,
	allow_methods=['*'],
	allow_headers=['*'],
)


# ========== 数据模型 ==========


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
	enabled: bool | None = None


class TestLoginRequest(BaseModel):
	username: str
	password: str


# ========== API 路由 ==========


@app.get('/')
async def read_root():
	"""返回前端页面"""
	html_file = Path(__file__).parent / 'templates' / 'index.html'
	if html_file.exists():
		return HTMLResponse(content=html_file.read_text(encoding='utf-8'))
	return {'message': 'AnyRouter 签到管理系统 API'}


@app.get('/api/health')
async def health_check():
	"""健康检查"""
	return {'status': 'ok'}


# ========== 账号管理 ==========


@app.get('/api/accounts')
async def get_accounts():
	"""获取所有账号列表"""
	try:
		accounts = db.get_all_accounts()
		# 不返回密码，并附加最新余额信息
		for account in accounts:
			account.pop('password', None)
			# 获取最新余额
			balance = db.get_latest_balance(account['id'])
			account['balance'] = balance
		return {'success': True, 'data': accounts}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.get('/api/accounts/{account_id}')
async def get_account(account_id: int):
	"""获取单个账号详情"""
	try:
		account = db.get_account(account_id)
		if not account:
			raise HTTPException(status_code=404, detail='账号不存在')

		# 不返回密码
		account.pop('password', None)

		# 获取最新余额
		latest_balance = db.get_latest_balance(account_id)

		return {'success': True, 'data': {'account': account, 'balance': latest_balance}}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.post('/api/accounts')
async def create_account(account: AccountCreate):
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

		# 调用数据库添加账号
		account_id = db.add_account(
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
async def update_account(account_id: int, account: AccountUpdate):
	"""更新账号信息"""
	try:
		# 检查账号是否存在
		existing = db.get_account(account_id)
		if not existing:
			raise HTTPException(status_code=404, detail='账号不存在')

		db.update_account(account_id, name=account.name, password=account.password, enabled=account.enabled)
		return {'success': True, 'message': '账号更新成功'}
	except HTTPException:
		raise
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


@app.delete('/api/accounts/{account_id}')
async def delete_account(account_id: int):
	"""删除账号"""
	try:
		# 检查账号是否存在
		existing = db.get_account(account_id)
		if not existing:
			raise HTTPException(status_code=404, detail='账号不存在')

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
async def get_logs(account_id: int | None = None, limit: int = 100):
	"""获取签到日志"""
	try:
		logs = db.get_checkin_logs(account_id=account_id, limit=limit)
		return {'success': True, 'data': logs}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 余额历史 ==========


@app.get('/api/balance/{account_id}')
async def get_balance_history(account_id: int, limit: int = 30):
	"""获取余额历史"""
	try:
		history = db.get_balance_history(account_id, limit=limit)
		return {'success': True, 'data': history}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 统计信息 ==========


@app.get('/api/statistics')
async def get_statistics():
	"""获取统计信息"""
	try:
		stats = db.get_statistics()
		return {'success': True, 'data': stats}
	except Exception as e:
		raise HTTPException(status_code=500, detail=str(e))


# ========== 手动签到 ==========


@app.post('/api/checkin/{account_id}')
async def manual_checkin(account_id: int):
	"""手动触发单个账号签到"""
	try:
		# 获取账号信息
		account = db.get_account(account_id)
		if not account:
			raise HTTPException(status_code=404, detail='账号不存在')

		if not account.get('enabled'):
			raise HTTPException(status_code=400, detail='账号已禁用')

		# 执行签到逻辑（导入原有的签到函数）
		from checkin import check_in_account
		from utils.config import AccountConfig, AppConfig

		# 根据认证类型获取 cookies 和 api_user
		if account.get('auth_type') == 'password':
			# 密码认证：自动登录获取 cookies
			login_result = await login_anyrouter(account['username'], account['password'])
			if not login_result or not login_result.get('success'):
				db.add_checkin_log(account_id, False, '自动登录失败')
				raise HTTPException(status_code=400, detail='自动登录失败')

			cookies = login_result['cookies']
			api_user = login_result['api_user']
		else:
			# Cookies认证：直接使用保存的 cookies 和 api_user
			import json
			cookies = json.loads(account['cookies']) if isinstance(account['cookies'], str) else account['cookies']
			api_user = account['api_user']

		# 构造账号配置
		account_config = AccountConfig(
			cookies=cookies, api_user=api_user, provider=account['provider'], name=account['name']
		)

		app_config = AppConfig.load_from_env()

		# 执行签到
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
async def checkin_all():
	"""手动触发所有账号签到"""
	try:
		accounts = db.get_all_accounts(enabled_only=True)
		results = []

		for account in accounts:
			try:
				# 调用单个账号签到
				result = await manual_checkin(account['id'])
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

	print('🚀 Starting AnyRouter 签到管理系统...')
	print('📝 访问地址: http://localhost:8080')
	uvicorn.run(app, host='0.0.0.0', port=8080)
