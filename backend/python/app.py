import os
import re
import json
from typing import Optional, Any

from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware

from db import pool
from migrations import apply_migrations
from auth import hash_password, check_password, sign_jwt, get_current_user, require_admin

ADMIN_SEED_PASSWORD = os.getenv("ADMIN_SEED_PASSWORD", "Admin12345!")

re_login = re.compile(r"^[A-Za-z0-9]{6,}$")
re_fullname = re.compile(r"^[А-Яа-яЁё ]+$")
re_phone = re.compile(r"^8\(\d{3}\)\d{3}-\d{2}-\d{2}$")
re_email = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

app = FastAPI(title="DemoVueApp Backend (Python)")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def err(code: int, msg: str):
    raise HTTPException(status_code=code, detail={"error": msg})

@app.on_event("startup")
def startup():
    apply_migrations(pool, "migrations")
    seed_admin()

def seed_admin():
    login = "Admin"
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE login=%s", (login,))
            if cur.fetchone():
                return
            pw_hash = hash_password(ADMIN_SEED_PASSWORD)
            cur.execute(
                """
                INSERT INTO users (login, password_hash, full_name, phone, email, role)
                VALUES (%s,%s,%s,%s,%s,%s)
                """,
                (login, pw_hash, "Администратор", "8(000)000-00-00", "admin@example.com", "admin"),
            )
        conn.commit()

@app.get("/api/health")
def health():
    return "ok"

# ---------- AUTH ----------

@app.post("/api/auth/register", status_code=201)
def register(payload: dict):
    login = (payload.get("login") or "").strip()
    password = payload.get("password") or ""
    full_name = (payload.get("full_name") or "").strip()
    phone = (payload.get("phone") or "").strip()
    email = (payload.get("email") or "").strip()

    if not re_login.match(login):
        err(400, "login must be latin letters/digits, min 6")
    if len(password) < 8:
        err(400, "password min length is 8")
    if not re_fullname.match(full_name):
        err(400, "full_name must be cyrillic letters and spaces")
    if not re_phone.match(phone):
        err(400, "phone must match 8(XXX)XXX-XX-XX")
    if not re_email.match(email):
        err(400, "invalid email")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT 1 FROM users WHERE login=%s", (login,))
            if cur.fetchone():
                err(409, "login already exists")

            pw_hash = hash_password(password)
            cur.execute(
                """
                INSERT INTO users (login, password_hash, full_name, phone, email, role)
                VALUES (%s,%s,%s,%s,%s,'user')
                RETURNING id, login, full_name, phone, email, role
                """,
                (login, pw_hash, full_name, phone, email),
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "id": str(row[0]),
        "login": row[1],
        "full_name": row[2],
        "phone": row[3],
        "email": row[4],
        "role": row[5],
    }

@app.post("/api/auth/login")
def login(payload: dict):
    login_ = (payload.get("login") or "").strip()
    password = payload.get("password") or ""
    if not login_ or not password:
        err(400, "login and password required")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, login, password_hash, full_name, role FROM users WHERE login=%s",
                (login_,),
            )
            row = cur.fetchone()

    if not row or not check_password(password, row[2]):
        err(401, "invalid login or password")

    token = sign_jwt(str(row[0]), row[1], row[4])
    return {
        "token": token,
        "user": {"id": str(row[0]), "login": row[1], "full_name": row[3], "role": row[4]},
    }

@app.get("/api/me")
def me(user=Depends(get_current_user)):
    user_id = user["user_id"]
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, login, full_name, phone, email, role FROM users WHERE id=%s",
                (user_id,),
            )
            row = cur.fetchone()
    if not row:
        err(404, "not found")
    return {
        "id": str(row[0]),
        "login": row[1],
        "full_name": row[2],
        "phone": row[3],
        "email": row[4],
        "role": row[5],
    }

# ---------- REQUESTS (USER) ----------

