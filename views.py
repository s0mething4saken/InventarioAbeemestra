import tkinter as tk
from tkinter import ttk, messagebox
from matplotlib import pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from models import (
    agregar_producto, obtener_productos, eliminar_producto, actualizar_producto,
    agregar_lote, obtener_lotes_por_producto, actualizar_lote, eliminar_lote,
    obtener_lotes_todos,
    registrar_movimiento, obtener_movimientos,
    obtener_resumen, obtener_stock_por_producto,
    buscar_lote_por_sku_trazabilidad
)

COLORES_CATEGORIA = {
    "Miel":              "#e8e8e8",
    "Productos con miel":    "#e8e8e8",
    "Cuida":          "#e8e8e8",
    "Productos embellece": "#e8e8e8",
    "Productos dulceria":         "#e8e8e8",
    "Productos kits":              "#e8e8e8"
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
    # TAB 1 — PRODUCTOS
    # ════════════════════════════════════════════════════════
    tab_productos = tk.Frame(notebook)
    notebook.add(tab_productos, text="Productos")

    # ── Formulario nuevo producto ────────────────────────────
    frame_form = tk.LabelFrame(tab_productos, text="Nuevo producto", padx=10, pady=6)
    frame_form.pack(fill="x", padx=10, pady=(6, 2))

    # Fila 0: datos del producto
    campos_prod = ["SKU", "Nombre", "Categoría", "Presentación", "Precio", "Código de barras", "Observaciones"]
    entradas = {}
    for i, campo in enumerate(campos_prod):
        ancho = 20 if campo in ("Nombre", "Observaciones") else 11
        tk.Label(frame_form, text=campo).grid(row=0, column=i*2, sticky="e", padx=(6,0))
        e = tk.Entry(frame_form, width=ancho)
        e.grid(row=0, column=i*2+1, padx=(2,6), pady=2)
        entradas[campo] = e

    # Fila 1: datos del primer lote
    tk.Label(frame_form, text="── Primer lote ──", font=("Arial", 10, "italic"),
             fg="#555").grid(row=1, column=0, columnspan=3, sticky="w", padx=6)
    campos_lote = ["Nº Lote", "Trazabilidad", "Caducidad", "Cantidad"]
    for i, campo in enumerate(campos_lote):
        tk.Label(frame_form, text=campo).grid(row=1, column=i*2+2, sticky="e", padx=(6,0))
        e = tk.Entry(frame_form, width=11)
        e.grid(row=1, column=i*2+3, padx=(2,6), pady=2)
        entradas[campo] = e

    tk.Button(frame_form, text="Agregar", command=lambda: guardar_producto(),
              bg="#4CAF50", fg="white").grid(row=1, column=14, padx=12, pady=2)

    # ── Barra búsqueda + filtro categoría + botón eliminar ───
    frame_barra = tk.Frame(tab_productos)
    frame_barra.pack(fill="x", padx=10, pady=(4, 2))

    tk.Label(frame_barra, text="🔍 Buscar:", font=fuente).pack(side="left")
    var_busqueda = tk.StringVar()
    tk.Entry(frame_barra, textvariable=var_busqueda,
             font=fuente, width=26).pack(side="left", padx=(4, 10))

    tk.Label(frame_barra, text="Categoría:", font=fuente).pack(side="left")
    CATEGORIAS_OPCIONES = ["Todas", "Miel", "Productos con miel", "Cuida",
                           "Productos embellece", "Productos dulceria", "Productos kits"]
    var_categoria = tk.StringVar(value="Todas")
    ttk.Combobox(frame_barra, textvariable=var_categoria,
                 values=CATEGORIAS_OPCIONES, width=16,
                 state="readonly").pack(side="left", padx=(4, 10))

    tk.Label(frame_barra, text="(doble clic para ver lotes / editar)",
             font=("Arial", 10), fg="#888").pack(side="left")
    tk.Button(frame_barra, text="Eliminar seleccionado",
              command=lambda: eliminar_seleccionado(),
              bg="#f44336", fg="white").pack(side="right", padx=6)

    # ── Tabla productos ──────────────────────────────────────
    cols = ("ID", "SKU", "Nombre", "Categoría", "Presentación",
            "Stock Total", "Precio", "Precio Total", "Código de barras", "Observaciones")
    anchos = {
        "ID": 40, "SKU": 65, "Nombre": 190, "Categoría": 120,
        "Presentación": 105, "Stock Total": 80, "Precio": 90,
        "Precio Total": 105, "Código de barras": 130, "Observaciones": 180
    }
    just = {
        "ID": "center", "SKU": "center", "Nombre": "w",
        "Categoría": "center", "Presentación": "center",
        "Stock Total": "center", "Precio": "center",
        "Precio Total": "center", "Código de barras": "center", "Observaciones": "w"
    }

    frame_tabla = tk.Frame(tab_productos)
    frame_tabla.pack(fill="both", expand=True, padx=10, pady=(2, 4))

    scroll_y = ttk.Scrollbar(frame_tabla, orient="vertical")
    scroll_x = ttk.Scrollbar(frame_tabla, orient="horizontal")
    tabla = ttk.Treeview(frame_tabla, columns=cols, show="headings",
                          yscrollcommand=scroll_y.set, xscrollcommand=scroll_x.set, height=18)
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

    cache = []  # cache de obtener_productos()

    def cargar_tabla(filtro=""):
        tabla.delete(*tabla.get_children())
        txt = filtro.lower()
        cat = var_categoria.get()
        for p in cache:
            if txt and txt not in str(p[2]).lower() and txt not in str(p[1]).lower():
                continue
            if cat != "Todas" and str(p[3]) != cat:
                continue
            tag = p[3] if p[3] in COLORES_CATEGORIA else ""
            tabla.insert("", "end", iid=str(p[0]), values=(
                p[0], p[1], p[2], p[3], p[4],
                int(p[5] or 0),
                f"${p[6]:,.2f}" if p[6] is not None else "-",
                f"${p[7]:,.2f}" if p[7] is not None else "-",
                p[8] or "-",
                p[9] or "-",
            ), tags=(tag,))

    def cargar_productos():
        nonlocal cache
        cache = obtener_productos()
        cargar_tabla(var_busqueda.get())

    var_busqueda.trace_add("write", lambda *_: cargar_tabla(var_busqueda.get()))
    var_categoria.trace_add("write", lambda *_: cargar_tabla(var_busqueda.get()))

    def guardar_producto():
        try:
            sku  = entradas["SKU"].get().strip()
            nombre = entradas["Nombre"].get().strip()
            if not sku or not nombre:
                messagebox.showwarning("Aviso", "SKU y Nombre son obligatorios.")
                return
            agregar_producto(
                sku, nombre,
                entradas["Categoría"].get(),
                entradas["Presentación"].get(),
                float(entradas["Precio"].get() or 0),
                entradas["Código de barras"].get(),
                entradas["Observaciones"].get(),
            )
            # Primer lote (opcional)
            nro = entradas["Nº Lote"].get().strip()
            if nro:
                prod = next((p for p in obtener_productos() if str(p[1]) == sku), None)
                if prod:
                    agregar_lote(
                        prod[0], nro,
                        entradas["Trazabilidad"].get(),
                        entradas["Caducidad"].get(),
                        int(entradas["Cantidad"].get() or 0)
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
        if not messagebox.askyesno("Confirmar", "¿Eliminar producto y todos sus lotes?"):
            return
        eliminar_producto(int(tabla.item(sel[0])["values"][0]))
        cargar_productos()

    # ── Popup: detalle del producto + tabla de lotes ─────────
    def abrir_popup(event):
        item = tabla.focus()
        if not item:
            return
        producto_id = int(item)
        p = next((x for x in cache if x[0] == producto_id), None)
        if not p:
            return

        popup = tk.Toplevel(ventana)
        popup.title(f"{p[2]}  —  SKU {p[1]}")
        popup.grab_set()

        bg = COLORES_CATEGORIA.get(p[3], "#f5f5f5")
        popup.configure(bg=bg)
        F  = ("Arial", 11)
        FB = ("Arial", 12, "bold")
        P  = {"padx": 14, "pady": 4}

        # Encabezado
        tk.Label(popup, text=p[2], font=("Arial", 14, "bold"), bg=bg).grid(
            row=0, column=0, columnspan=4, pady=(12,2), padx=14)
        tk.Label(popup, text=f"SKU: {p[1]}   Categoría: {p[3]}   Stock total: {int(p[5] or 0)}",
                 font=("Arial", 10), bg=bg, fg="#555").grid(
                 row=1, column=0, columnspan=4, **P)

        ttk.Separator(popup, orient="horizontal").grid(
            row=2, column=0, columnspan=4, sticky="ew", padx=14, pady=4)

        # Campos editables del producto
        tk.Label(popup, text="✏️ Datos del producto", font=FB, bg=bg).grid(
            row=3, column=0, columnspan=4, **P)

        def lbl_entry(row, col_lbl, col_ent, texto, valor):
            tk.Label(popup, text=texto+":", font=F, bg=bg, anchor="e", width=14).grid(
                row=row, column=col_lbl, sticky="e", **P)
            v = tk.StringVar(value=str(valor) if valor is not None else "")
            tk.Entry(popup, textvariable=v, font=F, width=18).grid(
                row=row, column=col_ent, sticky="w", **P)
            return v

        v_precio = lbl_entry(4, 0, 1, "Precio",        p[6])
        v_barcode = lbl_entry(4, 2, 3, "Código barras", p[8])
        v_obs     = lbl_entry(5, 0, 1, "Observaciones", p[9])

        lbl_prod_ok = tk.Label(popup, text="", font=("Arial", 10), bg=bg)
        lbl_prod_ok.grid(row=6, column=0, columnspan=2, sticky="w", padx=14)

        def guardar_producto_popup():
            try:
                actualizar_producto(producto_id,
                                    float(v_precio.get() or 0),
                                    v_barcode.get().strip(),
                                    v_obs.get().strip())
                lbl_prod_ok.config(text="✔ Guardado", fg="#2e7d32")
                cargar_productos()
            except ValueError:
                lbl_prod_ok.config(text="⚠ Precio inválido", fg="red")

        tk.Button(popup, text="Guardar producto", bg="#4caf50", fg="white",
                  font=F, command=guardar_producto_popup).grid(
                  row=6, column=2, columnspan=2, sticky="e", padx=14, pady=2)

        ttk.Separator(popup, orient="horizontal").grid(
            row=7, column=0, columnspan=4, sticky="ew", padx=14, pady=6)

        # ── Tabla de lotes ────────────────────────────────────
        tk.Label(popup, text="📦 Lotes", font=FB, bg=bg).grid(
            row=8, column=0, columnspan=4, sticky="w", padx=14)

        frame_lotes = tk.Frame(popup, bg=bg)
        frame_lotes.grid(row=9, column=0, columnspan=4, padx=14, pady=4, sticky="ew")

        cols_l = ("ID", "Nº Lote", "Trazabilidad", "Caducidad", "Stock")
        anchos_l = {"ID": 40, "Nº Lote": 100, "Trazabilidad": 120,
                    "Caducidad": 110, "Stock": 70}
        tabla_lotes = ttk.Treeview(frame_lotes, columns=cols_l, show="headings", height=6)
        for c in cols_l:
            tabla_lotes.heading(c, text=c)
            tabla_lotes.column(c, width=anchos_l.get(c, 100), anchor="center")
        tabla_lotes.pack(fill="x")

        def recargar_lotes():
            tabla_lotes.delete(*tabla_lotes.get_children())
            for l in obtener_lotes_por_producto(producto_id):
                tabla_lotes.insert("", "end", iid=str(l[0]),
                                   values=(l[0], l[1], l[2] or "-", l[3] or "-", l[4]))

        recargar_lotes()

        # ── Edición / alta de lote ────────────────────────────
        lbl_lote_status = tk.Label(popup, text="", font=("Arial", 10), bg=bg)
        lbl_lote_status.grid(row=13, column=0, columnspan=4, **P)

        frame_edit_lote = tk.LabelFrame(popup, text="Nuevo / editar lote",
                                         font=F, bg=bg, padx=8, pady=6)
        frame_edit_lote.grid(row=10, column=0, columnspan=4, padx=14, pady=4, sticky="ew")

        campos_l_edit = ["Nº Lote", "Trazabilidad", "Caducidad", "Stock"]
        vars_lote = {}
        for i, c in enumerate(campos_l_edit):
            tk.Label(frame_edit_lote, text=c+":", font=F, bg=bg).grid(
                row=0, column=i*2, sticky="e", padx=(6,0))
            v = tk.StringVar()
            tk.Entry(frame_edit_lote, textvariable=v, font=F, width=12).grid(
                row=0, column=i*2+1, padx=(2,8))
            vars_lote[c] = v

        lote_editando_id = [None]  # lista para mutabilidad en closure

        def cargar_lote_en_form(event):
            sel = tabla_lotes.focus()
            if not sel:
                return
            vals = tabla_lotes.item(sel)["values"]
            lote_editando_id[0] = vals[0]
            vars_lote["Nº Lote"].set(vals[1])
            vars_lote["Trazabilidad"].set("" if vals[2] == "-" else vals[2])
            vars_lote["Caducidad"].set("" if vals[3] == "-" else vals[3])
            vars_lote["Stock"].set(vals[4])
            lbl_lote_status.config(text="✏️ Editando lote seleccionado", fg="#1565c0")

        tabla_lotes.bind("<ButtonRelease-1>", cargar_lote_en_form)

        def limpiar_form_lote():
            lote_editando_id[0] = None
            for v in vars_lote.values():
                v.set("")
            lbl_lote_status.config(text="")

        def guardar_lote():
            nro = vars_lote["Nº Lote"].get().strip()
            if not nro:
                lbl_lote_status.config(text="⚠ Nº Lote es obligatorio", fg="red")
                return
            try:
                stk = int(vars_lote["Stock"].get() or 0)
            except ValueError:
                lbl_lote_status.config(text="⚠ Stock debe ser entero", fg="red")
                return
            if lote_editando_id[0]:
                actualizar_lote(lote_editando_id[0], nro,
                                vars_lote["Trazabilidad"].get().strip(),
                                vars_lote["Caducidad"].get().strip(), stk)
                lbl_lote_status.config(text="✔ Lote actualizado", fg="#2e7d32")
            else:
                agregar_lote(producto_id, nro,
                             vars_lote["Trazabilidad"].get().strip(),
                             vars_lote["Caducidad"].get().strip(), stk)
                lbl_lote_status.config(text="✔ Lote agregado", fg="#2e7d32")
            limpiar_form_lote()
            recargar_lotes()
            cargar_productos()

        def borrar_lote():
            if not lote_editando_id[0]:
                lbl_lote_status.config(text="⚠ Selecciona un lote primero", fg="red")
                return
            if messagebox.askyesno("Confirmar", "¿Eliminar este lote?", parent=popup):
                eliminar_lote(lote_editando_id[0])
                limpiar_form_lote()
                recargar_lotes()
                cargar_productos()

        frame_btn_lote = tk.Frame(popup, bg=bg)
        frame_btn_lote.grid(row=11, column=0, columnspan=4, pady=(2,6))
        tk.Button(frame_btn_lote, text="💾 Guardar lote", bg="#4caf50", fg="white",
                  font=F, command=guardar_lote).pack(side="left", padx=6)
        tk.Button(frame_btn_lote, text="➕ Nuevo", bg="#2196F3", fg="white",
                  font=F, command=limpiar_form_lote).pack(side="left", padx=6)
        tk.Button(frame_btn_lote, text="🗑 Eliminar lote", bg="#f44336", fg="white",
                  font=F, command=borrar_lote).pack(side="left", padx=6)

        popup.update_idletasks()
        pw = 800
        ph = popup.winfo_reqheight() + 20
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

    # ── Autocomplete helper ───────────────────────────────────
    class Autocomplete:
        def __init__(self, entry, obtener_opciones_fn, al_seleccionar=None):
            self.entry = entry
            self.obtener_opciones = obtener_opciones_fn
            self.al_seleccionar   = al_seleccionar
            self._popup   = None
            self._listbox = None
            self._ignorar = False
            entry.bind("<KeyRelease>", self._on_key)
            entry.bind("<FocusOut>",   self._cerrar_delay)
            entry.bind("<Escape>",     lambda e: self._cerrar())

        def _on_key(self, event):
            if event.keysym in ("Return", "Tab", "Escape"):
                return
            if event.keysym in ("Up", "Down") and self._listbox:
                self._listbox.focus_set(); return
            if self._ignorar:
                return
            texto = self.entry.get().strip()
            ops = [o for o in self.obtener_opciones()
                   if texto.lower() in str(o).lower()]
            self._mostrar(ops) if ops else self._cerrar()

        def _mostrar(self, ops):
            self._cerrar()
            self.entry.update_idletasks()
            x = self.entry.winfo_rootx()
            y = self.entry.winfo_rooty() + self.entry.winfo_height()
            w = max(self.entry.winfo_width(), 160)
            self._popup = tk.Toplevel()
            self._popup.wm_overrideredirect(True)
            self._popup.geometry(f"{w}x{min(len(ops),8)*22}+{x}+{y}")
            self._popup.lift()
            sb = tk.Scrollbar(self._popup, orient="vertical")
            self._listbox = tk.Listbox(self._popup, yscrollcommand=sb.set,
                                        font=("Arial", 11), activestyle="dotbox",
                                        selectbackground="#2196F3", selectforeground="white")
            sb.config(command=self._listbox.yview)
            sb.pack(side="right", fill="y")
            self._listbox.pack(fill="both", expand=True)
            for op in ops:
                self._listbox.insert("end", op)
            self._listbox.bind("<ButtonRelease-1>", self._elegir)
            self._listbox.bind("<Return>",           self._elegir)
            self._listbox.bind("<Escape>",           lambda e: self._cerrar())
            self._listbox.bind("<FocusOut>",         self._cerrar_delay)

        def _elegir(self, event):
            if not self._listbox: return
            sel = self._listbox.curselection()
            if not sel: return
            valor = self._listbox.get(sel[0])
            self._ignorar = True
            self.entry.delete(0, "end")
            self.entry.insert(0, valor)
            self._ignorar = False
            self._cerrar()
            self.entry.focus_set()
            if self.al_seleccionar:
                self.al_seleccionar(valor)

        def _cerrar_delay(self, event=None):
            self.entry.after(150, self._cerrar)

        def _cerrar(self, event=None):
            if self._popup:
                self._popup.destroy()
                self._popup = None
                self._listbox = None

    # ── Campos formulario movimiento ──────────────────────────
    tk.Label(frame_mov, text="SKU").grid(row=0, column=0, sticky="e", padx=(6,0))
    entry_sku_mov = tk.Entry(frame_mov, width=12)
    entry_sku_mov.grid(row=0, column=1, padx=4)

    tk.Label(frame_mov, text="Trazabilidad").grid(row=0, column=2, sticky="e", padx=(6,0))
    entry_lote_mov = tk.Entry(frame_mov, width=12)
    entry_lote_mov.grid(row=0, column=3, padx=4)

    tk.Label(frame_mov, text="Tipo").grid(row=0, column=4, sticky="e", padx=(6,0))
    tipo_var = tk.StringVar(value="entrada")
    ttk.Combobox(frame_mov, textvariable=tipo_var, values=["entrada", "salida"],
                 width=10, state="readonly").grid(row=0, column=5, padx=4)

    tk.Label(frame_mov, text="Cantidad").grid(row=0, column=6, sticky="e", padx=(6,0))
    entry_cant = tk.Entry(frame_mov, width=8)
    entry_cant.grid(row=0, column=7, padx=4)

    tk.Label(frame_mov, text="Nota").grid(row=0, column=8, sticky="e", padx=(6,0))
    entry_nota = tk.Entry(frame_mov, width=22)
    entry_nota.grid(row=0, column=9, padx=4)

    lbl_info_prod = tk.Label(frame_mov, text="", font=("Arial", 10), fg="#555", anchor="w")
    lbl_info_prod.grid(row=1, column=0, columnspan=10, sticky="w", padx=6, pady=(0,2))

    # cache de lotes para autocomplete en movimientos
    cache_lotes = []

    def refrescar_cache_lotes():
        nonlocal cache_lotes
        cache_lotes = obtener_lotes_todos()

    def opciones_sku():
        skus = list(dict.fromkeys(str(l[1]) for l in cache_lotes))
        return skus

    def opciones_trazabilidad_mov():
        sku_actual = entry_sku_mov.get().strip()
        return [str(l[5]) for l in cache_lotes
                if str(l[1]) == sku_actual and l[5] and str(l[5]).strip()]

    def al_seleccionar_sku(sku_val):
        prod = next((l for l in cache_lotes if str(l[1]) == str(sku_val)), None)
        if prod:
            stock_total = sum(l[6] for l in cache_lotes if str(l[1]) == str(sku_val))
            trazs = opciones_trazabilidad_mov()
            lbl_info_prod.config(
                text=f"{prod[3]}  |  Stock total: {stock_total}  |  Trazabilidades: {', '.join(trazs)}"
            )
            if len(trazs) == 1:
                entry_lote_mov.delete(0, "end")
                entry_lote_mov.insert(0, trazs[0])
        else:
            lbl_info_prod.config(text="")

    Autocomplete(entry_sku_mov,  opciones_sku,              al_seleccionar=al_seleccionar_sku)
    Autocomplete(entry_lote_mov, opciones_trazabilidad_mov)

    # ── Tabla historial movimientos ───────────────────────────
    cols_mov = ("SKU", "Trazabilidad", "Producto", "Categoría", "Tipo", "Cantidad", "Fecha", "Nota")
    anchos_mov = {"SKU": 70, "Trazabilidad": 110, "Producto": 190, "Categoría": 120,
                  "Tipo": 80, "Cantidad": 80, "Fecha": 130, "Nota": 180}

    frame_tabla_mov = tk.Frame(tab_mov)
    frame_tabla_mov.pack(fill="both", expand=True, padx=10, pady=5)

    scroll_mov_y = ttk.Scrollbar(frame_tabla_mov, orient="vertical")
    scroll_mov_x = ttk.Scrollbar(frame_tabla_mov, orient="horizontal")
    tabla_mov = ttk.Treeview(frame_tabla_mov, columns=cols_mov, show="headings",
                              yscrollcommand=scroll_mov_y.set,
                              xscrollcommand=scroll_mov_x.set, height=15)
    scroll_mov_y.config(command=tabla_mov.yview)
    scroll_mov_x.config(command=tabla_mov.xview)
    scroll_mov_y.pack(side="right", fill="y")
    scroll_mov_x.pack(side="bottom", fill="x")
    tabla_mov.pack(fill="both", expand=True)

    for col in cols_mov:
        tabla_mov.heading(col, text=col)
        tabla_mov.column(col, width=anchos_mov.get(col, 120), anchor="center")
    def ver_nota(event):
        item = tabla_mov.focus()
        if not item:
            return
        vals = tabla_mov.item(item)["values"]
        nota = str(vals[7]) if vals[7] else ""  # índice 7 = Nota
        if not nota or nota.strip() == "":
            return

        popup_nota = tk.Toplevel(ventana)
        popup_nota.title("Observación")
        popup_nota.resizable(True, True)
        popup_nota.grab_set()

        # Info del producto para contexto
        tk.Label(popup_nota, text=f"{vals[2]}  —  SKU {vals[0]}",
                 font=("Arial", 11, "bold")).pack(padx=16, pady=(12, 2))
        tk.Label(popup_nota, text=f"Trazabilidad: {vals[1]}   |   {vals[4]}   {vals[5]} uds   {vals[6]}",
                 font=("Arial", 10), fg="#555").pack(padx=16, pady=(0, 6))

        ttk.Separator(popup_nota, orient="horizontal").pack(fill="x", padx=16, pady=4)

        # Texto con scroll
        frame_txt = tk.Frame(popup_nota)
        frame_txt.pack(fill="both", expand=True, padx=16, pady=(4, 12))

        sb = tk.Scrollbar(frame_txt)
        sb.pack(side="right", fill="y")
        txt = tk.Text(frame_txt, font=("Arial", 12), wrap="word",
                      yscrollcommand=sb.set, relief="flat",
                      bg="#f9f9f9", width=50, height=8)
        txt.insert("1.0", nota)
        txt.config(state="disabled")
        txt.pack(fill="both", expand=True)
        sb.config(command=txt.yview)

        tk.Button(popup_nota, text="Cerrar", command=popup_nota.destroy,
                  bg="#555", fg="white", font=("Arial", 11)).pack(pady=(0, 12))

        popup_nota.update_idletasks()
        pw, ph = 480, 280
        x = ventana.winfo_x() + (ventana.winfo_width()  - pw) // 2
        y = ventana.winfo_y() + (ventana.winfo_height() - ph) // 2
        popup_nota.geometry(f"{pw}x{ph}+{x}+{y}")

    tabla_mov.bind("<Double-1>", ver_nota)

    def cargar_movimientos():
        tabla_mov.delete(*tabla_mov.get_children())
        for m in obtener_movimientos():
            tabla_mov.insert("", tk.END, values=m)

    def guardar_movimiento():
        sku  = entry_sku_mov.get().strip()
        lote = entry_lote_mov.get().strip()
        if not sku or not lote:
            messagebox.showwarning("Campos incompletos", "Ingresa SKU y Lote.")
            return
        try:
            cant = int(entry_cant.get())
            if cant <= 0: raise ValueError
        except ValueError:
            messagebox.showerror("Error", "La cantidad debe ser un entero positivo.")
            return
        exito, msg = registrar_movimiento(sku, lote, tipo_var.get(),
                                          cant, entry_nota.get().strip())
        if not exito:
            messagebox.showerror("Movimiento rechazado", msg)
            return
        for e in [entry_sku_mov, entry_lote_mov, entry_cant, entry_nota]:
            e.delete(0, tk.END)
        lbl_info_prod.config(text="")
        cargar_movimientos()
        cargar_productos()
        refrescar_cache_lotes()

    tk.Button(frame_mov, text="Registrar", command=guardar_movimiento,
              bg="#2196F3", fg="white").grid(row=0, column=10, padx=12)

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
    refrescar_cache_lotes()

    ventana.mainloop()


def _ordenar(tree, col, reverse):
    datos = [(tree.set(k, col), k) for k in tree.get_children("")]
    try:
        datos.sort(key=lambda t: float(
            t[0].replace("$","").replace(",","")), reverse=reverse)
    except ValueError:
        datos.sort(reverse=reverse)
    for i, (_, k) in enumerate(datos):
        tree.move(k, "", i)
    tree.heading(col, command=lambda: _ordenar(tree, col, not reverse))