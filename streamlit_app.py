# -*- coding: utf-8 -*-
"""
streamlit_app.py

Interfaz Streamlit equivalente a la GUI Tkinter para el calculo del
diagrama Momento x Curvatura (M x phi) segun NBR 6118:2023.

Ejecutar con:
    streamlit run streamlit_app.py
"""

import sys
import os
import io
import csv

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import streamlit as st

# Garantiza que core/ y utils/ son importables cuando se ejecuta desde raiz
sys.path.insert(0, os.path.dirname(__file__))

from core.materiales import Concreto, Acero
from core.geometria import centroide_seccion, barra_dentro
from core.diagrama import calcular_diagrama


# ─────────────────────────── CONFIGURACION ───────────────────────────────────

st.set_page_config(
    page_title="M x phi | NBR 6118:2023",
    layout="wide",
    initial_sidebar_state="expanded",
)

st.title("Diagrama Momento × Curvatura — NBR 6118:2023")
st.caption("Flexion pura (N = 0) · Solo fck ≤ 50 MPa · Compresion positiva")


# ─────────────────────────── SIDEBAR ─────────────────────────────────────────

with st.sidebar:

    # ── 1. Seccion ────────────────────────────────────────────────────────────
    st.header("1. Seccion")

    _verts_init = pd.DataFrame(
        {"X (mm)": [0.0, 250.0, 250.0, 0.0],
         "Y (mm)": [0.0, 0.0,   500.0, 500.0]}
    )
    df_verts = st.data_editor(
        _verts_init,
        num_rows="dynamic",
        key="ed_verts",
        column_config={
            "X (mm)": st.column_config.NumberColumn("X (mm)", format="%.1f"),
            "Y (mm)": st.column_config.NumberColumn("Y (mm)", format="%.1f"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # ── 2. Materiales ─────────────────────────────────────────────────────────
    st.header("2. Materiales")

    with st.expander("Concreto", expanded=True):
        fck = st.number_input(
            "fck (MPa)", value=30.0, min_value=1.0, max_value=50.0, step=1.0,
            help="Resistencia caracteristica a compresion. Maximo 50 MPa (NBR 6118)."
        )
        auto_fct = st.checkbox(
            "Calcular fct automaticamente  (0.3·fck^⅔)", value=False
        )
        if auto_fct:
            fct_val = 0.3 * fck ** (2.0 / 3.0)
            st.info(f"fct = {fct_val:.3f} MPa")
        else:
            fct_val = st.number_input(
                "fct (MPa)", value=2.9, min_value=0.01, step=0.1, format="%.3f"
            )
        gamma_c = st.number_input(
            "γc", value=1.4, min_value=0.1, step=0.05, format="%.2f",
            help="Coeficiente de minoracion del concreto."
        )

    with st.expander("Acero", expanded=True):
        fyk = st.number_input(
            "fyk (MPa)", value=500.0, min_value=1.0, step=10.0,
            help="Tension de escoamento caracteristica (CA50 = 500 MPa)."
        )
        gamma_s = st.number_input(
            "γs", value=1.15, min_value=0.1, step=0.05, format="%.2f",
            help="Coeficiente de minoracion del acero."
        )
        Es = st.number_input(
            "Es (MPa)", value=210000.0, min_value=1000.0, step=1000.0, format="%.0f"
        )

    # ── 3. Armaduras ─────────────────────────────────────────────────────────
    st.header("3. Armaduras")
    st.caption("As: area de la barra [mm²] · X, Y: posicion del centro [mm]")

    _barras_init = pd.DataFrame({
        "As (mm²)": [122.7, 122.7, 122.7, 122.7],
        "X (mm)":   [30.0,  220.0,  30.0,  220.0],
        "Y (mm)":   [30.0,   30.0, 470.0,  470.0],
    })
    df_barras = st.data_editor(
        _barras_init,
        num_rows="dynamic",
        key="ed_barras",
        column_config={
            "As (mm²)": st.column_config.NumberColumn(
                "As (mm²)", format="%.1f", min_value=0.0
            ),
            "X (mm)": st.column_config.NumberColumn("X (mm)", format="%.1f"),
            "Y (mm)": st.column_config.NumberColumn("Y (mm)", format="%.1f"),
        },
        use_container_width=True,
        hide_index=True,
    )

    # ── Vista previa de la seccion ────────────────────────────────────────────
    with st.expander("Vista previa de la seccion", expanded=False):
        try:
            verts_prev = list(zip(
                df_verts["X (mm)"].tolist(),
                df_verts["Y (mm)"].tolist()
            ))
            barras_prev = df_barras[["As (mm²)", "X (mm)", "Y (mm)"]].dropna().values

            if len(verts_prev) >= 3:
                fig_prev, ax_prev = plt.subplots(figsize=(3.5, 3.5))
                xs = [v[0] for v in verts_prev] + [verts_prev[0][0]]
                ys = [v[1] for v in verts_prev] + [verts_prev[0][1]]
                ax_prev.fill(xs, ys, alpha=0.20, color="#4c72b0")
                ax_prev.plot(xs, ys, "-o", color="#1f3b73", ms=4, lw=1.5)
                xc, yc = centroide_seccion(verts_prev)
                ax_prev.plot(xc, yc, "rx", ms=9, mew=2, label="CG")
                for row in barras_prev:
                    As, bx, by = float(row[0]), float(row[1]), float(row[2])
                    dentro = barra_dentro(bx, by, verts_prev)
                    color = "black" if dentro else "red"
                    ax_prev.scatter([bx], [by], s=max(As * 0.3, 20),
                                    color=color, zorder=5)
                ax_prev.set_xlabel("X (mm)", fontsize=8)
                ax_prev.set_ylabel("Y (mm)", fontsize=8)
                ax_prev.set_aspect("equal", adjustable="datalim")
                ax_prev.grid(True, alpha=0.3)
                ax_prev.legend(fontsize=7)
                fig_prev.tight_layout()
                st.pyplot(fig_prev)
                plt.close(fig_prev)
        except Exception:
            st.caption("(Defina al menos 3 vertices validos)")

    # ── 4. Parametros numericos ───────────────────────────────────────────────
    st.header("4. Parametros numericos")

    col_nx, col_ny = st.columns(2)
    with col_nx:
        nx = st.number_input(
            "nx", value=5, min_value=1, step=1,
            help="Divisiones de la malla en X."
        )
    with col_ny:
        ny = st.number_input(
            "ny", value=30, min_value=1, step=5,
            help="Divisiones en Y. Mayor ny = mayor precision."
        )

    tol = st.number_input(
        "Tolerancia (tol)", value=1e-4, min_value=1e-12,
        format="%.2e", help="Criterio adimensional de convergencia del equilibrio."
    )
    phi_f = st.number_input(
        "Curvatura final φf (rad/mm)", value=3e-5, min_value=1e-8,
        format="%.2e",
        help="Curvatura maxima del barrido. Aumente si Mu cae en el ultimo paso."
    )
    m_pasos = st.number_input(
        "Pasos (m)", value=100, min_value=2, step=10,
        help="Cantidad de puntos del diagrama."
    )

    st.caption("⚠ Si Mu cae en el ultimo paso, aumente φf.")
    st.caption("⚠ ny ≥ 50 para mayor precision.")

    # ── Boton Calcular ────────────────────────────────────────────────────────
    st.markdown("---")
    calcular_btn = st.button("▶  Calcular", type="primary", use_container_width=True)


# ─────────────────────────── CALCULO ─────────────────────────────────────────

if calcular_btn:
    errores = []

    # Validar vertices
    try:
        vertices = list(zip(
            df_verts["X (mm)"].dropna().tolist(),
            df_verts["Y (mm)"].dropna().tolist()
        ))
        if len(vertices) < 3:
            errores.append("La seccion debe tener al menos 3 vertices.")
    except Exception as exc:
        errores.append(f"Tabla de vertices: {exc}")

    # Validar armaduras
    try:
        _df_b = df_barras[["As (mm²)", "X (mm)", "Y (mm)"]].dropna()
        barras_arr = _df_b.values.astype(float).reshape(-1, 3)
    except Exception as exc:
        errores.append(f"Tabla de armaduras: {exc}")
        barras_arr = np.empty((0, 3))

    if errores:
        for err in errores:
            st.error(err)
        st.stop()

    concreto = Concreto(fck=fck, fct=fct_val, gamma_c=gamma_c)
    acero    = Acero(fyk=fyk, gamma_s=gamma_s, Es=Es)
    params   = {
        "nx":    int(nx),
        "ny":    int(ny),
        "tol":   float(tol),
        "phi_i": None,
        "phi_f": float(phi_f),
        "m":     int(m_pasos),
    }

    with st.spinner("Calculando diagrama M x phi…"):
        try:
            res = calcular_diagrama(vertices, barras_arr, concreto, acero, params)
        except Exception as exc:
            st.error(f"Error en el calculo: {exc}")
            st.stop()

    if len(res["phi"]) == 0:
        st.warning(
            "No se obtuvieron puntos validos. "
            "Revise la geometria, las armaduras y el intervalo de curvatura (phi_f)."
        )
        st.stop()

    st.session_state["resultado"] = res


# ─────────────────────────── RESULTADOS ──────────────────────────────────────

if "resultado" not in st.session_state:
    st.info("Configure los parametros en el panel izquierdo y presione **Calcular**.")
    st.stop()

res = st.session_state["resultado"]
p   = res["puntos"]

# Advertencias del calculo
for adv in res["advertencias"]:
    st.warning(adv)

# ── Metricas ──────────────────────────────────────────────────────────────────
c1, c2, c3 = st.columns(3)
with c1:
    st.metric(
        "Mcr (kN·m)",
        f"{p['Mcr'][1]:.2f}" if p["Mcr"] else "—",
        help="Momento de fisuracion (pico pre-fisura)"
    )
with c2:
    st.metric(
        "My (kN·m)",
        f"{p['My'][1]:.2f}" if p["My"] else "—",
        help="Momento de escoamento (primera barra)"
    )
with c3:
    st.metric(
        "Mu (kN·m)",
        f"{p['Mu'][1]:.2f}" if p["Mu"] else "—",
        help="Momento ultimo (maximo del diagrama)"
    )

# ── Diagrama M x phi ──────────────────────────────────────────────────────────
fig, ax = plt.subplots(figsize=(9, 5))
ax.plot(res["phi"], res["M"], "-b", lw=1.8, label="M × φ")

_colores = {"Mcr": "green", "My": "orange", "Mu": "red"}
for nombre, color in _colores.items():
    pt = p.get(nombre)
    if pt:
        ax.plot(pt[0], pt[1], "o", color=color, ms=9, label=nombre,
                clip_on=False, zorder=5)
        ax.annotate(
            f"{nombre}={pt[1]:.1f}",
            (pt[0], pt[1]),
            textcoords="offset points", xytext=(6, 6),
            fontsize=9, clip_on=False,
        )

ax.set_xlabel("Curvatura φ (rad/mm)")
ax.set_ylabel("Momento M (kN·m)")
ax.set_title("Diagrama Momento × Curvatura")
ax.grid(True, alpha=0.3)
ax.legend(loc="best", fontsize=9)
ax.margins(x=0.05)
fig.tight_layout()
st.pyplot(fig)
plt.close(fig)

# ── Tabla de resultados ───────────────────────────────────────────────────────
st.subheader("Tabla de resultados")
df_res = pd.DataFrame({
    "Paso":       range(1, len(res["phi"]) + 1),
    "φ (rad/mm)": res["phi"],
    "M (kN·m)":   res["M"],
    "y_na (mm)":  res["y_na"],
    "Estado":     res["estado"],
})
st.dataframe(
    df_res.style.format({
        "φ (rad/mm)": "{:.4e}",
        "M (kN·m)":   "{:.3f}",
        "y_na (mm)":  "{:.1f}",
    }),
    use_container_width=True,
    height=320,
)

# ── Descarga CSV ──────────────────────────────────────────────────────────────
buf = io.StringIO()
w = csv.writer(buf, delimiter=";")
w.writerow(["paso", "phi (rad/mm)", "M (kN.m)", "y_na (mm)", "estado"])
for i in range(len(res["phi"])):
    w.writerow([
        i + 1,
        "%.6e" % res["phi"][i],
        "%.4f"  % res["M"][i],
        "%.2f"  % res["y_na"][i],
        res["estado"][i],
    ])
w.writerow([])
w.writerow(["Punto caracteristico", "phi (rad/mm)", "M (kN.m)"])
for nombre in ("Mcr", "My", "Mu"):
    pt = res["puntos"].get(nombre)
    if pt:
        w.writerow([nombre, "%.6e" % pt[0], "%.4f" % pt[1]])

st.download_button(
    label="⬇  Descargar CSV",
    data=buf.getvalue().encode("utf-8"),
    file_name="resultado_Mxphi.csv",
    mime="text/csv",
    use_container_width=False,
)