@app.post("/api/requests", status_code=201)
def create_request(payload: dict, user=Depends(get_current_user)):
    typ = (payload.get("type") or "").strip()
    if not typ:
        err(400, "type required")

    pl = payload.get("payload")
    if pl is None:
        pl = {}
    if not isinstance(pl, (dict, list, str, int, float, bool)) and pl is not None:
        err(400, "payload must be json")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO requests (user_id, type, payload)
                VALUES (%s,%s,%s::jsonb)
                RETURNING id, user_id, type, payload, status, admin_comment,
                          created_at::text, updated_at::text
                """,
                (user["user_id"], typ, json.dumps(pl)),
            )
            row = cur.fetchone()
        conn.commit()

    return {
        "id": str(row[0]),
        "user_id": str(row[1]),
        "type": row[2],
        "payload": row[3],
        "status": row[4],
        "admin_comment": row[5],
        "created_at": row[6],
        "updated_at": row[7],
    }

@app.get("/api/requests")
def list_my_requests(user=Depends(get_current_user)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, user_id, type, payload, status, admin_comment,
                       created_at::text, updated_at::text
                FROM requests
                WHERE user_id=%s
                ORDER BY created_at DESC
                """,
                (user["user_id"],),
            )
            rows = cur.fetchall()

    items = [
        {
            "id": str(r[0]),
            "user_id": str(r[1]),
            "type": r[2],
            "payload": r[3],
            "status": r[4],
            "admin_comment": r[5],
            "created_at": r[6],
            "updated_at": r[7],
        }
        for r in rows
    ]
    return {"items": items}

# ---------- FEEDBACK ----------

@app.post("/api/requests/{request_id}/feedback", status_code=201)
def create_feedback(request_id: str, payload: dict, user=Depends(get_current_user)):
    rating = payload.get("rating")
    comment = payload.get("comment")

    if not isinstance(rating, int) or rating < 1 or rating > 5:
        err(400, "rating must be 1..5")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT 1 FROM requests WHERE id=%s AND user_id=%s",
                (request_id, user["user_id"]),
            )
            if not cur.fetchone():
                err(403, "forbidden")

            try:
                cur.execute(
                    """
                    INSERT INTO feedback (request_id, user_id, rating, comment)
                    VALUES (%s,%s,%s,%s)
                    RETURNING id, request_id, user_id, rating, comment, created_at::text
                    """,
                    (request_id, user["user_id"], rating, comment),
                )
                row = cur.fetchone()
            except Exception:
                err(400, "db error (maybe feedback already exists)")
        conn.commit()

    return {
        "id": str(row[0]),
        "request_id": str(row[1]),
        "user_id": str(row[2]),
        "rating": row[3],
        "comment": row[4],
        "created_at": row[5],
    }

# ---------- ADMIN ----------

@app.get("/api/admin/requests")
def admin_list_all(user=Depends(require_admin)):
    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT req.id, req.user_id, u.login, req.type, req.payload, req.status,
                       req.admin_comment, req.created_at::text, req.updated_at::text
                FROM requests req
                JOIN users u ON u.id = req.user_id
                ORDER BY req.created_at DESC
                """
            )
            rows = cur.fetchall()

    items = [
        {
            "id": str(r[0]),
            "user_id": str(r[1]),
            "user_login": r[2],
            "type": r[3],
            "payload": r[4],
            "status": r[5],
            "admin_comment": r[6],
            "created_at": r[7],
            "updated_at": r[8],
        }
        for r in rows
    ]
    return {"items": items}

@app.patch("/api/admin/requests/{request_id}/status")
def admin_update_status(request_id: str, payload: dict, user=Depends(require_admin)):
    status = (payload.get("status") or "").strip()
    admin_comment = payload.get("admin_comment")

    if status not in ("new", "in_progress", "approved", "rejected", "done"):
        err(400, "invalid status")

    with pool.connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "UPDATE requests SET status=%s, admin_comment=%s WHERE id=%s",
                (status, admin_comment, request_id),
            )
        conn.commit()

    return {"ok": True}

