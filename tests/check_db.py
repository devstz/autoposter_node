import os
import psycopg2

db_url = os.getenv("DATABASE_URL")

print("Проверяем подключение к базе...")

try:
    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT 1;")
    print("✅ Подключение к БД успешно!")
except Exception as e:
    print(f"❌ Ошибка подключения к БД: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
