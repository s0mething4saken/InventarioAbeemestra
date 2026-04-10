import sqlite3

sqliteConnection = sqlite3.connect('inventario.db')
cursor = sqliteConnection.cursor()

cursor.execute("select * from productos;")

result = cursor.fetchall()
print(result)

#commit y cerrar conexión
sqliteConnection.commit()
cursor.close()