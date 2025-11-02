import os
import socket
import psycopg2

db_url = os.getenv("DATABASE_URL")

print("Проверяем, не дублируется ли IP сервера в таблице bots...")

try:
    hostname = socket.gethostname()
    server_ip = socket.gethostbyname(hostname)

    conn = psycopg2.connect(db_url)
    cur = conn.cursor()
    cur.execute("SELECT server_ip FROM bots;")
    ips = [row[0] for row in cur.fetchall() if row[0]]

    if server_ip in ips:
        print(f"⚠️ IP {server_ip} уже зарегистрирован в таблице bots!")
    else:
        print(f"✅ IP {server_ip} не найден в списке — всё ок.")
except Exception as e:
    print(f"❌ Ошибка проверки IP: {e}")
finally:
    if 'cur' in locals():
        cur.close()
    if 'conn' in locals():
        conn.close()
