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
				# 将 username 和 password 改为可空
				print('[DATABASE] Migrated database schema to support both auth types')

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

	# ========== 账号管理 ==========

	def add_account(
		self,
		name: str,
		username: str = None,
		password: str = None,
		cookies: str = None,
		api_user: str = None,
		provider: str = 'anyrouter',
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
                    INSERT INTO accounts (name, username, password, auth_type, provider)
                    VALUES (?, ?, ?, ?, ?)
                ''',
					(name, username, encrypted_password, auth_type, provider),
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
                    INSERT INTO accounts (name, cookies, api_user, auth_type, provider)
                    VALUES (?, ?, ?, ?, ?)
                ''',
					(name, encrypted_cookies, api_user, auth_type, provider),
				)
			else:
				raise ValueError('必须提供用户名密码或 cookies+api_user')

			return cursor.lastrowid

	def update_account(self, account_id: int, name: str = None, password: str = None, enabled: bool = None):
		"""更新账号信息"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			updates = []
			params = []

			if name is not None:
				updates.append('name = ?')
				params.append(name)

			if password is not None:
				updates.append('password = ?')
				params.append(self._encrypt(password))

			if enabled is not None:
				updates.append('enabled = ?')
				params.append(1 if enabled else 0)

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
				# 根据认证类型解密对应字段
				if account.get('auth_type') == 'password' and account.get('password'):
					account['password'] = self._decrypt(account['password'])
				elif account.get('auth_type') == 'cookies' and account.get('cookies'):
					account['cookies'] = self._decrypt(account['cookies'])
				return account
			return None

	def get_all_accounts(self, enabled_only: bool = False) -> List[dict]:
		"""获取所有账号"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			if enabled_only:
				cursor.execute('SELECT * FROM accounts WHERE enabled = 1 ORDER BY id')
			else:
				cursor.execute('SELECT * FROM accounts ORDER BY id')

			accounts = []
			for row in cursor.fetchall():
				account = dict(row)
				# 根据认证类型解密对应字段
				if account.get('auth_type') == 'password' and account.get('password'):
					account['password'] = self._decrypt(account['password'])
				elif account.get('auth_type') == 'cookies' and account.get('cookies'):
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

	def get_checkin_logs(self, account_id: int = None, limit: int = 100) -> List[dict]:
		"""获取签到日志"""
		with self.get_connection() as conn:
			cursor = conn.cursor()
			if account_id:
				cursor.execute(
					'''
                    SELECT cl.*, a.name as account_name
                    FROM checkin_logs cl
                    JOIN accounts a ON cl.account_id = a.id
                    WHERE cl.account_id = ?
                    ORDER BY cl.created_at DESC
                    LIMIT ?
                ''',
					(account_id, limit),
				)
			else:
				cursor.execute(
					'''
                    SELECT cl.*, a.name as account_name
                    FROM checkin_logs cl
                    JOIN accounts a ON cl.account_id = a.id
                    ORDER BY cl.created_at DESC
                    LIMIT ?
                ''',
					(limit,),
				)

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

	# ========== 统计信息 ==========

	def get_statistics(self) -> dict:
		"""获取统计信息"""
		with self.get_connection() as conn:
			cursor = conn.cursor()

			# 总账号数
			cursor.execute('SELECT COUNT(*) as total, SUM(enabled) as enabled FROM accounts')
			account_stats = dict(cursor.fetchone())

			# 今日签到统计
			cursor.execute(
				'''
                SELECT COUNT(*) as total, SUM(success) as success
                FROM checkin_logs
                WHERE DATE(created_at) = DATE('now')
            '''
			)
			today_stats = dict(cursor.fetchone())

			# 总余额 - 获取每个账号的最新余额
			cursor.execute(
				'''
                SELECT SUM(quota) as total_quota, SUM(used_quota) as total_used
                FROM (
                    SELECT account_id, quota, used_quota
                    FROM balance_history bh1
                    WHERE created_at = (
                        SELECT MAX(created_at)
                        FROM balance_history bh2
                        WHERE bh2.account_id = bh1.account_id
                    )
                    GROUP BY account_id
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
