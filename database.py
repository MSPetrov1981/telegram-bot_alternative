import os
from datetime import date, datetime, time, timedelta

import aiosqlite


class Database:
    def __init__(self):
        self.conn = None
        self.db_path = os.path.join(os.path.dirname(__file__), "clinic_bot.db")

    async def init(self):
        self.conn = await aiosqlite.connect(self.db_path)
        await self._create_tables()

    async def _create_tables(self):
        await self.conn.execute("""
            CREATE TABLE IF NOT EXISTS appointments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                appointment_type TEXT NOT NULL,
                appointment_id TEXT NOT NULL,
                appointment_date DATE NOT NULL,
                appointment_time TIME NOT NULL,
                full_name TEXT NOT NULL,
                phone TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)
        await self.conn.commit()
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_date_time ON appointments (appointment_date, appointment_time)")
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_user_date ON appointments (user_id, appointment_date)")
        await self.conn.execute("CREATE INDEX IF NOT EXISTS idx_appointments_type_id_date_time ON appointments (appointment_type, appointment_id, appointment_date, appointment_time)")

    async def is_time_available(self, appointment_date: date, appointment_time: time,
                                appointment_type: str | None = None, appointment_id: str | None = None) -> bool:
        if appointment_type and appointment_id:
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND appointment_time = ? AND appointment_type = ? AND appointment_id = ?",
                (appointment_date.isoformat(), appointment_time.strftime("%H:%M:%S"), appointment_type, appointment_id)
            )
        else:
            cursor = await self.conn.execute(
                "SELECT COUNT(*) FROM appointments WHERE appointment_date = ? AND appointment_time = ?",
                (appointment_date.isoformat(), appointment_time.strftime("%H:%M:%S"))
            )
        count = (await cursor.fetchone())[0]
        return count == 0

    async def save_appointment(self, user_id: int, appointment_type: str, appointment_id: str,
                               appointment_date: date, appointment_time: time,
                               full_name: str, phone: str) -> int:
        cursor = await self.conn.execute(
            "INSERT INTO appointments (user_id, appointment_type, appointment_id, appointment_date, appointment_time, full_name, phone) VALUES (?, ?, ?, ?, ?, ?, ?)",
            (user_id, appointment_type, appointment_id, appointment_date.isoformat(), appointment_time.strftime("%H:%M:%S"), full_name, phone)
        )
        await self.conn.commit()
        return cursor.lastrowid

    async def get_tomorrow_appointments(self) -> list[tuple[int, str, str, date, time, str]]:
        tomorrow = (datetime.now() + timedelta(days=1)).date().isoformat()
        cursor = await self.conn.execute(
            "SELECT user_id, appointment_type, appointment_id, appointment_date, appointment_time, full_name FROM appointments WHERE appointment_date = ?",
            (tomorrow,)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            app_date = datetime.fromisoformat(row[3]).date()
            app_time = datetime.strptime(row[4], "%H:%M:%S").time()
            result.append((row[0], row[1], row[2], app_date, app_time, row[5]))
        return result

    async def get_user_appointments(self, user_id: int) -> list[tuple[int, str, str, date, time]]:
        today = datetime.now().date().isoformat()
        cursor = await self.conn.execute(
            "SELECT id, appointment_type, appointment_id, appointment_date, appointment_time FROM appointments WHERE user_id = ? AND appointment_date >= ? ORDER BY appointment_date, appointment_time",
            (user_id, today)
        )
        rows = await cursor.fetchall()
        result = []
        for row in rows:
            app_date = datetime.fromisoformat(row[3]).date()
            app_time = datetime.strptime(row[4], "%H:%M:%S").time()
            result.append((row[0], row[1], row[2], app_date, app_time))
        return result

    async def delete_appointment(self, appointment_id: int) -> bool:
        cursor = await self.conn.execute("DELETE FROM appointments WHERE id = ?", (appointment_id,))
        await self.conn.commit()
        return cursor.rowcount > 0

    async def close(self):
        if self.conn:
            await self.conn.close()


db = Database()
