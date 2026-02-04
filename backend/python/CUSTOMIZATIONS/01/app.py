import os
import json
import time
import bcrypt
import jwt

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials

from db import execute_on_conn, apply_schema

JWT_SECRET = "DEMO_JWT_SECRET"
JWT_ALG = "HS256"

ADMIN_LOGIN = "admin"
ADMIN_PWD = "admin"

app = FastAPI(title="Demo Backend")
bearer = HTTPBearer(auto_error=False)

@app.on_event("startup")
def startup():
    apply_schema()
    create_admin()

# Helpers --->

def JWT_encode(user_id: str, login: str, role: str) -> str:
    now = int(time.time())
    payload = {
        "user_id": user_id,
        "login": login,
        "role": role,
        "iat": now,
        "exp": now + 2 * 3600,
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALG)

def JWT_decode(token: str) -> dict:
    return jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALG])

def parse_claims(creds: HTTPAuthorizationCredentials = Depends(bearer)) -> dict:
    if not creds or creds.scheme.lower() != "bearer":
        raise HTTPException(status_code=401, detail={"error": "missing token"})
    try:
        return JWT_decode(creds.credentials)
    except Exception:
        raise HTTPException(status_code=401, detail={"error": "invalid token"})

def restrict_admin(claims: dict=Depends(parse_claims)) -> dict:
    if claims.get("role") != "admin":
        raise HTTPException(status_code=403, detail={"error": "forbidden"})
    return claims

def create_admin():

    def process(cur):
        global ADMIN_LOGIN
        global ADMIN_PWD

        cur.execute("SELECT 1 FROM users WHERE login=%s", (ADMIN_LOGIN,))
        if cur.fetchone():
            return
        cur.execute(
            """
            INSERT INTO users (login, password, full_name, phone, email, role)
            VALUES (%s,%s,%s,%s,%s,%s)
            """,
            (ADMIN_LOGIN, ADMIN_PWD, "Administrator", "8(000)000-00-00", "admin@gmail.com", "admin"),
        )

    execute_on_conn(process)

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
def api_user_register(input:dict):

    login = (input.get("login") or "").strip()
    password = input.get("password") or ""
    full_name = (input.get("full_name") or "").strip()
    phone = (input.get("phone") or "").strip()
    email = (input.get("email") or "").strip()

    output = {}

    def process(cur):
        nonlocal output

        cur.execute("SELECT 1 FROM users WHERE login=%s", (login,))
        if cur.fetchone():
            reply_error(409, "login already exists")

        cur.execute(
            """
            INSERT INTO users (login, password, full_name, phone, email, role)
            VALUES (%s,%s,%s,%s,%s,'user')
            RETURNING id, login, full_name, phone, email, role
            """,
            (login, password, full_name, phone, email),
        )
        row = cur.fetchone()
        output = {
            "id": str(row[0]),
            "login": row[1],
            "full_name": row[2],
            "phone": row[3],
            "email": row[4],
            "role": row[5],
        }

    execute_on_conn(process)
    return output

# curl -s http://localhost:8080/api/user/login \
#    -H "Content-Type: application/json" \
#    -d '{"login":"user123","password":"password123"}'

@app.post(API_USER_LOGIN)
def api_user_login(input:dict):

    login = (input.get("login") or "").strip()
    password = input.get("password") or ""
    if not login or not password:
        reply_error(400, "login and password required")

    output = {}

    def process(cur):
        nonlocal output

        cur.execute(
            "SELECT id, login, password, full_name, role FROM users WHERE login=%s",
            (login,),
        )
        row = cur.fetchone()
        if not row or row[2] != password:
            reply_error(401, "invalid login or password")
        token = JWT_encode(str(row[0]), row[1], row[4])
        output = {
            "token": token,
            "user": {
                "id": str(row[0]),
                "login": row[1],
                "full_name": row[3],
                "role": row[4]
            }
        }

    execute_on_conn(process)
    return output

# curl -i http://localhost:8080/api/user/reqs/create \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"type":"service_visit","payload":{"car_brand":"Toyota","car_model":"Camry","date":"2026-01-25","problem":"Something"}}'

