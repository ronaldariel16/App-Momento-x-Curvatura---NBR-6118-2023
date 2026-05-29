# -*- coding: utf-8 -*-
"""
gui/tab_armaduras.py

Pestaña 3: definicion de las barras de acero (area As y posicion X, Y), con
seleccion de diametros estandar brasileños y vista previa sobre la seccion.
"""

import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .widgets import TablaEditable
from core.geometria import centroide_seccion, barra_dentro


# Diametros estandar (mm) -> area (mm^2)
DIAMETROS = {
    "phi 6.3": 31.2,
    "phi 8.0": 50.3,
    "phi 10.0": 78.5,
    "phi 12.5": 122.7,
    "phi 16.0": 201.1,
    "phi 20.0": 314.2,
    "phi 25.0": 490.9,
}

# Armaduras por defecto: 4 barras phi 12.5 en las esquinas (cobertura 30 mm)
BARRAS_DEFAULT = [
    (122.7, 30, 30),
    (122.7, 220, 30),
    (122.7, 30, 470),
    (122.7, 220, 470),
]


class TabArmaduras(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        izq = ttk.Frame(self)
        izq.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(izq, text="Barras de acero",
                  font=("", 10, "bold")).pack(anchor="w")
        ttk.Label(izq, text="As: area de la barra. X, Y: posicion del centro.\n"
                            "Doble clic para editar una celda.",
                  foreground="#555").pack(anchor="w", pady=(0, 6))

        self.tabla = TablaEditable(izq, ["As (mm2)", "X (mm)", "Y (mm)"],
                                   on_change=self.refrescar_vista)
        self.tabla.pack(fill="y")

        # Selector de diametro
        sel = ttk.LabelFrame(izq, text="Agregar barra por diametro")
        sel.pack(fill="x", pady=8)
        ttk.Label(sel, text="Diametro:").grid(row=0, column=0, padx=4, pady=4)
        self.var_diam = tk.StringVar(value="phi 12.5")
        ttk.Combobox(sel, textvariable=self.var_diam, values=list(DIAMETROS),
                     width=10, state="readonly").grid(row=0, column=1, padx=4)
        ttk.Label(sel, text="X (mm):").grid(row=1, column=0, padx=4)
        self.var_x = tk.StringVar(value="30")
        ttk.Entry(sel, textvariable=self.var_x, width=8).grid(row=1, column=1)
        ttk.Label(sel, text="Y (mm):").grid(row=2, column=0, padx=4)
        self.var_y = tk.StringVar(value="30")
        ttk.Entry(sel, textvariable=self.var_y, width=8).grid(row=2, column=1)
        ttk.Button(sel, text="Agregar barra",
                   command=self._agregar_por_diametro).grid(
            row=3, column=0, columnspan=2, pady=6)

        botones = ttk.Frame(izq)
        botones.pack(fill="x", pady=6)
        ttk.Button(botones, text="Fila vacia",
                   command=lambda: self.tabla.agregar_fila(["0", "0", "0"])).pack(
            side="left", padx=2)
        ttk.Button(botones, text="Eliminar fila",
                   command=self.tabla.eliminar_seleccion).pack(side="left", padx=2)
        ttk.Button(botones, text="Limpiar",
                   command=self.tabla.limpiar).pack(side="left", padx=2)

        # Vista previa
        der = ttk.Frame(self)
        der.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        ttk.Label(der, text="Vista previa: seccion + armaduras",
                  font=("", 10, "bold")).pack(anchor="w")
        self.fig = Figure(figsize=(4.5, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=der)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        self.tabla.cargar_datos(BARRAS_DEFAULT)

    # ------------------------------------------------------------------ #
    def _agregar_por_diametro(self):
        area = DIAMETROS.get(self.var_diam.get(), 0)
        try:
            x = float(self.var_x.get().replace(",", "."))
            y = float(self.var_y.get().replace(",", "."))
        except ValueError:
            return
        self.tabla.agregar_fila(["%.1f" % area, "%.1f" % x, "%.1f" % y])

    # ------------------------------------------------------------------ #
    def get_barras(self):
        """Devuelve lista de barras [As, X, Y]."""
        return self.tabla.obtener_datos()

    # ------------------------------------------------------------------ #
    def refrescar_vista(self):
        """Redibuja la seccion (desde la pestaña de seccion) con las barras."""
        self.ax.clear()
        try:
            verts = self.app.tab_seccion.get_vertices()
        except Exception:
            verts = []

        if len(verts) >= 3:
            xs = [v[0] for v in verts] + [verts[0][0]]
            ys = [v[1] for v in verts] + [verts[0][1]]
            self.ax.fill(xs, ys, alpha=0.20, color="#4c72b0")
            self.ax.plot(xs, ys, "-", color="#1f3b73", lw=1.5)
            xc, yc = centroide_seccion(verts)
            self.ax.plot(xc, yc, "x", color="gray", ms=8)

        try:
            barras = self.get_barras()
        except ValueError:
            barras = []
        for b in barras:
            As, x, y = b
            r = max((As / 3.1416) ** 0.5, 3)  # radio visual a partir del area
            dentro = barra_dentro(x, y, verts) if len(verts) >= 3 else True
            color = "black" if dentro else "red"
            self.ax.scatter([x], [y], s=max(As * 0.3, 25), color=color, zorder=5)

        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.grid(True, alpha=0.3)
        if len(verts) >= 3:
            self.ax.set_aspect("equal", adjustable="datalim")
        self.fig.tight_layout()
        self.canvas.draw_idle()
