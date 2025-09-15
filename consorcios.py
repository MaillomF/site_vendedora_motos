from flask import Flask, render_template, request, redirect, url_for, session
import sqlite3, os
from werkzeug.utils import secure_filename

app = Flask(__name__)
app.secret_key = 'sua_chave_secreta_aqui'
UPLOAD_FOLDER = 'static/consorcios'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

# 🔧 Inicializa banco
def init_db():
    conn = sqlite3.connect('consorcios.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS consorcios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            imagem TEXT NOT NULL,
            descricao TEXT
        )
    ''')
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS usuarios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL,
            senha TEXT NOT NULL
        )
    ''')
    # Cria usuário padrão
    cursor.execute("SELECT * FROM usuarios WHERE username = 'admin'")
    if not cursor.fetchone():
        cursor.execute("INSERT INTO usuarios (username, senha) VALUES (?, ?)", ('admin', '1234'))
    conn.commit()
    conn.close()

init_db()



# 🔓 Logout
@app.route('/logout')
def logout():
    session.pop('usuario', None)
    return redirect('/login')

# 🛠️ Painel administrativo
@app.route('/painel-consorcios', methods=['GET', 'POST'])
def painel_consorcios():
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('consorcios.db')
    cursor = conn.cursor()

    if request.method == 'POST':
        imagem = request.files['imagem']
        descricao = request.form.get('descricao', '')
        filename = secure_filename(imagem.filename)
        path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        imagem.save(path)
        cursor.execute("INSERT INTO consorcios (imagem, descricao) VALUES (?, ?)", (filename, descricao))
        conn.commit()

    cursor.execute("SELECT * FROM consorcios")
    consorcios = cursor.fetchall()
    conn.close()
    return render_template('painel_consorcios.html', consorcios=consorcios)

# 🗑️ Excluir imagem
@app.route('/excluir-consorcio/<int:id>', methods=['POST'])
def excluir_consorcio(id):
    if 'usuario' not in session:
        return redirect('/login')

    conn = sqlite3.connect('consorcios.db')
    cursor = conn.cursor()
    cursor.execute("SELECT imagem FROM consorcios WHERE id = ?", (id,))
    imagem = cursor.fetchone()
    if imagem:
        caminho = os.path.join(app.config['UPLOAD_FOLDER'], imagem[0])
        if os.path.exists(caminho):
            os.remove(caminho)
    cursor.execute("DELETE FROM consorcios WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return redirect('/painel-consorcios')

# 🌐 Página pública
@app.route('/consorcios')
def consorcios_publico():
    conn = sqlite3.connect('consorcios.db')
    cursor = conn.cursor()
    cursor.execute("SELECT imagem, descricao FROM consorcios")
    consorcios = cursor.fetchall()
    conn.close()
    return render_template('consorcios_publico.html', consorcios=consorcios)

if __name__ == '__main__':
    app.run(debug=True)