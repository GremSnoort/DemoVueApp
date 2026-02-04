Two `.py` files only:

```bash
├── app.py
├── db.py
```

Unified DB schema with customizable point in `type` & `payload`:
```sql
  type          TEXT NOT NULL,
  payload       JSONB NOT NULL DEFAULT '{}'::jsonb,
```

No **FUNCTION**s, plain statements in code.

⚠️❗️Check & rewrite `DB_URL` in `db.py`:
```python
DB_URL = "<PROTO>://<LOGIN>:<PASSWORD>@<HOST_IPV4>:5432/<DBNAME>?sslmode=disable"
```
- `PROTO`: `postgresql`
- `LOGIN`: `postgres`
- `PASSWORD`: ❌ unknown ❌ ask for it before exam
- `HOST_IPV4`: `127.0.0.1`
- `DBNAME`: `postgres`
