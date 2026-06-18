import os
import time
from typing import Any

import psycopg
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware


DATABASE_URL = os.environ.get("DATABASE_URL", "")


def db_exec(sql: str, params: tuple[Any, ...] = ()) -> list[tuple[Any, ...]]:
    with psycopg.connect(DATABASE_URL, autocommit=True) as conn:
        with conn.cursor() as cur:
            cur.execute(sql, params)
            if cur.description is None:
                return []
            return list(cur.fetchall())


def wait_for_db(max_seconds: int = 60) -> None:
    start = time.time()
    while True:
        try:
            db_exec("SELECT 1;")
            return
        except Exception:
            if time.time() - start > max_seconds:
                raise
            time.sleep(1)


app = FastAPI(title="demo1-backend")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def startup() -> None:
    if not DATABASE_URL:
        raise RuntimeError("DATABASE_URL is required")
    wait_for_db()
    db_exec(
        """
        CREATE TABLE IF NOT EXISTS todos (
            id SERIAL PRIMARY KEY,
            title TEXT NOT NULL,
            done BOOLEAN NOT NULL DEFAULT FALSE
        );
        """
    )


@app.get("/api/health")
def health() -> dict[str, Any]:
    return {"ok": True}


@app.get("/api/todos")
def list_todos() -> dict[str, Any]:
    rows = db_exec("SELECT id, title, done FROM todos ORDER BY id DESC LIMIT 50;")
    return {
        "items": [{"id": r[0], "title": r[1], "done": r[2]} for r in rows],
    }


@app.post("/api/todos")
def create_todo(payload: dict[str, Any]) -> dict[str, Any]:
    title = (payload.get("title") or "").strip()
    if not title:
        return {"error": "title is required"}
    row = db_exec(
        "INSERT INTO todos (title, done) VALUES (%s, %s) RETURNING id, title, done;",
        (title, False),
    )[0]
    return {"item": {"id": row[0], "title": row[1], "done": row[2]}}


@app.post("/api/todos/{todo_id}/toggle")
def toggle(todo_id: int) -> dict[str, Any]:
    rows = db_exec(
        "UPDATE todos SET done = NOT done WHERE id = %s RETURNING id, title, done;",
        (todo_id,),
    )
    if not rows:
        return {"error": "not found"}
    row = rows[0]
    return {"item": {"id": row[0], "title": row[1], "done": row[2]}}

