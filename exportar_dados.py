import sqlite3
import pandas as pd
import os

# Nome do seu banco de dados SQLite local.
# O arquivo 'nomes.db' está na pasta D:\...\projeto_integrador2025\name_info\projeto_integrador2025\
# Se o arquivo nomes.db estiver dentro de projeto_nomes/, use DB_PATH = 'nomes.db'
DB_PATH = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'nomes.db')
OUTPUT_CSV = 'nomes_data.csv'

def exportar_sqlite_para_csv():
    """
    Conecta ao banco de dados SQLite local, lê a tabela 'nomes' e exporta
    os dados para um arquivo CSV.
    """
    if not os.path.exists(DB_PATH):
        print(f"ERRO: Arquivo de banco de dados SQLite não encontrado em: {DB_PATH}")
        print("Verifique se 'nomes.db' está na pasta raiz do projeto 'projeto_integrador2025'.")
        return

    try:
        # Conecta ao SQLite
        conn = sqlite3.connect(DB_PATH)
        
        # Lê todos os dados da tabela 'nomes'
        # IMPORTANTE: Garanta que a sua tabela se chama 'nomes'
        query = "SELECT nome, significado, origem, motivo_escolha, pesquisas FROM nomes"
        
        # O Pandas lê os dados e os armazena em um DataFrame
        df = pd.read_sql_query(query, conn)
        
        # Fecha a conexão
        conn.close()
        
        # Exporta o DataFrame para CSV
        # O argumento index=False impede que o Pandas adicione uma coluna de índice numérica extra.
        # Nós confiamos que o PostgreSQL irá gerar o ID (SERIAL PRIMARY KEY).
        df.to_csv(OUTPUT_CSV, index=False, encoding='utf-8')
        
        print(f"\n✅ SUCESSO: Dados exportados com sucesso para {OUTPUT_CSV}")
        print("Agora, importe este arquivo CSV no editor de tabelas do Supabase.")

    except Exception as e:
        print(f"❌ ERRO durante a exportação para CSV: {e}")

if __name__ == '__main__':
    exportar_sqlite_para_csv()
