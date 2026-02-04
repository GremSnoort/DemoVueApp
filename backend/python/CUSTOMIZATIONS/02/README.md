Two `.py` files only:

```bash
├── app.py
├── db.py
```

One `.sql` file:
```bash
├── init.sql
```

Unified DB schema `init.sql` with customizable point in `type` & `payload`:
```sql
  type          TEXT NOT NULL,
  payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
```

❗️Using PG **FUNCTION**s❗️

⚠️❗️Check & rewrite `DB_URL` in `db.py`:
```python
DB_URL = "<PROTO>://<LOGIN>:<PASSWORD>@<HOST_IPV4>:5432/<DBNAME>?sslmode=disable"
```
- `PROTO`: `postgresql`
- `LOGIN`: `postgres`
- `PASSWORD`: ❌ unknown ❌ ask for it before exam
- `HOST_IPV4`: `127.0.0.1`
- `DBNAME`: `postgres`

# Quick Start

Create virtual environment:

Linux:
```bash
python3 -m venv .venv
```
Windows:
```bash
python -m venv .venv
```
__________________________
Activate `venv`:

Linux:
```bash
source .venv/bin/activate
```

Windows PS:
```powershell
.venv\Scripts\Activate.ps1
```

Windows CMD:
```cmd
.venv\Scripts\Activate.bat
```
__________________________
Install requirements:
```bash
pip install -r requirements.txt
```
__________________________
Run server:
```bash
uvicorn app:app --host 127.0.0.1 --port 8080
```
