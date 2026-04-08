import tkinter as tk
from tkinter import ttk, messagebox
import sqlite3
from datetime import datetime
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

# ── BASE DE DATOS ────────────────────────────────────────────
def conectar():
    conn = sqlite3.connect("inventario.db")
    return conn

def crear_tablas():
    conn = conectar()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS productos (
            id        INTEGER PRIMARY KEY AUTOINCREMENT,
            sku       INTEGER NOT NULL,
            nombre    TEXT NOT NULL,
            presentacion TEXT NOT NULL,
            observaciones TEXT,
            precio    REAL,
            caducidad TEXT,
            barcode   TEXT,
            stock     INTEGER DEFAULT 0
        )
    """)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS movimientos (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            sku         INTEGER NOT NULL,
            producto_id INTEGER NOT NULL,
            tipo       TEXT NOT NULL,  -- 'entrada' o 'salida'
            cantidad   INTEGER NOT NULL,
            fecha      TEXT NOT NULL,
            nota       TEXT,
            FOREIGN KEY (producto_id) REFERENCES productos(id),
            FOREIGN KEY (sku) REFERENCES productos(sku)
        )
    """)
    conn.commit()
    conn.close()

# ── PRODUCTOS ────────────────────────────────────────────────
def agregar_producto(sku, nombre, presentacion,stock, observaciones, precio, caducidad, barcode):
    conn = conectar()
    conn.execute(
        "INSERT INTO productos (sku, nombre, presentacion,stock, observaciones, precio, caducidad, barcode) VALUES (?,?,?,?,?,?,?,?)",
        (sku, nombre, presentacion,stock, observaciones, precio, caducidad, barcode)
    ) 
    conn.commit()
    conn.close()

def obtener_productos():
    conn = conectar()
    filas = conn.execute("SELECT * FROM productos").fetchall()
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

    # registra el movimiento
    conn.execute(
        "INSERT INTO movimientos (sku, producto_id, tipo, cantidad, fecha, nota) VALUES (?,?,?,?,?,?)",
        (sku, producto_id, tipo, cantidad, fecha, nota)
    )

    # actualiza el stock según el tipo
    if tipo == "entrada":
        conn.execute("UPDATE productos SET stock = stock + ? WHERE id=? AND sku = ?", (cantidad, producto_id, sku))
    elif tipo == "salida":
        conn.execute("UPDATE productos SET stock = stock - ? WHERE id=? AND sku = ?", (cantidad, producto_id, sku))

    conn.commit()
    conn.close()

def obtener_movimientos():
    conn = conectar()
    filas = conn.execute("""
        SELECT p.sku, m.id, p.nombre, m.tipo, m.cantidad, m.fecha, m.nota
        FROM movimientos m
        JOIN productos p ON m.producto_id = p.id
        ORDER BY m.fecha DESC
    """).fetchall()
    conn.close()
    return filas

