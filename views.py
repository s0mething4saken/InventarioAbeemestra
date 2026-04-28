import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from models import (
    agregar_producto, obtener_productos, eliminar_producto,
    registrar_movimiento, obtener_movimientos,
    obtener_resumen, obtener_stock_por_producto
)

def construir_ventana():
    ventana = tk.Tk()
    ventana.title("Inventario")
    ventana.state("zoomed")

    #ícono de programa
    ventana.iconbitmap("icono.ico")

    # ── ESTILOS GLOBALES─────────────────────────────────────
    fuente = ("Arial", 12)  #tamaño de letra que se desea observar

    ventana.option_add("*Font", fuente)  # aplica a todos los widgets tk

    estilo = ttk.Style()
    estilo.configure(".", font=fuente)                  # todos los widgets ttk
    estilo.configure("Treeview", font=fuente, rowheight=28)  # tabla
    estilo.configure("Treeview.Heading", font=("Arial", 12, "bold"))  # encabezados tabla
    estilo.configure("TCombobox", font=fuente)
    estilo.configure("TNotebook.Tab", font=fuente)      # pestañas

    notebook = ttk.Notebook(ventana)

    notebook = ttk.Notebook(ventana)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # ── TAB PRODUCTOS ────────────────────────────────────────
    tab_productos = tk.Frame(notebook)
    notebook.add(tab_productos, text="Productos")

    frame_form = tk.LabelFrame(tab_productos, text="Nuevo producto", padx=10, pady=10)
    frame_form.pack(fill="x", padx=10, pady=5)

    # ── BARRA DE INSERCIÓN DE PRODUCTOS ────────────────────────
    campos = ["SKU", "Nombre","Categoría","Presentación", "Cantidad", "Observaciones", "Precio", "Caducidad", "Código de barras"]
    entradas = {}
    for i, campo in enumerate(campos):
        tk.Label(frame_form, text=campo).grid(row=0, column=i*2)
        entrada = tk.Entry(frame_form, width=10)
        entrada.grid(row=0, column=i*2+1, padx=4)
        entradas[campo] = entrada
    
    # ── TABLA DE VISTA DE PRODUCTOS ────────────────────────
    cols_prod = ("ID", "SKU", "Nombre","Categoría", "Presentación", "Stock", "Precio Unidad","Precio total" ,"Caducidad", "Código de barras", "Observaciones")
    tabla_prod = ttk.Treeview(tab_productos, columns=cols_prod, show="headings", height=14)
    #MODIFICACIÓN DE TAMAÑOS DE COLUMNAS INDEPENDIENTES
    anchos = {
        "ID": 40,
        "SKU": 50,
        "Nombre": 160,
        "Categoría":100,
        "Presentación": 100,
        "Stock": 50,
        "Precio Unidad": 100,
        "Precio total": 80,
        "Caducidad": 100,
        "Código de barras": 130,
        "Observaciones": 180
    }
    
    justificaciones = {
        "ID": "center",
        "SKU": "center",
        "Nombre": "w",
        "Categoría": "center",
        "Presentación": "center",
        "Stock": "center",
        "Precio Unidad": "center",
        "Precio total": "center",
        "Caducidad": "center",
        "Código de barras": "center",
        "Observaciones": "w"
    }

    for col in cols_prod:
        tabla_prod.heading(col, text=col, anchor=justificaciones.get(col))
        tabla_prod.column(col, width=anchos.get(col, 110), anchor=justificaciones.get(col))
    tabla_prod.pack(fill="both", expand=True, padx=10, pady=5)

    #──Declaración de colores para categorías ──────────────────────────────────────
    colores_categoria = {
        "Miel":              "#fff5a0",
        "Derivados Miel":    "#ffdf80",
        "Dulceria":          "#ffcba0",
        "Derivados Colmena": "#b8ffb0",
        "Embellece":         "#f0b0ff",
        "Kits":              "#dfffb0"
    }

    #──Declaración de colores para categorías ──────────────────────────────────────
    for categoria, color in colores_categoria.items():
        tag = categoria.lower().replace(" ", "_")
        tabla_prod.tag_configure(tag, background=color)

    def cargar_productos():
        for fila in tabla_prod.get_children():
            tabla_prod.delete(fila)
        for p in obtener_productos():
            categoria = str(p[3])
            tag = categoria.lower().replace(" ", "_")
            tabla_prod.insert("", tk.END, values=p, tags=(tag,))

    def guardar_producto():
        agregar_producto(
            entradas["SKU"].get(), entradas["Nombre"].get(), entradas["Categoría"].get(),
            entradas["Presentación"].get(), int (entradas["Cantidad"].get() or 0),
            entradas["Observaciones"].get(), float (entradas["Precio"].get() or 0),
            entradas["Caducidad"].get(), entradas["Código de barras"].get()
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
    
    #── Botones agregar y eliminar productos ──────────────────────────────────────
    tk.Button(frame_form, text="Agregar", command=guardar_producto, bg="#4CAF50", fg="white").grid(row=0, column=20, padx=8)
    tk.Button(tab_productos, text="Eliminar seleccionado", command=eliminar_seleccionado, bg="#f44336", fg="white").pack(pady=4)

    # ── TAB MOVIMIENTOS ──────────────────────────────────────
    tab_mov = tk.Frame(notebook)
    notebook.add(tab_mov, text="Movimientos")

    #──Frame de registro de movimientos ──────────────────────────────────────
    frame_mov = tk.LabelFrame(tab_mov, text="Registrar movimiento", padx=10, pady=10)
    frame_mov.pack(fill="x", padx=10, pady=5)

    #──Text box para registrar SKU ──────────────────────────────────────
    tk.Label(frame_mov, text="SKU").grid(row=0, column=0)
    entry_sku = tk.Entry(frame_mov, width=8)
    entry_sku.grid(row=0, column=1, padx=4)

    #──Text box para registrar ID producto ──────────────────────────────────────
    tk.Label(frame_mov, text="Producto ID").grid(row=0, column=2)
    entry_pid = tk.Entry(frame_mov, width=8)
    entry_pid.grid(row=0, column=3, padx=4)

    #──Text box para registrar categoría ──────────────────────────────────────
    tk.Label(frame_mov, text="Categoría").grid(row=0, column=4)
    entry_pid = tk.Entry(frame_mov, width=8)
    entry_pid.grid(row=0, column=5, padx=4)

    #──Text box para registrar Tipo (entrada/salida) ──────────────────────────────────────
    tk.Label(frame_mov, text="Tipo").grid(row=0, column=6)
    tipo_var = tk.StringVar(value="entrada")
    ttk.Combobox(frame_mov, textvariable=tipo_var, values=["entrada", "salida"], width=10).grid(row=0, column=7, padx=4)

    #──Text box para registrar Cantidad ──────────────────────────────────────
    tk.Label(frame_mov, text="Cantidad").grid(row=0, column=8)
    entry_cant = tk.Entry(frame_mov, width=8)
    entry_cant.grid(row=0, column=9, padx=4)

    #──Text box para registrar Nota ──────────────────────────────────────
    tk.Label(frame_mov, text="Nota").grid(row=0, column=10)
    entry_nota = tk.Entry(frame_mov, width=20)
    entry_nota.grid(row=0, column=11, padx=4)

    #──Columnas de tabla de movimientos ──────────────────────────────────────
    cols_mov = ("SKU", "ID", "Producto", "Categoria", "Tipo", "Cantidad", "Fecha", "Nota")
    tabla_mov = ttk.Treeview(tab_mov, columns=cols_mov, show="headings", height=16)
    for col in cols_mov:
        tabla_mov.heading(col, text=col)
        tabla_mov.column(col, width=130, anchor = "c")
    tabla_mov.pack(fill="both", expand=True, padx=10, pady=5)

    def cargar_movimientos():
        for fila in tabla_mov.get_children():
            tabla_mov.delete(fila)
        for m in obtener_movimientos():
            tabla_mov.insert("", tk.END, values=m)

    def guardar_movimiento():
        try:
            pid  = int(entry_pid.get())
            cant = int(entry_cant.get())
        except ValueError:
            messagebox.showerror("Error", "ID y cantidad deben ser números")
            return
        registrar_movimiento(entry_sku.get(), pid, tipo_var.get(), cant, entry_nota.get())
        for e in [entry_sku, entry_pid, entry_cant, entry_nota]:
            e.delete(0, tk.END)
        cargar_movimientos()
        cargar_productos()
    
    #──Botón para registrar movimiento ──────────────────────────────────────
    tk.Button(frame_mov, text="Registrar", command=guardar_movimiento, bg="#2196F3", fg="white").grid(row=0, column=13, padx=8)

    # ── TAB DASHBOARD ────────────────────────────────────────
    tab_dash = tk.Frame(notebook)
    notebook.add(tab_dash, text="Dashboard")

    frame_cards = tk.Frame(tab_dash)
    frame_cards.pack(fill="x", padx=10, pady=10)

    lbl_total_prod  = tk.Label(frame_cards, text="", font=("Arial", 16), relief="groove", padx=20, pady=10)
    lbl_total_stock = tk.Label(frame_cards, text="", font=("Arial", 16), relief="groove", padx=20, pady=10)
    lbl_entradas    = tk.Label(frame_cards, text="", font=("Arial", 16), relief="groove", padx=20, pady=10, fg="green")
    lbl_salidas     = tk.Label(frame_cards, text="", font=("Arial", 16), relief="groove", padx=20, pady=10, fg="red")

    lbl_total_prod.grid(row=0, column=0, padx=8)
    lbl_total_stock.grid(row=0, column=1, padx=8)
    lbl_entradas.grid(row=0, column=2, padx=8)
    lbl_salidas.grid(row=0, column=3, padx=8)

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
            nombres = [str(d[0])[:15] for d in datos]
            stocks  = [int(d[1] or 0) for d in datos]  # fuerza todo a entero
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
    actualizar_dashboard()

    cargar_productos()
    cargar_movimientos()
    ventana.mainloop()