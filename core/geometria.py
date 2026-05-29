# -*- coding: utf-8 -*-
"""
core/geometria.py

Discretizacion de la seccion transversal poligonal en puntos de integracion
(metodo de grilla rectangular con mascara por poligono) y calculo del
centroide geometrico.

Convencion de ejes:
    - Eje X horizontal, positivo a la derecha.
    - Eje Y vertical, positivo hacia arriba.
    - La fibra mas comprimida (para momento positivo) es la de mayor Y.
"""

import numpy as np

# Intento de usar shapely; si no esta disponible, se usa ray casting propio.
try:
    from shapely.geometry import Polygon, Point
    _SHAPELY = True
except Exception:  # pragma: no cover
    _SHAPELY = False


def _punto_en_poligono(x, y, vertices):
    """
    Algoritmo de ray casting (par/impar) como respaldo si shapely no existe.

    Parametros
    ----------
    x, y : float
        Coordenadas del punto a testear.
    vertices : list[tuple[float, float]]
        Vertices del poligono en orden.

    Retorna
    -------
    bool
        True si el punto esta dentro del poligono.
    """
    n = len(vertices)
    dentro = False
    j = n - 1
    for i in range(n):
        xi, yi = vertices[i]
        xj, yj = vertices[j]
        if ((yi > y) != (yj > y)) and \
           (x < (xj - xi) * (y - yi) / (yj - yi + 1e-300) + xi):
            dentro = not dentro
        j = i
    return dentro


def centroide_seccion(vertices):
    """
    Centroide geometrico de un poligono simple (formula del area con signo).

    Parametros
    ----------
    vertices : list[tuple[float, float]]
        Vertices del poligono en orden (horario o antihorario).

    Retorna
    -------
    tuple[float, float]
        Coordenadas (xc, yc) del centroide [mm].
    """
    v = np.asarray(vertices, dtype=float)
    x = v[:, 0]
    y = v[:, 1]
    x1 = np.roll(x, -1)
    y1 = np.roll(y, -1)
    cross = x * y1 - x1 * y
    area = cross.sum() / 2.0
    if abs(area) < 1e-12:
        # Degenerado: devolver promedio simple de vertices
        return float(x.mean()), float(y.mean())
    xc = ((x + x1) * cross).sum() / (6.0 * area)
    yc = ((y + y1) * cross).sum() / (6.0 * area)
    return float(xc), float(yc)


def area_poligono(vertices):
    """Area del poligono (valor absoluto) [mm^2]."""
    v = np.asarray(vertices, dtype=float)
    x = v[:, 0]
    y = v[:, 1]
    return abs(np.sum(x * np.roll(y, -1) - np.roll(x, -1) * y)) / 2.0


def discretizar_seccion(vertices, nx, ny):
    """
    Discretiza la seccion en una grilla de puntos de integracion.

    Se construye una grilla rectangular de nx x ny celdas sobre la bounding box
    del poligono. Se conserva el centro de cada celda cuyo centro cae dentro del
    poligono, con su area tributaria.

    Parametros
    ----------
    vertices : list[tuple[float, float]]
        Vertices del poligono en mm.
    nx : int
        Numero de divisiones en X.
    ny : int
        Numero de divisiones en Y.

    Retorna
    -------
    np.ndarray  (k, 3)
        Filas [x_centro, y_centro, area_tributaria] de los k puntos internos.
    """
    v = np.asarray(vertices, dtype=float)
    x_min, y_min = v[:, 0].min(), v[:, 1].min()
    x_max, y_max = v[:, 0].max(), v[:, 1].max()

    dx = (x_max - x_min) / nx
    dy = (y_max - y_min) / ny
    area_celda = dx * dy

    # Centros de celda
    xs = x_min + (np.arange(nx) + 0.5) * dx
    ys = y_min + (np.arange(ny) + 0.5) * dy
    XX, YY = np.meshgrid(xs, ys)
    XX = XX.ravel()
    YY = YY.ravel()

    if _SHAPELY:
        poly = Polygon(vertices)
        mask = np.array([poly.contains(Point(px, py)) for px, py in zip(XX, YY)])
    else:
        mask = np.array([_punto_en_poligono(px, py, vertices)
                         for px, py in zip(XX, YY)])

    puntos = np.column_stack([XX[mask], YY[mask],
                              np.full(mask.sum(), area_celda)])
    return puntos


def limites_y(vertices):
    """Devuelve (y_min, y_max) de la seccion [mm]."""
    v = np.asarray(vertices, dtype=float)
    return float(v[:, 1].min()), float(v[:, 1].max())


def barra_dentro(x, y, vertices):
    """True si la coordenada de una barra esta dentro del poligono de la seccion."""
    if _SHAPELY:
        return Polygon(vertices).contains(Point(x, y))
    return _punto_en_poligono(x, y, vertices)


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    # Rectangulo 250 x 500
    verts = [(0, 0), (250, 0), (250, 500), (0, 500)]
    pts = discretizar_seccion(verts, nx=5, ny=30)
    A_disc = pts[:, 2].sum()
    A_real = area_poligono(verts)
    xc, yc = centroide_seccion(verts)
    print("Puntos de integracion: %d" % len(pts))
    print("Area discretizada: %.1f mm^2 | Area real: %.1f mm^2 | error: %.3f%%"
          % (A_disc, A_real, 100 * abs(A_disc - A_real) / A_real))
    print("Centroide: (%.1f, %.1f) mm" % (xc, yc))
    print("Shapely disponible:", _SHAPELY)
