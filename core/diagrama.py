# -*- coding: utf-8 -*-
"""
core/diagrama.py

Loop principal: barrido de curvatura para construir el diagrama Momento-Curvatura
(M x phi) y deteccion de puntos caracteristicos:
    - Mcr : momento de fissuracion (primer punto fissurado del concreto en traccion)
    - My  : momento de escoamento (primera barra que alcanza eps_yd)
    - Mu  : momento ultimo (maximo del diagrama, o cuando se alcanza eps_cu)
"""

import numpy as np

try:
    # Uso como paquete (importado desde la GUI)
    from .materiales import Concreto, Acero
    from .geometria import discretizar_seccion, centroide_seccion, limites_y
    from .equilibrio import encontrar_linea_neutra, calcular_resultante
except ImportError:
    # Uso como script directo (python diagrama.py para validacion)
    from materiales import Concreto, Acero
    from geometria import discretizar_seccion, centroide_seccion, limites_y
    from equilibrio import encontrar_linea_neutra, calcular_resultante


# Estados posibles de un punto del diagrama
ESTADO_ELASTICO = "Elastico"
ESTADO_FISSURADO = "Fissurado"
ESTADO_FLUENCIA = "Fluencia"
ESTADO_ULTIMO = "Ultimo"


def calcular_diagrama(vertices, barras, concreto, acero, params_numericos,
                      callback_progreso=None):
    """
    Construye el diagrama M x phi de la seccion.

    Parametros
    ----------
    vertices : list[tuple[float, float]]
        Vertices del poligono de la seccion [mm].
    barras : np.ndarray (b,3)
        Barras de acero [As, x, y] en [mm^2, mm, mm].
    concreto : Concreto
        Modelo del concreto.
    acero : Acero
        Modelo del acero.
    params_numericos : dict
        Claves: nx, ny, tol, phi_i, phi_f, m.
        Si phi_i es None o <= 0, se usa phi_f / m.
    callback_progreso : callable | None
        Funcion opcional callback(i, m) para reportar avance (usada por la GUI).

    Retorna
    -------
    dict
        {
          'phi'      : np.ndarray de curvaturas validas [rad/mm],
          'M'        : np.ndarray de momentos [kN.m],
          'y_na'     : np.ndarray de posiciones de linea neutra [mm],
          'estado'   : list[str] estado por punto,
          'puntos'   : {'Mcr': (phi,M)|None, 'My': (phi,M)|None, 'Mu': (phi,M)|None},
          'advertencias': list[str]
        }
    """
    nx = int(params_numericos.get("nx", 5))
    ny = int(params_numericos.get("ny", 30))
    tol = float(params_numericos.get("tol", 1e-4))
    phi_f = float(params_numericos.get("phi_f", 3e-5))
    m = int(params_numericos.get("m", 100))
    phi_i = params_numericos.get("phi_i", None)
    if phi_i is None or float(phi_i) <= 0.0:
        phi_i = phi_f / m
    phi_i = float(phi_i)

    barras = np.asarray(barras, dtype=float).reshape(-1, 3) if barras is not None \
        else np.empty((0, 3))

    # Discretizacion y referencia de momento (centroide geometrico)
    puntos = discretizar_seccion(vertices, nx, ny)
    _, yc = centroide_seccion(vertices)
    y_min, y_max = limites_y(vertices)
    altura = y_max - y_min

    phis = np.linspace(phi_i, phi_f, m)

    phi_list, M_list, yna_list, estado_list = [], [], [], []
    advertencias = []

    punto_cr = None
    punto_y = None
    # Para Mcr usamos el pico de momento ANTES de la primera fissuracion
    # (definicion fisica del momento de fissuracion: justo antes de perder
    # la traccion del concreto). Guardamos el ultimo punto no fissurado.
    M_pre_crack = None
    phi_pre_crack = None
    ya_fissuro = False

    for i, phi in enumerate(phis):
        if callback_progreso is not None:
            callback_progreso(i + 1, m)

        y_na = encontrar_linea_neutra(phi, puntos, barras, concreto, acero,
                                      altura=altura, y_ref=yc, tol=tol)
        if y_na is None:
            advertencias.append(
                "Sin convergencia de linea neutra en phi=%.3e (paso %d)" % (phi, i))
            continue

        N, M = calcular_resultante(phi, y_na, puntos, barras, concreto, acero,
                                   y_ref=yc)
        M_kNm = M / 1e6  # N.mm -> kN.m

        # --- Determinacion de estados del paso ---
        # Concreto: deformaciones en los puntos de integracion
        eps_c = phi * (puntos[:, 1] - y_na)
        fibra_max_comp = eps_c.max()       # compresion (positivo)
        fibra_max_trac = -eps_c.min()      # traccion (positivo si min negativo)

        fissurado = fibra_max_trac > concreto.eps_cr
        ultimo = fibra_max_comp >= concreto.eps_cu

        # Acero: deformaciones en las barras
        escoado = False
        if len(barras) > 0:
            eps_s = phi * (barras[:, 2] - y_na)
            escoado = np.any(np.abs(eps_s) >= acero.eps_yd)

        # Etiqueta de estado (jerarquia: Ultimo > Fluencia > Fissurado > Elastico)
        if ultimo:
            estado = ESTADO_ULTIMO
        elif escoado:
            estado = ESTADO_FLUENCIA
        elif fissurado:
            estado = ESTADO_FISSURADO
        else:
            estado = ESTADO_ELASTICO

        # Registrar momento de fissuracion: el pico justo antes de fissurar.
        if not ya_fissuro:
            if fissurado:
                ya_fissuro = True
                # Mcr = mayor momento alcanzado hasta antes de fissurar
                if M_pre_crack is not None and M_pre_crack >= M_kNm:
                    punto_cr = (phi_pre_crack, M_pre_crack)
                else:
                    punto_cr = (phi, M_kNm)
            else:
                # Aun no fissura: actualizar el candidato a pico pre-fissuracion
                if M_pre_crack is None or M_kNm >= M_pre_crack:
                    M_pre_crack = M_kNm
                    phi_pre_crack = phi
        if punto_y is None and escoado:
            punto_y = (phi, M_kNm)

        phi_list.append(phi)
        M_list.append(M_kNm)
        yna_list.append(y_na)
        estado_list.append(estado)

    phi_arr = np.array(phi_list)
    M_arr = np.array(M_list)
    yna_arr = np.array(yna_list)

    # Momento ultimo = maximo del diagrama
    punto_u = None
    if len(M_arr) > 0:
        idx_max = int(np.argmax(M_arr))
        punto_u = (float(phi_arr[idx_max]), float(M_arr[idx_max]))
        # Si el maximo cae en el ultimo paso valido, el diagrama puede no haber
        # alcanzado su pico real: conviene aumentar phi_f.
        if idx_max >= len(M_arr) - 1:
            advertencias.append(
                "El momento maximo se alcanza en el ultimo paso de curvatura. "
                "El diagrama podria no haber llegado a su pico real; "
                "considere aumentar phi_f.")

    return {
        "phi": phi_arr,
        "M": M_arr,
        "y_na": yna_arr,
        "estado": estado_list,
        "puntos": {"Mcr": punto_cr, "My": punto_y, "Mu": punto_u},
        "advertencias": advertencias,
    }


