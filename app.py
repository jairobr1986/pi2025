import os
import io
import pandas as pd
from flask import Flask, render_template, request, redirect, url_for, flash
import matplotlib.pyplot as plt
import base64

import db_postgres as db_conexao

app = Flask(__name__)
app.secret_key = os.environ.get('FLASK_SECRET_KEY', 'sua_chave_secreta_padrao_muito_segura')

try:
    db_conexao.init_db()
except Exception as e:
    print(f"FATAL: Falha ao inicializar o banco de dados PostgreSQL. Verifique DB_CONFIG ou .env. Erro: {e}")
    exit(1)

def fetch_all(query, params=None):
    conn = None
    try:
        conn = db_conexao.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        columns = [desc[0] for desc in cursor.description]
        results = [dict(zip(columns, row)) for row in cursor.fetchall()]
        return results
    except Exception as e:
        flash(f"Erro de banco de dados: {e}", 'error')
        print(f"Erro de banco de dados (fetch_all): {e}")
        return []
    finally:
        if conn:
            cursor.close()
            db_conexao.connection_pool.putconn(conn)

def execute_query(query, params=None):
    conn = None
    try:
        conn = db_conexao.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        conn.commit()
        return True
    except Exception as e:
        flash(f"Erro ao salvar no banco de dados: {e}", 'error')
        print(f"Erro ao salvar no banco de dados (execute_query): {e}")
        return False
    finally:
        if conn:
            cursor.close()
            db_conexao.connection_pool.putconn(conn)

def fetch_one(query, params=None):
    conn = None
    try:
        conn = db_conexao.get_connection()
        cursor = conn.cursor()
        cursor.execute(query, params or ())
        columns = [desc[0] for desc in cursor.description]
        row = cursor.fetchone()
        return dict(zip(columns, row)) if row else None
    except Exception as e:
        flash(f"Erro de banco de dados: {e}", 'error')
        print(f"Erro de banco de dados (fetch_one): {e}")
        return None
    finally:
        if conn:
            cursor.close()
            db_conexao.connection_pool.putconn(conn)

@app.route('/')
def index():
    total_result = fetch_one("SELECT COUNT(id) as total FROM nomes")
    total = total_result['total'] if total_result else 0
    query_top10 = "SELECT nome, pesquisas FROM nomes ORDER BY pesquisas DESC LIMIT 10"
    top_nomes = fetch_all(query_top10)
    return render_template('index.html', total=total, top_nomes=top_nomes)

@app.route('/buscar', methods=['GET', 'POST'])
def buscar():
    termo_pesquisado = ''
    resultados = []
    if request.method == 'POST':
        termo_pesquisado = request.form.get('termo', '').strip()
        if termo_pesquisado:
            query_busca = """
                SELECT id, nome, significado, origem, motivo_escolha, pesquisas
                FROM nomes
                WHERE nome ILIKE %s
                ORDER BY nome ASC
            """
            resultados = fetch_all(query_busca, (f'%{termo_pesquisado}%',))
            if resultados:
                for row in resultados:
                    novo_total = row['pesquisas'] + 1
                    query_update = "UPDATE nomes SET pesquisas = %s WHERE id = %s"
                    execute_query(query_update, (novo_total, row['id']))
                    row['pesquisas'] = novo_total
                flash(f"{len(resultados)} nome(s) encontrado(s) e contador(es) atualizado(s).", 'success')
            else:
                flash(f"Nenhum nome encontrado para '{termo_pesquisado}'.", 'warning')
        else:
            flash("Por favor, digite um nome para buscar.", 'error')
    return render_template('buscar.html', resultados=resultados, termo_pesquisado=termo_pesquisado)

