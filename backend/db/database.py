"""
database.py
Manages the asyncpg connection pool for the chess application.
"""

import asyncpg
import os
from typing import Optional

DB_HOST     = os.getenv("DB_HOST",     "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_NAME     = os.getenv("DB_NAME",     "chess_db")
DB_USER     = os.getenv("DB_USER",     "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "postgres")

DB_MIN_CONNECTIONS = int(os.getenv("DB_MIN_CONNECTIONS", "2"))
DB_MAX_CONNECTIONS = int(os.getenv("DB_MAX_CONNECTIONS", "10"))

_pool: Optional[asyncpg.Pool] = None


async def init_pool() -> None:
    global _pool
    _pool = await asyncpg.create_pool(
        host=DB_HOST,
        port=DB_PORT,
        database=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD,
        min_size=DB_MIN_CONNECTIONS,
        max_size=DB_MAX_CONNECTIONS,
    )
    print(f"[DB] Pool created → {DB_USER}@{DB_HOST}:{DB_PORT}/{DB_NAME}")


async def close_pool() -> None:
    global _pool
    if _pool:
        await _pool.close()
        _pool = None
        print("[DB] Pool closed.")


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError(
            "Database pool is not initialised. "
            "Call `await init_pool()` before using the pool."
        )
    return _pool


# async def get_connection() -> asyncpg.Connection:
#     return await get_pool().acquire()