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

    def get_admins_id(self):
        """Получить список ID всех администраторов"""
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT user_id FROM users WHERE is_admin = TRUE")
            admins = cursor.fetchall()
            return [admin[0] for admin in admins] if admins else []

    def get_user_settings(self, user_id: int) -> dict:
        """Получить настройки пользователя (столбцы, начинающиеся на 'set')"""
        with self.get_connection() as conn:
            cursor = conn.cursor(dictionary=True)
            cursor.execute("""
                           SELECT *
                           FROM users
                           WHERE user_id = %s
                           """, (user_id,))
            user_data = cursor.fetchone()

            if not user_data:
                return {}

            # Фильтруем только столбцы, начинающиеся с "set"
            settings = {}
            for key, value in user_data.items():
                if key.startswith('set'):
                    settings[key] = value

            return settings
    def organization_info_reload(self, user_id: int, new_info: str ):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                            UPDATE organizations 
                            SET organization_info_data = %s 
                            WHERE id = (
                                SELECT organization 
                                FROM users
                                WHERE user_id = %s)
                            """,(new_info, user_id))
            conn.commit()

    def add_administrator(self, username: str):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                            UPDATE users
                            SET is_admin = %s 
                            WHERE username = %s
                            """, (True, username))
            conn.commit()
        return True

    def get_organization_info(self, user_id: int):
        with self.get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute("""
                            SELECT organization_info_data, organization_name
                            FROM organizations
                            WHERE id = (
                                SELECT organization
                                FROM users
                                WHERE user_id = %s)""",(user_id,))
            result = cursor.fetchone()
            return result

    def set_user_settings(self, user_id: int, settings: dict):
        try:
            with self.get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("""
                               UPDATE users
                               SET set_org_info   = %s,
                                   set_style_type = %s,
                                   set_size       = %s,
                                   set_tone       = %s
                               WHERE user_id = %s
                               """, (settings['set_org_info'], settings['set_style_type'], settings['set_size'],
                                     settings['set_tone'], user_id))
                conn.commit()
                return cursor.rowcount > 0  # Возвращает True если обновление прошло успешно
        except Exception as e:
            print(f"Ошибка при обновлении настроек пользователя {user_id}: {e}")
            return False