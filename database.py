import sqlite3

def conectar():
    conn = sqlite3.connect("inventario.db")
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def crear_tablas():
    conn = conectar()

    # ── Tabla productos (una fila por producto) ───────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            sku          TEXT NOT NULL UNIQUE,
            nombre       TEXT NOT NULL,
            categoria    TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            precio       REAL DEFAULT 0,
            barcode      TEXT,
            observaciones TEXT
        )
    """)

    # ── Tabla lotes (una fila por lote de cada producto) ──────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS lotes (
            id           INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id  INTEGER NOT NULL,
            numero_lote  TEXT NOT NULL,
            trazabilidad TEXT,
            caducidad    TEXT,
            stock        INTEGER DEFAULT 0,
            FOREIGN KEY (producto_id) REFERENCES productos(id)
        )
    """)

    # ── Tabla movimientos ─────────────────────────────────────
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            producto_id INTEGER NOT NULL,
            lote_id     INTEGER NOT NULL,
            tipo        TEXT NOT NULL,
            categoria   TEXT NOT NULL,
            cantidad    INTEGER NOT NULL,
            fecha       TEXT NOT NULL,
            nota        TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (lote_id)     REFERENCES lotes(id)
        )
    """)

    conn.commit()
    conn.close()