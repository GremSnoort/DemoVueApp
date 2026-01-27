# Quick Start

## Database

Prerequisites:
```bash
sudo apt install postgresql postgresql-contrib
```

Create DB:
```bash
export PGDATA="/tmp/pgdata-demo"
initdb -D "$PGDATA" --encoding=UTF8 --locale=C.UTF-8
```
or
```bash
export PGDATA="/tmp/pgdata-demo"
initdb -D "$PGDATA" --encoding=UTF8 --locale=C
```

Run DB:
```bash
pg_ctl -D "$PGDATA" -l "$PGDATA/server.log" start
```

Check:
```bash
pg_ctl -D "$PGDATA" status
```

Stop:
```bash
pg_ctl -D "$PGDATA" stop
```

Create user and DB:
```
createuser -h localhost -p 5432 app
createdb -h localhost -p 5432 -O app app
```

## Service

Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Install requirements:
```bash
pip install -r requirements.txt
```

Set environment variables:
```
export DB_DSN="postgres://app:app@localhost:5432/app?sslmode=disable"
export JWT_SECRET="change_me_super_secret"
export ADMIN_SEED_PASSWORD="Admin12345!"
```

Run server:
```bash
uvicorn app:app --host 0.0.0.0 --port 8080
```
