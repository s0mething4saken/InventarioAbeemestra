import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from models import (
    agregar_producto, obtener_productos, eliminar_producto,
    registrar_movimiento, obtener_movimientos,
    obtener_resumen, obtener_stock_por_producto,
    actualizar_producto_detalle
)

COLORES_CATEGORIA = {
    "Miel":              "#fff5a0",
    "Derivados Miel":    "#ffdf80",
    "Dulceria":          "#ffcba0",
    "Derivados Colmena": "#b8ffb0",
    "Embellece":         "#f0b0ff",
    "Kits":              "#dfffb0"
}

def construir_ventana():
    ventana = tk.Tk()
    ventana.title("Inventario")
    ventana.state("zoomed")
    try:
        ventana.iconbitmap("icono.ico")
    except Exception:
        pass

    fuente = ("Arial", 12)
    ventana.option_add("*Font", fuente)
    estilo = ttk.Style()
    estilo.configure(".", font=fuente)
    estilo.configure("Treeview", font=fuente, rowheight=28)
    estilo.configure("Treeview.Heading", font=("Arial", 12, "bold"))
    estilo.configure("TCombobox", font=fuente)
    estilo.configure("TNotebook.Tab", font=fuente)

    notebook = ttk.Notebook(ventana)
    notebook.pack(fill="both", expand=True, padx=10, pady=10)

    # ════════════════════════════════════════════════════════
    # TAB 1 — PRODUCTOS (formulario + búsqueda + tabla + popup)
    # ════════════════════════════════════════════════════════
    tab_productos = tk.Frame(notebook)
    notebook.add(tab_productos, text="Productos")

    # ── Formulario nuevo producto ────────────────────────────
    frame_form = tk.LabelFrame(tab_productos, text="Nuevo producto", padx=10, pady=6)
    frame_form.pack(fill="x", padx=10, pady=(6, 2))

    campos_fila0 = ["SKU", "Nombre", "Categoría", "Presentación", "Cantidad", "Precio"]
    campos_fila1 = ["Caducidad", "Código de barras", "Trazabilidad", "Lotes", "Observaciones"]
    entradas = {}

    for i, campo in enumerate(campos_fila0):
        tk.Label(frame_form, text=campo).grid(row=0, column=i * 2, sticky="e", padx=(6, 0))
        entrada = tk.Entry(frame_form, width=11)
        entrada.grid(row=0, column=i * 2 + 1, padx=(2, 6), pady=2)
        entradas[campo] = entrada

    for i, campo in enumerate(campos_fila1):
        ancho = 22 if campo == "Observaciones" else 11
        tk.Label(frame_form, text=campo).grid(row=1, column=i * 2, sticky="e", padx=(6, 0))
        entrada = tk.Entry(frame_form, width=ancho)
        entrada.grid(row=1, column=i * 2 + 1, padx=(2, 6), pady=2)
        entradas[campo] = entrada

    tk.Button(frame_form, text="Agregar", command=lambda: guardar_producto(),
              bg="#4CAF50", fg="white").grid(row=1, column=10, padx=12, pady=2)

    # ── Barra búsqueda + botón eliminar ─────────────────────
    frame_barra = tk.Frame(tab_productos)
    frame_barra.pack(fill="x", padx=10, pady=(4, 2))

    tk.Label(frame_barra, text="🔍 Buscar:", font=fuente).pack(side="left")
    var_busqueda = tk.StringVar()
    tk.Entry(frame_barra, textvariable=var_busqueda,
             font=fuente, width=32).pack(side="left", padx=6)
    tk.Label(frame_barra, text="(doble clic en una fila para ver detalle / editar)",
             font=("Arial", 10), fg="#888").pack(side="left", padx=10)
    tk.Button(frame_barra, text="Eliminar seleccionado",
              command=lambda: eliminar_seleccionado(),
              bg="#f44336", fg="white").pack(side="right", padx=6)

    # ── Tabla única ──────────────────────────────────────────
    cols = (
        "ID", "SKU", "Nombre", "Categoría", "Presentación",
        "Stock", "Precio", "Precio Total", "Caducidad",
        "Código de barras", "Observaciones", "Trazabilidad", "Lotes"
    )
    anchos = {
        "ID": 40, "SKU": 60, "Nombre": 180, "Categoría": 120,
        "Presentación": 105, "Stock": 55, "Precio": 90,
        "Precio Total": 100, "Caducidad": 105,
        "Código de barras": 130, "Observaciones": 160,
        "Trazabilidad": 115, "Lotes": 55
    }
    just = {
        "ID": "center", "SKU": "center", "Nombre": "w",
        "Categoría": "center", "Presentación": "center", "Stock": "center",
        "Precio": "center", "Precio Total": "center",
        "Caducidad": "center", "Código de barras": "center",
        "Observaciones": "w", "Trazabilidad": "center", "Lotes": "center"
    }

    frame_tabla = tk.Frame(tab_productos)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=(2, 4))

    scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical")
    scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal")

    tabla = ttk.Treeview(
        frame_tabla, columns=cols, show="headings",
        yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set,
        height=18
    )
    scroll_y.config(command=tabla.yview)
    scroll_x.config(command=tabla.xview)
    scroll_y.pack(side="right", fill="y")
    scroll_x.pack(side="bottom", fill="x")
    tabla.pack(fill="both", expand=True)

    for col in cols:
        tabla.heading(col, text=col, anchor=just.get(col, "center"),
                      command=lambda c=col: _ordenar(tabla, c, False))
        tabla.column(col, width=anchos.get(col, 100), anchor=just.get(col, "center"))

    for categoria, color in COLORES_CATEGORIA.items():
        tabla.tag_configure(categoria, background=color)

    cache = []

    def cargar_tabla(filtro=""):
        tabla.delete(*tabla.get_children())
        txt = filtro.lower()
        for p in cache:
            if txt and txt not in str(p[2]).lower() and txt not in str(p[1]).lower():
                continue
            tag = p[3] if p[3] in COLORES_CATEGORIA else ""
            precio_fmt = f"${p[6]:,.2f}" if p[6] is not None else "-"
            total_fmt  = f"${p[7]:,.2f}" if p[7] is not None else "-"
            tabla.insert("", "end", iid=str(p[0]), values=(
                p[0],
                p[1],
                p[2],
                p[3],
                p[4],
                int(p[5] or 0),
                precio_fmt,
                total_fmt,
                p[8] or "-",
                p[9] or "-",
                p[10] or "-",
                p[11] or "-",
                int(p[12] or 0),
            ), tags=(tag,))

    def cargar_productos():
        nonlocal cache
        cache = obtener_productos()
        cargar_tabla(var_busqueda.get())

    var_busqueda.trace_add("write", lambda *_: cargar_tabla(var_busqueda.get()))

    def guardar_producto():
        try:
            agregar_producto(
                entradas["SKU"].get(),
                entradas["Nombre"].get(),
                entradas["Categoría"].get(),
                entradas["Presentación"].get(),
                int(entradas["Cantidad"].get() or 0),
                entradas["Observaciones"].get(),
                float(entradas["Precio"].get() or 0),
                entradas["Caducidad"].get(),
                entradas["Código de barras"].get(),
                trazabilidad=entradas["Trazabilidad"].get(),
                cantidad_lotes=int(entradas["Lotes"].get() or 0)
            )
            for e in entradas.values():
                e.delete(0, tk.END)
            cargar_productos()
        except ValueError as err:
            messagebox.showerror("Error", f"Valor inválido: {err}")

    def eliminar_seleccionado():
        sel = tabla.selection()
        if not sel:
            messagebox.showwarning("Aviso", "Selecciona un producto")
            return
        id_prod = tabla.item(sel[0])["values"][0]
        eliminar_producto(id_prod)
        cargar_productos()

    # ── Popup de detalle / edición ───────────────────────────
    def abrir_popup(event):
        item = tabla.focus()
        if not item:
            return
        producto_id = int(item)
        p = next((x for x in cache if x[0] == producto_id), None)
        if not p:
            return

        popup = tk.Toplevel(ventana)
        popup.title(f"Detalle — {p[2]}")
        popup.resizable(False, False)
        popup.grab_set()

        bg = COLORES_CATEGORIA.get(p[3], "#f5f5f5")
        popup.configure(bg=bg)

        F  = ("Arial", 11)
        FB = ("Arial", 12, "bold")
        P  = {"padx": 16, "pady": 5}

        tk.Label(popup, text=p[2], font=("Arial", 14, "bold"),
                 bg=bg).grid(row=0, column=0, columnspan=2, pady=(14, 2), padx=16)
        tk.Label(popup, text=f"Código: {p[1]}   |   Categoría: {p[3]}",
                 font=("Arial", 10), bg=bg, fg="#555").grid(
                 row=1, column=0, columnspan=2, **P)

        ttk.Separator(popup, orient="horizontal").grid(
            row=2, column=0, columnspan=2, sticky="ew", padx=16, pady=4)

        datos_ro = [
            ("Código (SKU)",        p[1]),
            ("Nombre producto",     p[2]),
            ("Categoría",           p[3]),
            ("Cantidad en almacén", int(p[5] or 0)),
            ("Precio total inv.",   f"${p[7]:,.2f}" if p[7] else "-"),
        ]
        for i, (lbl, val) in enumerate(datos_ro, start=3):
            tk.Label(popup, text=lbl + ":", font=F, bg=bg,
                     anchor="e", width=20).grid(row=i, column=0, sticky="e", **P)
            tk.Label(popup, text=str(val), font=F, bg=bg,
                     anchor="w").grid(row=i, column=1, sticky="w", **P)

        fila = 3 + len(datos_ro)
        ttk.Separator(popup, orient="horizontal").grid(
            row=fila, column=0, columnspan=2, sticky="ew", padx=16, pady=4)
        fila += 1
        tk.Label(popup, text="✏️  Campos editables", font=FB,
                 bg=bg).grid(row=fila, column=0, columnspan=2, **P)
        fila += 1

        vars_edit = {}

        def campo_edit(f, label, valor):
            tk.Label(popup, text=label + ":", font=F, bg=bg,
                     anchor="e", width=20).grid(row=f, column=0, sticky="e", **P)
            v = tk.StringVar(value=str(valor) if valor is not None else "")
            tk.Entry(popup, textvariable=v, font=F, width=22).grid(
                row=f, column=1, sticky="w", **P)
            return v

        vars_edit["traz"]  = campo_edit(fila,     "Trazabilidad",    p[11])
        vars_edit["cad"]   = campo_edit(fila + 1, "Fecha caducidad", p[8])
        vars_edit["lotes"] = campo_edit(fila + 2, "Cant. lotes",     p[12])
        vars_edit["prec"]  = campo_edit(fila + 3, "Precio unitario", p[6])

        fila_btn = fila + 4
        lbl_ok = tk.Label(popup, text="", font=("Arial", 10), bg=bg)
        lbl_ok.grid(row=fila_btn + 1, column=0, columnspan=2)

        def guardar_popup():
            try:
                actualizar_producto_detalle(
                    producto_id,
                    trazabilidad   = vars_edit["traz"].get().strip(),
                    caducidad      = vars_edit["cad"].get().strip(),
                    cantidad_lotes = int(vars_edit["lotes"].get() or 0),
                    precio         = float(vars_edit["prec"].get() or 0),
                )
                lbl_ok.config(text="✔ Guardado", fg="#2e7d32")
                cargar_productos()
            except ValueError:
                lbl_ok.config(text="⚠ Lotes y precio deben ser números", fg="red")

        tk.Button(popup, text="💾 Guardar cambios", font=("Arial", 11, "bold"),
                  bg="#4caf50", fg="white", command=guardar_popup).grid(
                  row=fila_btn, column=0, columnspan=2, pady=(12, 4))

        ventana.update_idletasks()
        pw, ph = 440, 580
        x = ventana.winfo_x() + (ventana.winfo_width()  - pw) // 2
        y = ventana.winfo_y() + (ventana.winfo_height() - ph) // 2
        popup.geometry(f"{pw}x{ph}+{x}+{y}")

    tabla.bind("<Double-1>", abrir_popup)

    # ════════════════════════════════════════════════════════
    # TAB 2 — MOVIMIENTOS
    # ════════════════════════════════════════════════════════
    tab_mov = tk.Frame(notebook)
    notebook.add(tab_mov, text="Movimientos")

    frame_mov = tk.LabelFrame(tab_mov, text="Registrar movimiento", padx=10, pady=10)
    frame_mov.pack(fill="x", padx=10, pady=5)

    tk.Label(frame_mov, text="SKU").grid(row=0, column=0)
    entry_sku = tk.Entry(frame_mov, width=8)
    entry_sku.grid(row=0, column=1, padx=4)

    tk.Label(frame_mov, text="Producto ID").grid(row=0, column=2)
    entry_pid = tk.Entry(frame_mov, width=8)
    entry_pid.grid(row=0, column=3, padx=4)

    tk.Label(frame_mov, text="Tipo").grid(row=0, column=4)
    tipo_var = tk.StringVar(value="entrada")
    ttk.Combobox(frame_mov, textvariable=tipo_var,
                 values=["entrada", "salida"], width=10).grid(row=0, column=5, padx=4)

    tk.Label(frame_mov, text="Cantidad").grid(row=0, column=6)
    entry_cant = tk.Entry(frame_mov, width=8)
    entry_cant.grid(row=0, column=7, padx=4)

    tk.Label(frame_mov, text="Nota").grid(row=0, column=8)
    entry_nota = tk.Entry(frame_mov, width=20)
    entry_nota.grid(row=0, column=9, padx=4)

    cols_mov = ("SKU", "ID", "Producto", "Categoría", "Tipo", "Cantidad", "Fecha", "Nota")
    tabla_mov = ttk.Treeview(tab_mov, columns=cols_mov, show="headings", height=16)
    for col in cols_mov:
        tabla_mov.heading(col, text=col)
        tabla_mov.column(col, width=130, anchor="center")
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

    tk.Button(frame_mov, text="Registrar", command=guardar_movimiento,
              bg="#2196F3", fg="white").grid(row=0, column=11, padx=8)

    # ════════════════════════════════════════════════════════
    # TAB 3 — DASHBOARD
    # ════════════════════════════════════════════════════════
    tab_dash = tk.Frame(notebook)
    notebook.add(tab_dash, text="Dashboard")

    frame_cards = tk.Frame(tab_dash)
    frame_cards.pack(fill="x", padx=10, pady=10)

    lbl_total_prod  = tk.Label(frame_cards, text="", font=("Arial", 16),
                                relief="groove", padx=20, pady=10)
    lbl_total_stock = tk.Label(frame_cards, text="", font=("Arial", 16),
                                relief="groove", padx=20, pady=10)
    lbl_entradas    = tk.Label(frame_cards, text="", font=("Arial", 16),
                                relief="groove", padx=20, pady=10, fg="green")
    lbl_salidas     = tk.Label(frame_cards, text="", font=("Arial", 16),
                                relief="groove", padx=20, pady=10, fg="red")

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
            stocks  = [int(d[1] or 0) for d in datos]
            colores = ["#4CAF50" if s > 5 else "#f44336" for s in stocks]
            ax.barh(nombres, stocks, color=colores)
            ax.set_xlabel("Stock")
            ax.set_title("Stock por producto (verde = ok, rojo = bajo)")
            ax.invert_yaxis()
        else:
            ax.text(0.5, 0.5, "Sin datos aún", ha="center", va="center",
                    transform=ax.transAxes)
        fig.tight_layout()
        canvas.draw()

    tk.Button(tab_dash, text="Actualizar dashboard", command=actualizar_dashboard,
              bg="#673AB7", fg="white").pack(pady=4)
    actualizar_dashboard()

    # ── Carga inicial ────────────────────────────────────────
    cargar_productos()
    cargar_movimientos()

    ventana.mainloop()


# ── Ordenamiento de columnas ─────────────────────────────────
def _ordenar(tree, col, reverse):
    datos = [(tree.set(k, col), k) for k in tree.get_children("")]
    try:
        datos.sort(key=lambda t: float(
            t[0].replace("$", "").replace(",", "")), reverse=reverse)
    except ValueError:
        datos.sort(reverse=reverse)
    for index, (_, k) in enumerate(datos):
        tree.move(k, "", index)
    tree.heading(col, command=lambda: _ordenar(tree, col, not reverse))