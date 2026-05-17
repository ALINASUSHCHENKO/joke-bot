import aiosqlite

class DatabaseManager:
    def __init__(self, db_path="bot_data.db"):
        self.db_path = db_path

    async def init_db(self):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    name TEXT,
                    phone TEXT,
                    activity TEXT
                )
            """)
            await db.commit()

    async def save_user(self, user_id, name, phone, activity):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR REPLACE INTO users (user_id, name, phone, activity) VALUES (?, ?, ?, ?)",
                (user_id, name, phone, activity)
            )
            await db.commit()

    async def get_user(self, user_id):
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM users WHERE user_id = ?", (user_id,)) as cursor:
                return await cursor.fetchone()

db_manager = DatabaseManager()
