from db import get_connection

try:
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT version();")
    version = cursor.fetchone()
    print("🟢 Conectado ao banco de dados com sucesso!")
    print("Versão do PostgreSQL:", version)
except Exception as e:
    print("❌ Falha na conexão:", e)
finally:
    if conn:
        cursor.close()
        conn.close()
