import os
from psycopg2 import pool
from dotenv import load_dotenv

# Carregar variáveis do .env
load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    raise Exception("❌ Faltando a variável DATABASE_URL no .env!")

connection_pool = None

def get_connection():
    """Obtém uma conexão do pool."""
    global connection_pool
    if connection_pool is None:
        print("🔄 Inicializando pool de conexões PostgreSQL (Supabase/Render)...")
        connection_pool = pool.ThreadedConnectionPool(
            minconn=1,
            maxconn=5,  # Mantém uso leve
            dsn=DATABASE_URL,
            sslmode='require' # Necessário para Supabase/Render
        )
    return connection_pool.getconn()

def init_db():
    """Cria tabela 'nomes' se não existir."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nomes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                significado TEXT,
                origem VARCHAR(100),
                motivo_escolha TEXT,
                pesquisas INTEGER DEFAULT 0
            );
            
            -- Cria índices (opcional, mas bom para performance)
            CREATE INDEX IF NOT EXISTS idx_nome ON nomes(nome);
            CREATE INDEX IF NOT EXISTS idx_origem ON nomes(origem);
        """)
        conn.commit()
        print("✅ Tabela 'nomes' verificada/criada com sucesso no PostgreSQL.")
    except Exception as e:
        print(f"❌ Erro ao inicializar o banco: {e}")
        # Re-raise para o app.py capturar e encerrar se o banco falhar
        raise 
    finally:
        if conn:
            cursor.close()
            connection_pool.putconn(conn)
