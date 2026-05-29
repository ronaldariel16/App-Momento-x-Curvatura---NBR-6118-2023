# -*- coding: utf-8 -*-
"""
gui/tab_materiales.py

Pestaña 2: propiedades de los materiales (concreto y acero), con calculo
automatico opcional de fct y visualizacion de los diagramas tension-deformacion.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np
from matplotlib.figure import Figure
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

from core.materiales import Concreto, Acero


class TabMateriales(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        cont = ttk.Frame(self)
        cont.pack(anchor="nw", padx=16, pady=16)

        # --- Concreto ---
        gc = ttk.LabelFrame(cont, text="Concreto")
        gc.grid(row=0, column=0, sticky="nw", padx=8, pady=8)

        ttk.Label(gc, text="fck (MPa):").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.var_fck = tk.StringVar(value="30")
        ttk.Entry(gc, textvariable=self.var_fck, width=10).grid(row=0, column=1)

        self.var_auto_fct = tk.BooleanVar(value=False)
        ttk.Checkbutton(gc, text="Calcular fct automaticamente (0.3*fck^(2/3))",
                        variable=self.var_auto_fct,
                        command=self._toggle_fct).grid(
            row=1, column=0, columnspan=2, sticky="w", padx=4)

        ttk.Label(gc, text="fct (MPa):").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        self.var_fct = tk.StringVar(value="2.9")
        self.entry_fct = ttk.Entry(gc, textvariable=self.var_fct, width=10)
        self.entry_fct.grid(row=2, column=1)

        ttk.Label(gc, text="gamma_c:").grid(row=3, column=0, sticky="e", padx=4, pady=4)
        self.var_gc = tk.StringVar(value="1.4")
        ttk.Entry(gc, textvariable=self.var_gc, width=10).grid(row=3, column=1)

        ttk.Button(gc, text="Ver diagrama sigma-eps del concreto",
                   command=self._ver_concreto).grid(
            row=4, column=0, columnspan=2, pady=8)

        # --- Acero ---
        ga = ttk.LabelFrame(cont, text="Acero")
        ga.grid(row=0, column=1, sticky="nw", padx=8, pady=8)

        ttk.Label(ga, text="fyk (MPa):").grid(row=0, column=0, sticky="e", padx=4, pady=4)
        self.var_fyk = tk.StringVar(value="500")
        ttk.Entry(ga, textvariable=self.var_fyk, width=10).grid(row=0, column=1)

        ttk.Label(ga, text="gamma_s:").grid(row=1, column=0, sticky="e", padx=4, pady=4)
        self.var_gs = tk.StringVar(value="1.15")
        ttk.Entry(ga, textvariable=self.var_gs, width=10).grid(row=1, column=1)

        ttk.Label(ga, text="Es (MPa):").grid(row=2, column=0, sticky="e", padx=4, pady=4)
        self.var_es = tk.StringVar(value="210000")
        ttk.Entry(ga, textvariable=self.var_es, width=10).grid(row=2, column=1)

        ttk.Button(ga, text="Ver diagrama sigma-eps del acero",
                   command=self._ver_acero).grid(
            row=3, column=0, columnspan=2, pady=8)

        # Nota
        ttk.Label(cont, text="Nota: por defecto se usan valores de calculo "
                            "(fcd = fck/gamma_c, fyd = fyk/gamma_s),\n"
                            "coherentes con el manual de referencia (diagrama "
                            "parabola-rectangulo).",
                  foreground="#555").grid(row=1, column=0, columnspan=2,
                                          sticky="w", padx=8, pady=8)

    # ------------------------------------------------------------------ #
    def _toggle_fct(self):
        if self.var_auto_fct.get():
            try:
                fck = float(self.var_fck.get().replace(",", "."))
                self.var_fct.set("%.3f" % (0.3 * fck ** (2.0 / 3.0)))
            except ValueError:
                pass
            self.entry_fct.configure(state="disabled")
        else:
            self.entry_fct.configure(state="normal")

    # ------------------------------------------------------------------ #
    def get_materiales(self):
        """
        Devuelve un dict con fck, fct, fyk, gamma_c, gamma_s, Es.
        Lanza ValueError si algun campo no es numerico o es invalido.
        """
        def num(var, nombre, minimo=None):
            try:
                v = float(var.get().replace(",", "."))
            except ValueError:
                raise ValueError("El campo '%s' debe ser numerico." % nombre)
            if minimo is not None and v <= minimo:
                raise ValueError("El campo '%s' debe ser mayor que %s." % (nombre, minimo))
            return v

        fck = num(self.var_fck, "fck", 0)
        if self.var_auto_fct.get():
            fct = 0.3 * fck ** (2.0 / 3.0)
        else:
            fct = num(self.var_fct, "fct", 0)
        return {
            "fck": fck,
            "fct": fct,
            "fyk": num(self.var_fyk, "fyk", 0),
            "gamma_c": num(self.var_gc, "gamma_c", 0),
            "gamma_s": num(self.var_gs, "gamma_s", 0),
            "Es": num(self.var_es, "Es", 0),
        }

    # ------------------------------------------------------------------ #
    def _ventana_grafico(self, titulo, x, y, xlabel, ylabel):
        top = tk.Toplevel(self)
        top.title(titulo)
        fig = Figure(figsize=(5, 4), dpi=100)
        ax = fig.add_subplot(111)
        ax.plot(x, y, "-b", lw=2)
        ax.axhline(0, color="k", lw=0.6)
        ax.axvline(0, color="k", lw=0.6)
        ax.set_xlabel(xlabel)
        ax.set_ylabel(ylabel)
        ax.set_title(titulo)
        ax.grid(True, alpha=0.3)
        fig.tight_layout()
        canvas = FigureCanvasTkAgg(fig, master=top)
        canvas.draw()
        canvas.get_tk_widget().pack(fill="both", expand=True)

    def _ver_concreto(self):
        try:
            m = self.get_materiales()
        except ValueError as e:
            messagebox.showerror("Datos invalidos", str(e))
            return
        c = Concreto(m["fck"], m["fct"], m["gamma_c"])
        eps = np.linspace(-2 * c.eps_cr, c.eps_cu * 1.1, 600)
        sig = c.sigma(eps)
        self._ventana_grafico("Concreto sigma-eps (compresion +)",
                              eps * 1000, sig, "eps (1/1000)", "sigma (MPa)")

    def _ver_acero(self):
        try:
            m = self.get_materiales()
        except ValueError as e:
            messagebox.showerror("Datos invalidos", str(e))
            return
        s = Acero(m["fyk"], m["gamma_s"], m["Es"])
        eps = np.linspace(-1.5 * s.eps_yd * 5, 1.5 * s.eps_yd * 5, 600)
        sig = s.sigma(eps)
        self._ventana_grafico("Acero sigma-eps",
                              eps * 1000, sig, "eps (1/1000)", "sigma (MPa)")
