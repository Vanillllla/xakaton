import mysql.connector
from mysql.connector import Error
from contextlib import contextmanager

class Database:
    def __init__(self, config):
        self.config = config

    @contextmanager
    def get_connection(self):
        conn = None
        try:
            conn = mysql.connector.connect(**self.config)
            yield conn
        except Error as e:
            print(f"Database error: {e}")
            raise
        finally:
            if conn and conn.is_connected():
                conn.close()

    def create_users_table(self):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id BIGINT UNIQUE NOT NULL,
                    username VARCHAR(255),
                    full_name VARCHAR(255),
                    is_admin BOOLEAN DEFAULT FALSE,
                    registered_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            conn.commit()

    def register_user(self, user_id: int, username: str, full_name: str, is_admin: bool = False):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT IGNORE INTO users (user_id, username, full_name, is_admin)
                VALUES (%s, %s, %s, %s)
            """, (user_id, username, full_name, is_admin))
            conn.commit()

    def is_admin(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT is_admin FROM users WHERE user_id = %s", (user_id,))
            result = cursor.fetchone()
            return result[0] if result else False

    def user_exists(self, user_id: int) -> bool:
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT 1 FROM users WHERE user_id = %s", (user_id,))
            return bool(cursor.fetchone())