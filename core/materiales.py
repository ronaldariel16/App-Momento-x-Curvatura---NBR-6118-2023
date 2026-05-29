# -*- coding: utf-8 -*-
"""
core/materiales.py

Modelos constitutivos (leyes tension-deformacion) para concreto y acero,
segun la NBR 6118:2023.

CONVENCION DE SIGNOS UNIFICADA EN TODO EL PROGRAMA:
    - Compresion POSITIVA, traccion NEGATIVA (tanto para concreto como acero).
    - Esto difiere de la nota literal del prompt original ("traccion positiva en
      el acero"), que mezclaba convenciones. Se unifica deliberadamente para
      evitar errores de signo en el equilibrio. La interpretacion fisica es
      identica; solo cambia el signo de referencia.

Las tensiones se devuelven en MPa y las deformaciones son adimensionales.
Todas las funciones aceptan escalares o arrays de numpy.
"""

import numpy as np


class Concreto:
    """
    Modelo de concreto:
      - Compresion: parabola-rectangulo (NBR 6118:2023), valido para fck <= 50 MPa.
      - Traccion: bilineal simplificado (elastico hasta fissuracion, luego nulo).

    Parametros
    ----------
    fck : float
        Resistencia caracteristica a compresion del concreto [MPa].
    fct : float | None
        Resistencia a traccion [MPa]. Si es None, se estima como 0.3*fck^(2/3).
    gamma_c : float
        Coeficiente de minoracion del concreto (default 1.4).
    usar_fcd : bool
        Si True usa fcd = fck/gamma_c (valores de diseno, coherente con el manual
        de referencia). Si False usa fck directamente (respuesta media estimada).
    """

    def __init__(self, fck, fct=None, gamma_c=1.4, usar_fcd=True):
        self.fck = float(fck)
        self.gamma_c = float(gamma_c)
        self.usar_fcd = bool(usar_fcd)

        # Resistencia de calculo de compresion
        self.fcd = self.fck / self.gamma_c if usar_fcd else self.fck

        # Coeficiente alpha_c (0.85) y parametros del diagrama parabola-rectangulo
        self.alpha_c = 0.85
        self.eps_c2 = 0.002    # deformacion al final de la parabola (fck <= 50 MPa)
        self.eps_cu = 0.0035   # deformacion ultima de compresion (fck <= 50 MPa)
        self.n = 2.0           # exponente de la parabola (fck <= 50 MPa)

        # Modulo tangente inicial (NBR 6118:2023). Eci = alpha_E * 5600 * sqrt(fck)
        # Se adopta alpha_E = 1.0 (agregado generico) como simplificacion.
        self.Eci = 5600.0 * np.sqrt(self.fck)

        # Resistencia a traccion
        if fct is None:
            self.fct = 0.3 * self.fck ** (2.0 / 3.0)
        else:
            self.fct = float(fct)

        # Deformacion de fissuracion (en magnitud)
        self.eps_cr = self.fct / self.Eci

    def sigma(self, eps):
        """
        Tension del concreto para una deformacion dada (compresion positiva).

        Parametros
        ----------
        eps : float | np.ndarray
            Deformacion (compresion +, traccion -).

        Retorna
        -------
        float | np.ndarray
            Tension [MPa] (compresion +, traccion -). Cero si el material
            esta aplastado (eps > eps_cu) o fissurado (|eps| > eps_cr en traccion).
        """
        escalar = np.isscalar(eps)
        eps = np.asarray(eps, dtype=float)
        sig = np.zeros_like(eps)

        # --- Rama de compresion ---
        m_par = (eps > 0.0) & (eps <= self.eps_c2)          # parabola
        m_plat = (eps > self.eps_c2) & (eps <= self.eps_cu)  # plato (rectangulo)

        sig[m_par] = self.alpha_c * self.fcd * (
            1.0 - (1.0 - eps[m_par] / self.eps_c2) ** self.n
        )
        sig[m_plat] = self.alpha_c * self.fcd
        # eps > eps_cu  -> aplastado -> sig = 0 (ya inicializado)

        # --- Rama de traccion (elastica hasta fissuracion) ---
        m_ten = (eps < 0.0) & (-eps <= self.eps_cr)
        sig[m_ten] = self.Eci * eps[m_ten]  # eps negativo -> sig negativo (traccion)
        # -eps > eps_cr -> fissurado -> sig = 0 (ya inicializado)

        return float(sig) if escalar else sig


