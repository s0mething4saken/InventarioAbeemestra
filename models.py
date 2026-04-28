from database import conectar
from datetime import datetime

# ── PRODUCTOS ────────────────────────────────────────────────
def agregar_producto(sku, nombre, presentacion, stock, observaciones, precio, caducidad, barcode):
    conn = conectar()
    conn.execute(
        "INSERT INTO productos (sku, nombre, presentacion, stock, observaciones, precio, caducidad, barcode) VALUES (?,?,?,?,?,?,?,?)",
        (sku, nombre, presentacion, stock, observaciones, precio, caducidad, barcode)
    )
    conn.commit()
    conn.close()

def obtener_productos():
    conn = conectar()
    filas = conn.execute("""
                        SELECT
                         id, sku, nombre, categoria, presentacion, stock,
                         precio, precio * stock as precio_Total, caducidad,
                         barcode, observaciones
                         FROM productos""").fetchall()
    conn.close()
    return filas

def eliminar_producto(id_producto):
    conn = conectar()
    conn.execute("DELETE FROM productos WHERE id=?", (id_producto,))
    conn.commit()
    conn.close()

# ── MOVIMIENTOS ──────────────────────────────────────────────
def registrar_movimiento(sku, producto_id, tipo, cantidad, nota=""):
    conn = conectar()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")
    conn.execute(
        "INSERT INTO movimientos (sku, producto_id, tipo, cantidad, fecha, nota) VALUES (?,?,?,?,?,?)",
        (sku, producto_id, tipo, cantidad, fecha, nota)
    )
    if tipo == "entrada":
        conn.execute("UPDATE productos SET stock = stock + ? WHERE id=? AND sku=?", (cantidad, producto_id, sku))
    elif tipo == "salida":
        conn.execute("UPDATE productos SET stock = stock - ? WHERE id=? AND sku=?", (cantidad, producto_id, sku))
    conn.commit()
    conn.close()

def obtener_movimientos():
    conn = conectar()
    filas = conn.execute("""
        SELECT p.sku, m.id, p.nombre, p.categoria, m.tipo, m.cantidad, m.fecha, m.nota
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id
        ORDER BY m.fecha DESC
    """).fetchall()
    conn.close()
    return filas

# ── DASHBOARD ────────────────────────────────────────────────
def obtener_resumen():
    conn = conectar()
    from datetime import datetime
    total_productos = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
    total_stock     = conn.execute("SELECT SUM(stock) FROM productos").fetchone()[0] or 0
    entradas_hoy    = conn.execute("""
        SELECT SUM(cantidad) FROM movimientos
        WHERE tipo='entrada' AND fecha LIKE ?
    """, (datetime.now().strftime("%Y-%m-%d") + "%",)).fetchone()[0] or 0
    salidas_hoy     = conn.execute("""
        SELECT SUM(cantidad) FROM movimientos
        WHERE tipo='salida' AND fecha LIKE ?
    """, (datetime.now().strftime("%Y-%m-%d") + "%",)).fetchone()[0] or 0
    conn.close()
    return total_productos, total_stock, entradas_hoy, salidas_hoy

def obtener_stock_por_producto():
    conn = conectar()
    filas = conn.execute("SELECT nombre, stock FROM productos ORDER BY stock DESC LIMIT 10").fetchall()
    conn.close()
    return filas