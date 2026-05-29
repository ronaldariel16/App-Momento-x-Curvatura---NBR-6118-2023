# Diagrama Momento x Curvatura (M x φ)

Aplicación de escritorio en Python para calcular y graficar el diagrama
Momento–Curvatura de secciones de concreto armado, según la NBR 6118:2023.
Uso académico. Modelos: parábola-rectángulo (concreto en compresión), bilineal
de tracción (concreto), y elástico-plástico perfecto (acero).

## Instalación

```bash
pip install -r requirements.txt
# En Linux, si falta Tkinter:  sudo apt install python3-tk
```

## Ejecución

```bash
python main.py
```

## Estructura

```
momento_curvatura/
├── main.py                # Punto de entrada (lanza la GUI)
├── core/
│   ├── materiales.py      # Leyes constitutivas concreto/acero
│   ├── geometria.py       # Discretización del polígono y centroide
│   ├── equilibrio.py      # Solver de equilibrio (línea neutra por bisección)
│   └── diagrama.py        # Loop M×φ + detección de Mcr, My, Mu
├── gui/                   # Interfaz Tkinter (5 pestañas)
├── utils/exportar.py      # Exportación CSV / PNG
└── requirements.txt
```

## Validación del núcleo (sin GUI)

```bash
cd core
python diagrama.py
```

Ejecuta el ejemplo del manual (b=250, h=500, fck=30, fct=2.9, fy=500, 4 barras
de 123 mm² en las esquinas con cobertura 30 mm) y genera `validacion_diagrama.png`.
Resultado de referencia: Mcr≈19.5, My≈47.2, Mu≈48.5 kN.m.

## Convenciones

- Eje Y positivo hacia arriba; origen en la esquina inferior izquierda.
- Compresión POSITIVA en concreto y acero (convención unificada).
- La fibra más comprimida (momento positivo) es la de mayor Y.
- ε(y) = φ · (y − y_na); momentos en kN.m; curvaturas en rad/mm.

## Limitaciones conocidas (importantes)

1. **Solo fck ≤ 50 MPa** (n=2, εc2=2‰, εcu=3,5‰). Concretos de alta resistencia
   no están implementados.
2. **Valores de cálculo por defecto** (fcd = fck/γc, fyd = fyk/γs). Esto produce
   un diagrama de resistencia de diseño, no la respuesta media esperada. Para
   comportamiento real, usar valores medios (fcm, fym) requiere modificar los
   modelos.
3. **Sin tension-stiffening**: la tracción del concreto cae a cero de golpe al
   fisurar, lo que produce una caída abrupta en M cerca de Mcr (artefacto del
   modelo, no comportamiento físico real).
4. **El módulo tangente del concreto en compresión** (parábola) no coincide con
   Eci usado en tracción; la rama "elástica" no replica EI bruto clásico.
5. **Flexión pura uniaxial** (N=0). No incluye flexo-compresión ni flexión
   oblicua.
6. **No se descuenta** el área de concreto desplazada por las barras (doble
   conteo menor). Activable con `descontar_concreto=True` en equilibrio.py.
7. **Convergencia**: a curvaturas muy altas la línea neutra puede salir del
   intervalo de búsqueda y el paso se omite. Si el máximo cae en el último paso,
   aumentar φ_f.
```
