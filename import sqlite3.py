import sqlite3

conn = sqlite3.connect('motos.db')
cursor = conn.cursor()

cursor.execute("SELECT id, modelo, imagem FROM motos")
motos = cursor.fetchall()

for moto in motos:
    print(f"ID: {moto[0]}, Modelo: {moto[1]}, Imagens: {moto[2]}")

conn.close()