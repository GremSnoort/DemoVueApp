#!/usr/bin/env python3
import json
import os
import re
import time
import hmac
import base64
import hashlib
import secrets
import sqlite3
from http import HTTPStatus
from http.server import ThreadingHTTPServer, BaseHTTPRequestHandler
from urllib.parse import urlparse, parse_qs

# ---------------- Config ----------------
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "app.db")
SCHEMA_PATH = os.path.join(BASE_DIR, "schema.sql")
STATIC_DIR = os.path.join(BASE_DIR, "static")

HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8080"))

ADMIN_LOGIN = os.getenv("ADMIN_LOGIN", "Admin")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD", "Admin12345!")
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL", "admin@example.com")

SESSION_TTL_SEC = 2 * 3600

# Validation
re_login = re.compile(r"^[A-Za-z0-9]{6,}$")
re_fullname = re.compile(r"^[А-Яа-яЁё ]+$")
re_phone = re.compile(r"^8\(\d{3}\)\d{3}-\d{2}-\d{2}$")
re_email = re.compile(r"^[^\s@]+@[^\s@]+\.[^\s@]+$")

# ---------------- DB helpers ----------------
def db_connect():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON;")
    return conn

def db_init():
    with db_connect() as conn:
        sql = open(SCHEMA_PATH, "r", encoding="utf-8").read()
        conn.executescript(sql)
        conn.commit()

def pbkdf2_hash_password(password: str, salt: bytes) -> bytes:
    return hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 200_000, dklen=32)

def create_admin_if_missing():
    salt = secrets.token_bytes(16)
    pw_hash = pbkdf2_hash_password(ADMIN_PASSWORD, salt)
    with db_connect() as conn:
        cur = conn.execute("SELECT 1 FROM users WHERE login = ?", (ADMIN_LOGIN,))
        if cur.fetchone():
            return
        conn.execute(
            """
            INSERT INTO users (login, pw_salt, pw_hash, full_name, phone, email, role)
            VALUES (?, ?, ?, ?, ?, ?, 'admin')
            """,
            (ADMIN_LOGIN, salt, pw_hash, "Администратор", "8(000)000-00-00", ADMIN_EMAIL),
        )
        conn.commit()

def session_create(user_id: int) -> str:
    sid = secrets.token_urlsafe(32)
    expires_at = int(time.time()) + SESSION_TTL_SEC
    with db_connect() as conn:
        conn.execute("INSERT INTO sessions (sid, user_id, expires_at) VALUES (?, ?, ?)", (sid, user_id, expires_at))
        conn.commit()
    return sid

def session_delete(sid: str):
    if not sid:
        return
    with db_connect() as conn:
        conn.execute("DELETE FROM sessions WHERE sid = ?", (sid,))
        conn.commit()

def session_get_user(sid: str):
    if not sid:
        return None
    now = int(time.time())
    with db_connect() as conn:
        row = conn.execute(
            """
            SELECT u.id, u.login, u.full_name, u.phone, u.email, u.role
            FROM sessions s
            JOIN users u ON u.id = s.user_id
            WHERE s.sid = ? AND s.expires_at > ?
            """,
            (sid, now),
        ).fetchone()
    if not row:
        return None
    return dict(row)

# ---------------- HTTP helpers ----------------
def parse_cookies(cookie_header: str) -> dict:
    out = {}
    if not cookie_header:
        return out
    parts = cookie_header.split(";")
    for p in parts:
        if "=" in p:
            k, v = p.strip().split("=", 1)
            out[k] = v
    return out

