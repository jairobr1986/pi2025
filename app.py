# ==========================================
# app.py - SERVIDOR WEB DO PROJETO "LIVRO DOS NOMES"
# ==========================================
# Autor: Jairo (com ajuda do Grok)
# Descrição: Aplicação Flask para gerenciar nomes com:
#   - Cadastro
#   - Busca (com 3+ letras, início do nome)
#   - Listagem com paginação
#   - Contador de pesquisas
#   - Estatísticas e gráficos
#   - Top 10 mais pesquisados
# ==========================================

import os
import io
import base64
from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import matplotlib.pyplot as plt

# Importa funções de conexão com o banco (db.py)
import db as db_conexao

# ==========================================
# CONFIGURAÇÃO DO FLASK
# ==========================================
app = Flask(__name__)

# Chave secreta para sessões e flash messages (NUNCA deixe fixa em produção!)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'chave_muito_secreta_2025_troque_isso')

# ==========================================
# INICIALIZAÇÃO DO BANCO DE DADOS
# ==========================================
try:
    db_conexao.init_db()  # Cria tabela e índices se não existirem
    print("Banco de dados inicializado com sucesso.")
except Exception as e:
    print(f"[FATAL] Falha ao conectar com o banco: {e}")
    exit(1)  # Encerra o app se o banco não funcionar


# ==========================================
# FUNÇÕES AUXILIARES DE BANCO
# ==========================================

def fetch_all(query, params=None):
    """
    Executa uma consulta SELECT e retorna todos os resultados como lista de dicionários.
    Ex: [{'id': 1, 'nome': 'João', ...}, ...]
    """
    conn = None
    try:
        conn = db_conexao.get_connection()
        cursor = conn.cursor()
        print(f"[DEBUG] Executando: {query} | Parâmetros: {params}")
        cursor.execute(query, params or ())
        
        # Pega nomes das colunas
        columns = [desc[0] for desc in cursor.description]
        rows = cursor.fetchall()
        
        # Converte para lista de dicionários
        results = [dict(zip(columns, row)) for row in rows]
        
        print(f"[DEBUG] {len(results)} registro(s) retornado(s).")
        return results
    except Exception as e:
        flash(f"Erro ao buscar dados: {e}", 'error')
        print(f"[ERRO] fetch_all: {e}")
        return []
    finally:
        if conn:
            cursor.close()
            db_conexao.connection_pool.putconn(conn)


def fetch_one(query, params=None):
    """
    Executa consulta que retorna apenas UM registro.
    Útil para COUNT, SELECT por ID, etc.
    """
    conn = None
    try:
        conn = db_conexao.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    except Exception as e:
        flash(f"Erro ao buscar dado único: {e}", 'error')
        print(f"[ERRO] fetch_one: {e}")
        return None
    finally:
        if conn:
            cursor.close()
            db_conexao.connection_pool.putconn(conn)


def execute_query(query, params=None):
    """
    Executa INSERT, UPDATE, DELETE.
    Retorna True se sucesso, False se falha.
    """
    conn = None
    try:
        conn = db_conexao.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return True
    except Exception as e:
        flash(f"Erro ao salvar no banco: {e}", 'error')
        print(f"[ERRO] execute_query: {e}")
        return False
    finally:
        if conn:
            cursor.close()
            db_conexao.connection_pool.putconn(conn)


# ==========================================
# ROTAS DO SITE
# ==========================================

@app.route('/')
def index():
    """
    Página inicial: mostra total de nomes e top 10 mais pesquisados.
    """
    # Total de nomes no banco
    total_result = fetch_one("SELECT COUNT(id) as total FROM nomes")
    total = total_result['total'] if total_result else 0

    # Top 10 mais pesquisados
    top_nomes = fetch_all("""
        SELECT nome, pesquisas 
        FROM nomes 
        ORDER BY pesquisas DESC 
        LIMIT 10
    """)

    return render_template('index.html', total=total, top_nomes=top_nomes)


@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    """
    Busca nomes que COMECEM com o termo (mínimo 3 letras).
    Atualiza contador de pesquisas.
    """
    termo_pesquisado = ''
    resultados = []

    if request.method == 'POST':
        termo_pesquisado = request.form.get('termo', '').strip()

        # Validação de entrada
        if not termo_pesquisado:
            flash("Por favor, digite um nome para buscar.", 'error')
        elif len(termo_pesquisado) < 3:
            flash("Digite pelo menos 3 letras para buscar.", 'warning')
        else:
            try:
                # Busca nomes que começam com o termo
                query = """
                    SELECT id, nome, significado, origem, motivo_escolha, pesquisas
                    FROM nomes
                    WHERE nome ILIKE %s
                    ORDER BY nome ASC
                """
                resultados = fetch_all(query, (f"{termo_pesquisado}%",))

                if resultados:
                    # Atualiza contador de pesquisas
                    for row in resultados:
                        novo_total = row['pesquisas'] + 1
                        if execute_query(
                            "UPDATE nomes SET pesquisas = %s WHERE id = %s",
                            (novo_total, row['id'])
                        ):
                            row['pesquisas'] = novo_total
                    flash(f"Encontrado(s) {len(resultados)} nome(s)!", 'success')
                else:
                    flash(f"Nenhum nome encontrado começando com '{termo_pesquisado}'.", 'info')

            except Exception as e:
                flash("Erro ao realizar busca. Tente novamente.", 'error')
                print(f"[ERRO] Busca falhou: {e}")

    return render_template(
        'buscar.html',
        resultados=resultados,
        termo_pesquisado=termo_pesquisado
    )


