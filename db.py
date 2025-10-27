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

def clear_db():
    """Deleta todos os dados da tabela 'nomes' e reinicia o contador SERIAL ID."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("🗑️ TRUNCATE: Apagando todos os dados da tabela 'nomes' e reiniciando IDs...")
        # TRUNCATE... RESTART IDENTITY garante que o ID volte a contar de 1.
        cursor.execute("TRUNCATE TABLE nomes RESTART IDENTITY CASCADE;") 
        conn.commit()
        print("✅ TRUNCATE concluído com sucesso.")
    except Exception as e:
        print(f"❌ Erro ao limpar o banco: {e}")
        if conn:
            conn.rollback()
        raise 
    finally:
        if conn:
            cursor.close()
            connection_pool.putconn(conn)

def init_db():
    """Cria tabela 'nomes' se não existir e garante a restrição UNIQUE."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        
        # 1. Cria a tabela (sem o UNIQUE inicialmente para evitar conflito se já existir)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS nomes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                significado TEXT,
                origem VARCHAR(100),
                motivo_escolha TEXT,
                pesquisas INTEGER DEFAULT 0
            );
        """)
        
        # 2. Tenta adicionar a restrição UNIQUE, ignorando o erro se ela já existir.
        # Isso garante que a restrição seja aplicada, mesmo se a tabela já existia.
        try:
            cursor.execute("""
                ALTER TABLE nomes 
                ADD CONSTRAINT nomes_nome_unique 
                UNIQUE (nome);
            """)
            print("✅ Restrição UNIQUE na coluna 'nome' aplicada.")
        except Exception:
             # Se der erro aqui (porque a restrição já existe), precisamos reverter a transação no banco.
            conn.rollback() # <<<<<< CORREÇÃO APLICADA AQUI
            pass
        
        # 3. Cria índices (opcional, mas bom para performance)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_nome ON nomes(nome);
            CREATE INDEX IF NOT EXISTS idx_origem ON nomes(origem);
        """)
        
        conn.commit()
        print("✅ Tabela 'nomes' verificada/ajustada com sucesso no PostgreSQL.")
    except Exception as e:
        print(f"❌ Erro ao inicializar o banco: {e}")
        # Re-raise para o app.py capturar e encerrar se o banco falhar
        raise 
    finally:
        if conn:
            cursor.close()
            connection_pool.putconn(conn)
