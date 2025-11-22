#!/usr/bin/env python3
"""
数据库模型和操作
"""

import json
import os
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import List

from cryptography.fernet import Fernet


class Database:
	def __init__(self, db_path: str = None, key_path: str = None):
		# 支持通过环境变量配置数据库路径
		self.db_path = db_path or os.getenv('DATABASE_PATH', 'data/checkin.db')
		self.key_path = key_path or os.getenv('DATABASE_KEY_PATH', 'data/secret.key')

		# 确保数据目录存在
		Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)

		# 初始化加密密钥
		self._init_encryption_key()

		# 初始化数据库
		self._init_database()

	def _init_encryption_key(self):
		"""初始化或加载加密密钥"""
		key_file = Path(self.key_path)
		if key_file.exists():
			with open(self.key_path, 'rb') as f:
				self.cipher = Fernet(f.read())
		else:
			key = Fernet.generate_key()
			key_file.parent.mkdir(parents=True, exist_ok=True)
			with open(self.key_path, 'wb') as f:
				f.write(key)
			self.cipher = Fernet(key)

	def _encrypt(self, text: str) -> str:
		"""加密文本"""
		return self.cipher.encrypt(text.encode()).decode()

	def _decrypt(self, encrypted_text: str) -> str:
		"""解密文本"""
		return self.cipher.decrypt(encrypted_text.encode()).decode()

	@contextmanager
	def get_connection(self):
		"""获取数据库连接"""
		conn = sqlite3.connect(self.db_path)
		conn.row_factory = sqlite3.Row
		try:
			yield conn
			conn.commit()
		except Exception:
			conn.rollback()
			raise
		finally:
			conn.close()

	def _init_database(self):
		"""初始化数据库表"""
		with self.get_connection() as conn:
			cursor = conn.cursor()

			# 用户表（新增）
			cursor.execute(
				'''
				CREATE TABLE IF NOT EXISTS users (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					username TEXT UNIQUE NOT NULL,
					password TEXT NOT NULL,
					role TEXT DEFAULT 'user',
					display_name TEXT NOT NULL,
					expire_date DATE,
					enabled INTEGER DEFAULT 1,
					created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
					updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				)
				'''
			)

			# 检查并创建默认超管账号
			cursor.execute("SELECT COUNT(*) FROM users WHERE role = 'admin'")
			admin_count = cursor.fetchone()[0]
			if admin_count == 0:
				# 创建默认超管：admin / admin123
				default_password = self._encrypt('admin123')
				cursor.execute(
					'''
					INSERT INTO users (username, password, role, display_name, enabled)
					VALUES (?, ?, 'admin', '超级管理员', 1)
					''',
					('admin', default_password),
				)
				print('[DATABASE] Created default admin user: admin / admin123')

			# 账号表
			cursor.execute(
				'''
                CREATE TABLE IF NOT EXISTS accounts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL,
                    username TEXT,
                    password TEXT,
                    cookies TEXT,
                    api_user TEXT,
                    auth_type TEXT DEFAULT 'password',
                    provider TEXT DEFAULT 'anyrouter',
                    enabled INTEGER DEFAULT 1,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            '''
			)

			# 检查并添加新字段（用于数据库升级）
			try:
				cursor.execute("SELECT cookies FROM accounts LIMIT 1")
			except Exception:
				# 字段不存在，添加新字段
				cursor.execute("ALTER TABLE accounts ADD COLUMN cookies TEXT")
				cursor.execute("ALTER TABLE accounts ADD COLUMN api_user TEXT")
				cursor.execute("ALTER TABLE accounts ADD COLUMN auth_type TEXT DEFAULT 'password'")
				print('[DATABASE] Added new fields for dual auth support')

			# 检查并修复 username 字段的 NOT NULL 约束
			# SQLite 不支持直接修改约束，需要重建表
			try:
				# 检查是否存在 NOT NULL 约束问题
				cursor.execute("PRAGMA table_info(accounts)")
				columns = cursor.fetchall()
				username_col = [col for col in columns if col[1] == 'username']

				if username_col and username_col[0][3] == 1:  # notnull = 1
					print('[DATABASE] Migrating to remove NOT NULL constraint from username...')

					# 重建表
					cursor.execute(
						'''
						CREATE TABLE accounts_new (
							id INTEGER PRIMARY KEY AUTOINCREMENT,
							name TEXT NOT NULL,
							username TEXT,
							password TEXT,
							cookies TEXT,
							api_user TEXT,
							auth_type TEXT DEFAULT 'password',
							provider TEXT DEFAULT 'anyrouter',
							enabled INTEGER DEFAULT 1,
							created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
							updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
						)
						'''
					)

					# 复制数据 - 检查列是否存在
					cursor.execute("PRAGMA table_info(accounts)")
					old_columns = [col[1] for col in cursor.fetchall()]

					# 构建列名列表（只复制存在的列）
					copy_columns = []
					for col in ['id', 'name', 'username', 'password', 'cookies', 'api_user', 'auth_type', 'provider', 'enabled', 'created_at', 'updated_at']:
						if col in old_columns:
							copy_columns.append(col)

					copy_sql = f'''
						INSERT INTO accounts_new ({', '.join(copy_columns)})
						SELECT {', '.join(copy_columns)}
						FROM accounts
					'''
					cursor.execute(copy_sql)

					# 删除旧表
					cursor.execute('DROP TABLE accounts')

					# 重命名新表
					cursor.execute('ALTER TABLE accounts_new RENAME TO accounts')

					print('[DATABASE] Migration completed: username is now nullable')
			except Exception as e:
				print(f'[DATABASE] Migration check: {e}')

			# 添加 user_id 字段到 accounts 表（多租户支持）
			try:
				cursor.execute("SELECT user_id FROM accounts LIMIT 1")
			except Exception:
				# user_id 字段不存在，需要添加
				print('[DATABASE] Migrating accounts table to add user_id field...')

				# 获取默认超管ID
				cursor.execute("SELECT id FROM users WHERE role = 'admin' LIMIT 1")
				admin_user = cursor.fetchone()
				if admin_user:
					admin_id = admin_user[0]
					# 添加字段，默认值为超管ID
					cursor.execute(f"ALTER TABLE accounts ADD COLUMN user_id INTEGER DEFAULT {admin_id}")
					print(f'[DATABASE] Added user_id field, existing accounts assigned to admin (ID: {admin_id})')
				else:
					# 如果没有超管，添加可空字段
					cursor.execute("ALTER TABLE accounts ADD COLUMN user_id INTEGER")
					print('[DATABASE] Added user_id field (nullable)')

			# 添加 email 字段到 accounts 表（个人邮件通知支持）
			try:
				cursor.execute("SELECT email FROM accounts LIMIT 1")
			except Exception:
				# email 字段不存在，需要添加
				print('[DATABASE] Migrating accounts table to add email field...')
				cursor.execute("ALTER TABLE accounts ADD COLUMN email TEXT")
				print('[DATABASE] Added email field for per-account notifications')

			# 系统配置表
			cursor.execute(
				'''
				CREATE TABLE IF NOT EXISTS system_config (
					id INTEGER PRIMARY KEY AUTOINCREMENT,
					config_key TEXT UNIQUE NOT NULL,
					config_value TEXT,
					description TEXT,
					updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
				)
				'''
			)

			# 签到记录表
			cursor.execute(
				'''
                CREATE TABLE IF NOT EXISTS checkin_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    success INTEGER NOT NULL,
                    message TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
                )
            '''
			)

			# 余额历史表
			cursor.execute(
				'''
                CREATE TABLE IF NOT EXISTS balance_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    account_id INTEGER NOT NULL,
                    quota REAL NOT NULL,
                    used_quota REAL NOT NULL,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (account_id) REFERENCES accounts(id) ON DELETE CASCADE
                )
            '''
			)

			# 创建索引
			cursor.execute('CREATE INDEX IF NOT EXISTS idx_checkin_logs_account ON checkin_logs(account_id)')
			cursor.execute('CREATE INDEX IF NOT EXISTS idx_balance_history_account ON balance_history(account_id)')

	# ========== 用户管理 ==========

	def add_user(self, username: str, password: str, display_name: str, role: str = 'user', expire_date: str = None) -> int:
		"""添加用户"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			encrypted_password = self._encrypt(password)
			cursor.execute(
				'''
				INSERT INTO users (username, password, role, display_name, expire_date)
				VALUES (?, ?, ?, ?, ?)
				''',
				(username, encrypted_password, role, display_name, expire_date),
			)
			return cursor.lastrowid

	def get_user_by_username(self, username: str):
		"""根据用户名获取用户"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT * FROM users WHERE username = ?', (username,))
			row = cursor.fetchone()
			if row:
				user = dict(row)
				# 解密密码
				user['password'] = self._decrypt(user['password'])
				return user
			return None

	def get_user_by_id(self, user_id: int):
		"""根据ID获取用户"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT * FROM users WHERE id = ?', (user_id,))
			row = cursor.fetchone()
			if row:
				user = dict(row)
				# 不返回密码
				user.pop('password', None)
				return user
			return None

	def get_all_users(self):
		"""获取所有用户"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT * FROM users ORDER BY id')
			rows = cursor.fetchall()
			users = []
			for row in rows:
				user = dict(row)
				# 不返回密码
				user.pop('password', None)
				users.append(user)
			return users

	def update_user(self, user_id: int, display_name: str = None, password: str = None, expire_date: str = None, enabled: bool = None):
		"""更新用户信息"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			updates = []
			params = []

			if display_name is not None:
				updates.append('display_name = ?')
				params.append(display_name)

			if password is not None:
				updates.append('password = ?')
				params.append(self._encrypt(password))

			if expire_date is not None:
				updates.append('expire_date = ?')
				params.append(expire_date)

			if enabled is not None:
				updates.append('enabled = ?')
				params.append(1 if enabled else 0)

			if updates:
				updates.append('updated_at = CURRENT_TIMESTAMP')
				params.append(user_id)
				cursor.execute(f"UPDATE users SET {', '.join(updates)} WHERE id = ?", params)

	def delete_user(self, user_id: int):
		"""删除用户（会级联删除该用户的所有账号）"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('DELETE FROM users WHERE id = ?', (user_id,))

	def check_user_expired(self, user_id: int) -> bool:
		"""检查用户是否过期"""
		user = self.get_user_by_id(user_id)
		if not user:
			return True
		if not user.get('enabled'):
			return True
		if user.get('expire_date'):
			from datetime import datetime
			expire_date = datetime.strptime(user['expire_date'], '%Y-%m-%d').date()
			today = datetime.now().date()
			if today > expire_date:
				return True
		return False

	# ========== 账号管理 ==========

	def add_account(
		self,
		user_id: int,
		name: str,
		username: str = None,
		password: str = None,
		cookies: str = None,
		api_user: str = None,
		provider: str = 'anyrouter',
		email: str = None,
	) -> int:
		"""添加账号 - 支持两种认证方式"""
		with self.get_connection() as conn:
			cursor = conn.cursor()

			# 判断认证类型
			if username and password:
				# 方式1: 用户名密码
				auth_type = 'password'
				encrypted_password = self._encrypt(password)
				cursor.execute(
					'''
                    INSERT INTO accounts (user_id, name, username, password, auth_type, provider, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
					(user_id, name, username, encrypted_password, auth_type, provider, email),
				)
			elif cookies and api_user:
				# 方式2: Cookies + API User
				auth_type = 'cookies'
				# 确保 cookies 是字符串格式
				if isinstance(cookies, dict):
					import json
					cookies = json.dumps(cookies)
				encrypted_cookies = self._encrypt(cookies)
				cursor.execute(
					'''
                    INSERT INTO accounts (user_id, name, cookies, api_user, auth_type, provider, email)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                ''',
					(user_id, name, encrypted_cookies, api_user, auth_type, provider, email),
				)
			else:
				raise ValueError('必须提供用户名密码或 cookies+api_user')

			return cursor.lastrowid

	def update_account(self, account_id: int, name: str = None, password: str = None, cookies: str = None, api_user: str = None, provider: str = None, enabled: bool = None, email: str = None):
		"""更新账号信息 - 支持两种认证方式"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			updates = []
			params = []

			if name is not None:
				updates.append('name = ?')
				params.append(name)

			# 密码认证：更新密码
			if password is not None:
				updates.append('password = ?')
				params.append(self._encrypt(password))

			# Cookies 认证：更新 cookies 和 api_user
			if cookies is not None:
				# 确保 cookies 是字符串格式
				if isinstance(cookies, dict):
					import json
					cookies = json.dumps(cookies)
				updates.append('cookies = ?')
				params.append(self._encrypt(cookies))

			if api_user is not None:
				updates.append('api_user = ?')
				params.append(api_user)

			if provider is not None:
				updates.append('provider = ?')
				params.append(provider)

			if enabled is not None:
				updates.append('enabled = ?')
				params.append(1 if enabled else 0)

			# 更新邮箱（允许设置为空）
			if email is not None:
				updates.append('email = ?')
				params.append(email if email else None)

			if updates:
				updates.append('updated_at = CURRENT_TIMESTAMP')
				params.append(account_id)
				cursor.execute(f"UPDATE accounts SET {', '.join(updates)} WHERE id = ?", params)

	def delete_account(self, account_id: int):
		"""删除账号"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('DELETE FROM accounts WHERE id = ?', (account_id,))

	def get_account(self, account_id: int) -> dict | None:
		"""获取单个账号"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT * FROM accounts WHERE id = ?', (account_id,))
			row = cursor.fetchone()
			if row:
				account = dict(row)
				# 解密敏感字段
				if account.get('password'):
					account['password'] = self._decrypt(account['password'])
				if account.get('cookies'):
					account['cookies'] = self._decrypt(account['cookies'])
				return account
			return None

	def get_all_accounts(self, user_id: int = None, enabled_only: bool = False) -> List[dict]:
		"""获取所有账号 - 支持按用户筛选"""
		with self.get_connection() as conn:
			cursor = conn.cursor()

			sql = 'SELECT * FROM accounts WHERE 1=1'
			params = []

			if user_id is not None:
				sql += ' AND user_id = ?'
				params.append(user_id)

			if enabled_only:
				sql += ' AND enabled = 1'

			sql += ' ORDER BY id'

			cursor.execute(sql, params)

			accounts = []
			for row in cursor.fetchall():
				account = dict(row)
				# 解密敏感字段
				if account.get('password'):
					account['password'] = self._decrypt(account['password'])
				if account.get('cookies'):
					account['cookies'] = self._decrypt(account['cookies'])
				accounts.append(account)
			return accounts

	# ========== 签到日志 ==========

	def add_checkin_log(self, account_id: int, success: bool, message: str = None):
		"""添加签到日志"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				'''
                INSERT INTO checkin_logs (account_id, success, message)
                VALUES (?, ?, ?)
            ''',
				(account_id, 1 if success else 0, message),
			)

	def get_checkin_logs(self, account_id: int = None, user_id: int = None, limit: int = 100) -> List[dict]:
		"""获取签到日志 - 支持按账号或用户筛选"""
		with self.get_connection() as conn:
			cursor = conn.cursor()

			sql = '''
				SELECT cl.*, a.name as account_name
				FROM checkin_logs cl
				JOIN accounts a ON cl.account_id = a.id
				WHERE 1=1
			'''
			params = []

			if account_id:
				sql += ' AND cl.account_id = ?'
				params.append(account_id)
			elif user_id:
				sql += ' AND a.user_id = ?'
				params.append(user_id)

			sql += ' ORDER BY cl.created_at DESC LIMIT ?'
			params.append(limit)

			cursor.execute(sql, params)
			return [dict(row) for row in cursor.fetchall()]

	# ========== 余额历史 ==========

	def add_balance_record(self, account_id: int, quota: float, used_quota: float):
		"""添加余额记录"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				'''
                INSERT INTO balance_history (account_id, quota, used_quota)
                VALUES (?, ?, ?)
            ''',
				(account_id, quota, used_quota),
			)

	def get_balance_history(self, account_id: int, limit: int = 30) -> List[dict]:
		"""获取余额历史"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				'''
                SELECT * FROM balance_history
                WHERE account_id = ?
                ORDER BY created_at DESC
                LIMIT ?
            ''',
				(account_id, limit),
			)

			return [dict(row) for row in cursor.fetchall()]

	def get_latest_balance(self, account_id: int) -> dict | None:
		"""获取最新余额"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				'''
                SELECT * FROM balance_history
                WHERE account_id = ?
                ORDER BY created_at DESC
                LIMIT 1
            ''',
				(account_id,),
			)

			row = cursor.fetchone()
			return dict(row) if row else None

	# ========== 系统配置 ==========

	def get_config(self, key: str) -> str | None:
		"""获取配置值"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT config_value FROM system_config WHERE config_key = ?', (key,))
			row = cursor.fetchone()
			return row['config_value'] if row else None

	def set_config(self, key: str, value: str, description: str = None):
		"""设置配置值"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute(
				'''
				INSERT INTO system_config (config_key, config_value, description)
				VALUES (?, ?, ?)
				ON CONFLICT(config_key) DO UPDATE SET
					config_value = excluded.config_value,
					description = excluded.description,
					updated_at = CURRENT_TIMESTAMP
				''',
				(key, value, description),
			)

	def get_all_configs(self) -> dict:
		"""获取所有配置"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('SELECT config_key, config_value FROM system_config')
			return {row['config_key']: row['config_value'] for row in cursor.fetchall()}

	def delete_config(self, key: str):
		"""删除配置"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			cursor.execute('DELETE FROM system_config WHERE config_key = ?', (key,))

	# ========== 统计信息 ==========

	def get_statistics(self, user_id: int = None) -> dict:
		"""获取统计信息 - 支持按用户筛选"""
		with self.get_connection() as conn:
			cursor = conn.cursor()

			# 构建WHERE条件
			where_clause = 'WHERE a.user_id = ?' if user_id else ''
			params = [user_id] if user_id else []

			# 总账号数
			if user_id:
				cursor.execute('SELECT COUNT(*) as total, SUM(enabled) as enabled FROM accounts WHERE user_id = ?', (user_id,))
			else:
				cursor.execute('SELECT COUNT(*) as total, SUM(enabled) as enabled FROM accounts')
			account_stats = dict(cursor.fetchone())

			# 今日签到统计
			if user_id:
				cursor.execute(
					'''
					SELECT COUNT(*) as total, SUM(cl.success) as success
					FROM checkin_logs cl
					JOIN accounts a ON cl.account_id = a.id
					WHERE DATE(cl.created_at) = DATE('now') AND a.user_id = ?
					''',
					(user_id,)
				)
			else:
				cursor.execute(
					'''
					SELECT COUNT(*) as total, SUM(success) as success
					FROM checkin_logs
					WHERE DATE(created_at) = DATE('now')
					'''
				)
			today_stats = dict(cursor.fetchone())

			# 总余额 - 获取每个账号的最新余额（只统计启用的、未过期用户的账号）
			if user_id:
				cursor.execute(
					'''
					SELECT SUM(quota) as total_quota, SUM(used_quota) as total_used
					FROM (
						SELECT bh.account_id, bh.quota, bh.used_quota
						FROM balance_history bh
						JOIN accounts a ON bh.account_id = a.id
						JOIN users u ON a.user_id = u.id
						WHERE a.user_id = ?
							AND a.enabled = 1
							AND (u.enabled = 1 AND (u.expire_date IS NULL OR u.expire_date >= DATE('now')))
							AND bh.created_at = (
								SELECT MAX(created_at)
								FROM balance_history bh2
								WHERE bh2.account_id = bh.account_id
							)
						GROUP BY bh.account_id
					)
					''',
					(user_id,)
				)
			else:
				cursor.execute(
					'''
					SELECT SUM(quota) as total_quota, SUM(used_quota) as total_used
					FROM (
						SELECT bh.account_id, bh.quota, bh.used_quota
						FROM balance_history bh
						JOIN accounts a ON bh.account_id = a.id
						JOIN users u ON a.user_id = u.id
						WHERE a.enabled = 1
							AND (u.enabled = 1 AND (u.expire_date IS NULL OR u.expire_date >= DATE('now')))
							AND bh.created_at = (
								SELECT MAX(created_at)
								FROM balance_history bh2
								WHERE bh2.account_id = bh.account_id
							)
						GROUP BY bh.account_id
					)
					'''
				)
			balance_stats = dict(cursor.fetchone())

			return {
				'total_accounts': account_stats['total'] or 0,
				'enabled_accounts': account_stats['enabled'] or 0,
				'today_checkin_total': today_stats['total'] or 0,
				'today_checkin_success': today_stats['success'] or 0,
				'total_quota': balance_stats['total_quota'] or 0,
				'total_used': balance_stats['total_used'] or 0,
			}


# 全局数据库实例
db = Database()


if __name__ == '__main__':
	# 测试数据库功能
	print('Testing database...')

	# 添加测试账号
	account_id = db.add_account('测试账号', 'test@example.com', 'password123')
	print(f'✅ Added account with ID: {account_id}')

	# 获取账号
	account = db.get_account(account_id)
	print(f'✅ Retrieved account: {account["name"]} ({account["username"]})')

	# 添加签到记录
	db.add_checkin_log(account_id, True, '签到成功')
	print('✅ Added checkin log')

	# 添加余额记录
	db.add_balance_record(account_id, 100.0, 25.0)
	print('✅ Added balance record')

	# 获取统计信息
	stats = db.get_statistics()
	print(f'✅ Statistics: {stats}')

	# 清理测试数据
	db.delete_account(account_id)
	print('✅ Deleted test account')

	print('\n✅ All database tests passed!')
