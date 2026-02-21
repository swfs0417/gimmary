from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
import argon2
from authlib.jose import jwt
from authlib.jose.errors import JoseError

from gimmary.app.auth.settings import AUTH_SETTINGS
from gimmary.database.models import User
from gimmary.database.connection import get_db_session


HTTP_BEARER = HTTPBearer()

def verify_password(plain_password: str, hashed_password: str) -> None:
	try:
		argon2.PasswordHasher().verify(hashed_password, plain_password)
	except argon2.exceptions.VerifyMismatchError:
		raise HTTPException(status_code=401, detail='Invalid credentials')

def hash_password(password: str) -> str:
  return argon2.PasswordHasher().hash(password)

def issue_token(user_id: str, lifespan_minutes: int, secret: str) -> str:
	header = {'alg': 'HS256'}
	payload = {
		'sub': user_id,
		'exp': int((datetime.now() + timedelta(minutes=lifespan_minutes)).timestamp())
	}
	return str(jwt.encode(header, payload, key=secret), 'utf-8')

def verify_token(token: str, secret: str, expected_type: str) -> str:
  try:
    claims = jwt.decode(token, secret)
    claims.validate_exp(now=datetime.now().timestamp(), leeway=0)
    if claims.get("type") != expected_type:
      raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Invalid token type",
        headers={"WWW-Authenticate": "Bearer"},
      )
    return claims.get("sub")
  except JoseError:
    raise HTTPException(
      status_code=status.HTTP_401_UNAUTHORIZED,
      detail="Invalid or expired token",
      headers={"WWW-Authenticate": "Bearer"},
    )

def get_header_token(credentials: HTTPAuthorizationCredentials = Depends(HTTP_BEARER)) -> str:
  return credentials.credentials

def refresh_token(token: Annotated[str | None, Depends(get_header_token)] = None) -> str:
  return verify_token(token, AUTH_SETTINGS.REFRESH_TOKEN_SECRET, "refresh")

def login_with_header(token: Annotated[str | None, Depends(get_header_token)] = None) -> str:
  return verify_token(token, AUTH_SETTINGS.ACCESS_TOKEN_SECRET, "access")

def get_current_user(user_id: Annotated[str, Depends(login_with_header)]) -> str:
  db_session = get_db_session()
  user = db_session.query(User).filter(User.id == user_id).first()
  if not user:
    raise HTTPException(status_code=404, detail="User not found")
  return user