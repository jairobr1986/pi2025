import psycopg2
from psycopg2 import pool
import os
from dotenv import load_dotenv  # Para suportar .env localmente

# Carrega variáveis de ambiente do arquivo .env (local)
load_dotenv()

# Use variáveis de ambiente, com fallback para valores locais (apenas para teste)
DB_HOST = os.environ.get('DB_HOST', 'db.cgrxdexfgqnyguteaobu.supabase.co')
DB_PORT = os.environ.get('DB_PORT', '5432')
DB_NAME = os.environ.get('DB_NAME', 'postgres')
DB_USER = os.environ.get('DB_USER', 'postgres')
DB_PASSWORD = os.environ.get('DB_PASSWORD', 'projeto_integrador_2025_banco_de_dados')  # Fallback local

# Adiciona debug para verificar as variáveis
print(f"DB_HOST: {DB_HOST}, DB_PASSWORD: {DB_PASSWORD[:4]}... (fallback usado)")  # Mostra só os primeiros 4 chars por segurança

# Pool de conexões para serverless
connection_pool = None

def get_connection():
    """Retorna uma conexão do pool ou inicializa o pool se necessário."""
    global connection_pool
    if connection_pool is None:
        try:
            connection_pool = psycopg2.pool.ThreadedConnectionPool(
                1,  # Min connections
                20, # Max connections
                host=DB_HOST,
                port=DB_PORT,
                database=DB_NAME,
                user=DB_USER,
                password=DB_PASSWORD
            )
        except psycopg2.Error as e:
            print(f"Erro ao inicializar o pool de conexões: {e}")
            raise
    return connection_pool.getconn()

def init_db():
    """Inicializa o banco de dados, criando a tabela 'nomes' se ela não existir."""
    conn = None
    try:
        conn = get_connection()
        cursor = conn.cursor()
        create_table_query = """
            CREATE TABLE IF NOT EXISTS nomes (
                id SERIAL PRIMARY KEY,
                nome VARCHAR(255) NOT NULL,
                significado TEXT,
                origem VARCHAR(100),
                motivo_escolha TEXT,
                pesquisas INTEGER DEFAULT 0
            );
        """
        cursor.execute(create_table_query)
        conn.commit()
        print("Tabela 'nomes' verificada/criada no PostgreSQL na nuvem com sucesso.")
    except psycopg2.Error as e:
        print(f"Erro durante a inicialização do DB: {e}")
        raise
    finally:
        if conn:
            cursor.close()
            connection_pool.putconn(conn)  # Retorna ao pool

if __name__ == '__main__':
    init_db()