@app.route('/listar')
def listar():
    """
    Lista todos os nomes com paginação (10 por página).
    Suporta filtro por nome e origem.
    """
    try:
        page = int(request.args.get('page', 1))
        per_page = int(request.args.get('per_page', 10))
    except ValueError:
        page = 1
        per_page = 10

    # Garante valores válidos
    page = max(1, page)
    per_page = max(1, min(100, per_page))  # Limite de segurança
    offset = (page - 1) * per_page

    filtro_nome = request.args.get('nome', '').strip()
    filtro_origem = request.args.get('origem', '').strip()

    # --- CONTAGEM TOTAL ---
    count_query = "SELECT COUNT(id) as total FROM nomes WHERE 1=1"
    params = []
    if filtro_nome:
        count_query += " AND nome ILIKE %s"
        params.append(f"%{filtro_nome}%")
    if filtro_origem:
        count_query += " AND origem ILIKE %s"
        params.append(f"%{filtro_origem}%")

    total_result = fetch_one(count_query, tuple(params))
    total_registros = total_result['total'] if total_result else 0
    total_pages = (total_registros + per_page - 1) // per_page

    # Ajusta página inválida
    if page > total_pages and total_pages > 0:
        page = total_pages
        offset = (page - 1) * per_page

    # --- BUSCA COM PAGINAÇÃO ---
    query = """
        SELECT id, nome, significado, origem, motivo_escolha, pesquisas
        FROM nomes
        WHERE 1=1
    """
    params = []
    if filtro_nome:
        query += " AND nome ILIKE %s"
        params.append(f"%{filtro_nome}%")
    if filtro_origem:
        query += " AND origem ILIKE %s"
        params.append(f"%{filtro_origem}%")

    query += " ORDER BY nome ASC LIMIT %s OFFSET %s"
    params.extend([per_page, offset])

    nomes = fetch_all(query, tuple(params))

    return render_template(
        'listar.html',
        nomes=nomes,
        page=page,
        total_pages=total_pages,
        filtro_nome=filtro_nome,
        filtro_origem=filtro_origem,
        per_page=per_page
    )


@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    """
    Cadastro de novo nome com validação.
    """
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        significado = request.form.get('significado', '').strip()
        origem = request.form.get('origem', '').strip()
        motivo_escolha = request.form.get('motivo_escolha', '').strip()

        if not (nome and significado and origem):
            flash("Nome, Significado e Origem são obrigatórios.", 'error')
        else:
            # Verifica duplicata
            if fetch_one("SELECT id FROM nomes WHERE nome ILIKE %s", (nome,)):
                flash(f"O nome '{nome}' já existe.", 'error')
            else:
                if execute_query("""
                    INSERT INTO nomes (nome, significado, origem, motivo_escolha, pesquisas)
                    VALUES (%s, %s, %s, %s, 0)
                """, (nome, significado, origem, motivo_escolha)):
                    flash(f"Nome '{nome}' cadastrado com sucesso!", 'success')
                    return redirect(url_for('listar'))
                else:
                    flash("Erro ao cadastrar. Tente novamente.", 'error')

    return render_template('cadastrar.html')


@app.route('/top10')
def top10():
    """
    Exibe os 10 nomes mais pesquisados.
    """
    top_nomes = fetch_all("""
        SELECT nome, pesquisas 
        FROM nomes 
        ORDER BY pesquisas DESC 
        LIMIT 10
    """)
    # Adiciona ranking
    for i, nome in enumerate(top_nomes, 1):
        nome['ranking'] = i

    return render_template('top10.html', top_nomes=top_nomes)


import io
import base64
import matplotlib.pyplot as plt

