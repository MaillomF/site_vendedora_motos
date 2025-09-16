import os
import sqlite3
from flask import Flask, render_template, request, redirect, session, url_for
from werkzeug.utils import secure_filename
from flask import jsonify
from babel.numbers import format_currency






BASE_DIR = os.path.dirname(os.path.abspath(__file__))
motos_db = os.path.join(BASE_DIR, "motos.db")
consorcios_db = os.path.join(BASE_DIR, "consorcios.db")


app = Flask(__name__,
    static_folder=os.path.join(os.path.dirname(__file__), 'static'),
    template_folder=os.path.join(os.path.dirname(__file__), 'templates')
)

app.secret_key = '182015'
UPLOAD_FOLDER = 'static/consorcios'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

from babel.numbers import format_currency

@app.template_filter('moeda')
def formatar_moeda(valor):
    try:
        valor_float = float(valor)
        return format_currency(valor_float, 'BRL', locale='pt_BR')
    except:
        return "Valor inválido"


# Pasta onde as imagens serão salvas
UPLOAD_FOLDER = 'static/imagens'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER




@app.route('/login', methods=['GET', 'POST'])
def login():
    destino = request.args.get('next', 'painel')  # padrão: painel de motos
    if request.method == 'POST':
        usuario = request.form['usuario']
        senha = request.form['senha']
        if usuario == 'vendedoratop' and senha == '182015':
            session['usuario'] = usuario
            return redirect(url_for(destino))
        else:
            return render_template('login.html', erro='Usuário ou senha inválidos')
    return render_template('login.html')

