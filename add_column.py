import sqlite3

conn = sqlite3.connect("nomes.db")
cursor = conn.cursor()

# Adiciona a coluna 'pesquisas' caso ela não exista
try:
    cursor.execute("ALTER TABLE nomes ADD COLUMN pesquisas INTEGER DEFAULT 0")
    print("Coluna 'pesquisas' adicionada com sucesso!")
except sqlite3.OperationalError:
    print("Coluna 'pesquisas' já existe.")

conn.commit()
conn.close()
