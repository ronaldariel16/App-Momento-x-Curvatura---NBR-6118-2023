# -*- coding: utf-8 -*-
"""
gui/widgets.py

Widget reutilizable: tabla editable basada en ttk.Treeview con edicion de
celdas mediante doble clic. Usada por las pestañas de Seccion y Armaduras.
"""

import tkinter as tk
from tkinter import ttk


class TablaEditable(ttk.Frame):
    """
    Tabla editable con columnas numericas.

    Parametros
    ----------
    master : widget
        Contenedor padre.
    columnas : list[str]
        Nombres de las columnas.
    on_change : callable | None
        Funcion llamada cada vez que cambia el contenido de la tabla.
    """

    def __init__(self, master, columnas, on_change=None):
        super().__init__(master)
        self.columnas = columnas
        self.on_change = on_change
        self._editor = None

        self.tree = ttk.Treeview(self, columns=columnas, show="headings",
                                 height=8, selectmode="browse")
        for col in columnas:
            self.tree.heading(col, text=col)
            self.tree.column(col, width=110, anchor="center")

        vsb = ttk.Scrollbar(self, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=vsb.set)
        self.tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(0, weight=1)

        # Doble clic para editar una celda
        self.tree.bind("<Double-1>", self._iniciar_edicion)

    # ------------------------------------------------------------------ #
    def _iniciar_edicion(self, event):
        """Crea un Entry superpuesto sobre la celda para editarla."""
        if self._editor is not None:
            self._editor.destroy()
            self._editor = None

        fila = self.tree.identify_row(event.y)
        col = self.tree.identify_column(event.x)
        if not fila or not col:
            return

        idx_col = int(col.replace("#", "")) - 1
        x, y, w, h = self.tree.bbox(fila, col)
        valor = self.tree.set(fila, self.columnas[idx_col])

        self._editor = ttk.Entry(self.tree)
        self._editor.place(x=x, y=y, width=w, height=h)
        self._editor.insert(0, valor)
        self._editor.focus_set()
        self._editor.select_range(0, "end")

        def confirmar(_e=None):
            nuevo = self._editor.get().strip().replace(",", ".")
            try:
                float(nuevo)  # validar que sea numero
                self.tree.set(fila, self.columnas[idx_col], nuevo)
                if self.on_change:
                    self.on_change()
            except ValueError:
                pass  # valor invalido: se ignora
            self._editor.destroy()
            self._editor = None

        self._editor.bind("<Return>", confirmar)
        self._editor.bind("<FocusOut>", confirmar)
        self._editor.bind("<Escape>", lambda e: (self._editor.destroy(),
                                                  setattr(self, "_editor", None)))

    # ------------------------------------------------------------------ #
    def agregar_fila(self, valores=None):
        """Agrega una fila. valores: lista de strings/numeros por columna."""
        if valores is None:
            valores = ["0"] * len(self.columnas)
        self.tree.insert("", "end", values=[str(v) for v in valores])
        if self.on_change:
            self.on_change()

    def eliminar_seleccion(self):
        """Elimina la fila seleccionada."""
        sel = self.tree.selection()
        for item in sel:
            self.tree.delete(item)
        if self.on_change:
            self.on_change()

    def limpiar(self):
        """Elimina todas las filas."""
        for item in self.tree.get_children():
            self.tree.delete(item)
        if self.on_change:
            self.on_change()

    def obtener_datos(self):
        """Devuelve una lista de listas de floats con el contenido de la tabla."""
        datos = []
        for item in self.tree.get_children():
            fila = self.tree.item(item, "values")
            datos.append([float(str(v).replace(",", ".")) for v in fila])
        return datos

    def cargar_datos(self, filas):
        """Reemplaza el contenido con una lista de filas."""
        self.limpiar()
        for fila in filas:
            self.tree.insert("", "end", values=[str(v) for v in fila])
        if self.on_change:
            self.on_change()
