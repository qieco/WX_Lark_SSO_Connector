import aiosqlite
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "endpoints.db")

CREATE_TABLE_SQL = """
CREATE TABLE IF NOT EXISTS endpoints (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    route_name TEXT NOT NULL UNIQUE,
    instance_id TEXT NOT NULL,
    app_id TEXT NOT NULL,
    description TEXT DEFAULT '',
    created_at TEXT DEFAULT (datetime('now')),
    updated_at TEXT DEFAULT (datetime('now'))
);
"""

CREATE_SETTINGS_SQL = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL DEFAULT '',
    description TEXT DEFAULT ''
);
"""

DEFAULT_SETTINGS = [
    ("wenxue_base_url", "https://wenxue.example.com", "问学平台基础地址"),
]


async def init_db():
    """Create tables and seed defaults."""
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(CREATE_TABLE_SQL)
        await db.execute(CREATE_SETTINGS_SQL)
        # Seed default settings if missing
        for key, value, desc in DEFAULT_SETTINGS:
            await db.execute(
                "INSERT OR IGNORE INTO settings (key, value, description) VALUES (?, ?, ?)",
                (key, value, desc),
            )
        await db.commit()


async def get_db():
    """Return an aiosqlite connection. Use as: async with get_db() as db:"""
    db = await aiosqlite.connect(DB_PATH)
    db.row_factory = aiosqlite.Row
    try:
        yield db
    finally:
        await db.close()

