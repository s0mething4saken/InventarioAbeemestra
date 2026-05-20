from database import conectar
from datetime import datetime

# ════════════════════════════════════════════════════════
# PRODUCTOS
# ════════════════════════════════════════════════════════

def agregar_producto(sku, nombre, categoria, presentacion,
                     precio=0, barcode="", observaciones=""):
    conn = conectar()
    conn.execute("""
        INSERT INTO productos (sku, nombre, categoria, presentacion,
                               precio, barcode, observaciones)
        VALUES (?,?,?,?,?,?,?)
    """, (sku, nombre, categoria, presentacion,
          float(precio or 0), barcode, observaciones))
    conn.commit()
    conn.close()


def obtener_productos():
    """
    Devuelve una fila por producto con el stock total sumado de sus lotes.
    Índices:
      0=id, 1=sku, 2=nombre, 3=categoria, 4=presentacion,
      5=stock_total, 6=precio, 7=precio_total, 8=barcode, 9=observaciones
    """
    conn = conectar()
    filas = conn.execute("""
        SELECT
            p.id,                                        -- 0
            p.sku,                                       -- 1
            p.nombre,                                    -- 2
            p.categoria,                                 -- 3
            p.presentacion,                              -- 4
            COALESCE(SUM(l.stock), 0)   AS stock_total,  -- 5
            p.precio,                                    -- 6
            ROUND(p.precio * COALESCE(SUM(l.stock), 0), 2) AS precio_total, -- 7
            p.barcode,                                   -- 8
            p.observaciones                              -- 9
        FROM productos p
        LEFT JOIN lotes l ON l.producto_id = p.id
        GROUP BY p.id
        ORDER BY p.id
    """).fetchall()
    conn.close()
    return filas


def eliminar_producto(producto_id):
    conn = conectar()
    conn.execute("DELETE FROM lotes    WHERE producto_id=?", (producto_id,))
    conn.execute("DELETE FROM productos WHERE id=?",         (producto_id,))
    conn.commit()
    conn.close()


def actualizar_producto(producto_id, precio, barcode, observaciones):
    conn = conectar()
    conn.execute("""
        UPDATE productos SET precio=?, barcode=?, observaciones=?
        WHERE id=?
    """, (float(precio or 0), barcode, observaciones, producto_id))
    conn.commit()
    conn.close()


# ════════════════════════════════════════════════════════
# LOTES
# ════════════════════════════════════════════════════════

def agregar_lote(producto_id, numero_lote, trazabilidad="",
                 caducidad="", stock=0):
    conn = conectar()
    conn.execute("""
        INSERT INTO lotes (producto_id, numero_lote, trazabilidad, caducidad, stock)
        VALUES (?,?,?,?,?)
    """, (producto_id, numero_lote, trazabilidad, caducidad, int(stock or 0)))
    conn.commit()
    conn.close()


def obtener_lotes_por_producto(producto_id):
    """
    Índices: 0=id, 1=numero_lote, 2=trazabilidad, 3=caducidad, 4=stock
    """
    conn = conectar()
    filas = conn.execute("""
        SELECT id, numero_lote, trazabilidad, caducidad, stock
        FROM lotes
        WHERE producto_id=?
        ORDER BY numero_lote
    """, (producto_id,)).fetchall()
    conn.close()
    return filas


def actualizar_lote(lote_id, numero_lote, trazabilidad, caducidad, stock):
    conn = conectar()
    conn.execute("""
        UPDATE lotes SET numero_lote=?, trazabilidad=?, caducidad=?, stock=?
        WHERE id=?
    """, (numero_lote, trazabilidad, caducidad, int(stock or 0), lote_id))
    conn.commit()
    conn.close()


def eliminar_lote(lote_id):
    conn = conectar()
    conn.execute("DELETE FROM lotes WHERE id=?", (lote_id,))
    conn.commit()
    conn.close()


def obtener_lotes_todos():
    """Para autocomplete en movimientos: devuelve todos los lotes con su SKU."""
    conn = conectar()
    filas = conn.execute("""
        SELECT l.id, p.sku, p.id, p.nombre, p.categoria,
               l.trazabilidad, l.stock
        FROM lotes l
        JOIN productos p ON l.producto_id = p.id
        ORDER BY p.sku
    """).fetchall()
    conn.close()
    return filas


# ════════════════════════════════════════════════════════
# MOVIMIENTOS
# ════════════════════════════════════════════════════════

