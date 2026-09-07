import aiosqlite
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import config


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    async def _connect(self):
        return await aiosqlite.connect(self.db_path)

    async def init(self):
        async with await self._connect() as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    username TEXT,
                    language TEXT DEFAULT 'en',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS subscriptions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    tier TEXT NOT NULL,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    expires_at TIMESTAMP NOT NULL,
                    payment_method TEXT,
                    tx_id TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            await db.execute("""
                CREATE TABLE IF NOT EXISTS sessions (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    total_emails INTEGER DEFAULT 0,
                    valid_count INTEGER DEFAULT 0,
                    invalid_count INTEGER DEFAULT 0,
                    locked_count INTEGER DEFAULT 0,
                    retry_count INTEGER DEFAULT 0,
                    timeout_count INTEGER DEFAULT 0,
                    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    completed_at TIMESTAMP,
                    result_file TEXT,
                    FOREIGN KEY (user_id) REFERENCES users(user_id)
                )
            """)
            cursor = await db.execute("PRAGMA table_info(sessions)")
            columns = [row[1] for row in await cursor.fetchall()]
            if "locked_count" not in columns:
                await db.execute("ALTER TABLE sessions ADD COLUMN locked_count INTEGER DEFAULT 0")
            if "retry_count" not in columns:
                await db.execute("ALTER TABLE sessions ADD COLUMN retry_count INTEGER DEFAULT 0")
            await db.commit()

    # Users
    async def get_or_create_user(self, user_id: int, username: Optional[str] = None) -> Dict[str, Any]:
        async with await self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                await db.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
                await db.commit()
                return {"user_id": user_id, "username": username, "language": "en"}

    async def set_language(self, user_id: int, language: str):
        async with await self._connect() as db:
            await db.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            await db.commit()

    async def get_language(self, user_id: int) -> str:
        async with await self._connect() as db:
            async with db.execute("SELECT language FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else "en"

    # Subscriptions
    async def add_subscription(self, user_id: int, tier: str, duration_days: int, payment_method: str, tx_id: Optional[str] = None):
        expires = datetime.utcnow() + timedelta(days=duration_days)
        async with await self._connect() as db:
            await db.execute(
                "INSERT INTO subscriptions (user_id, tier, expires_at, payment_method, tx_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, tier, expires, payment_method, tx_id)
            )
            await db.commit()

    async def get_active_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with await self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? AND expires_at > ? ORDER BY expires_at DESC LIMIT 1",
                (user_id, datetime.utcnow())
            ) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def is_subscribed(self, user_id: int) -> bool:
        return await self.get_active_subscription(user_id) is not None

    # Sessions
    async def create_session(self, user_id: int, total_emails: int) -> int:
        async with await self._connect() as db:
            cursor = await db.execute("INSERT INTO sessions (user_id, total_emails) VALUES (?, ?)", (user_id, total_emails))
            await db.commit()
            return cursor.lastrowid

    async def update_session_counts(self, session_id: int, valid: int, invalid: int, locked: int, retry: int, timeout_count: int):
        async with await self._connect() as db:
            await db.execute(
                "UPDATE sessions SET valid_count=?, invalid_count=?, locked_count=?, retry_count=?, timeout_count=? WHERE id=?",
                (valid, invalid, locked, retry, timeout_count, session_id)
            )
            await db.commit()

    async def complete_session(self, session_id: int, result_file: str):
        async with await self._connect() as db:
            await db.execute("UPDATE sessions SET completed_at=?, result_file=? WHERE id=?", (datetime.utcnow(), result_file, session_id))
            await db.commit()

    async def get_latest_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        async with await self._connect() as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT 1", (user_id,)) as cursor:
                row = await cursor.fetchone()
                return dict(row) if row else None

    async def get_stats(self) -> Dict[str, int]:
        async with await self._connect() as db:
            users = (await (await db.execute("SELECT COUNT(*) FROM users")).fetchone())[0]
            subs = (await (await db.execute("SELECT COUNT(*) FROM subscriptions")).fetchone())[0]
            sessions = (await (await db.execute("SELECT COUNT(*) FROM sessions")).fetchone())[0]
            return {"users": users, "subscriptions": subs, "sessions": sessions}


db = Database()