class App(BaseHTTPRequestHandler):
    server_version = "DemoMin/0.1"

    def log_message(self, fmt, *args):
        # чуть тише
        print("%s - - [%s] %s" % (self.client_address[0], self.log_date_time_string(), fmt % args))

    def send_json(self, code: int, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def send_error_json(self, code: int, msg: str):
        self.send_json(code, {"error": msg})

    def read_json(self):
        length = int(self.headers.get("Content-Length", "0") or "0")
        raw = self.rfile.read(length) if length > 0 else b""
        if not raw:
            return {}
        try:
            return json.loads(raw.decode("utf-8"))
        except Exception:
            self.send_error_json(400, "bad json")
            return None

    def send_file(self, path: str, content_type: str):
        try:
            with open(path, "rb") as f:
                data = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(data)))
            self.end_headers()
            self.wfile.write(data)
        except FileNotFoundError:
            self.send_response(404)
            self.end_headers()

    def get_sid(self):
        cookies = parse_cookies(self.headers.get("Cookie", ""))
        return cookies.get("sid")

    def require_user(self):
        user = session_get_user(self.get_sid())
        if not user:
            self.send_error_json(401, "unauthorized")
            return None
        return user

    def require_admin(self):
        user = self.require_user()
        if not user:
            return None
        if user.get("role") != "admin":
            self.send_error_json(403, "forbidden")
            return None
        return user

    # ---------------- Routing ----------------
    def do_GET(self):
        p = urlparse(self.path)
        path = p.path

        # Static
        if path == "/" or path == "/login":
            return self.send_file(os.path.join(STATIC_DIR, "login.html"), "text/html; charset=utf-8")
        if path == "/register":
            return self.send_file(os.path.join(STATIC_DIR, "register.html"), "text/html; charset=utf-8")
        if path == "/requests":
            return self.send_file(os.path.join(STATIC_DIR, "requests.html"), "text/html; charset=utf-8")
        if path == "/requests/new":
            return self.send_file(os.path.join(STATIC_DIR, "request_new.html"), "text/html; charset=utf-8")
        if path == "/admin":
            return self.send_file(os.path.join(STATIC_DIR, "admin.html"), "text/html; charset=utf-8")
        if path == "/app.css":
            return self.send_file(os.path.join(STATIC_DIR, "app.css"), "text/css; charset=utf-8")

        # API
        if path == "/api/health":
            return self.send_json(200, {"ok": True})

        if path == "/api/me":
            user = self.require_user()
            if not user:
                return
            return self.send_json(200, {"user": user})

        if path == "/api/requests":
            user = self.require_user()
            if not user:
                return
            with db_connect() as conn:
                rows = conn.execute(
                    """
                    SELECT id, user_id, type, payload_json, status, admin_comment, created_at, updated_at
                    FROM requests
                    WHERE user_id = ?
                    ORDER BY created_at DESC
                    """,
                    (user["id"],),
                ).fetchall()
            items = []
            for r in rows:
                items.append({
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "type": r["type"],
                    "payload": json.loads(r["payload_json"] or "{}"),
                    "status": r["status"],
                    "admin_comment": r["admin_comment"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                })
            return self.send_json(200, {"items": items})

        if path == "/api/admin/requests":
            _ = self.require_admin()
            if not _:
                return
            with db_connect() as conn:
                rows = conn.execute(
                    """
                    SELECT r.id, r.user_id, u.login AS user_login, r.type, r.payload_json, r.status, r.admin_comment,
                           r.created_at, r.updated_at
                    FROM requests r
                    JOIN users u ON u.id = r.user_id
                    ORDER BY r.created_at DESC
                    """
                ).fetchall()
            items = []
            for r in rows:
                items.append({
                    "id": r["id"],
                    "user_id": r["user_id"],
                    "user_login": r["user_login"],
                    "type": r["type"],
                    "payload": json.loads(r["payload_json"] or "{}"),
                    "status": r["status"],
                    "admin_comment": r["admin_comment"],
                    "created_at": r["created_at"],
                    "updated_at": r["updated_at"],
                })
            return self.send_json(200, {"items": items})

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        p = urlparse(self.path)
        path = p.path

        if path == "/api/auth/register":
            body = self.read_json()
            if body is None:
                return

            login = (body.get("login") or "").strip()
            password = body.get("password") or ""
            full_name = (body.get("full_name") or "").strip()
            phone = (body.get("phone") or "").strip()
            email = (body.get("email") or "").strip()

            if not re_login.match(login):
                return self.send_error_json(400, "login must be latin letters/digits, min 6")
            if len(password) < 8:
                return self.send_error_json(400, "password min length is 8")
            if not re_fullname.match(full_name):
                return self.send_error_json(400, "full_name must be cyrillic letters and spaces")
            if not re_phone.match(phone):
                return self.send_error_json(400, "phone must match 8(XXX)XXX-XX-XX")
            if not re_email.match(email):
                return self.send_error_json(400, "invalid email")

            salt = secrets.token_bytes(16)
            pw_hash = pbkdf2_hash_password(password, salt)

            try:
                with db_connect() as conn:
                    conn.execute(
                        """
                        INSERT INTO users (login, pw_salt, pw_hash, full_name, phone, email, role)
                        VALUES (?, ?, ?, ?, ?, ?, 'user')
                        """,
                        (login, salt, pw_hash, full_name, phone, email),
                    )
                    conn.commit()
            except sqlite3.IntegrityError:
                return self.send_error_json(409, "login already exists")

            return self.send_json(201, {"ok": True})

        if path == "/api/auth/login":
            body = self.read_json()
            if body is None:
                return
            login = (body.get("login") or "").strip()
            password = body.get("password") or ""
            if not login or not password:
                return self.send_error_json(400, "login and password required")

            with db_connect() as conn:
                row = conn.execute(
                    "SELECT id, login, pw_salt, pw_hash, full_name, phone, email, role FROM users WHERE login = ?",
                    (login,),
                ).fetchone()

            if not row:
                return self.send_error_json(401, "invalid login or password")

            calc = pbkdf2_hash_password(password, row["pw_salt"])
            if not hmac.compare_digest(calc, row["pw_hash"]):
                return self.send_error_json(401, "invalid login or password")

            sid = session_create(int(row["id"]))

            user = {
                "id": row["id"],
                "login": row["login"],
                "full_name": row["full_name"],
                "phone": row["phone"],
                "email": row["email"],
                "role": row["role"],
            }

            payload = json.dumps({"user": user}, ensure_ascii=False).encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.send_header("Set-Cookie", f"sid={sid}; HttpOnly; Path=/; SameSite=Lax")
            self.send_header("Content-Length", str(len(payload)))
            self.end_headers()
            self.wfile.write(payload)
            return

        if path == "/api/auth/logout":
            sid = self.get_sid()
            session_delete(sid)
            self.send_response(200)
            self.send_header("Set-Cookie", "sid=; Max-Age=0; Path=/; SameSite=Lax")
            self.send_header("Content-Type", "application/json; charset=utf-8")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')
            return

        if path == "/api/requests":
            user = self.require_user()
            if not user:
                return

            body = self.read_json()
            if body is None:
                return
            typ = (body.get("type") or "").strip()
            payload = body.get("payload")
            if not typ:
                return self.send_error_json(400, "type required")

            # payload должен быть JSON-совместимым (здесь просто сериализуем)
            try:
                payload_json = json.dumps(payload if payload is not None else {}, ensure_ascii=False)
            except Exception:
                return self.send_error_json(400, "payload must be json")

            with db_connect() as conn:
                cur = conn.execute(
                    """
                    INSERT INTO requests (user_id, type, payload_json, status)
                    VALUES (?, ?, ?, 'new')
                    """,
                    (user["id"], typ, payload_json),
                )
                req_id = cur.lastrowid
                conn.commit()

            return self.send_json(201, {"id": req_id, "status": "new"})

        # feedback: /api/requests/<id>/feedback
        if path.startswith("/api/requests/") and path.endswith("/feedback"):
            user = self.require_user()
            if not user:
                return
            parts = path.split("/")
            if len(parts) != 5:
                return self.send_response(404)
            req_id = parts[3]

            body = self.read_json()
            if body is None:
                return
            rating = body.get("rating")
            comment = body.get("comment")

            if not isinstance(rating, int) or rating < 1 or rating > 5:
                return self.send_error_json(400, "rating must be 1..5")

            with db_connect() as conn:
                own = conn.execute(
                    "SELECT 1 FROM requests WHERE id = ? AND user_id = ?",
                    (req_id, user["id"]),
                ).fetchone()
                if not own:
                    return self.send_error_json(403, "forbidden")
                try:
                    conn.execute(
                        """
                        INSERT INTO feedback (request_id, user_id, rating, comment)
                        VALUES (?, ?, ?, ?)
                        """,
                        (req_id, user["id"], rating, comment),
                    )
                    conn.commit()
                except sqlite3.IntegrityError:
                    return self.send_error_json(400, "feedback already exists")

            return self.send_json(201, {"ok": True})

        # admin status: /api/admin/requests/<id>/status
        if path.startswith("/api/admin/requests/") and path.endswith("/status"):
            _ = self.require_admin()
            if not _:
                return
            parts = path.split("/")
            if len(parts) != 6:
                return self.send_response(404)
            req_id = parts[4]

            body = self.read_json()
            if body is None:
                return
            status = (body.get("status") or "").strip()
            admin_comment = body.get("admin_comment")

            if status not in ("new", "in_progress", "approved", "rejected", "done"):
                return self.send_error_json(400, "invalid status")

            with db_connect() as conn:
                cur = conn.execute(
                    "UPDATE requests SET status = ?, admin_comment = ? WHERE id = ?",
                    (status, admin_comment, req_id),
                )
                conn.commit()
                if cur.rowcount == 0:
                    return self.send_error_json(404, "not found")

            return self.send_json(200, {"ok": True})

        self.send_response(404)
        self.end_headers()

# ---------------- main ----------------
if __name__ == "__main__":
    db_init()
    create_admin_if_missing()

    print(f"Admin: login={ADMIN_LOGIN} password={ADMIN_PASSWORD}")
    print(f"Open: http://{HOST}:{PORT}/login")

    httpd = ThreadingHTTPServer((HOST, PORT), App)
    httpd.serve_forever()
