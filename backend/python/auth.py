import os
import time
import bcrypt
import jwt
from fastapi import Depends, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

JWT_SECRET = os.getenv("JWT_SECRET", "")
if not JWT_SECRET:
    raise RuntimeError("JWT_SECRET is required")

JWT_ALG = "HS256"
JWT_TTL_SEC = 24 * 3600

bearer = HTTPBearer(auto_error=False)

def hash_password(pw: str) -> str:
    return bcrypt.hashpw(pw.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

def check_password(pw: str, pw_hash: str) -> bool:
    try:
        return bcrypt.checkpw(pw.encode("utf-8"), pw_hash.encode("utf-8"))
    except Exception:
        return False

def sign_jwt(user_id: str, login: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "user_id": user_id,
        "login": login,
        "role": role,
        "iat": now,
        "exp": now + JWT_TTL_SEC,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def verify_jwt(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def get_current_user(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"error": "missing token"})
    try:
        claims = verify_jwt(creds.credentials)
        return claims
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "invalid token"})

def require_admin(user: dict = Depends(get_current_user)) -> dict:
    if user.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    return user

