import os
import smtplib
from email.mime.text import MIMEText
from typing import Literal

import httpx


class NotificationKit:
	def __init__(self):
		# 优先从数据库读取配置，fallback 到环境变量
		self.email_user: str = self._get_config('email_user') or os.getenv('EMAIL_USER', '')
		self.email_pass: str = self._get_config('email_pass') or os.getenv('EMAIL_PASS', '')
		self.email_to: str = os.getenv('EMAIL_TO', '')
		self.smtp_server: str = self._get_config('custom_smtp_server') or os.getenv('CUSTOM_SMTP_SERVER', '')
		self.pushplus_token = os.getenv('PUSHPLUS_TOKEN')
		self.server_push_key = os.getenv('SERVERPUSHKEY')
		self.dingding_webhook = os.getenv('DINGDING_WEBHOOK')
		self.feishu_webhook = os.getenv('FEISHU_WEBHOOK')
		self.weixin_webhook = os.getenv('WEIXIN_WEBHOOK')
		self.telegram_bot_token = os.getenv('TELEGRAM_BOT_TOKEN')
		self.telegram_chat_id = os.getenv('TELEGRAM_CHAT_ID')

	def _get_config(self, key: str) -> str | None:
		"""从数据库获取配置（如果可用）"""
		try:
			# 动态导入避免循环依赖
			from web.database import db
			value = db.get_config(key)
			return value
		except Exception as e:
			# 如果数据库不可用（比如在 GitHub Actions 环境），返回 None
			print(f'[WARN] Failed to get config "{key}" from database: {e}')
			return None

	def send_email(self, title: str, content: str, msg_type: Literal['text', 'html'] = 'text'):
		if not self.email_user or not self.email_pass or not self.email_to:
			raise ValueError('Email configuration not set')

		# MIMEText 需要 'plain' 或 'html'，而不是 'text'
		mime_subtype = 'plain' if msg_type == 'text' else 'html'
		msg = MIMEText(content, mime_subtype, 'utf-8')
		msg['From'] = f'AnyRouter Assistant <{self.email_user}>'
		msg['To'] = self.email_to
		msg['Subject'] = title

		smtp_server = self.smtp_server if self.smtp_server else f'smtp.{self.email_user.split("@")[1]}'

		# 尝试 SSL 连接，失败则尝试 STARTTLS
		import ssl
		server = None
		try:
			context = ssl.create_default_context()
			server = smtplib.SMTP_SSL(smtp_server, 465, timeout=10, context=context)
			server.login(self.email_user, self.email_pass)
			server.send_message(msg)
			server.quit()
		except Exception:
			# 如果 SSL 失败，尝试 STARTTLS (587端口)
			if server:
				try:
					server.quit()
				except Exception:
					pass
			server = smtplib.SMTP(smtp_server, 587, timeout=10)
			server.starttls()
			server.login(self.email_user, self.email_pass)
			server.send_message(msg)
			server.quit()

	def send_email_to(
		self, to_email: str, title: str, content: str, msg_type: Literal['text', 'html'] = 'text'
	):
		"""发送邮件到指定邮箱（用于单个账号通知）"""
		if not self.email_user or not self.email_pass:
			raise ValueError('Email configuration (EMAIL_USER and EMAIL_PASS) not set')

		if not to_email:
			raise ValueError('Recipient email address not provided')

		# MIMEText 需要 'plain' 或 'html'，而不是 'text'
		mime_subtype = 'plain' if msg_type == 'text' else 'html'
		msg = MIMEText(content, mime_subtype, 'utf-8')
		msg['From'] = f'AnyRouter Assistant <{self.email_user}>'
		msg['To'] = to_email
		msg['Subject'] = title

		smtp_server = self.smtp_server if self.smtp_server else f'smtp.{self.email_user.split("@")[1]}'

		# 尝试 SSL 连接，失败则尝试 STARTTLS
		import ssl
		server = None
		try:
			context = ssl.create_default_context()
			server = smtplib.SMTP_SSL(smtp_server, 465, timeout=10, context=context)
			server.login(self.email_user, self.email_pass)
			server.send_message(msg)
			server.quit()
		except Exception:
			# 如果 SSL 失败，尝试 STARTTLS (587端口)
			if server:
				try:
					server.quit()
				except Exception:
					pass
			server = smtplib.SMTP(smtp_server, 587, timeout=10)
			server.starttls()
			server.login(self.email_user, self.email_pass)
			server.send_message(msg)
			server.quit()

	def send_pushplus(self, title: str, content: str):
		if not self.pushplus_token:
			raise ValueError('PushPlus Token not configured')

		data = {'token': self.pushplus_token, 'title': title, 'content': content, 'template': 'html'}
		with httpx.Client(timeout=30.0) as client:
			client.post('http://www.pushplus.plus/send', json=data)

	def send_serverPush(self, title: str, content: str):
		if not self.server_push_key:
			raise ValueError('Server Push key not configured')

		data = {'title': title, 'desp': content}
		with httpx.Client(timeout=30.0) as client:
			client.post(f'https://sctapi.ftqq.com/{self.server_push_key}.send', json=data)

	def send_dingtalk(self, title: str, content: str):
		if not self.dingding_webhook:
			raise ValueError('DingTalk Webhook not configured')

		data = {'msgtype': 'text', 'text': {'content': f'{title}\n{content}'}}
		with httpx.Client(timeout=30.0) as client:
			client.post(self.dingding_webhook, json=data)

	def send_feishu(self, title: str, content: str):
		if not self.feishu_webhook:
			raise ValueError('Feishu Webhook not configured')

		data = {
			'msg_type': 'interactive',
			'card': {
				'elements': [{'tag': 'markdown', 'content': content, 'text_align': 'left'}],
				'header': {'template': 'blue', 'title': {'content': title, 'tag': 'plain_text'}},
			},
		}
		with httpx.Client(timeout=30.0) as client:
			client.post(self.feishu_webhook, json=data)

	def send_wecom(self, title: str, content: str):
		if not self.weixin_webhook:
			raise ValueError('WeChat Work Webhook not configured')

		data = {'msgtype': 'text', 'text': {'content': f'{title}\n{content}'}}
		with httpx.Client(timeout=30.0) as client:
			client.post(self.weixin_webhook, json=data)

	def send_telegram(self, title: str, content: str):
		if not self.telegram_bot_token or not self.telegram_chat_id:
			raise ValueError('Telegram Bot Token or Chat ID not configured')

		message = f'<b>{title}</b>\n\n{content}'
		data = {'chat_id': self.telegram_chat_id, 'text': message, 'parse_mode': 'HTML'}
		url = f'https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage'
		with httpx.Client(timeout=30.0) as client:
			client.post(url, json=data)

	def push_message(self, title: str, content: str, msg_type: Literal['text', 'html'] = 'text'):
		notifications = [
			('Email', lambda: self.send_email(title, content, msg_type)),
			('PushPlus', lambda: self.send_pushplus(title, content)),
			('Server Push', lambda: self.send_serverPush(title, content)),
			('DingTalk', lambda: self.send_dingtalk(title, content)),
			('Feishu', lambda: self.send_feishu(title, content)),
			('WeChat Work', lambda: self.send_wecom(title, content)),
			('Telegram', lambda: self.send_telegram(title, content)),
		]

		for name, func in notifications:
			try:
				func()
				print(f'[{name}]: Message push successful!')
			except Exception as e:
				print(f'[{name}]: Message push failed! Reason: {str(e)}')


notify = NotificationKit()
