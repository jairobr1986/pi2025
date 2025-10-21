import os
import sqlite3

# Caminho absoluto do banco (garante que não será criado em outro lugar)
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATABASE = os.path.join(BASE_DIR, "nomes.db")

def get_connection():
    """Retorna uma conexão com o banco de dados SQLite."""
    conn = sqlite3.connect(DATABASE, timeout=10)
    conn.row_factory = sqlite3.Row  # permite acessar colunas pelo nome (row["nome"])
    return conn

def init_db():
    """Cria a tabela 'nomes' se não existir."""
    conn = get_connection()
    cursor = conn.cursor()

    # Melhora desempenho para múltiplos acessos
    cursor.execute("PRAGMA journal_mode=WAL;")

    # Cria tabela
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS nomes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT NOT NULL,
            significado TEXT,
            origem TEXT,
            motivo_escolha TEXT,
            pesquisas INTEGER DEFAULT 0
        )
    """)

    # Índices aceleram buscas por nome e origem
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_nome ON nomes(nome)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_origem ON nomes(origem)")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Banco de dados usado:", DATABASE)
    init_db()
    print("Tabela verificada/criada com sucesso!")
