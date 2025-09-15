import sqlite3

conn = sqlite3.connect('consorcios.db')
cursor = conn.cursor()

# Criar a tabela de imagens se ainda não existir
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
print("Tabela de imagens criada com sucesso!")