"""
Importa inventarioAbril.csv al nuevo esquema:
  - productos: una fila por SKU único
  - lotes: una fila por fila del CSV (cada fila es un lote)
"""
import csv
import sqlite3

CSV_FILE = 'inventarioAbril.csv'
DB_FILE  = 'inventario.db'

try:
    # ── Leer CSV ──────────────────────────────────────────────
    with open(CSV_FILE, 'r', encoding='latin-1') as fin:
        dr = csv.DictReader(fin)
        filas = list(dr)
    print(f"{len(filas)} filas leídas del CSV")

    # ── Conectar y crear tablas ───────────────────────────────
    conn = sqlite3.connect(DB_FILE)
    conn.execute("PRAGMA foreign_keys = ON")
    cur  = conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            sku           TEXT NOT NULL UNIQUE,
            nombre        TEXT NOT NULL,
            categoria     TEXT NOT NULL,
            presentacion  TEXT NOT NULL,
            precio        REAL DEFAULT 0,
            barcode       TEXT,
            observaciones TEXT
        )
    """)
    cur.execute("""
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
    cur.execute("""
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

    # ── Insertar filas ────────────────────────────────────────
    productos_insertados = 0
    lotes_insertados     = 0
    errores              = []

    for idx, row in enumerate(filas, start=2):  # fila 2 = primera de datos
        try:
            sku    = str(row['Codigo']).strip()
            nombre = row['Nombre del producto'].strip()
            precio = float(str(row['Precio']).replace(',', '.') or 0)
            stock  = int(str(row['Cantidad en almacen']).replace(',', '') or 0)

            # ── Producto: insertar solo si el SKU no existe ───
            cur.execute("SELECT id FROM productos WHERE sku=?", (sku,))
            prod = cur.fetchone()
            if prod is None:
                cur.execute("""
                    INSERT INTO productos
                        (sku, nombre, categoria, presentacion, precio, barcode, observaciones)
                    VALUES (?,?,?,?,?,?,?)
                """, (
                    sku, nombre,
                    row['Categoria'].strip(),
                    row['Presentacion'].strip(),
                    precio,
                    '',  # barcode no está en el CSV
                    row['Observaciones'].strip()
                ))
                producto_id = cur.lastrowid
                productos_insertados += 1
            else:
                producto_id = prod[0]

            # ── Lote ──────────────────────────────────────────
            numero_lote  = str(row['Lotes']).strip()
            trazabilidad = str(row['Trazabilidad']).strip()
            caducidad    = str(row['Fecha de caducidad']).strip()

            cur.execute("""
                INSERT INTO lotes (producto_id, numero_lote, trazabilidad, caducidad, stock)
                VALUES (?,?,?,?,?)
            """, (producto_id, numero_lote, trazabilidad, caducidad, stock))
            lotes_insertados += 1

        except Exception as e:
            errores.append(f"Fila {idx}: {e} → {dict(row)}")

    conn.commit()

    # ── Resumen ───────────────────────────────────────────────
    print(f"\n✔ Productos insertados/encontrados: {productos_insertados} nuevos")
    print(f"✔ Lotes insertados:                 {lotes_insertados}")

    if errores:
        print(f"\n⚠ {len(errores)} errores:")
        for e in errores:
            print(" ", e)
    else:
        print("\n✔ Sin errores.")

    # Verificación rápida
    total_p = cur.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    total_l = cur.execute("SELECT COUNT(*) FROM lotes").fetchone()[0]
    print(f"\nBD final → productos: {total_p}, lotes: {total_l}")

except Exception as err:
    print("Error general:", err)

finally:
    try:
        conn.close()
        print("Conexión cerrada.")
    except Exception:
        pass