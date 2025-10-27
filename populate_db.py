import os
import db as db_conexao # Importa o módulo db com as funções init_db e clear_db
from dotenv import load_dotenv
import csv 
import sys

# Garante que a codificação UTF-8 é usada para evitar erros de acentuação
sys.stdout.reconfigure(encoding='utf-8')

# Carregar variáveis do .env (necessário para rodar localmente)
load_dotenv()

# Caminho do arquivo CSV. Assumindo que está na raiz do projeto.
CSV_FILEPATH = 'nomes.csv' 

def popular_banco_via_csv():
    """Lê dados do CSV, limpa o banco e os insere no PostgreSQL."""
    print(f"🔄 Tentando ler o arquivo: {CSV_FILEPATH}")
    
    # 1. --- LER CSV ---
    dados_do_csv = []
    try:
        # Usamos 'utf-8-sig' para lidar com o cabeçalho \ufeff que seu CSV pode ter
        with open(CSV_FILEPATH, mode='r', encoding='utf-8-sig') as file:
            # reader do CSV
            csv_reader = csv.reader(file, delimiter=';') # Mude o delimitador se não for ';'
            
            # Pula o cabeçalho
            header = next(csv_reader, None)
            print(f"Header (Cabeçalho) do CSV lido: {header}")
            
            for row in csv_reader:
                # O CSV que você mostrou tem: ID, Nome, Significado, Origem, Motivo, Pesquisas
                # O banco precisa de: Nome, Significado, Origem, Motivo, Pesquisas (ID é gerado)
                
                # Garantimos que a linha tenha pelo menos 5 colunas (Nome, Significado, Origem, Motivo, Pesquisas)
                if len(row) >= 5: 
                    # Ignoramos a primeira coluna (row[0], o ID antigo)
                    nome = row[1].strip()
                    significado = row[2].strip()
                    origem = row[3].strip()
                    motivo_escolha = row[4].strip()
                    
                    # Tenta ler 'pesquisas' como inteiro, usando o valor da coluna 5 (índice 5)
                    pesquisas = int(row[5].strip()) if len(row) > 5 and row[5].strip().isdigit() else 0

                    # Adiciona os 5 campos (Nome, Significado, Origem, Motivo, Pesquisas)
                    dados_do_csv.append((nome, significado, origem, motivo_escolha, pesquisas)) 
                # Ignoramos linhas que não tenham dados suficientes

    except FileNotFoundError:
        print(f"❌ Erro: Arquivo CSV não encontrado no caminho: {CSV_FILEPATH}")
        return
    except Exception as e:
        print(f"❌ Erro ao ler o arquivo CSV: {e}")
        return

    if not dados_do_csv:
        print("❌ Nenhum dado válido encontrado no arquivo CSV para inserção.")
        return
        
    print(f"✅ {len(dados_do_csv)} registros lidos do arquivo CSV.")

    # 2. --- INSERÇÃO NO BANCO ---
    conn = None
    try:
        # A. Inicializa o banco (cria a tabela com a restrição UNIQUE se não existir)
        db_conexao.init_db() 
        
        # B. LIMPA O BANCO COMPLETAMENTE (isso resolve as 5514 repetições)
        db_conexao.clear_db() 

        conn = db_conexao.get_connection()
        cursor = conn.cursor()

        print(f"🔄 Inserindo {len(dados_do_csv)} registros no PostgreSQL...")
        
        # Query de inserção com ON CONFLICT (que agora funcionará com a restrição UNIQUE)
        query_insert = """
            INSERT INTO nomes (nome, significado, origem, motivo_escolha, pesquisas)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (nome) DO NOTHING; 
        """
        
        # Executa a inserção de todos os dados
        cursor.executemany(query_insert, dados_do_csv)
        
        conn.commit()
        
        # Novo check de contagem total
        cursor.execute("SELECT COUNT(*) FROM nomes")
        final_count = cursor.fetchone()[0]
        
        print(f"✅ Carga massiva concluída. Total de registros na tabela: {final_count}")

    except Exception as e:
        print(f"❌ Erro ao popular o banco de dados (SQL/Conexão): {e}")
        if conn:
            conn.rollback() # Reverte em caso de erro
    finally:
        if conn:
            cursor.close()
            db_conexao.connection_pool.putconn(conn)

if __name__ == '__main__':
    popular_banco_via_csv()