@app.post(API_USER_REQS_CREATE, status_code=201)
def api_user_reqs_create(input:dict, claims=Depends(parse_claims)):

    typ = (input.get("type") or "").strip()
    if not typ:
        reply_error(400, "type required")

    pl = input.get("payload")

    output = {}

    def process(cur):
        nonlocal output

        cur.execute(
            """
            INSERT INTO requests (user_id, type, payload)
            VALUES (%s,%s,%s::jsonb)
            RETURNING id, user_id, type, payload, status
            """,
            (claims["user_id"], typ, json.dumps(pl)),
        )
        row = cur.fetchone()
        output = {
            "id": str(row[0]),
            "user_id": str(row[1]),
            "type": row[2],
            "payload": row[3],
            "status": row[4]
        }

    execute_on_conn(process)
    return output

# curl -s http://localhost:8080/api/user/reqs/list -H "Authorization: Bearer $TOKEN" | jq

@app.get(API_USER_REQS_LIST)
def api_user_reqs_list(claims=Depends(parse_claims)):

    output = {}

    def process(cur):
        nonlocal output
        cur.execute(
            """
            SELECT id, user_id, type, payload, status
            FROM requests
            WHERE user_id=%s
            """,
            (claims["user_id"],),
        )
        rows = cur.fetchall()
        output = [
            {
                "id": str(r[0]),
                "user_id": str(r[1]),
                "type": r[2],
                "payload": r[3],
                "status": r[4]
            }
            for r in rows
        ]

    execute_on_conn(process)
    return {"items":output}

# curl -i http://localhost:8080/api/user/reqs/$ITEM_ID/rate \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"rating":5,"comment":"OK!"}'

@app.post(f'{API_USER_REQS}' "/{req_id}/rate", status_code=201)
def api_user_reqs_rate(req_id:str, input:dict, claims=Depends(parse_claims)):

    rating = input.get("rating")
    comment = input.get("comment")

    if not isinstance(rating, int) or rating < 0 or rating > 5:
        reply_error(400, "rating must be 1..5")

    output = {}

    def process(cur):
        nonlocal output

        cur.execute(
            "SELECT 1 FROM requests WHERE id=%s AND user_id=%s",
            (req_id, claims["user_id"]),
        )
        if not cur.fetchone():
            reply_error(403, "forbidden")

        try:
            cur.execute(
                """
                INSERT INTO feedback (request_id, user_id, rating, comment)
                VALUES (%s,%s,%s,%s)
                RETURNING id, request_id, user_id, rating, comment
                """,
                (req_id, claims["user_id"], rating, comment),
            )
            row = cur.fetchone()
        except Exception:
            reply_error(400, "db error")

        output = {
            "id": str(row[0]),
            "request_id": str(row[1]),
            "user_id": str(row[2]),
            "rating": row[3],
            "comment": row[4]
        }

    execute_on_conn(process)
    return output

# Admin --->

# Login Admin:
# curl -s http://localhost:8080/api/user/login \
#    -H "Content-Type: application/json" \
#    -d '{"login":"admin","password":"admin"}'

# curl -s http://localhost:8080/api/admin/reqs/list -H "Authorization: Bearer $TOKEN" | jq

@app.get(API_ADMIN_REQS_LIST)
def api_admin_reqs_list(claims=Depends(restrict_admin)):
    output = {}

    def process(cur):
        nonlocal output

        cur.execute(
            """
            SELECT r.id, r.user_id, u.login, r.type, r.payload, r.status
            FROM requests r
            JOIN users u ON u.id = r.user_id
            """
        )
        rows = cur.fetchall()
        output = [
            {
                "id": str(r[0]),
                "user_id": str(r[1]),
                "user_login": r[2],
                "type": r[3],
                "payload": r[4],
                "status": r[5]
            }
            for r in rows
        ]

    execute_on_conn(process)
    return {"items":output}

# curl -s http://localhost:8080/api/admin/reqs/$ITEM_ID/status \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"status":"in_progress"}'

@app.post(f'{API_ADMIN_REQS}' "/{req_id}/status")
def api_admin_reqs_status(req_id:str, input:dict, claims=Depends(restrict_admin)):

    status = (input.get("status") or "").strip()

    if status not in ("new", "in_progress", "approved", "rejected", "done"):
        reply_error(400, "invalid status")

    def process(cur):
        cur.execute(
            "UPDATE requests SET status=%s WHERE id=%s",
            (status, req_id),
        )

    execute_on_conn(process)
    return {"status":True}
