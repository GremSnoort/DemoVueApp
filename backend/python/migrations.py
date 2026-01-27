from pathlib import Path

def apply_migrations(pool, migrations_dir: str = "migrations") -> None:
    p = Path(migrations_dir)
    if not p.exists():
        raise RuntimeError(f"migrations dir not found: {migrations_dir}")

    for sql_file in sorted(p.glob("*.sql")):
        sql = sql_file.read_text(encoding="utf-8")
        with pool.connection() as conn:
            with conn.cursor() as cur:
                cur.execute(sql)
            conn.commit()

