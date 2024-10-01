from flask import Flask, render_template, request, redirect, flash, jsonify, url_for, json
import psycopg2
import requests

app = Flask(__name__)
app.secret_key = 'KSJD(P@#$¨HRF*¨#@$Fgw8d7yfb830730erhf7H7DHRF30EG)'

pdf_selections = {}

@app.route('/save_config', methods=['POST'])
def save_config_route():
    host = request.form.get('host')
    port = request.form.get('port')
    name = request.form.get('name')
    user = request.form.get('user')
    password = request.form.get('password')

    config_data = {
        'DB_HOST': host,
        'DB_PORT': port,
        'DB_NAME': name,
        'DB_USER': user,
        'DB_PASSWORD': password
    }

    save_config(config_data)
    flash('Configurações salvas com sucesso!')
    return redirect(url_for('index'))

def load_config():
    try:
        with open('db_config.json', 'r') as f:
            config_data = json.load(f)
            return config_data
    except FileNotFoundError:
        return None

def save_config(config_data):
    with open('db_config.json', 'w') as f:
        json.dump(config_data, f)

def get_db_connection():
    config_data = load_config()

    if config_data:
        DB_HOST = config_data.get('DB_HOST', '')
        DB_PORT = config_data.get('DB_PORT', '')
        DB_NAME = config_data.get('DB_NAME', '')
        DB_USER = config_data.get('DB_USER', '')
        DB_PASSWORD = config_data.get('DB_PASSWORD', '')
    else:
        DB_HOST = ''
        DB_PORT = ''
        DB_NAME = ''
        DB_USER = ''
        DB_PASSWORD = ''

    try:
        conn = psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            dbname=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Erro ao conectar ao banco de dados: {e}")
        return None



@app.route('/reset_database')
def reset_database():
    conn = get_db_connection()
    cur = conn.cursor()
    try:
        sql = "TRUNCATE TABLE pdf_selection_history"
        cur.execute(sql)
        conn.commit()  # Confirmar a transação
        flash('Tabela limpa com sucesso!', 'success')
    except Exception as e:
        conn.rollback()  # Reverter em caso de erro
        flash(f'Erro ao limpar a tabela: {str(e)}', 'danger')
    finally:
        cur.close()
        conn.close()
    
    return redirect(url_for('show_index'))

@app.route('/save', methods=['POST'])
def save():
    data = request.get_json()
    title = data.get('title')
    content = 'INCLUA UM TEXTO'
    pageTitle = "Pop's Função Respiratória"

    print(data)

    conn = get_db_connection()
    cur = conn.cursor()

    sql_insert = """
        INSERT INTO tb_fat_atualizacao (ds_titulo, ds_text, ds_categoria)
        VALUES (%s, %s, %s)
    """
    cur.execute(sql_insert, (title, content, pageTitle))
    conn.commit()
    cur.close()
    conn.close()

    flash('Atualização registrada com sucesso!', 'success')

    # Retornar um JSON de sucesso para a requisição AJAX
    return jsonify({'message': 'Alteração salva com sucesso!'})




@app.route('/')
def show_index():
    conn = get_db_connection()
    cur = conn.cursor()
    sql = """select 
                co_doc,
                no_documento,
                no_autor,
                nu_revisoes,
                to_char(dt_revisao, 'dd/mm/yyyy')
            from tb_fat_lista_mestra            
            """
    
    cur.execute(sql)
    revisao = cur.fetchall()  # Busca todos os resultados

    cur.close()
    conn.close()
    
    # Passa os dados para o template
    return render_template('index.html', revisao=revisao)



@app.route('/assistenciais')
def assistenciais():

    response = requests.get('http://192.168.1.25:5099/pdfs')
    pdfs = response.json()
    return render_template('assistenciais.html', pdfs=pdfs)



@app.route('/medicacoes')
def medicacoes():
    response = requests.get('http://192.168.1.25:5099/pdfs')
    pdfs = response.json()

    return render_template('medicacoes.html', pdfs=pdfs)



@app.route('/bloco_cirurgico')
def bloco_cirurgico():
    response = requests.get('http://192.168.1.25:5099/pdfs')
    pdfs = response.json()

    return render_template('bloco_cirurgico.html', pdfs=pdfs)



@app.route('/cme')
def cme():
    response = requests.get('http://192.168.1.25:5099/pdfs')
    pdfs = response.json()

    return render_template('cme.html', pdfs=pdfs)



