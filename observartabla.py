import sqlite3

sqliteConnection = sqlite3.connect('inventario.db')
cursor = sqliteConnection.cursor()
#añadir columnas para observar con la base de datos que ya se tiene
cursor.execute("""
                ALTER TABLE productos
                ADD COLUMN categoria TEXT""")
cursor.execute("""
                ALTER TABLE movimientos
                ADD COLUMN categoria TEXT""")

result = cursor.fetchall()
print(result)

#commit y cerrar conexión
sqliteConnection.commit()
cursor.close()