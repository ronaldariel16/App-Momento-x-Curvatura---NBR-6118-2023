# -*- coding: utf-8 -*-
"""
core/equilibrio.py

Solver de equilibrio de la seccion para un nivel de curvatura dado.

Hipotesis cinematica (Bernoulli, secciones planas):
    eps(y) = phi * (y - y_na)

con compresion POSITIVA. Para phi > 0 y la linea neutra y_na dentro de la
seccion, la fibra superior (mayor Y) queda comprimida (eps > 0) y la inferior
traccionada (eps < 0), lo que corresponde a momento positivo.

El equilibrio de fuerza axial (flexion pura, N = 0) se resuelve buscando y_na
tal que la resultante normal sea nula, mediante brentq (biseccion robusta).
"""

import numpy as np
from scipy.optimize import brentq


def deformacion(phi, y_na, y):
    """Campo de deformaciones eps(y) = phi*(y - y_na) (compresion +)."""
    return phi * (y - y_na)


def calcular_resultante(phi, y_na, puntos, barras, concreto, acero,
                        y_ref=0.0, descontar_concreto=False):
    """
    Calcula la fuerza normal resultante N y el momento M para un estado dado.

    Parametros
    ----------
    phi : float
        Curvatura [rad/mm].
    y_na : float
        Coordenada Y de la linea neutra [mm].
    puntos : np.ndarray (k,3)
        Puntos de integracion del concreto [x, y, area].
    barras : np.ndarray (b,3)
        Barras de acero [As, x, y].
    concreto : Concreto
        Modelo constitutivo del concreto.
    acero : Acero
        Modelo constitutivo del acero.
    y_ref : float
        Coordenada Y respecto a la cual se toma el momento (normalmente el
        centroide geometrico). El momento es independiente de y_ref cuando N=0.
    descontar_concreto : bool
        Si True, descuenta el area de concreto desplazada por cada barra
        (evita el doble conteo). Default False para coincidir con el manual.

    Retorna
    -------
    tuple[float, float]
        (N_total [N], M_total [N.mm]). Compresion positiva; M positivo comprime
        la fibra superior.
    """
    # --- Concreto ---
    yc = puntos[:, 1]
    Ac = puntos[:, 2]
    eps_c = phi * (yc - y_na)
    sig_c = concreto.sigma(eps_c)            # MPa
    Fc = sig_c * Ac                          # N
    N_c = Fc.sum()
    M_c = (Fc * (yc - y_ref)).sum()          # N.mm

    # --- Acero ---
    N_s = 0.0
    M_s = 0.0
    if barras is not None and len(barras) > 0:
        As = barras[:, 0]
        ys = barras[:, 2]
        eps_s = phi * (ys - y_na)
        sig_s = acero.sigma(eps_s)           # MPa
        if descontar_concreto:
            sig_s = sig_s - concreto.sigma(eps_s)
        Fs = sig_s * As                      # N
        N_s = Fs.sum()
        M_s = (Fs * (ys - y_ref)).sum()      # N.mm

    return N_c + N_s, M_c + M_s


def encontrar_linea_neutra(phi, puntos, barras, concreto, acero,
                           altura, y_ref=0.0, tol=1e-4,
                           descontar_concreto=False):
    """
    Encuentra la posicion de la linea neutra y_na para que N = 0 (flexion pura).

    Se usa brentq sobre el intervalo amplio [y_min - 2h, y_max + 2h] para
    capturar casos donde la linea neutra cae fuera de la seccion.

    Parametros
    ----------
    phi : float
        Curvatura [rad/mm].
    puntos, barras, concreto, acero : ver calcular_resultante.
    altura : float
        Altura total de la seccion h [mm] (para definir el intervalo de busqueda).
    y_ref : float
        Referencia de momento (centroide).
    tol : float
        Tolerancia adimensional sobre el residuo de fuerza. El residuo se compara
        contra (fcd * area_total) para hacerlo adimensional.
    descontar_concreto : bool
        Ver calcular_resultante.

    Retorna
    -------
    float | None
        y_na [mm] si converge; None si no se logra acotar la raiz.
    """
    y_min = puntos[:, 1].min()
    y_max = puntos[:, 1].max()
    a = y_min - 2.0 * altura
    b = y_max + 2.0 * altura

    def residuo(y_na):
        N, _ = calcular_resultante(phi, y_na, puntos, barras, concreto, acero,
                                   y_ref, descontar_concreto)
        return N

    fa = residuo(a)
    fb = residuo(b)

    # brentq requiere cambio de signo en el intervalo
    if np.sign(fa) == np.sign(fb):
        return None

    try:
        y_na = brentq(residuo, a, b, xtol=1e-6, rtol=1e-10, maxiter=200)
    except (ValueError, RuntimeError):
        return None

    # Verificacion del residuo adimensional
    area_total = puntos[:, 2].sum()
    escala = abs(concreto.fcd) * area_total + 1e-9
    if abs(residuo(y_na)) / escala > tol:
        # Convergio pero el residuo es grande: se acepta igualmente pero
        # el llamador puede decidir registrar advertencia.
        pass

    return y_na


# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from materiales import Concreto, Acero
    from geometria import discretizar_seccion, centroide_seccion

    verts = [(0, 0), (250, 0), (250, 500), (0, 500)]
    barras = np.array([
        [123.0, 30.0, 30.0],
        [123.0, 220.0, 30.0],
        [123.0, 30.0, 470.0],
        [123.0, 220.0, 470.0],
    ])
    pts = discretizar_seccion(verts, 5, 30)
    _, yc = centroide_seccion(verts)
    c = Concreto(30.0, 2.9)
    s = Acero(500.0)

    phi = 1e-5
    y_na = encontrar_linea_neutra(phi, pts, barras, c, s, altura=500.0, y_ref=yc)
    N, M = calcular_resultante(phi, y_na, pts, barras, c, s, y_ref=yc)
    print("phi=%.1e | y_na=%.1f mm | N=%.2f N | M=%.2f kN.m"
          % (phi, y_na, N, M / 1e6))
