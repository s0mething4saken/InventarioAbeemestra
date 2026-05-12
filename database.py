import sqlite3
 
def conectar():
    conn = sqlite3.connect("inventario.db")
    return conn
 
def crear_tablas():
    conn = conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sku           INTEGER NOT NULL,
            nombre        TEXT NOT NULL,
            categoria     TEXT NOT NULL,
            presentacion  TEXT NOT NULL,
            observaciones TEXT,
            precio        REAL,
            caducidad     TEXT,
            barcode       TEXT,
            stock         INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            sku         INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            tipo        TEXT NOT NULL,
            categoria   TEXT NOT NULL,
            cantidad    INTEGER NOT NULL,
            fecha       TEXT NOT NULL,
            nota        TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (sku) REFERENCES productos(sku)
        )
    """)
 
    # ── Columnas nuevas: migración segura (no falla si ya existen) ──
    for columna, definicion in [
        ("trazabilidad",   "TEXT"),
        ("cantidad_lotes", "INTEGER DEFAULT 0"),
    ]:
        try:
            conn.execute(f"ALTER TABLE productos ADD COLUMN {columna} {definicion}")
        except Exception:
            pass  # Ya existe, se ignora
 
    conn.commit()
    conn.close()