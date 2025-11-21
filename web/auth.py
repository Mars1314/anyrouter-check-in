"""
用户认证模块
实现 JWT token 生成和验证
"""

import os
from datetime import datetime, timedelta
from typing import Optional

import jwt
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

# JWT 配置
SECRET_KEY = os.getenv('JWT_SECRET_KEY', 'your-secret-key-change-in-production-please')
ALGORITHM = 'HS256'
ACCESS_TOKEN_EXPIRE_MINUTES = 60 * 24 * 7  # 7 天

security = HTTPBearer()


def create_access_token(data: dict, expires_delta: Optional[timedelta] = None):
	"""创建 JWT token"""
	to_encode = data.copy()
	if expires_delta:
		expire = datetime.utcnow() + expires_delta
	else:
		expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

	to_encode.update({'exp': expire})
	encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)
	return encoded_jwt


def verify_token(token: str) -> dict:
	"""验证 JWT token"""
	try:
		payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM])
		return payload
	except jwt.ExpiredSignatureError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='Token 已过期')
	except jwt.JWTError:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='无效的 Token')


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security)) -> dict:
	"""从 token 获取当前用户信息"""
	token = credentials.credentials
	payload = verify_token(token)

	user_id = payload.get('user_id')
	if user_id is None:
		raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail='无效的认证凭据')

	return {'user_id': user_id, 'username': payload.get('username'), 'role': payload.get('role')}


def require_admin(current_user: dict = Depends(get_current_user)) -> dict:
	"""要求管理员权限"""
	if current_user.get('role') != 'admin':
		raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail='需要管理员权限')
	return current_user