@app.route('/listar')
def listar():
    try:
        page = int(request.args.get('page', 1))
    except ValueError:
        page = 1
    per_page = 10
    offset = (page - 1) * per_page
    filtro_nome = request.args.get('nome', '').strip()
    filtro_origem = request.args.get('origem', '').strip()
    query_count = "SELECT COUNT(id) as total FROM nomes WHERE 1=1"
    params = []
    if filtro_nome:
        query_count += " AND nome ILIKE %s"
        params.append(f"%{filtro_nome}%")
    if filtro_origem:
        query_count += " AND origem ILIKE %s"
        params.append(f"%{filtro_origem}%")
    total_result = fetch_one(query_count, tuple(params))
    total_registros = total_result['total'] if total_result else 0
    total_pages = (total_registros + per_page - 1) // per_page
    if page < 1:
        page = 1
    if page > total_pages and total_pages > 0:
        page = total_pages
        offset = (page - 1) * per_page
    query = "SELECT id, nome, significado, origem, motivo_escolha, pesquisas FROM nomes WHERE 1=1"
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
    print(f"Debug /listar: Total registros: {total_registros}, Nomes encontrados: {len(nomes)}")
    for i, nome in enumerate(nomes):
        nome['indice'] = offset + i + 1
    return render_template('listar.html', 
                           nomes=nomes, 
                           page=page, 
                           total_pages=total_pages,
                           filtro_nome=filtro_nome,
                           filtro_origem=filtro_origem)

@app.route('/cadastrar', methods=['GET', 'POST'])
def cadastrar():
    if request.method == 'POST':
        nome = request.form.get('nome', '').strip()
        significado = request.form.get('significado', '').strip()
        origem = request.form.get('origem', '').strip()
        motivo_escolha = request.form.get('motivo_escolha', '').strip()
        if nome and significado and origem:
            query_check = "SELECT id FROM nomes WHERE nome ILIKE %s"
            existing_name = fetch_one(query_check, (nome,))
            if existing_name:
                flash(f"O nome '{nome}' já existe no banco de dados.", 'error')
            else:
                query_insert = """
                    INSERT INTO nomes (nome, significado, origem, motivo_escolha, pesquisas)
                    VALUES (%s, %s, %s, %s, 0)
                """
                if execute_query(query_insert, (nome, significado, origem, motivo_escolha)):
                    flash(f"Nome '{nome}' cadastrado com sucesso!", 'success')
                    return redirect(url_for('listar'))
                else:
                    flash("Falha ao cadastrar o nome.", 'error')
        else:
            flash("Nome, Significado e Origem são campos obrigatórios.", 'error')
    return render_template('cadastrar.html')

@app.route('/top10')
def top10():
    query = "SELECT nome, pesquisas FROM nomes ORDER BY pesquisas DESC LIMIT 10"
    top_nomes = fetch_all(query)
    for i, nome in enumerate(top_nomes):
        nome['ranking'] = i + 1
    return render_template('top10.html', top_nomes=top_nomes)

@app.route('/estatisticas')
def estatisticas():
    query_origem = "SELECT origem, COUNT(id) as count FROM nomes GROUP BY origem ORDER BY count DESC"
    data_origem = fetch_all(query_origem)
    query_top5 = "SELECT nome, pesquisas FROM nomes ORDER BY pesquisas DESC LIMIT 5"
    data_top5 = fetch_all(query_top5)

    def generate_chart(labels, values, chart_type, title, ylabel=None):
        plt.figure(figsize=(10, 6))
        if chart_type == 'pie':
            plt.pie(values, labels=labels, autopct='%1.1f%%', startangle=90, wedgeprops={'edgecolor': 'black'})
            plt.title(title)
            plt.axis('equal')
        elif chart_type == 'bar':
            plt.bar(labels, values, color='skyblue')
            plt.title(title)
            if ylabel:
                plt.ylabel(ylabel)
            plt.xlabel('Nome')
            plt.xticks(rotation=45, ha='right')
            plt.tight_layout()
        buf = io.BytesIO()
        plt.savefig(buf, format='png', transparent=True)
        plt.close()
        data = base64.b64encode(buf.getvalue()).decode('utf-8')
        return f"data:image/png;base64,{data}"

    origens = [d['origem'] for d in data_origem]
    contagens = [d['count'] for d in data_origem]
    grafico_origem_url = generate_chart(origens, contagens, 'pie', 'Distribuição de Nomes por Origem')
    top_nomes_labels = [d['nome'] for d in data_top5]
    top_nomes_pesquisas = [d['pesquisas'] for d in data_top5]
    grafico_top5_url = generate_chart(top_nomes_labels, top_nomes_pesquisas, 'bar', 'Top 5 Nomes Mais Pesquisados', 'Número de Pesquisas')

    return render_template('estatisticas.html', 
                           grafico_origem_url=grafico_origem_url, 
                           grafico_top5_url=grafico_top5_url,
                           tabela_origem=data_origem,
                           tabela_top5=data_top5)

if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))