@app.route('/painel')
def painel():
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect(motos_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM motos")
    motos = cursor.fetchall()
    conn.close()

    return render_template('painel.html', motos=motos)

@app.route('/painel-consorcios')
def painel_consorcios():
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consorcios")
    consorcios_raw = cursor.fetchall()

    consorcios = []
    for c in consorcios_raw:
        cursor.execute("SELECT nome_arquivo FROM imagens_consorcio WHERE consorcio_id = ?", (c[0],))
        imagens = [i[0] for i in cursor.fetchall()]
        consorcios.append({
                    'id': c[0],
                    'descricao': c[2],
                    'imagem_principal': c[1] if c[1] else 'default.jpg',  # usa o campo 'imagem' da tabela consorcios
                    'imagens': imagens
                })

    conn.close()
    return render_template('painel_consorcios.html', consorcios=consorcios)

# Cria o banco e a tabela se não existir
def init_db():
    conn = sqlite3.connect(motos_db)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS motos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            modelo TEXT NOT NULL,
            marca TEXT NOT NULL,
            ano INTEGER NOT NULL,
            valor REAL NOT NULL,
            descricao TEXT,
            imagem TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()



def init_consorcios_db():
    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consorcios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imagem TEXT,
            descricao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS imagens_consorcio (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            consorcio_id INTEGER,
            nome_arquivo TEXT,
            FOREIGN KEY (consorcio_id) REFERENCES consorcios(id)
        )
    ''')
    conn.commit()
    conn.close()


@app.route('/filtrar')
def filtrar():
    marca = request.args.get('marca', '')
    modelo = request.args.get('modelo', '')
    ano = request.args.get('ano', '')

    conn = sqlite3.connect('motos_db')
    cursor = conn.cursor()

    query = "SELECT * FROM motos WHERE 1=1"
    params = []

    if marca:
        query += " AND marca = ?"
        params.append(marca)
    if modelo:
        query += " AND modelo = ?"
        params.append(modelo)
    if ano:
        query += " AND ano = ?"
        params.append(ano)

    cursor.execute(query, params)
    motos = cursor.fetchall()
    conn.close()

    # Retornar como JSON
    return jsonify(motos)

@app.route('/')
def sabrina():
    return render_template('sabrina.html')  # renomeie index.html para sabrina.html
# Executa o app

# Rota principal: mostra as motos cadastradas
@app.route('/catalago')
def index():
    
    marca = request.args.get('marca', '')
    modelo = request.args.get('modelo', '')
    ano = request.args.get('ano', '')

    conn = sqlite3.connect('motos_db')
    cursor = conn.cursor()

    # Buscar valores únicos para os filtros
    cursor.execute("SELECT DISTINCT marca FROM motos")
    marcas = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT modelo FROM motos")
    modelos = [row[0] for row in cursor.fetchall()]

    cursor.execute("SELECT DISTINCT ano FROM motos ORDER BY ano DESC")
    anos = [row[0] for row in cursor.fetchall()]

    # Montar a query de filtro
    query = "SELECT * FROM motos WHERE 1=1"
    params = []

    if marca:
        query += " AND marca = ?"
        params.append(marca)
    if modelo:
        query += " AND modelo = ?"
        params.append(modelo)
    if ano:
        query += " AND ano = ?"
        params.append(ano)

    cursor.execute(query, params)
    motos = cursor.fetchall()
    conn.close()

    return render_template('index.html', motos=motos, marcas=marcas, modelos=modelos, anos=anos, marca=marca, modelo=modelo, ano=ano)



# Rota de cadastro
@app.route('/cadastro', methods=['GET', 'POST'])
def cadastro():
    if 'usuario' not in session:
        return redirect('/login')
    erros = []
    if request.method == 'GET':
        return render_template('cadastro.html', erros=erros)

    modelo = request.form['modelo']
    marca = request.form['marca']
    ano = request.form['ano']
    valor = request.form['valor']
    descricao = request.form['descricao']
    imagens_files = request.files.getlist('imagens')

    try:
        valor = float(valor)
        if valor <= 0:
            erros.append("Valor deve ser maior que zero.")
    except ValueError:
        erros.append("Valor deve ser um número válido.")

    if erros:
        return render_template('cadastro.html', erros=erros)

    nomes_imagens = []

    # Salva todas as imagens enviadas
    for imagem in imagens_files:
        if imagem and imagem.filename != '':
            filename = secure_filename(imagem.filename)
            imagem_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            imagem.save(imagem_path)
            nomes_imagens.append(filename)

    # Se nenhuma imagem foi enviada, define uma padrão
    if not nomes_imagens:
        nomes_imagens.append('default.jpg')

    imagens_str = ';'.join(nomes_imagens)

    conn = sqlite3.connect(motos_db)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO motos (modelo, marca, ano, valor, descricao, imagem)
        VALUES (?, ?, ?, ?, ?, ?)
    """, (modelo, marca, ano, valor, descricao, imagens_str))
    conn.commit()
    conn.close()

    return redirect('/')

@app.route('/excluir/<int:id>')
def excluir(id):
    conn = sqlite3.connect(motos_db)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM motos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect('/painel')

import os
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = 'static/imagens'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/editar/<int:id>', methods=['GET', 'POST'])
def editar(id):
    conn = sqlite3.connect(motos_db)
    cursor = conn.cursor()

    if request.method == 'POST':
        modelo = request.form['modelo']
        marca = request.form['marca']
        ano = request.form['ano']
        valor = request.form['valor']

            

        imagens_files = request.files.getlist('imagens')
        novas_imagens = []

        for imagem in imagens_files:
            if imagem and imagem.filename != '':
                filename = secure_filename(imagem.filename)
                imagem.save(os.path.join(app.config['UPLOAD_FOLDER'], filename))
                novas_imagens.append(filename)
                

        # Recuperar imagens antigas
        cursor.execute("SELECT imagem FROM motos WHERE id=?", (id,))
        resultado = cursor.fetchone()
        imagens_anteriores = resultado[0].split(';') if resultado and resultado[0] else []

        # Combinar imagens antigas com novas
        todas_imagens = imagens_anteriores + novas_imagens
        imagens_str = ';'.join(todas_imagens)

        cursor.execute("UPDATE motos SET modelo=?, marca=?, ano=?, valor=?, imagem=? WHERE id=?", (modelo, marca, ano, valor, imagens_str, id))

        conn.commit()
        conn.close()
        return redirect('/painel')

    cursor.execute("SELECT * FROM motos WHERE id=?", (id,))
    moto = cursor.fetchone()
    conn.close()
    return render_template('editar.html', moto=moto)

@app.route('/remover-imagem/<int:id>')
def remover_imagem(id):
    imagem_remover = request.args.get('imagem')
    if not imagem_remover:
        return redirect(f'/editar/{id}')

    conn = sqlite3.connect(motos_db)
    cursor = conn.cursor()

    # Buscar imagens atuais
    cursor.execute("SELECT imagem FROM motos WHERE id=?", (id,))
    resultado = cursor.fetchone()
    imagens_atuais = resultado[0].split(';') if resultado and resultado[0] else []

    # Remover imagem da lista
    imagens_atuais = [img for img in imagens_atuais if img != imagem_remover]

    # Atualizar banco
    nova_str = ';'.join(imagens_atuais)
    cursor.execute("UPDATE motos SET imagem=? WHERE id=?", (nova_str, id))
    conn.commit()
    conn.close()

    # Remover arquivo físico
    caminho_imagem = os.path.join(app.config['UPLOAD_FOLDER'], imagem_remover)
    if os.path.exists(caminho_imagem):
        os.remove(caminho_imagem)

    return redirect(f'/editar/{id}')



@app.route('/consorcios')
def consorcios_publico():
    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consorcios")
    consorcios_raw = cursor.fetchall()
    


    consorcios = []
    for c in consorcios_raw:
        cursor.execute("SELECT nome_arquivo FROM imagens_consorcio WHERE consorcio_id = ?", (c[0],))
        imagens = [i[0] for i in cursor.fetchall()]
        consorcios.append({
            'id': c[0],
            'descricao': c[2],
            'imagem_principal': c[1] if c[1] else 'default.jpg',  # usa o campo 'imagem' da tabela consorcios
            'imagens': imagens
        })

    conn.close()
    return render_template('consorcios_publico.html', consorcios=consorcios)


@app.route('/upload-consorcio', methods=['POST'])
def upload_consorcio():
    descricao = request.form['descricao']
    imagens = request.files.getlist('imagens')

    if not imagens or imagens[0].filename == '':
        return "Erro: pelo menos uma imagem é obrigatória", 400

    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()

    # Salvar imagem principal
    imagem_principal = secure_filename(imagens[0].filename)
    imagens[0].save(os.path.join('static/consorcios', imagem_principal))

    cursor.execute("INSERT INTO consorcios (imagem, descricao) VALUES (?, ?)", (imagem_principal, descricao))
    consorcio_id = cursor.lastrowid

    # Salvar todas as imagens
    for imagem in imagens[1:]:  # começa da segunda
        nome_arquivo = secure_filename(imagem.filename)
        imagem.save(os.path.join('static/consorcios', nome_arquivo))
        cursor.execute("INSERT INTO imagens_consorcio (consorcio_id, nome_arquivo) VALUES (?, ?)", (consorcio_id, nome_arquivo))

    conn.commit()
    conn.close()
    return redirect('/painel-consorcios')

@app.route('/editar-consorcio/<int:id>')
def editar_consorcio(id):
    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM consorcios WHERE id = ?", (id,))
    consorcio_raw = cursor.fetchone()
    consorcio = {
    'id': consorcio_raw[0],
    'descricao': consorcio_raw[2]  # índice 2 porque a coluna 1 é 'imagem'
}

    cursor.execute("SELECT nome_arquivo FROM imagens_consorcio WHERE consorcio_id = ?", (id,))
    imagens = [{'nome': i[0], 'id': i[1]} for i in cursor.fetchall()]
    conn.close()

    return render_template('editar_consorcio.html', consorcio=consorcio, imagens=imagens)

@app.route('/editar-consorcio/<int:id>', methods=['POST'])
def salvar_edicao_consorcio(id):
    nova_descricao = request.form['descricao']
    novas_imagens = request.files.getlist('novas_imagens')

    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()

    cursor.execute("UPDATE consorcios SET descricao = ? WHERE id = ?", (nova_descricao, id))

    if novas_imagens:
        for i, imagem in enumerate(novas_imagens):
            nome_arquivo = secure_filename(imagem.filename)
            caminho = os.path.join(app.static_folder, 'consorcios', nome_arquivo)
            imagem.save(caminho)

            cursor.execute("INSERT INTO imagens_consorcio (consorcio_id, nome_arquivo) VALUES (?, ?)", (id, nome_arquivo))

            if i == 0:
                cursor.execute("UPDATE consorcios SET imagem = ? WHERE id = ?", (nome_arquivo, id))

    conn.commit()
    conn.close()
    return redirect('/painel-consorcios')


@app.route('/excluir-imagem/<int:id>', methods=['POST'])
def excluir_imagem(id):
    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()

    cursor.execute("SELECT nome_arquivo, consorcio_id FROM imagens_consorcio WHERE id = ?", (id,))
    imagem = cursor.fetchone()

    if imagem:
        caminho = os.path.join('static/consorcios', imagem[0])
        if os.path.exists(caminho):
            os.remove(caminho)
        cursor.execute("DELETE FROM imagens_consorcio WHERE id = ?", (id,))
        conn.commit()

    conn.close()
    return redirect(f'/editar-consorcio/{imagem[1]}')

@app.route('/excluir-consorcio/<int:id>')
def excluir_consorcio(id):
    if 'usuario' not in session:
        return redirect(url_for('login', next='painel-consorcios'))

    conn = sqlite3.connect(consorcios_db)
    cursor = conn.cursor()

    # Buscar imagens associadas
    cursor.execute("SELECT nome_arquivo FROM imagens_consorcio WHERE consorcio_id = ?", (id,))
    imagens = cursor.fetchall()
    for img in imagens:
        caminho = os.path.join('static/consorcios', img[0])
        if os.path.exists(caminho):
            os.remove(caminho)

    # Excluir registros
    cursor.execute("DELETE FROM imagens_consorcio WHERE consorcio_id = ?", (id,))
    cursor.execute("DELETE FROM consorcios WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return redirect(url_for('painel_consorcios'))


@app.route('/teste')
def teste():
    return "<h1>Funcionando no Replit!</h1>"


if __name__ == '__main__':
    init_consorcios_db()
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))





