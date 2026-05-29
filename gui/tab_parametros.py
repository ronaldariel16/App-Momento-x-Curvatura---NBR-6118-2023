# -*- coding: utf-8 -*-
"""
gui/tab_parametros.py

Pestaña 4: parametros numericos del algoritmo de barrido de curvatura.
"""

import tkinter as tk
from tkinter import ttk


class TabParametros(ttk.Frame):
    def __init__(self, master, app):
        super().__init__(master)
        self.app = app

        cont = ttk.Frame(self)
        cont.pack(anchor="nw", padx=20, pady=20)

        ttk.Label(cont, text="Parametros numericos",
                  font=("", 11, "bold")).grid(row=0, column=0, columnspan=3,
                                              sticky="w", pady=(0, 10))

        # (variable, etiqueta, valor_default, ayuda)
        campos = [
            ("nx", "Divisiones en X (nx):", "5",
             "Numero de divisiones de la malla en direccion horizontal."),
            ("ny", "Divisiones en Y (ny):", "30",
             "Divisiones en vertical. Mayor ny = mejor captura de gradientes."),
            ("tol", "Tolerancia (tol):", "1e-4",
             "Criterio adimensional de convergencia del equilibrio de fuerzas."),
            ("phi_i", "Curvatura inicial phi_i:", "",
             "Vacio = automatico (phi_f / m). En rad/mm."),
            ("phi_f", "Curvatura final phi_f:", "3e-5",
             "Curvatura maxima del barrido (rad/mm)."),
            ("m", "Numero de pasos (m):", "100",
             "Cantidad de puntos del diagrama."),
        ]

        self.vars = {}
        for i, (clave, etiqueta, default, ayuda) in enumerate(campos, start=1):
            ttk.Label(cont, text=etiqueta).grid(row=i, column=0, sticky="e",
                                                padx=4, pady=6)
            var = tk.StringVar(value=default)
            self.vars[clave] = var
            ttk.Entry(cont, textvariable=var, width=14).grid(row=i, column=1,
                                                             padx=4)
            ttk.Label(cont, text=ayuda, foreground="#555").grid(
                row=i, column=2, sticky="w", padx=8)

        ttk.Label(cont, text="Recomendacion: para mayor precision use ny >= 50.",
                  foreground="#a05000").grid(row=len(campos) + 1, column=0,
                                             columnspan=3, sticky="w", pady=(14, 0))
        ttk.Label(cont, text="Si el momento maximo cae en el ultimo paso, "
                            "aumente phi_f para capturar el pico real.",
                  foreground="#a05000").grid(row=len(campos) + 2, column=0,
                                             columnspan=3, sticky="w")

    # ------------------------------------------------------------------ #
    def get_parametros(self):
        """Devuelve el dict de parametros numericos validados."""
        def num(clave, tipo, minimo=None, permitir_vacio=False):
            txt = self.vars[clave].get().strip().replace(",", ".")
            if txt == "" and permitir_vacio:
                return None
            try:
                v = tipo(float(txt)) if tipo is int else tipo(txt)
            except ValueError:
                raise ValueError("El parametro '%s' no es valido." % clave)
            if minimo is not None and v <= minimo:
                raise ValueError("El parametro '%s' debe ser mayor que %s."
                                 % (clave, minimo))
            return v

        return {
            "nx": num("nx", int, 0),
            "ny": num("ny", int, 0),
            "tol": num("tol", float, 0),
            "phi_i": num("phi_i", float, 0, permitir_vacio=True),
            "phi_f": num("phi_f", float, 0),
            "m": num("m", int, 1),
        }