# ---------------------------------------------------------------------------
# Validacion rapida (ejemplo del manual), SIN GUI.
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    import matplotlib
    matplotlib.use("Agg")  # backend sin display para entorno headless
    import matplotlib.pyplot as plt

    # --- Datos del ejemplo del manual ---
    vertices = [(0, 0), (250, 0), (250, 500), (0, 500)]      # b=250, h=500 mm
    barras = np.array([
        [123.0, 30.0, 30.0],
        [123.0, 220.0, 30.0],
        [123.0, 30.0, 470.0],
        [123.0, 220.0, 470.0],
    ])
    concreto = Concreto(fck=30.0, fct=2.9, gamma_c=1.4)
    acero = Acero(fyk=500.0, gamma_s=1.15)
    params = {"nx": 5, "ny": 30, "tol": 1e-4,
              "phi_i": None, "phi_f": 3e-5, "m": 100}

    res = calcular_diagrama(vertices, barras, concreto, acero, params)

    p = res["puntos"]
    print("=== Validacion ejemplo del manual (b=250, h=500, fck=30, fy=500) ===")
    print("Puntos validos:", len(res["phi"]))
    if p["Mcr"]:
        print("Mcr = %.2f kN.m  (phi = %.3e rad/mm)" % (p["Mcr"][1], p["Mcr"][0]))
    if p["My"]:
        print("My  = %.2f kN.m  (phi = %.3e rad/mm)" % (p["My"][1], p["My"][0]))
    if p["Mu"]:
        print("Mu  = %.2f kN.m  (phi = %.3e rad/mm)" % (p["Mu"][1], p["Mu"][0]))
    if res["advertencias"]:
        print("Advertencias:", len(res["advertencias"]))

    # Grafico de validacion
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.plot(res["phi"], res["M"], "-b", lw=1.8, label="M x phi")
    for nombre, color in [("Mcr", "green"), ("My", "orange"), ("Mu", "red")]:
        pt = p[nombre]
        if pt:
            ax.plot(pt[0], pt[1], "o", color=color, ms=8, label=nombre)
            ax.annotate("%s=%.1f" % (nombre, pt[1]), (pt[0], pt[1]),
                        textcoords="offset points", xytext=(6, 6), fontsize=9)
    ax.set_xlabel(r"Curvatura $\phi$ (rad/mm)")
    ax.set_ylabel("Momento M (kN.m)")
    ax.set_title("Diagrama Momento x Curvatura - Validacion")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    fig.savefig("validacion_diagrama.png", dpi=150)
    print("Grafico guardado en validacion_diagrama.png")
