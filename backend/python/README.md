# Quick Start

## Database

Install prerequisites:
```bash
apt update && apt install postgresql postgresql-contrib sudo python3.12-venv
```

Not all Postgres binaries are located in `/usr/bin`, so check binaries path:
```bash
ls -la /usr/lib/postgresql/16/bin/
```

Use default user `ubuntu`:
```bash
passwd ubuntu
usermod -aG sudo ubuntu
echo "ubuntu ALL=(ALL) NOPASSWD:ALL" > "/etc/sudoers.d/ubuntu"
login ubuntu
```

Update `PATH`:
```bash
export PATH=$PATH:/usr/lib/postgresql/16/bin
```

Check binaries:
```bash
which initdb
which pg_ctl
which psql
which createuser
which createdb
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

```bash
sudo mkdir -p /var/run/postgresql
sudo chown ubuntu:ubuntu /var/run/postgresql
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

Windows `psql`:
```sql
-- 1) создать роль с паролем
CREATE ROLE app WITH LOGIN PASSWORD 'StrongPass123!';

-- 2) создать базу и сделать app владельцем
CREATE DATABASE app OWNER app;

-- 3) (опционально) дать все права на базу
GRANT ALL PRIVILEGES ON DATABASE app TO app;
```

## Service

Create virtual environment:
```bash
python3 -m venv .venv
source .venv/bin/activate
```

Windows:
```bash
python -m venv .venv
./.venv/Scripts/Activate.ps1
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
