# -*- coding: utf-8 -*-
"""
gui/app.py

Ventana principal de la aplicacion. Coordina las cinco pestañas y centraliza
la recopilacion y validacion de los datos de entrada antes del calculo.
"""

import tkinter as tk
from tkinter import ttk, messagebox

import numpy as np

from core.materiales import Concreto, Acero
from .tab_seccion import TabSeccion
from .tab_materiales import TabMateriales
from .tab_armaduras import TabArmaduras
from .tab_parametros import TabParametros
from .tab_resultados import TabResultados


class App(tk.Tk):
    """Aplicacion principal Momento x Curvatura."""

    def __init__(self):
        super().__init__()
        self.title("Diagrama Momento x Curvatura - NBR 6118:2023")
        self.geometry("1000x720")
        self.minsize(900, 640)

        # Estilo
        style = ttk.Style(self)
        try:
            style.theme_use("clam")
        except tk.TclError:
            pass

        # Notebook con las pestañas
        self.notebook = ttk.Notebook(self)
        self.notebook.pack(fill="both", expand=True, padx=8, pady=8)

        self.tab_seccion = TabSeccion(self.notebook, self)
        self.tab_materiales = TabMateriales(self.notebook, self)
        self.tab_armaduras = TabArmaduras(self.notebook, self)
        self.tab_parametros = TabParametros(self.notebook, self)
        self.tab_resultados = TabResultados(self.notebook, self)

        self.notebook.add(self.tab_seccion, text="1. Seccion")
        self.notebook.add(self.tab_materiales, text="2. Materiales")
        self.notebook.add(self.tab_armaduras, text="3. Armaduras")
        self.notebook.add(self.tab_parametros, text="4. Parametros")
        self.notebook.add(self.tab_resultados, text="5. Resultados")

        # Refrescar la vista de armaduras cuando se cambia de pestaña
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_changed)

    # ------------------------------------------------------------------ #
    def _on_tab_changed(self, _event):
        """Al entrar a la pestaña de armaduras, refrescar la vista con la seccion."""
        actual = self.notebook.select()
        if actual == str(self.tab_armaduras):
            try:
                self.tab_armaduras.refrescar_vista()
            except Exception:
                pass

    # ------------------------------------------------------------------ #
    def obtener_datos(self):
        """
        Recopila y valida todos los datos de entrada de las pestañas.

        Retorna
        -------
        dict | None
            Diccionario con claves: vertices, barras, concreto, acero, params.
            Devuelve None si hay un error de validacion (ya notificado al usuario).
        """
        try:
            vertices = self.tab_seccion.get_vertices()
            if len(vertices) < 3:
                messagebox.showerror("Error de geometria",
                                     "La seccion debe tener al menos 3 vertices.")
                return None

            mat = self.tab_materiales.get_materiales()
            concreto = Concreto(fck=mat["fck"], fct=mat["fct"],
                                gamma_c=mat["gamma_c"])
            acero = Acero(fyk=mat["fyk"], gamma_s=mat["gamma_s"], Es=mat["Es"])

            barras = self.tab_armaduras.get_barras()

            # Validar que las barras esten dentro de la seccion
            from core.geometria import barra_dentro
            fuera = [i + 1 for i, b in enumerate(barras)
                     if not barra_dentro(b[1], b[2], vertices)]
            if fuera:
                if not messagebox.askyesno(
                        "Barras fuera de la seccion",
                        "Las barras %s estan fuera del poligono de la seccion.\n"
                        "¿Desea continuar de todos modos?" % fuera):
                    return None

            params = self.tab_parametros.get_parametros()

            return {
                "vertices": vertices,
                "barras": np.asarray(barras, dtype=float).reshape(-1, 3),
                "concreto": concreto,
                "acero": acero,
                "params": params,
            }
        except ValueError as e:
            messagebox.showerror("Error en los datos de entrada", str(e))
            return None
