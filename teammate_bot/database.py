# database.py
import sqlite3
import json

class Database:
    def __init__(self, db_name='teammates.db'):
        self.conn = sqlite3.connect(db_name, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.create_tables()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS profiles (
                user_id INTEGER PRIMARY KEY,
                nickname TEXT,
                age INTEGER,
                gender TEXT,
                steam_url TEXT,
                steamid64 TEXT,
                csstats_url TEXT,
                main_games TEXT,
                about TEXT,
                telegram_username TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS likes (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                from_user_id INTEGER NOT NULL,
                to_user_id INTEGER NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                UNIQUE(from_user_id, to_user_id)
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user1_id INTEGER NOT NULL,
                user2_id INTEGER NOT NULL,
                matched_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                status TEXT DEFAULT 'active',
                UNIQUE(user1_id, user2_id)
            )
        ''')
        self.conn.commit()

    def save_profile(self, user_id, telegram_username=None, **data):
        if telegram_username is not None:
            data['telegram_username'] = telegram_username

        self.cursor.execute("SELECT 1 FROM profiles WHERE user_id = ?", (user_id,))
        exists = self.cursor.fetchone()
        if exists:
            fields = []
            values = []
            for key, value in data.items():
                if value is not None:
                    fields.append(f"{key} = ?")
                    values.append(value)
            if fields:
                values.append(user_id)
                query = f"UPDATE profiles SET {', '.join(fields)}, updated_at = CURRENT_TIMESTAMP WHERE user_id = ?"
                self.cursor.execute(query, values)
        else:
            fields = ['user_id'] + list(data.keys())
            placeholders = ['?'] * len(fields)
            values = [user_id] + list(data.values())
            query = f"INSERT INTO profiles ({', '.join(fields)}) VALUES ({', '.join(placeholders)})"
            self.cursor.execute(query, values)
        self.conn.commit()

    def get_profile(self, user_id):
        self.cursor.execute("SELECT * FROM profiles WHERE user_id = ?", (user_id,))
        row = self.cursor.fetchone()
        if not row:
            return None
        columns = [col[0] for col in self.cursor.description]
        return dict(zip(columns, row))

    def delete_user_data(self, user_id):
        try:
            self.cursor.execute("DELETE FROM profiles WHERE user_id = ?", (user_id,))
            self.cursor.execute("DELETE FROM likes WHERE from_user_id = ? OR to_user_id = ?", (user_id, user_id))
            self.cursor.execute("DELETE FROM matches WHERE user1_id = ? OR user2_id = ?", (user_id, user_id))
            self.conn.commit()
            return True
        except Exception as e:
            print(f"Ошибка при удалении: {e}")
            return False

    def get_all_profiles_except(self, user_id, exclude_ids=None):
        query = "SELECT * FROM profiles WHERE user_id != ?"
        params = [user_id]
        if exclude_ids:
            placeholders = ','.join('?' * len(exclude_ids))
            query += f" AND user_id NOT IN ({placeholders})"
            params.extend(exclude_ids)
        self.cursor.execute(query, params)
        rows = self.cursor.fetchall()
        columns = [col[0] for col in self.cursor.description]
        return [dict(zip(columns, row)) for row in rows]

    def get_matches_for_user(self, user_id):
        self.cursor.execute("""
            SELECT 
                CASE WHEN user1_id = ? THEN user2_id ELSE user1_id END as teammate_id,
                matched_at
            FROM matches
            WHERE (user1_id = ? OR user2_id = ?) AND status = 'active'
        """, (user_id, user_id, user_id))
        return self.cursor.fetchall()

    def add_like(self, from_id, to_id):
        try:
            self.cursor.execute("INSERT INTO likes (from_user_id, to_user_id) VALUES (?, ?)", (from_id, to_id))
            self.conn.commit()
            return True
        except sqlite3.IntegrityError:
            return False

    def is_mutual_like(self, user1, user2):
        self.cursor.execute("SELECT 1 FROM likes WHERE from_user_id = ? AND to_user_id = ?", (user2, user1))
        return self.cursor.fetchone() is not None

    def create_match(self, user1, user2):
        self.cursor.execute("SELECT 1 FROM matches WHERE (user1_id = ? AND user2_id = ?) OR (user1_id = ? AND user2_id = ?)",
                            (user1, user2, user2, user1))
        if not self.cursor.fetchone():
            self.cursor.execute("INSERT INTO matches (user1_id, user2_id) VALUES (?, ?)", (user1, user2))
            self.conn.commit()