@app.route('/estatisticas')
def estatisticas():
    """
    Gera gráficos dinâmicos com foco em clareza.
    - Top 10 origens (barras horizontais)
    - Top 5 pesquisados (barras verticais)
    """
    try:
        # === DISTRIBUIÇÃO POR ORIGEM (TOP 10 + "Outras") ===
        origens_raw = fetch_all("""
            SELECT origem, COUNT(id) as count 
            FROM nomes 
            GROUP BY origem 
            ORDER BY count DESC
        """)

        # Separa top 10 e o resto
        top_10_origens = origens_raw[:10]
        outras_count = sum(item['count'] for item in origens_raw[10:]) if len(origens_raw) > 10 else 0

        origens_labels = [item['origem'] for item in top_10_origens]
        origens_valores = [item['count'] for item in top_10_origens]
        if outras_count > 0:
            origens_labels.append("Outras")
            origens_valores.append(outras_count)

        # === TOP 5 PESQUISADOS ===
        data_top5 = fetch_all("""
            SELECT nome, pesquisas 
            FROM nomes 
            ORDER BY pesquisas DESC 
            LIMIT 5
        """)

        nomes_top = [d['nome'] for d in data_top5]
        pesquisas_top = [d['pesquisas'] for d in data_top5]

        # === FUNÇÃO PARA GERAR GRÁFICO ===
        def gerar_grafico(labels, values, tipo, titulo, xlabel=None, ylabel=None):
            plt.figure(figsize=(10, 6))
            colors = plt.cm.Set3(range(len(labels))) if tipo == 'barh' else ['#4e79a7']

            if tipo == 'barh':  # Barras horizontais
                bars = plt.barh(labels, values, color=colors, edgecolor='navy', alpha=0.8)
                plt.title(titulo, fontsize=14, fontweight='bold', pad=20)
                plt.xlabel(xlabel or 'Quantidade de Nomes', fontsize=12)
                plt.grid(axis='x', alpha=0.3, linestyle='--')
                plt.gca().invert_yaxis()  # Maior no topo
                for i, bar in enumerate(bars):
                    width = bar.get_width()
                    plt.text(width + 0.5, bar.get_y() + bar.get_height()/2,
                             f'{int(width)}', va='center', fontsize=10, fontweight='bold')
            elif tipo == 'bar':  # Barras verticais
                bars = plt.bar(labels, values, color='#66b3ff', edgecolor='navy', linewidth=1)
                plt.title(titulo, fontsize=14, fontweight='bold', pad=20)
                plt.ylabel(ylabel or 'Pesquisas', fontsize=12)
                plt.xlabel('Nome', fontsize=12)
                plt.xticks(rotation=45, ha='right')
                plt.grid(axis='y', alpha=0.3)
                for bar in bars:
                    height = bar.get_height()
                    plt.text(bar.get_x() + bar.get_width()/2., height + 0.1,
                             f'{int(height)}', ha='center', va='bottom', fontsize=10)

            plt.tight_layout()
            buf = io.BytesIO()
            plt.savefig(buf, format='png', transparent=True, bbox_inches='tight', dpi=120)
            plt.close()
            return f"data:image/png;base64,{base64.b64encode(buf.getvalue()).decode()}"

        # === GERA GRÁFICOS ===
        grafico_origem_url = gerar_grafico(
            origens_labels, origens_valores, 'barh',
            'Top 10 Origens Mais Comuns + Outras', 'Quantidade'
        ) if origens_labels else None

        grafico_top5_url = gerar_grafico(
            nomes_top, pesquisas_top, 'bar',
            'Top 5 Nomes Mais Pesquisados', ylabel='Pesquisas'
        ) if data_top5 else None

        return render_template(
            'estatisticas.html',
            grafico_origem_url=grafico_origem_url,
            grafico_top5_url=grafico_top5_url,
            tabela_origem=top_10_origens + ([{'origem': 'Outras', 'count': outras_count}] if outras_count > 0 else []),
            tabela_top5=data_top5
        )

    except Exception as e:
        flash("Erro ao gerar estatísticas.", "error")
        print(f"[ERRO] Estatísticas: {e}")
        return render_template('estatisticas.html')

# ==========================================
# ROTA: EXPORTAR DADOS PARA CSV
# ==========================================
from flask import make_response
import csv
from io import StringIO

@app.route('/exportar_csv')
def exportar_csv():
    """
    Exporta todos os nomes do banco para um arquivo CSV.
    """
    try:
        # Busca todos os nomes
        nomes = fetch_all("""
            SELECT nome, significado, origem, motivo_escolha, pesquisas 
            FROM nomes 
            ORDER BY nome ASC
        """)
        
        # Cria CSV em memória
        output = StringIO()
        writer = csv.writer(output)
        
        # Cabeçalho
        writer.writerow(['Nome', 'Significado', 'Origem', 'Motivo da Escolha', 'Pesquisas'])
        
        # Dados
        for n in nomes:
            writer.writerow([
                n['nome'],
                n['significado'],
                n['origem'],
                n['motivo_escolha'],
                n['pesquisas']
            ])
        
        # Resposta com download
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=nomes_exportados.csv"
        response.headers["Content-type"] = "text/csv; charset=utf-8"
        
        flash("CSV exportado com sucesso!", "success")
        return response
        
    except Exception as e:
        flash("Erro ao exportar CSV.", "error")
        print(f"[ERRO] Exportação CSV: {e}")
        return redirect(url_for('index'))


# ==========================================
# EXECUÇÃO DO SERVIDOR
# ==========================================
if __name__ == '__main__':
    """
    Inicia o servidor Flask.
    - debug=True: recarrega automaticamente
    - host='0.0.0.0': acessível na rede local
    - port=5000: porta padrão
    """
    print("Servidor iniciando em http://127.0.0.1:5000")
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))