class Acero:
    """
    Modelo bilineal elastico-plastico perfecto para acero pasivo (NBR 6118:2023).

    Parametros
    ----------
    fyk : float
        Tension de escoamento caracteristica [MPa] (ej. 500 para CA50).
    gamma_s : float
        Coeficiente de minoracion del acero (default 1.15).
    Es : float
        Modulo de elasticidad [MPa] (default 210000).
    eps_su : float
        Deformacion ultima admisible (default 0.10 = 10/1000... aqui 0.10 = 10%).
        Nota: el manual de referencia usa eps_su = 0.10.
    usar_fyd : bool
        Si True usa fyd = fyk/gamma_s (diseno). Si False usa fyk directamente.
    """

    def __init__(self, fyk, gamma_s=1.15, Es=210000.0, eps_su=0.10, usar_fyd=True):
        self.fyk = float(fyk)
        self.gamma_s = float(gamma_s)
        self.Es = float(Es)
        self.eps_su = float(eps_su)
        self.usar_fyd = bool(usar_fyd)

        self.fyd = self.fyk / self.gamma_s if usar_fyd else self.fyk
        self.eps_yd = self.fyd / self.Es  # deformacion de escoamento de calculo

    def sigma(self, eps):
        """
        Tension del acero para una deformacion dada (compresion +, traccion -).

        Parametros
        ----------
        eps : float | np.ndarray
            Deformacion del acero.

        Retorna
        -------
        float | np.ndarray
            Tension [MPa]. Cero si |eps| > eps_su (rotura).
        """
        escalar = np.isscalar(eps)
        eps = np.asarray(eps, dtype=float)
        sig = np.zeros_like(eps)
        abse = np.abs(eps)

        m_el = abse <= self.eps_yd                       # tramo elastico
        m_pl = (abse > self.eps_yd) & (abse <= self.eps_su)  # plato plastico

        sig[m_el] = self.Es * eps[m_el]
        sig[m_pl] = self.fyd * np.sign(eps[m_pl])
        # |eps| > eps_su -> rotura -> sig = 0 (ya inicializado)

        return float(sig) if escalar else sig


# ---------------------------------------------------------------------------
# Bloque de prueba rapida de los modelos constitutivos
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    c = Concreto(fck=30.0, fct=2.9)
    s = Acero(fyk=500.0)
    print("Concreto fck=30: fcd=%.2f MPa, Eci=%.0f MPa, eps_cr=%.2e"
          % (c.fcd, c.Eci, c.eps_cr))
    print("  sigma(+0.002) = %.2f MPa (pico compresion)" % c.sigma(0.002))
    print("  sigma(+0.0035)= %.2f MPa (platos)" % c.sigma(0.0035))
    print("  sigma(-1e-5)  = %.3f MPa (traccion elastica)" % c.sigma(-1e-5))
    print("  sigma(-1e-3)  = %.3f MPa (fissurado)" % c.sigma(-1e-3))
    print("Acero fyk=500: fyd=%.2f MPa, eps_yd=%.4f" % (s.fyd, s.eps_yd))
    print("  sigma(+0.001) = %.2f MPa (elastico)" % s.sigma(0.001))
    print("  sigma(+0.01)  = %.2f MPa (escoamento)" % s.sigma(0.01))
    print("  sigma(-0.01)  = %.2f MPa (escoamento compresion)" % s.sigma(-0.01))
    print("  sigma(+0.2)   = %.2f MPa (rotura)" % s.sigma(0.2))
