# -*- coding: utf-8 -*-
"""
gui/tab_seccion.py

Pestaña 1: definicion de la geometria de la seccion mediante vertices (X, Y),
con vista previa 2D del poligono y su centroide.
"""

import tkinter as tk
from tkinter import ttk

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from .widgets import TablaEditable
from core.geometria import centroide_seccion


# Seccion rectangular por defecto: b = 250 mm, h = 500 mm
VERTICES_DEFAULT = [(0, 0), (250, 0), (250, 500), (0, 500)]


class TabSeccion(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        # --- Panel izquierdo: tabla de vertices y botones ---
        izq = ttk.Frame(self)
        izq.pack(side="left", fill="y", padx=8, pady=8)

        ttk.Label(izq, text="Vertices de la seccion (mm)",
                  font=("", 10, "bold")).pack(anchor="w")
        ttk.Label(izq, text="Ingrese los vertices en orden (horario o\n"
                            "antihorario). Doble clic para editar.",
                  foreground="#555").pack(anchor="w", pady=(0, 6))

        self.tabla = TablaEditable(izq, ["X (mm)", "Y (mm)"],
                                   on_change=self.refrescar_vista)
        self.tabla.pack(fill="y", expand=False)

        botones = ttk.Frame(izq)
        botones.pack(fill="x", pady=6)
        ttk.Button(botones, text="Agregar fila",
                   command=lambda: self.tabla.agregar_fila(["0", "0"])).pack(
            side="left", padx=2)
        ttk.Button(botones, text="Eliminar fila",
                   command=self.tabla.eliminar_seleccion).pack(side="left", padx=2)
        ttk.Button(botones, text="Limpiar",
                   command=self.tabla.limpiar).pack(side="left", padx=2)

        # Atajo: rectangulo rapido por b y h
        rect = ttk.LabelFrame(izq, text="Rectangulo rapido")
        rect.pack(fill="x", pady=8)
        ttk.Label(rect, text="b (mm):").grid(row=0, column=0, padx=4, pady=4)
        self.var_b = tk.StringVar(value="250")
        ttk.Entry(rect, textvariable=self.var_b, width=8).grid(row=0, column=1)
        ttk.Label(rect, text="h (mm):").grid(row=0, column=2, padx=4)
        self.var_h = tk.StringVar(value="500")
        ttk.Entry(rect, textvariable=self.var_h, width=8).grid(row=0, column=3)
        ttk.Button(rect, text="Generar",
                   command=self._generar_rectangulo).grid(
            row=1, column=0, columnspan=4, pady=4)

        # --- Panel derecho: vista previa ---
        der = ttk.Frame(self)
        der.pack(side="left", fill="both", expand=True, padx=8, pady=8)
        ttk.Label(der, text="Vista previa de la seccion",
                  font=("", 10, "bold")).pack(anchor="w")

        self.fig = Figure(figsize=(4.5, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self.canvas = FigureCanvasTkAgg(self.fig, master=der)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)

        # Cargar valores por defecto
        self.tabla.cargar_datos(VERTICES_DEFAULT)

    # ------------------------------------------------------------------ #
    def _generar_rectangulo(self):
        try:
            b = float(self.var_b.get().replace(",", "."))
            h = float(self.var_h.get().replace(",", "."))
        except ValueError:
            return
        self.tabla.cargar_datos([(0, 0), (b, 0), (b, h), (0, h)])

    # ------------------------------------------------------------------ #
    def get_vertices(self):
        """Devuelve la lista de vertices [(x, y), ...]."""
        return [tuple(f) for f in self.tabla.obtener_datos()]

    # ------------------------------------------------------------------ #
    def refrescar_vista(self):
        """Redibuja el poligono de la seccion y su centroide."""
        try:
            verts = self.get_vertices()
        except ValueError:
            return
        self.ax.clear()
        if len(verts) >= 3:
            xs = [v[0] for v in verts] + [verts[0][0]]
            ys = [v[1] for v in verts] + [verts[0][1]]
            self.ax.fill(xs, ys, alpha=0.25, color="#4c72b0")
            self.ax.plot(xs, ys, "-o", color="#1f3b73", ms=4)
            xc, yc = centroide_seccion(verts)
            self.ax.plot(xc, yc, "rx", ms=10, mew=2, label="Centroide")
            self.ax.legend(loc="best", fontsize=8)
            self.ax.set_aspect("equal", adjustable="datalim")
        self.ax.set_xlabel("X (mm)")
        self.ax.set_ylabel("Y (mm)")
        self.ax.grid(True, alpha=0.3)
        self.fig.tight_layout()
        self.canvas.draw_idle()
