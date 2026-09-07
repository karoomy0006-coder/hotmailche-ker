import sqlite3
import asyncio
from datetime import datetime, timedelta
from typing import Optional, Dict, Any
import config  # <-- أضف هذا السطر


class Database:
    def __init__(self, db_path: str = config.DATABASE_PATH):
        self.db_path = db_path

    def _get_conn(self):
        return sqlite3.connect(self.db_path)

    def _init_sync(self):
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                language TEXT DEFAULT 'en',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        cursor.execute("""
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
        cursor.execute("""
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
        cursor.execute("PRAGMA table_info(sessions)")
        columns = [row[1] for row in cursor.fetchall()]
        if "locked_count" not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN locked_count INTEGER DEFAULT 0")
        if "retry_count" not in columns:
            cursor.execute("ALTER TABLE sessions ADD COLUMN retry_count INTEGER DEFAULT 0")
        conn.commit()
        conn.close()

    async def init(self):
        await asyncio.to_thread(self._init_sync)

    # ─── Users ───
    async def get_or_create_user(self, user_id: int, username: Optional[str] = None) -> Dict[str, Any]:
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            if row:
                conn.close()
                return {"user_id": row[0], "username": row[1], "language": row[2], "created_at": row[3]}
            cursor.execute("INSERT INTO users (user_id, username) VALUES (?, ?)", (user_id, username))
            conn.commit()
            conn.close()
            return {"user_id": user_id, "username": username, "language": "en", "created_at": datetime.utcnow()}
        return await asyncio.to_thread(_sync)

    async def set_language(self, user_id: int, language: str):
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE users SET language = ? WHERE user_id = ?", (language, user_id))
            conn.commit()
            conn.close()
        await asyncio.to_thread(_sync)

    async def get_language(self, user_id: int) -> str:
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT language FROM users WHERE user_id = ?", (user_id,))
            row = cursor.fetchone()
            conn.close()
            return row[0] if row else "en"
        return await asyncio.to_thread(_sync)

    # ─── Subscriptions ───
    async def add_subscription(self, user_id: int, tier: str, duration_days: int, payment_method: str, tx_id: Optional[str] = None):
        expires = datetime.utcnow() + timedelta(days=duration_days)
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO subscriptions (user_id, tier, expires_at, payment_method, tx_id) VALUES (?, ?, ?, ?, ?)",
                (user_id, tier, expires, payment_method, tx_id)
            )
            conn.commit()
            conn.close()
        await asyncio.to_thread(_sync)

    async def get_active_subscription(self, user_id: int) -> Optional[Dict[str, Any]]:
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "SELECT * FROM subscriptions WHERE user_id = ? AND expires_at > ? ORDER BY expires_at DESC LIMIT 1",
                (user_id, datetime.utcnow())
            )
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            return {
                "id": row[0],
                "user_id": row[1],
                "tier": row[2],
                "started_at": row[3],
                "expires_at": row[4],
                "payment_method": row[5],
                "tx_id": row[6]
            }
        return await asyncio.to_thread(_sync)

    # ─── التعديل الأساسي: جعل الأدمن مشتركاً دائماً ───
    async def is_subscribed(self, user_id: int) -> bool:
        # إذا كان المستخدم في قائمة الأدمن، فهو مشترك دائماً
        if user_id in config.ADMIN_IDS:
            return True
        sub = await self.get_active_subscription(user_id)
        return sub is not None

    # ─── Sessions ───
    async def create_session(self, user_id: int, total_emails: int) -> int:
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("INSERT INTO sessions (user_id, total_emails) VALUES (?, ?)", (user_id, total_emails))
            conn.commit()
            session_id = cursor.lastrowid
            conn.close()
            return session_id
        return await asyncio.to_thread(_sync)

    async def update_session_counts(self, session_id: int, valid: int, invalid: int, locked: int, retry: int, timeout_count: int):
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute(
                "UPDATE sessions SET valid_count=?, invalid_count=?, locked_count=?, retry_count=?, timeout_count=? WHERE id=?",
                (valid, invalid, locked, retry, timeout_count, session_id)
            )
            conn.commit()
            conn.close()
        await asyncio.to_thread(_sync)

    async def complete_session(self, session_id: int, result_file: str):
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("UPDATE sessions SET completed_at=?, result_file=? WHERE id=?", (datetime.utcnow(), result_file, session_id))
            conn.commit()
            conn.close()
        await asyncio.to_thread(_sync)

    async def get_latest_session(self, user_id: int) -> Optional[Dict[str, Any]]:
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM sessions WHERE user_id = ? ORDER BY started_at DESC LIMIT 1", (user_id,))
            row = cursor.fetchone()
            conn.close()
            if not row:
                return None
            return {
                "id": row[0],
                "user_id": row[1],
                "total_emails": row[2],
                "valid_count": row[3],
                "invalid_count": row[4],
                "locked_count": row[5] if len(row) > 5 else 0,
                "retry_count": row[6] if len(row) > 6 else 0,
                "timeout_count": row[7] if len(row) > 7 else 0,
                "started_at": row[8] if len(row) > 8 else None,
                "completed_at": row[9] if len(row) > 9 else None,
                "result_file": row[10] if len(row) > 10 else None,
            }
        return await asyncio.to_thread(_sync)

    async def get_stats(self) -> Dict[str, int]:
        def _sync():
            conn = self._get_conn()
            cursor = conn.cursor()
            users = cursor.execute("SELECT COUNT(*) FROM users").fetchone()[0]
            subs = cursor.execute("SELECT COUNT(*) FROM subscriptions").fetchone()[0]
            sessions = cursor.execute("SELECT COUNT(*) FROM sessions").fetchone()[0]
            conn.close()
            return {"users": users, "subscriptions": subs, "sessions": sessions}
        return await asyncio.to_thread(_sync)


db = Database()