# ── VENTANA PRINCIPAL ────────────────────────────────────────
def main():
    crear_tablas()

    ventana = tk.Tk()
    ventana.title("Inventario")
    ventana.geometry("1400x750")

    notebook = ttk.Notebook(ventana)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # ── PESTAÑA 1: PRODUCTOS ─────────────────────────────────
    tab_productos = tk.Frame(notebook)
    notebook.add(tab_productos, text="Productos")

    frame_form = tk.LabelFrame(tab_productos, text="Nuevo producto", padx=10, pady=10)
    frame_form.pack(fill="x", padx=10, pady=5)

    campos = ["SKU", "Nombre","Presentación","Cantidad","Observaciones", "Precio", "Caducidad", "Código de barras"]
    entradas = {}
    for i, campo in enumerate(campos):
        tk.Label(frame_form, text=campo).grid(row=0, column=i*2)
        entrada = tk.Entry(frame_form, width=14)
        entrada.grid(row=0, column=i*2+1, padx=4)
        entradas[campo] = entrada

    cols_prod = ("ID", "SKU", "Nombre", "Presentación","Cantidad","Observaciones" "Precio", "Caducidad", "Código de barras", "Stock")
    tabla_prod = ttk.Treeview(tab_productos, columns=cols_prod, show="headings", height=14)
    for col in cols_prod:
        tabla_prod.heading(col, text=col)
        tabla_prod.column(col, width=110)
    tabla_prod.pack(fill="both", expand=True, padx=10, pady=5)

    def cargar_productos():
        for fila in tabla_prod.get_children():
            tabla_prod.delete(fila)
        for p in obtener_productos():
            tabla_prod.insert("", tk.END, values=p)

    def guardar_producto():
        agregar_producto(
            entradas["SKU"].get(), entradas["Nombre"].get(),
            entradas["Presentación"].get(),entradas["Cantidad"].get(),
            entradas["Observaciones"].get(),
            entradas["Precio"].get(), entradas["Caducidad"].get(),
            entradas["Código de barras"].get()
        )
        for e in entradas.values():
            e.delete(0, tk.END)
        cargar_productos()

    def eliminar_seleccionado():
        sel = tabla_prod.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un producto")
            return
        id_prod = tabla_prod.item(sel[0])["values"][0]
        eliminar_producto(id_prod)
        cargar_productos()

    tk.Button(frame_form, text="Agregar", command=guardar_producto, bg="#4CAF50", fg="white").grid(row=0, column=16, padx=8)
    tk.Button(tab_productos, text="Eliminar seleccionado", command=eliminar_seleccionado, bg="#f44336", fg="white").pack(pady=4)
    tab_mov = tk.Frame(notebook)
    notebook.add(tab_mov, text="Movimientos")
    # ── PESTAÑA 3: DASHBOARD ─────────────────────────────────
    # ── DATOS PARA EL DASHBOARD ──────────────────────────────────
    def obtener_resumen():
        conn = conectar()
        total_productos = conn.execute("SELECT COUNT(*) FROM productos").fetchone()[0]
        total_stock = conn.execute("SELECT SUM(stock) FROM productos").fetchone()[0] or 0
        entradas_hoy = conn.execute("""
            SELECT SUM(cantidad) FROM movimientos
            WHERE tipo='entrada' AND fecha LIKE ?
        """, (datetime.now().strftime("%Y-%m-%d") + "%",)).fetchone()[0] or 0
        salidas_hoy = conn.execute("""
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

    def obtener_movimientos_semana():
        conn = conectar()
        filas = conn.execute("""
            SELECT DATE(fecha) as dia, tipo, SUM(cantidad)
            FROM movimientos
            GROUP BY dia, tipo
            ORDER BY dia DESC LIMIT 14
        """).fetchall()
        conn.close()
        return filas

    tab_dash = tk.Frame(notebook)
    notebook.add(tab_dash, text="Dashboard")

    # --- Tarjetas de resumen arriba ---
    frame_cards = tk.Frame(tab_dash)
    frame_cards.pack(fill="x", padx=10, pady=10)

    lbl_total_prod  = tk.Label(frame_cards, text="", font=("Arial", 13), relief="groove", padx=20, pady=10)
    lbl_total_stock = tk.Label(frame_cards, text="", font=("Arial", 13), relief="groove", padx=20, pady=10)
    lbl_entradas    = tk.Label(frame_cards, text="", font=("Arial", 13), relief="groove", padx=20, pady=10, fg="green")
    lbl_salidas     = tk.Label(frame_cards, text="", font=("Arial", 13), relief="groove", padx=20, pady=10, fg="red")

    lbl_total_prod.grid(row=0, column=0, padx=8)
    lbl_total_stock.grid(row=0, column=1, padx=8)
    lbl_entradas.grid(row=0, column=2, padx=8)
    lbl_salidas.grid(row=0, column=3, padx=8)

    # --- Gráfica de barras: stock por producto ---
    fig, ax = plt.subplots(figsize=(8, 3.5))
    canvas = FigureCanvasTkAgg(fig, master=tab_dash)
    canvas.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    def actualizar_dashboard():
        total_p, total_s, ent, sal = obtener_resumen()
        lbl_total_prod.config(text=f"Productos: {total_p}")
        lbl_total_stock.config(text=f"Stock total: {total_s}")
        lbl_entradas.config(text=f"Entradas hoy: {ent}")
        lbl_salidas.config(text=f"Salidas hoy: {sal}")

        datos = obtener_stock_por_producto()
        ax.clear()
        if datos:
            nombres = [d[0][:15] for d in datos]  # recorta nombres largos
            stocks  = [d[1] for d in datos]
            colores = ["#4CAF50" if s > 5 else "#f44336" for s in stocks]
            ax.barh(nombres, stocks, color=colores)
            ax.set_xlabel("Stock")
            ax.set_title("Stock por producto (verde = ok, rojo = bajo)")
            ax.invert_yaxis()
        else:
            ax.text(0.5, 0.5, "Sin datos aún", ha="center", va="center", transform=ax.transAxes)

        fig.tight_layout()
        canvas.draw()

    tk.Button(tab_dash, text="Actualizar dashboard", command=actualizar_dashboard, bg="#673AB7", fg="white").pack(pady=4)
    actualizar_dashboard()  # carga al iniciar

    frame_mov = tk.LabelFrame(tab_mov, text="Registrar movimiento", padx=10, pady=10)
    frame_mov.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_mov, text="Sku").grid(row=0, column=0)
    entry_sku = tk.Entry(frame_mov, width=8)
    entry_sku.grid(row=0, column=1, padx=4)

    tk.Label(frame_mov, text="Producto ID").grid(row=0, column=2)
    entry_pid = tk.Entry(frame_mov, width=8)
    entry_pid.grid(row=0, column=3, padx=4)

    tk.Label(frame_mov, text="Tipo").grid(row=0, column=4)
    tipo_var = tk.StringVar(value="entrada")
    ttk.Combobox(frame_mov, textvariable=tipo_var, values=["entrada", "salida"], width=10).grid(row=0, column=5, padx=4)

    tk.Label(frame_mov, text="Cantidad").grid(row=0, column=6)
    entry_cant = tk.Entry(frame_mov, width=8)
    entry_cant.grid(row=0, column=7, padx=4)

    tk.Label(frame_mov, text="Nota").grid(row=0, column=8)
    entry_nota = tk.Entry(frame_mov, width=20)
    entry_nota.grid(row=0, column=9, padx=4)

    cols_mov = ("Sku","ID", "Producto", "Tipo", "Cantidad", "Fecha", "Nota")
    tabla_mov = ttk.Treeview(tab_mov, columns=cols_mov, show="headings", height=16)
    for col in cols_mov:
        tabla_mov.heading(col, text=col)
        tabla_mov.column(col, width=130)
    tabla_mov.pack(fill="both", expand=True, padx=10, pady=5)

    def cargar_movimientos():
        for fila in tabla_mov.get_children():
            tabla_mov.delete(fila)
        for m in obtener_movimientos():
            tabla_mov.insert("", tk.END, values=m)

    def guardar_movimiento():
        try:
            pid = int(entry_pid.get())
            cant = int(entry_cant.get())
        except ValueError:
            messagebox.showerror("Error", "ID y cantidad deben ser números")
            return
        registrar_movimiento(entry_sku.get(), pid, tipo_var.get(), cant, entry_nota.get())
        entry_sku.delete(0, tk.END)
        entry_pid.delete(0, tk.END)
        entry_cant.delete(0, tk.END)
        entry_nota.delete(0, tk.END)
        cargar_movimientos()
        cargar_productos()  # refresca el stock en la otra pestaña
    

    tk.Button(frame_mov, text="Registrar", command=guardar_movimiento, bg="#2196F3", fg="white").grid(row=0, column=11, padx=8)

    cargar_productos()
    cargar_movimientos()
    ventana.mainloop()


main()