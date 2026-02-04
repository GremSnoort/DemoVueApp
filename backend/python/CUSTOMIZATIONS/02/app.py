import os
import json
import time
import bcrypt
import jwt

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db import db_run, apply_sql

JWT_SECRET = "DEMO_JWT_SECRET"
JWT_ALG = "HS256"

ADMIN_LOGIN = "admin"
ADMIN_PWD = "admin"

app = FastAPI(title="Demo Backend")
bearer = HTTPBearer(auto_error=False)

@app.on_event("startup")
def startup():
    apply_sql()
    create_admin()

# Helpers --->

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

def restrict_admin(claims: dict=Depends(parse_claims)) -> dict:
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    return claims

def create_admin():

    def action(cur):
        global ADMIN_LOGIN
        global ADMIN_PWD

        cur.execute("SELECT create_admin(%s, %s, %s, %s, %s)",
            (ADMIN_LOGIN, ADMIN_PWD, "Administrator", "8(000)000-00-00", "admin@test.com"))
        created = cur.fetchone()[0] # bool

    db_run(action)

def reply_error(code:int, msg:str):
    raise HTTPException(status_code=code, detail={"error":msg})

# API --->

API_USER_LOGIN = "/api/user/login"
API_USER_REGISTER = "/api/user/register"
API_USER_REQS_CREATE = "/api/user/reqs/create"
API_USER_REQS = "/api/user/reqs"
API_ADMIN_REQS = "/api/admin/reqs"
API_USER_REQS_LIST = "/api/user/reqs/list"
API_ADMIN_REQS_LIST = "/api/admin/reqs/list"

# User --->

# curl -i http://localhost:8080/api/user/register \
#    -H "Content-Type: application/json" \
#    -d '{"login":"user123","password":"password123","full_name":"Some Name","phone":"8(999)111-22-33","email":"u@ex.com"}'

@app.post(API_USER_REGISTER, status_code=201)
def handler_user_register(input:dict):

    login = (input.get("login") or "").strip()
    password = input.get("password") or ""
    full_name = (input.get("full_name") or "").strip()
    phone = (input.get("phone") or "").strip()
    email = (input.get("email") or "").strip()

    output = {}

    def action(cur):
        nonlocal output
        try:
            cur.execute(
                "SELECT user_register(%s,%s,%s,%s,%s)",
                (login, password, full_name, phone, email),
            )
            output = cur.fetchone()[0] # json/jsonb
        except Exception as e:
            if getattr(e, "sqlstate", None) == "23505":
                reply_error(409, "login already exists")
            else:
                reply_error(400, str(e))

    db_run(action)
    return output

# curl -s http://localhost:8080/api/user/login \
#    -H "Content-Type: application/json" \
#    -d '{"login":"user123","password":"password123"}'

@app.post(API_USER_LOGIN)
def handler_user_login(input:dict):

    login = (input.get("login") or "").strip()
    password = input.get("password") or ""
    if not login or not password:
        reply_error(400, "login and password required")

    output = {}

    def action(cur):
        nonlocal output

        try:
            cur.execute("SELECT user_login(%s, %s)", (login, password))
            user = cur.fetchone()[0] # json/jsonb
        except Exception as e:
            if getattr(e, "sqlstate", None) == "28P01":
                reply_error(401, "invalid login or password")
            else:
                reply_error(400, str(e))

        token = create_token(user["id"], user["login"], user["role"])
        output = {
            "token": token,
            "user": user
        }

    db_run(action)
    return output

# curl -i http://localhost:8080/api/user/reqs/create \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"type":"service_visit","payload":{"car_brand":"Toyota","car_model":"Camry","date":"2026-01-25","problem":"Something"}}'

@app.post(API_USER_REQS_CREATE, status_code=201)
def handler_user_reqs_create(input:dict, claims=Depends(parse_claims)):

    typ = (input.get("type") or "").strip()
    if not typ:
        reply_error(400, "type required")

    pl = input.get("payload")

    output = {}

    def action(cur):
        nonlocal output

        try:
            cur.execute(
                "SELECT user_request_create(%s, %s, %s::jsonb)",
                (claims["user_id"], typ, json.dumps(pl)),
            )
            output = cur.fetchone()[0]
        except Exception as e:
            if getattr(e, "sqlstate", None) == "22023":
                reply_error(400, "type required")
            else:
                reply_error(400, str(e))

    db_run(action)
    return output

# curl -s http://localhost:8080/api/user/reqs/list -H "Authorization: Bearer $TOKEN" | jq

@app.get(API_USER_REQS_LIST)
def handler_user_reqs_list(claims=Depends(parse_claims)):

    output = {}

    def action(cur):
        nonlocal output
        cur.execute("SELECT user_requests_list(%s)", (claims["user_id"],))
        output = cur.fetchone()[0] # jsonb

    db_run(action)
    return output

# curl -i http://localhost:8080/api/user/reqs/$ITEM_ID/rate \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"rating":5,"comment":"OK!"}'

@app.post(f'{API_USER_REQS}' "/{req_id}/rate", status_code=201)
def handler_user_reqs_rate(req_id:str, input:dict, claims=Depends(parse_claims)):

    rating = input.get("rating")
    comment = input.get("comment")

    output = {}

    def action(cur):
        nonlocal output

        try:
            cur.execute(
                "SELECT user_request_rate(%s::uuid, %s::uuid, %s::int, %s::text)",
                (req_id, claims["user_id"], rating, comment),
            )
            output = cur.fetchone()[0] # jsonb
        except Exception as e:
            msg = str(e)
            if "22023" in msg:
                reply_error(400, "rating must be 0..5")
            if "42501" in msg:
                reply_error(403, "forbidden")
            if "23505" in msg:
                reply_error(400, "feedback already exists")
            reply_error(400, str(e))

    db_run(action)
    return output

# Admin --->

# Login Admin:
# curl -s http://localhost:8080/api/user/login \
#    -H "Content-Type: application/json" \
#    -d '{"login":"admin","password":"admin"}'

# curl -s http://localhost:8080/api/admin/reqs/list -H "Authorization: Bearer $TOKEN" | jq

@app.get(API_ADMIN_REQS_LIST)
def handler_admin_reqs_list(claims=Depends(restrict_admin)):
    output = {}

    def action(cur):
        nonlocal output
        cur.execute("SELECT admin_requests_list()")
        output = cur.fetchone()[0]

    db_run(action)
    return output

# curl -s http://localhost:8080/api/admin/reqs/$ITEM_ID/status \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"status":"in_progress"}'

@app.post(f'{API_ADMIN_REQS}' "/{req_id}/status")
def handler_admin_reqs_status(req_id:str, input:dict, claims=Depends(restrict_admin)):

    status = input.get("status")
    if not status:
        reply_error(400, "status required")

    def action(cur):
        try:
            cur.execute(
                "SELECT admin_request_set_status(%s, %s)",
                (req_id, status)
            )
        except Exception as e:
            reply_error(400, str(e))

    db_run(action)
    return {"status":True}