def buscar_lote_por_sku_trazabilidad(sku, trazabilidad):
    """
    Valida SKU + trazabilidad.
    Retorna (lote_row, error_msg).
    lote_row: id[0], producto_id[1], nombre[2], categoria[3], stock[4], trazabilidad[5]
    """
    conn = conectar()
    prod = conn.execute(
        "SELECT id, nombre, categoria FROM productos WHERE sku=?", (str(sku),)
    ).fetchone()

    if prod is None:
        conn.close()
        return None, f"SKU '{sku}' no existe en el inventario."

    lote = conn.execute("""
        SELECT l.id, l.producto_id, p.nombre, p.categoria, l.stock, l.trazabilidad
        FROM lotes l
        JOIN productos p ON l.producto_id = p.id
        WHERE p.sku=? AND l.trazabilidad=?
    """, (str(sku), str(trazabilidad))).fetchone()
    conn.close()

    if lote is None:
        return None, (
            f"La trazabilidad '{trazabilidad}' no existe para el SKU {sku}."
        )
    return lote, None


def registrar_movimiento(sku, trazabilidad, tipo, cantidad, nota=""):
    """Retorna (éxito: bool, mensaje: str)."""
    lote, error = buscar_lote_por_sku_trazabilidad(sku, trazabilidad)
    if error:
        return False, error

    lote_id      = lote[0]
    producto_id  = lote[1]
    categoria    = lote[3]
    stock_actual = int(lote[4] or 0)

    if tipo == "salida" and stock_actual - cantidad < 0:
        return False, (
            f"Stock insuficiente (trazabilidad {trazabilidad}). "
            f"Stock actual: {stock_actual}, solicitado: {cantidad}."
        )

    conn = conectar()
    fecha = datetime.now().strftime("%Y-%m-%d %H:%M")

    conn.execute("""
        INSERT INTO movimientos (producto_id, lote_id, tipo, categoria, cantidad, fecha, nota)
        VALUES (?,?,?,?,?,?,?)
    """, (producto_id, lote_id, tipo, categoria, cantidad, fecha, nota))

    if tipo == "entrada":
        conn.execute("UPDATE lotes SET stock = stock + ? WHERE id=?",
                     (cantidad, lote_id))
    elif tipo == "salida":
        conn.execute("UPDATE lotes SET stock = stock - ? WHERE id=?",
                     (cantidad, lote_id))
        # Si el lote quedó en 0, eliminarlo automáticamente
        stock_restante = conn.execute(
            "SELECT stock FROM lotes WHERE id=?", (lote_id,)
        ).fetchone()[0]
        if stock_restante == 0:
            conn.execute("DELETE FROM lotes WHERE id=?", (lote_id,))

    conn.commit()
    conn.close()
    return True, "Movimiento registrado correctamente."


def obtener_movimientos():
    """
    Índices: sku[0], trazabilidad[1], nombre[2], categoria[3],
             tipo[4], cantidad[5], fecha[6], nota[7]
    """
    conn = conectar()
    filas = conn.execute("""
        SELECT p.sku, l.trazabilidad, p.nombre, p.categoria,
               m.tipo, m.cantidad, m.fecha, m.nota
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id
        JOIN lotes     l ON m.lote_id     = l.id
        ORDER BY m.fecha DESC
    """).fetchall()
    conn.close()
    return filas


# ════════════════════════════════════════════════════════
# DASHBOARD
# ════════════════════════════════════════════════════════

def obtener_resumen():
    conn = conectar()
    total_productos = conn.execute(
        "SELECT COUNT(*) FROM productos").fetchone()[0]
    total_stock = conn.execute(
        "SELECT COALESCE(SUM(stock),0) FROM lotes").fetchone()[0]
    hoy = datetime.now().strftime("%Y-%m-%d") + "%"
    entradas_hoy = conn.execute(
        "SELECT COALESCE(SUM(cantidad),0) FROM movimientos WHERE tipo='entrada' AND fecha LIKE ?",
        (hoy,)).fetchone()[0]
    salidas_hoy = conn.execute(
        "SELECT COALESCE(SUM(cantidad),0) FROM movimientos WHERE tipo='salida' AND fecha LIKE ?",
        (hoy,)).fetchone()[0]
    conn.close()
    return total_productos, total_stock, entradas_hoy, salidas_hoy


def obtener_stock_por_producto():
    conn = conectar()
    filas = conn.execute("""
        SELECT p.nombre, COALESCE(SUM(l.stock),0) AS stock_total
        FROM productos p
        LEFT JOIN lotes l ON l.producto_id = p.id
        GROUP BY p.id
        ORDER BY stock_total DESC
        LIMIT 10
    """).fetchall()
    conn.close()
    return filas