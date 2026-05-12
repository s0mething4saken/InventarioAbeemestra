import sqlite3
import shutil
from datetime import datetime

# ── Respaldo por seguridad ───────────────────────────────────
shutil.copy("inventario.db", f"inventario_respaldo_{datetime.now().strftime('%Y%m%d_%H%M%S')}.db")
print("Respaldo creado.")

conn = sqlite3.connect("inventario.db")

# ── 1. Agrega columna categoria a productos si no existe ─────
try:
    conn.execute("ALTER TABLE productos ADD COLUMN categoria TEXT NOT NULL DEFAULT 'Sin categoría'")
    conn.commit()
    print("Columna categoria agregada a productos.")
except Exception as e:
    print(f"Columna categoria ya existe o error: {e}")

# ── 2. Recrea la tabla movimientos limpia ────────────────────
conn.execute("ALTER TABLE movimientos RENAME TO movimientos_old")
conn.execute("""
    CREATE TABLE movimientos (
        id          INTEGER PRIMARY KEY AUTOINCREMENT,
        sku         INTEGER NOT NULL,
        producto_id INTEGER NOT NULL,
        tipo        TEXT NOT NULL,
        categoria   TEXT NOT NULL DEFAULT 'Sin categoría',
        cantidad    INTEGER NOT NULL,
        fecha       TEXT NOT NULL,
        nota        TEXT,
        FOREIGN KEY (producto_id) REFERENCES productos(id),
        FOREIGN KEY (sku) REFERENCES productos(sku)
    )
""")

# ── 3. Copia los movimientos viejos a la nueva tabla ─────────
conn.execute("""
    INSERT INTO movimientos (id, sku, producto_id, tipo, categoria, cantidad, fecha, nota)
    SELECT
        m.id, m.sku, m.producto_id, m.tipo,
        COALESCE(p.categoria, 'Sin categoría'),
        m.cantidad, m.fecha, m.nota
    FROM movimientos_old m
    LEFT JOIN productos p ON m.producto_id = p.id
""")
conn.commit()

# ── 4. Elimina la tabla vieja ────────────────────────────────
conn.execute("DROP TABLE movimientos_old")
conn.commit()

conn.close()
print("Migración completada. Ya puedes correr main.py.")