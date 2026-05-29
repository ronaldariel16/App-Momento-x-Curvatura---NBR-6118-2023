# -*- coding: utf-8 -*-
"""
gui/tab_resultados.py

Pestaña 5: ejecuta el calculo del diagrama M x phi y muestra el grafico con los
puntos caracteristicos, la tabla de resultados, barra de progreso y exportacion.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog

from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.diagrama import calcular_diagrama
from utils.exportar import exportar_csv, exportar_png


class TabResultados(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app
        self.resultado = None

        # --- Barra superior de acciones ---
        top = ttk.Frame(self)
        top.pack(fill="x", padx=8, pady=6)
        ttk.Button(top, text="Calcular", command=self.calcular).pack(side="left")
        ttk.Button(top, text="Exportar CSV",
                   command=self.exportar_csv).pack(side="left", padx=4)
        ttk.Button(top, text="Exportar grafico PNG",
                   command=self.exportar_png).pack(side="left", padx=4)
        ttk.Button(top, text="Limpiar",
                   command=self.limpiar).pack(side="left", padx=4)

        self.progress = ttk.Progressbar(top, mode="determinate", length=200)
        self.progress.pack(side="right", padx=4)
        self.lbl_estado = ttk.Label(top, text="")
        self.lbl_estado.pack(side="right", padx=8)

        # --- Panel principal dividido: grafico | tabla ---
        panel = ttk.Panedwindow(self, orient="horizontal")
        panel.pack(fill="both", expand=True, padx=8, pady=6)

        # Grafico
        marco_fig = ttk.Frame(panel)
        self.fig = Figure(figsize=(5, 4.5), dpi=100)
        self.ax = self.fig.add_subplot(111)
        self._fig_vacia()
        self.canvas = FigureCanvasTkAgg(self.fig, master=marco_fig)
        self.canvas.get_tk_widget().pack(fill="both", expand=True)
        panel.add(marco_fig, weight=3)

        # Tabla de resultados
        marco_tab = ttk.Frame(panel)
        cols = ("paso", "phi", "M", "estado")
        self.tree = ttk.Treeview(marco_tab, columns=cols, show="headings")
        encabezados = {"paso": "Paso", "phi": "phi (rad/mm)",
                       "M": "M (kN.m)", "estado": "Estado"}
        anchos = {"paso": 50, "phi": 110, "M": 90, "estado": 90}
        for c in cols:
            self.tree.heading(c, text=encabezados[c])
            self.tree.column(c, width=anchos[c], anchor="center")
        vsb = ttk.Scrollbar(marco_tab, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        vsb.pack(side="right", fill="y")
        panel.add(marco_tab, weight=2)

        # Etiqueta de resumen de puntos caracteristicos
        self.lbl_resumen = ttk.Label(self, text="", font=("", 10, "bold"),
                                     foreground="#1f3b73")
        self.lbl_resumen.pack(anchor="w", padx=10, pady=(0, 8))

    # ------------------------------------------------------------------ #
    def _fig_vacia(self):
        self.ax.clear()
        self.ax.set_xlabel("Curvatura phi (rad/mm)")
        self.ax.set_ylabel("Momento M (kN.m)")
        self.ax.set_title("Diagrama Momento x Curvatura")
        self.ax.grid(True, alpha=0.3)

    def _progreso(self, i, m):
        """Callback de progreso llamado por calcular_diagrama."""
        self.progress["maximum"] = m
        self.progress["value"] = i
        self.lbl_estado.configure(text="Calculando %d/%d" % (i, m))
        self.update_idletasks()

    # ------------------------------------------------------------------ #
    def calcular(self):
        datos = self.app.obtener_datos()
        if datos is None:
            return
        self.progress["value"] = 0
        try:
            res = calcular_diagrama(
                datos["vertices"], datos["barras"],
                datos["concreto"], datos["acero"], datos["params"],
                callback_progreso=self._progreso)
        except Exception as e:
            messagebox.showerror("Error en el calculo",
                                 "Ocurrio un error durante el calculo:\n%s" % e)
            self.lbl_estado.configure(text="Error")
            return

        if len(res["phi"]) == 0:
            messagebox.showwarning(
                "Sin resultados",
                "No se obtuvieron puntos validos. Revise la geometria, las "
                "armaduras y el intervalo de curvatura (phi_f).")
            self.lbl_estado.configure(text="Sin resultados")
            return

        self.resultado = res
        self.lbl_estado.configure(text="Listo (%d puntos)" % len(res["phi"]))
        self._dibujar(res)
        self._llenar_tabla(res)
        self._mostrar_resumen(res)

        if res["advertencias"]:
            messagebox.showinfo(
                "Avisos del calculo",
                "\n".join("- " + a for a in res["advertencias"][:6]))

    # ------------------------------------------------------------------ #
    def _dibujar(self, res):
        self.ax.clear()
        self.ax.plot(res["phi"], res["M"], "-b", lw=1.8, label="M x phi")
        colores = {"Mcr": "green", "My": "orange", "Mu": "red"}
        for nombre, color in colores.items():
            pt = res["puntos"].get(nombre)
            if pt:
                self.ax.plot(pt[0], pt[1], "o", color=color, ms=8, label=nombre,
                             clip_on=False, zorder=5)
                self.ax.annotate("%s=%.1f" % (nombre, pt[1]), (pt[0], pt[1]),
                                 textcoords="offset points", xytext=(6, 6),
                                 fontsize=8, clip_on=False)
        self.ax.set_xlabel("Curvatura phi (rad/mm)")
        self.ax.set_ylabel("Momento M (kN.m)")
        self.ax.set_title("Diagrama Momento x Curvatura")
        self.ax.grid(True, alpha=0.3)
        self.ax.legend(loc="best", fontsize=8)
        self.ax.margins(x=0.05)
        self.fig.tight_layout()
        self.canvas.draw_idle()

    def _llenar_tabla(self, res):
        for item in self.tree.get_children():
            self.tree.delete(item)
        for i in range(len(res["phi"])):
            self.tree.insert("", "end", values=(
                i + 1,
                "%.3e" % res["phi"][i],
                "%.2f" % res["M"][i],
                res["estado"][i]))

    def _mostrar_resumen(self, res):
        partes = []
        for nombre in ("Mcr", "My", "Mu"):
            pt = res["puntos"].get(nombre)
            if pt:
                partes.append("%s = %.2f kN.m" % (nombre, pt[1]))
        self.lbl_resumen.configure(text="   |   ".join(partes))

    # ------------------------------------------------------------------ #
    def exportar_csv(self):
        if self.resultado is None:
            messagebox.showinfo("Sin datos", "Primero ejecute el calculo.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".csv", filetypes=[("CSV", "*.csv")],
            title="Guardar resultados como CSV")
        if ruta:
            exportar_csv(ruta, self.resultado)
            messagebox.showinfo("Exportado", "Resultados guardados en:\n%s" % ruta)

    def exportar_png(self):
        if self.resultado is None:
            messagebox.showinfo("Sin datos", "Primero ejecute el calculo.")
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".png", filetypes=[("PNG", "*.png")],
            title="Guardar grafico como PNG")
        if ruta:
            exportar_png(ruta, self.fig, dpi=300)
            messagebox.showinfo("Exportado", "Grafico guardado en:\n%s" % ruta)

    def limpiar(self):
        self.resultado = None
        self._fig_vacia()
        self.canvas.draw_idle()
        for item in self.tree.get_children():
            self.tree.delete(item)
        self.lbl_resumen.configure(text="")
        self.lbl_estado.configure(text="")
        self.progress["value"] = 0
