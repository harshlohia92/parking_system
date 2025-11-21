import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path="parking.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.conn.row_factory = sqlite3.Row
        self.create_tables()

    def create_tables(self):

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS parking (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            plate TEXT,
            vehicle_type TEXT,
            slot TEXT,
            entry_time TEXT,
            exit_time TEXT,
            duration_minutes INTEGER,
            amount INTEGER,
            status TEXT
        );
        """)


        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS parking_slots(
            slot_id TEXT PRIMARY KEY,
            slot_type TEXT,
            is_occupied INTEGER DEFAULT 0,
            vehicle_number TEXT,
            entry_time TEXT
        );
        """)
        self.conn.commit()
        self._ensure_default_slots()

    def _ensure_default_slots(self):
        cur = self.conn.execute("SELECT COUNT(*) FROM parking_slots")
        count = cur.fetchone()[0]

        if count == 0:

            slot_config = {
                "small": 20,
                "medium": 40,
                "large": 30,
                "xl": 10
            }
            for slot_type, qty in slot_config.items():
                for i in range(1, qty + 1):
                    slot_id = f"{slot_type.upper()}-{i}"
                    self.conn.execute("""
                        INSERT INTO parking_slots (slot_id, slot_type)
                        VALUES (?, ?)
                    """, (slot_id, slot_type))
            self.conn.commit()
            print("Default parking slots created.")


    def insert_entry(self, plate, vehicle_type, slot):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute("""
            INSERT INTO parking (plate, vehicle_type, slot, entry_time, status)
            VALUES (?, ?, ?, ?, 'IN')
        """, (plate, vehicle_type, slot, now))
        self.conn.commit()

    def close_parking(self, plate, duration_minutes, amount):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.conn.execute("""
            UPDATE parking
            SET exit_time=?, duration_minutes=?, amount=?, status='OUT'
            WHERE plate=? AND status='IN'
        """, (now, duration_minutes, amount, plate))
        self.conn.commit()

    def get_active_entry(self, plate):
        cur = self.conn.execute("""
            SELECT id, entry_time, vehicle_type, slot
            FROM parking
            WHERE plate=? AND status='IN'
            ORDER BY id DESC
            LIMIT 1
        """, (plate,))
        row = cur.fetchone()
        return row if row else None

    def list_all(self):
        cur = self.conn.execute("SELECT * FROM parking ORDER BY id DESC")
        return [dict(r) for r in cur.fetchall()]

    def search(self, plate_query):
        cur = self.conn.execute("SELECT * FROM parking WHERE plate LIKE ? ORDER BY id DESC",
                                (f"%{plate_query}%",))
        return [dict(r) for r in cur.fetchall()]


    def find_and_reserve_slot(self, slot_type, plate_number):
        """
        Atomically reserve a free slot of slot_type.
        Returns slot_id or None.
        """
        cur = self.conn.execute("""
            SELECT slot_id FROM parking_slots
            WHERE slot_type=? AND is_occupied=0
            LIMIT 1
        """, (slot_type,))
        row = cur.fetchone()
        if not row:
            return None

        slot_id = row["slot_id"]
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        update = self.conn.execute("""
            UPDATE parking_slots
            SET is_occupied=1, vehicle_number=?, entry_time=?
            WHERE slot_id=? AND is_occupied=0
        """, (plate_number, now, slot_id))
        self.conn.commit()

        return slot_id if update.rowcount == 1 else None

    def reserve_any_slot(self, plate_number):

        for t in ("medium", "large", "xl", "small"):
            s = self.find_and_reserve_slot(t, plate_number)
            if s:
                return s
        return None

    def release_slot_by_id(self, slot_id):
        self.conn.execute("""
            UPDATE parking_slots
            SET is_occupied=0, vehicle_number=NULL, entry_time=NULL
            WHERE slot_id=?
        """, (slot_id,))
        self.conn.commit()

    def release_slot_by_plate(self, plate_number):
        cur = self.conn.execute("SELECT slot_id FROM parking_slots WHERE vehicle_number=?", (plate_number,))
        row = cur.fetchone()
        if not row:
            return None
        slot_id = row["slot_id"]
        self.release_slot_by_id(slot_id)
        return slot_id

    def get_slot_status(self):
        cur = self.conn.execute("SELECT * FROM parking_slots ORDER BY slot_type, slot_id")
        return [dict(r) for r in cur.fetchall()]
