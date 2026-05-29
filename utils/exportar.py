# -*- coding: utf-8 -*-
"""
utils/exportar.py

Exportacion de resultados del diagrama M x phi a CSV y del grafico a PNG.
"""

import csv


def exportar_csv(ruta, resultado):
    """
    Exporta la tabla de resultados a un archivo CSV.

    Parametros
    ----------
    ruta : str
        Ruta del archivo CSV de salida.
    resultado : dict
        Diccionario devuelto por calcular_diagrama (claves phi, M, y_na, estado).
    """
    phi = resultado["phi"]
    M = resultado["M"]
    yna = resultado["y_na"]
    estado = resultado["estado"]

    with open(ruta, "w", newline="", encoding="utf-8") as f:
        w = csv.writer(f, delimiter=";")
        w.writerow(["paso", "phi (rad/mm)", "M (kN.m)", "y_na (mm)", "estado"])
        for i in range(len(phi)):
            w.writerow([i + 1,
                        "%.6e" % phi[i],
                        "%.4f" % M[i],
                        "%.2f" % yna[i],
                        estado[i]])

        # Resumen de puntos caracteristicos
        w.writerow([])
        w.writerow(["Punto caracteristico", "phi (rad/mm)", "M (kN.m)"])
        for nombre in ("Mcr", "My", "Mu"):
            pt = resultado["puntos"].get(nombre)
            if pt:
                w.writerow([nombre, "%.6e" % pt[0], "%.4f" % pt[1]])


def exportar_png(ruta, figura, dpi=300):
    """
    Guarda una figura de matplotlib como PNG.

    Parametros
    ----------
    ruta : str
        Ruta del archivo PNG de salida.
    figura : matplotlib.figure.Figure
        Figura a guardar.
    dpi : int
        Resolucion (default 300).
    """
    figura.savefig(ruta, dpi=dpi, bbox_inches="tight")
