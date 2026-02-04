import time
import json

import jwt
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db import apply_sql, db_call_json

JWT_SECRET = "DEMO_JWT_SECRET"
JWT_ALG = "HS256"

ADMIN_LOGIN = "admin"
ADMIN_PWD = "admin"

app = FastAPI(title="Demo Backend")
bearer = HTTPBearer(auto_error=False)

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------- helpers ----------------

def reply_error(code: int, msg: str):
    raise HTTPException(status_code=code, detail={"error": msg})

def create_token(user_id: str, login: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "user_id": user_id,
        "login": login,
        "role": role,
        "iat": now,
        "exp": now + 2 * 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def parse_token(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def parse_claims(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"error": "missing token"})
    try:
        return parse_token(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "invalid token"})

def restrict_admin(claims: dict = Depends(parse_claims)) -> dict:
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    return claims

def create_admin():
    global ADMIN_LOGIN
    global ADMIN_PWD
    _ = db_call_json(
        "api_seed_admin(%s, %s)",
        (ADMIN_LOGIN, ADMIN_PWD),
    )

@app.on_event("startup")
def startup():
    apply_sql()
    create_admin()

# ---------------- routes ----------------

API_USER_LOGIN = "/api/user/login"
API_USER_REGISTER = "/api/user/register"
API_USER_REQS_CREATE = "/api/user/reqs/create"
API_USER_REQS = "/api/user/reqs"
API_ADMIN_REQS = "/api/admin/reqs"
API_USER_REQS_LIST = "/api/user/reqs/list"
API_ADMIN_REQS_LIST = "/api/admin/reqs/list"

# -------- User --------

@app.post(API_USER_REGISTER, status_code=201)
def api_user_register(input: dict):
    login = (input.get("login") or "").strip()
    password = input.get("password") or ""
    full_name = (input.get("full_name") or "").strip()
    phone = (input.get("phone") or "").strip()
    email = (input.get("email") or "").strip()

    return db_call_json(
        "api_user_register(%s, %s, %s, %s, %s)",
        (login, password, full_name, phone, email),
    )

@app.post(API_USER_LOGIN)
def api_user_login(input: dict):
    login = (input.get("login") or "").strip()
    password = input.get("password") or ""
    if not login or not password:
        reply_error(400, "login and password required")

    user = db_call_json("api_user_login(%s, %s)", (login, password))

    token = create_token(user["id"], user["login"], user["role"])
    return {"token": token, "user": user}

@app.post(API_USER_REQS_CREATE, status_code=201)
def api_user_reqs_create(input: dict, claims=Depends(parse_claims)):
    typ = (input.get("type") or "").strip()
    if not typ:
        reply_error(400, "type required")

    pl = input.get("payload")
    if pl is None:
        pl = {}

    return db_call_json(
        "api_user_requests_create(%s, %s, %s::jsonb)",
        (claims["user_id"], typ, json.dumps(pl)),
    )

@app.get(API_USER_REQS_LIST)
def api_user_reqs_list(claims=Depends(parse_claims)):
    return db_call_json("api_user_requests_list(%s)", (claims["user_id"],))

@app.post(f"{API_USER_REQS}" + "/{req_id}/rate", status_code=201)
def api_user_reqs_rate(req_id: str, input: dict, claims=Depends(parse_claims)):
    rating = input.get("rating")
    comment = input.get("comment")

    return db_call_json(
        "api_user_request_rate(%s::uuid, %s::uuid, %s::int, %s::text)",
        (claims["user_id"], req_id, rating, comment),
    )

# -------- Admin --------

@app.get(API_ADMIN_REQS_LIST)
def api_admin_reqs_list(claims=Depends(restrict_admin)):
    return db_call_json("api_admin_requests_list(%s)", (claims["user_id"],))

@app.post(f"{API_ADMIN_REQS}" + "/{req_id}/status")
def api_admin_reqs_status(req_id: str, input: dict, claims=Depends(restrict_admin)):
    status = (input.get("status") or "").strip()
    if not status:
        reply_error(400, "status required")

    _ = db_call_json("api_admin_request_set_status(%s, %s, %s)", (claims["user_id"], req_id, status))
    return {"status": True}
