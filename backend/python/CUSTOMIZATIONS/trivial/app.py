import os
import json
import time
import bcrypt
import jwt

from fastapi import FastAPI, HTTPException, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi.middleware.cors import CORSMiddleware

from db import execute_on_conn, apply_schema


JWT_SECRET = "DEMO_JWT_SECRET"
JWT_ALG = "HS256"


app = FastAPI(title="Demo Backend")


app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


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
        login = "admin"
        pwd = "admin"

        cur.execute("""
            DELETE FROM users WHERE role='admin';
        """)

        cur.execute("""
            WITH ins AS (
                INSERT INTO users (login, password, name, phone, email, role)
                VALUES (%s,%s,%s,%s,%s,'admin')
                ON CONFLICT DO NOTHING
                RETURNING 1
            )
            SELECT EXISTS (SELECT 1 FROM ins);
        """,
        (login, pwd, "Administrator", "8(000)000-00-00", "admin@gmail.com"),)

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
#    -d '{"login":"user123","password":"password123","name":"Some Name","phone":"8(999)111-22-33","email":"u@ex.com"}'

@app.post(API_USER_REGISTER, status_code=201)
def api_user_register(input:dict):

    login = input.get("login")
    password = input.get("password")
    name = input.get("name")
    phone = input.get("phone")
    email = input.get("email")

    if not login or not password or not name or not phone or not email:
        reply_error(400, "incomplete data")

    output = {}

    def process(cur):
        nonlocal output

        cur.execute("""
            INSERT INTO users (login, password, name, phone, email, role)
            VALUES (%s,%s,%s,%s,%s,'user')
            ON CONFLICT (login) DO NOTHING
            RETURNING jsonb_build_object(
                'id', id::text,
                'login', login,
                'name', name,
                'phone', phone,
                'email', email,
                'role', role
            );
        """, (login, password, name, phone, email),)

        row = cur.fetchone()
        if not row:
            reply_error(409, "login already exists")

        output = row[0]

    execute_on_conn(process)
    return output


# curl -s http://localhost:8080/api/user/login \
#    -H "Content-Type: application/json" \
#    -d '{"login":"user123","password":"password123"}'

@app.post(API_USER_LOGIN)
def api_user_login(input:dict):

    login = input.get("login")
    password = input.get("password")

    if not login or not password:
        reply_error(400, "login and password required")

    output = {}

    def process(cur):
        nonlocal output

        cur.execute("""
            SELECT jsonb_build_object(
                'id', u.id::text,
                'login', u.login,
                'name', u.name,
                'role', u.role
            )
            FROM users u
            WHERE u.login = %s
            AND u.password = %s;
        """, (login, password),)

        row = cur.fetchone()
        if not row:
            reply_error(401, "invalid login or password")

        user = row[0]

        token = JWT_encode(user["id"], user["login"], user["role"])
        output = {
            "token": token,
            "user": user
        }

    execute_on_conn(process)
    return output


# curl -i http://localhost:8080/api/user/reqs/create \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"type":"service_visit","payload":{"car_brand":"Toyota","car_model":"Camry","date":"2026-01-25","problem":"Something"}}'

@app.post(API_USER_REQS_CREATE, status_code=201)
def api_user_reqs_create(input:dict, claims=Depends(parse_claims)):

    typ = input.get("type")
    pl = input.get("payload")

    if not typ or not pl:
        reply_error(400, "incomplete data")

    output = {}

    def process(cur):
        nonlocal output

        cur.execute(
            """
            INSERT INTO requests (user_id, type, payload)
            VALUES (%s, %s, COALESCE(%s::jsonb, '{}'::jsonb))
            RETURNING jsonb_build_object(
                'id', id::text,
                'user_id', user_id::text,
                'type', type,
                'payload', payload,
                'status', status
            );
            """, (claims["user_id"], typ, json.dumps(pl),),)

        row = cur.fetchone()
        output = row[0]

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
            SELECT jsonb_build_object(
              'items',
              COALESCE(jsonb_agg(
                jsonb_build_object(
                  'id', r.id::text,
                  'user_id', r.user_id::text,
                  'type', r.type,
                  'payload', r.payload,
                  'status', r.status::text,
                  'feedback',
                    CASE
                      WHEN f.id IS NOT NULL THEN
                        jsonb_build_object(
                          'id', f.id::text,
                          'rating', f.rating,
                          'comment', f.comment
                        )
                      ELSE NULL
                    END
                )
                ORDER BY r.id
              ), '[]'::jsonb)
            )
            FROM requests r
            LEFT JOIN feedback f
              ON f.request_id = r.id
             AND f.user_id = %s
            WHERE r.user_id = %s;
            """,
            (claims["user_id"], claims["user_id"]))

        row = cur.fetchone()
        output = row[0]

    execute_on_conn(process)
    return output


# curl -i http://localhost:8080/api/user/reqs/$ITEM_ID/rate \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"rating":5,"comment":"OK!"}'

@app.post(f"{API_USER_REQS}/{{req_id}}/rate", status_code=201)
def api_user_reqs_rate(req_id:str, input:dict, claims=Depends(parse_claims)):

    rating = input.get("rating")
    comment = input.get("comment")

    if not isinstance(rating, int) or rating < 0 or rating > 5:
        reply_error(400, "rating must be 0..5")

    output = {}

    def process(cur):
        nonlocal output

        cur.execute(
            "SELECT 1 FROM requests WHERE id=%s AND user_id=%s",
            (req_id, claims["user_id"],),
        )
        if not cur.fetchone():
            reply_error(403, "forbidden")

        try:
            cur.execute(
                """
                INSERT INTO feedback (request_id, user_id, rating, comment)
                VALUES (%s,%s,%s,%s)
                RETURNING jsonb_build_object(
                    'id', id::text,
                    'request_id', request_id::text,
                    'user_id', user_id::text,
                    'rating', rating,
                    'comment', comment
                )
                """, (req_id, claims["user_id"], rating, comment,),)

            row = cur.fetchone()
            if not row:
                reply_error(403, "forbidden")
            output = row[0]

        except Exception:
            reply_error(400, "db error")

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
            SELECT jsonb_build_object(
              'items',
              COALESCE(jsonb_agg(
                  jsonb_build_object(
                    'id', r.id::text,
                    'user_id', r.user_id::text,
                    'user_login', u.login,
                    'type', r.type,
                    'payload', r.payload,
                    'status', r.status::text
                  )
                  ORDER BY r.id
                ), '[]'::jsonb
              ))
            FROM requests r JOIN users u ON u.id = r.user_id;
        """)

        row = cur.fetchone()
        output = row[0]

    execute_on_conn(process)
    return output


# curl -s http://localhost:8080/api/admin/reqs/$ITEM_ID/status \
#    -H "Authorization: Bearer $TOKEN" \
#    -H "Content-Type: application/json" \
#    -d '{"status":"in_progress"}'

@app.post(f"{API_ADMIN_REQS}/{{req_id}}/status")
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
