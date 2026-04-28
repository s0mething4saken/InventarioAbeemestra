import csv
import sqlite3
from datetime import datetime

try:
    #IMPORTAR EL CSV Y EXTRAER LOS DATOS
    with open('inventariocsvb.csv','r') as fin:
        dr = csv.DictReader(fin)
        info = [(i['Codigo'], i['Nombre del producto'], i['Categoria'], i['Presentacion'],i['Cantidad en almacen'],i['Observaciones'],i['Precio Producto al Publico'])for i in dr]
        print(info)
    #conexión a sqlite
    sqliteConnection = sqlite3.connect('inventario.db')
    cursor = sqliteConnection.cursor()

    #crear la tabla
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sku       INTEGER NOT NULL,
            nombre    TEXT NOT NULL,
            categoria TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            stock     INTEGER DEFAULT 0,
            precio    REAL NOT NULL,
            caducidad TEXT,
            barcode   TEXT,
            observaciones TEXT
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sku         INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            tipo       TEXT NOT NULL,  -- 'entrada' o 'salida'
            categoria TEXT NOT NULL,
            cantidad   INTEGER NOT NULL,
            fecha      TEXT NOT NULL,
            nota       TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (sku) REFERENCES productos(sku),
            FOREIGN KEY (categoria) REFERENCES productos(categoria)
        )
    """)
    #insert data 
    cursor.executemany(
        """
        INSERT INTO productos (sku, nombre, categoria, presentacion, stock, observaciones, precio)
        VALUES (?,?,?,?,?,?,?)
    """,info)

    #cursor.execute(
     #   """
      #  INSERT INTO movimientos (sku,producto_id,tipo,categoria,cantidad,fecha,nota)
        #VALUES (?,?,?,?,?,?,?)
    #"""#(1111,1111,'entrada',0000,datetime.now().strftime("%Y-%m-%d %H:%M"),"Vaciado excel")
    #) 

    #mostrar la tabla
    cursor.execute("select * from productos;")

    result = cursor.fetchall()
    print(result)

    #commit y cerrar conexión
    sqliteConnection.commit()
    cursor.close()

except sqlite3.Error as error:
    print('Error occurred - ', error)

finally:
    if sqliteConnection:
        sqliteConnection.close()
        print('SQLite Connection closed')