@app.route('/hemoterapia')
def hemoterapia():
    response = requests.get('http://192.168.1.25:5099/pdfs')
    pdfs = response.json()

    return render_template('hemoterapia.html', pdfs=pdfs)



@app.route('/limpeza_desinfeccao')
def limpeza_desinfeccao():
    response = requests.get('http://192.168.1.25:5099/pdfs')
    pdfs = response.json()

    return render_template('limpeza_desinfeccao.html', pdfs=pdfs)



@app.route('/funcao_respiratoria')
def funcao_respiratoria():
    response = requests.get('http://192.168.1.25:5099/pdfs')
    pdfs = response.json()

    return render_template('funcao_respiratoria.html', pdfs=pdfs)


@app.route('/farmacia')
def farmacia():
    # Requisição diretamente para a subpasta "farmacia"
    response = requests.get('http://192.168.1.140:5088/farmacia')
    
    if response.status_code == 404:
        return "Erro: Subpasta não encontrada", 404
    
    pdfs = response.json()
    return render_template('farmacia.html', pdfs=pdfs)



@app.route('/save_selection', methods=['POST'])
def save_selection():
    data = request.json
    section_id = data.get('section_id')
    selected_pdf = data.get('selected_pdf')
    page_identifier = data.get('page_identifier')
    
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Verificar se já existe uma seleção para a seção
    cur.execute("SELECT id, selected_pdf, page_identifier FROM pdf_selections WHERE section_id = %s", (section_id,))
    existing_selection = cur.fetchone()
    
    if existing_selection:
        # Atualizar a seleção existente
        cur.execute(
            "UPDATE pdf_selections SET selected_pdf = %s, page_identifier = %s, created_at = CURRENT_TIMESTAMP WHERE section_id = %s",
            (selected_pdf, page_identifier, section_id)
        )
        
        # Registrar a alteração no histórico
        cur.execute(
            "INSERT INTO pdf_selection_history (selection_id, section_id, selected_pdf, page_identifier, action) VALUES (%s, %s, %s, %s, %s)",
            (existing_selection[0], section_id, existing_selection[1], existing_selection[2], 'update')
        )
    else:
        # Inserir uma nova seleção
        cur.execute(
            "INSERT INTO pdf_selections (section_id, selected_pdf, page_identifier) VALUES (%s, %s, %s) RETURNING id",
            (section_id, selected_pdf, page_identifier)
        )
        new_id = cur.fetchone()[0]

        # Registrar a inserção no histórico
        cur.execute(
            "INSERT INTO pdf_selection_history (selection_id, section_id, selected_pdf, page_identifier, action) VALUES (%s, %s, %s, %s, %s)",
            (new_id, section_id, selected_pdf, page_identifier, 'insert')
        )
    
    conn.commit()
    cur.close()
    conn.close()
    
    return jsonify({"message": "Selection saved successfully!"}), 200





@app.route('/get_selection/<int:section_id>/<string:page_identifier>', methods=['GET'])
def get_selection(section_id, page_identifier):
    conn = get_db_connection()
    cur = conn.cursor()
    
    # Agora a consulta inclui page_identifier
    cur.execute("SELECT selected_pdf FROM pdf_selections WHERE section_id = %s AND page_identifier = %s", (section_id, page_identifier))
    selected_pdf = cur.fetchone()
    
    cur.close()
    conn.close()
    
    if selected_pdf:
        return jsonify({"selected_pdf": selected_pdf[0]}), 200
    else:
        return jsonify({"selected_pdf": ""}), 200
    

@app.route('/save_revisao', methods=['POST'])
def save_revisao():
    co_doc = request.form.get('co_doc')
    no_documento = request.form.get('no_documento')
    no_autor  = request.form.get('no_autor')
    nu_revisoes = request.form.get('nu_revisoes')
    dt_revisao = request.form.get('dt_revisao')

    conn = get_db_connection()
    cur = conn.cursor()

    sql_insert = """
        INSERT INTO tb_fat_lista_mestra (co_doc, no_documento, no_autor, nu_revisoes, dt_revisao)
        VALUES (%s, %s, %s, %s, %s)
    """
    cur.execute(sql_insert, (co_doc, no_documento, no_autor, nu_revisoes, dt_revisao))
    conn.commit()
    cur.close()
    conn.close()

    flash('Revisão registrada com sucesso!', 'success')

    return redirect(url_for('show_index'))



if __name__ == '__main__':
    app.run(debug=True, host='0.0.0.0', port='5009')
