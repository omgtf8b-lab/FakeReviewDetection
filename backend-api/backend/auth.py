from __future__ import annotations

import base64
import hashlib
import hmac
import json
import os
import time
from datetime import datetime, timedelta, timezone

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

import models
from config import settings
from database import get_db

PBKDF2_ITERATIONS = 310_000
bearer_scheme = HTTPBearer(auto_error=False)


def _b64(data: bytes) -> str:
    return base64.urlsafe_b64encode(data).rstrip(b"=").decode("ascii")


def _unb64(data: str) -> bytes:
    return base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))


def hash_password(password: str) -> str:
    salt = os.urandom(16)
    derived = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, PBKDF2_ITERATIONS)
    return f"pbkdf2_sha256${PBKDF2_ITERATIONS}${_b64(salt)}${_b64(derived)}"


def verify_password(password: str, encoded: str) -> bool:
    try:
        scheme, iterations, salt_b64, hash_b64 = encoded.split("$", 3)
        if scheme != "pbkdf2_sha256":
            return False
        salt = _unb64(salt_b64)
        expected = _unb64(hash_b64)
        actual = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, int(iterations))
        return hmac.compare_digest(actual, expected)
    except (ValueError, TypeError):
        return False


def create_access_token(user: models.User) -> str:
    from sqlalchemy.orm import object_session
    from extended_models import Profile
    session = object_session(user)
    profile = session.get(Profile, user.id) if session else None
    version = profile.token_version if profile else 0
    now = int(time.time())
    exp = now + settings.access_token_expire_minutes * 60
    header = _b64(json.dumps({"alg": "HS256", "typ": "JWT"}, separators=(",", ":")).encode())
    payload = _b64(json.dumps({"sub": str(user.id), "role": user.role, "ver": version, "iat": now, "exp": exp}, separators=(",", ":")).encode())
    unsigned = f"{header}.{payload}".encode("ascii")
    signature = _b64(hmac.new(settings.secret_key.encode("utf-8"), unsigned, hashlib.sha256).digest())
    return f"{header}.{payload}.{signature}"


def decode_access_token(token: str) -> dict:
    try:
        header_b64, payload_b64, signature_b64 = token.split(".", 2)
        unsigned = f"{header_b64}.{payload_b64}".encode("ascii")
        expected = hmac.new(settings.secret_key.encode("utf-8"), unsigned, hashlib.sha256).digest()
        actual = _unb64(signature_b64)
        if not hmac.compare_digest(expected, actual):
            raise ValueError("Invalid signature")
        header = json.loads(_unb64(header_b64))
        payload = json.loads(_unb64(payload_b64))
        if header.get("alg") != "HS256" or header.get("typ") != "JWT":
            raise ValueError("Invalid token header")
        exp = int(payload.get("exp", 0))
        if exp <= int(time.time()):
            raise ValueError("Expired token")
        return payload
    except (ValueError, TypeError, KeyError, json.JSONDecodeError, UnicodeDecodeError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ hoặc đã hết hạn")


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: Session = Depends(get_db),
):
    if credentials is None or credentials.scheme.lower() != "bearer":
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing or invalid Bearer token")
    payload = decode_access_token(credentials.credentials)
    try:
        user_id = int(payload.get("sub"))
    except (TypeError, ValueError):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token không hợp lệ")

    user = db.query(models.User).filter(models.User.id == user_id).first()
    if not user or not user.is_active:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Tài khoản không tồn tại hoặc đã bị khóa")
    from extended_models import Profile
    profile = db.get(Profile, user.id)
    if payload.get('ver', 0) != (profile.token_version if profile else 0):
        raise HTTPException(401, 'Mật khẩu đã thay đổi. Vui lòng đăng nhập lại.')
    return user


def require_roles(*roles: str):
    def dependency(current_user: models.User = Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Bạn không có quyền thực hiện thao tác này")
        return current_user
    return dependency
