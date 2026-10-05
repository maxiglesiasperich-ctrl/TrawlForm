"""
Resistencia: números de Froude, rangos de validez, corrección de correlación y
valores a una velocidad dada.

Rangos de validez copiados del manual de Maxsurf Resistance
(ResistanceManual.pdf, Appendix B Applicability, págs. 51-53).
"""

import math

G = 9.81
NUDO = 1852 / 3600  # m/s


def froudes(v, casco):
    """Froude de eslora (FnL), de volumen (Fnv) y de manga (Fnb) a v [m/s]."""
    return {
        "FnL": v / math.sqrt(G * casco["LWL"]),
        "Fnv": v / math.sqrt(G * casco["Volumen"] ** (1 / 3)),
        "Fnb": v / math.sqrt(G * casco["B"]),
    }


def parametros(casco):
    """Parámetros del casco que usan las tablas de validez."""
    L, B, T, V = casco["LWL"], casco["B"], casco["T"], casco["Volumen"]
    return {
        "L [m]": L,
        "Volumen [m3]": V,
        "L/B": L / B,
        "B/T": B / T,
        "L/V^1/3": L / V ** (1 / 3),
        "B^3/V": B ** 3 / V,
        "V/L^3": V / L ** 3,
        "Cb": V / (L * B * T),
        "Cp": casco["Cp"],
        "Cm": casco["Cm"],
        "Cwp": casco["Cwp"],
        "LCG/L [%]": 100 * casco["LCG desde maestra"] / L,
        "At/Ax": casco["Área espejo"] / casco["Área sección máx."],
        "Semiángulo entrada [°]": casco["Semiángulo entrada"],
    }


# Rango de velocidad: lista de (tipo de Froude, mínimo, máximo); None = sin límite.
RANGOS_VELOCIDAD = {
    "Savitsky pre-planeo": [("Fnv", 1.0, 2.0)],
    # Sin máximo en el manual, pero "con precaución" por encima de Fnv 6-7.
    "Savitsky planeo": [("Fnb", 1.0, None), ("Fnv", None, 6.0)],
    "Blount-Fox": [("Fnv", 1.0, None), ("Fnv", None, 6.0)],
    "Lahtiharju (pantoque redondo)": [("Fnv", 1.5, 3.8)],
    "Lahtiharju (codillo)": [("Fnv", 1.5, 5.0)],
    "Holtrop": [("FnL", None, 0.80)],
    "Compton": [("FnL", 0.1, 0.6)],
    "Fung": [("FnL", 0.134, 0.908)],
    "Van Oortmerssen": [("FnL", None, 0.50)],
    "Series 60": [("Fnv", 0.282, 0.677)],
    "Delft I-II": [("FnL", None, 0.75)],
    "Delft III": [("FnL", None, 0.75)],
    "Slender Body": [("FnL", None, 1.0)],
    "Wyman": [],
    "KR Barge": [("FnL", None, 0.50)],
}

# Rango de dimensiones: lista de (parámetro, mínimo, máximo).
_DELFT = [("L/B", 2.76, 5.00), ("B/T", 2.46, 19.32), ("L/V^1/3", 4.34, 8.50),
          ("LCG/L [%]", -6.0, 0.0), ("Cp", 0.52, 0.60)]
RANGOS_CASCO = {
    "Savitsky pre-planeo": [("L/V^1/3", 3.07, 12.4), ("Semiángulo entrada [°]", 3.7, 28.6),
                            ("L/B", 2.52, 18.26), ("B/T", 1.7, 9.8), ("At/Ax", 0.0, 1.0),
                            ("LCG/L [%]", -6.56, 0.3)],
    "Savitsky planeo": [],
    "Blount-Fox": [],
    "Lahtiharju (pantoque redondo)": [("L/V^1/3", 4.47, 8.30), ("B^3/V", 0.68, 7.76),
                                      ("L/B", 3.33, 8.21), ("B/T", 1.72, 10.21),
                                      ("At/Ax", 0.16, 0.82), ("Cm", 0.57, 0.89)],
    "Lahtiharju (codillo)": [("L/V^1/3", 4.49, 6.81), ("L/B", 2.73, 5.43),
                             ("B/T", 3.75, 7.54), ("At/Ax", 0.43, 0.995)],
    "Holtrop": [("Cp", 0.55, 0.85), ("L/B", 3.9, 15.0), ("B/T", 2.1, 4.0)],
    "Compton": [("LCG/L [%]", -13.0, -2.0), ("L/B", 4.0, 5.2), ("V/L^3", 0.00368, 0.00525)],
    "Fung": [("V/L^3", 0.00057, 0.01257), ("B/T", 1.696, 10.204), ("Cp", 0.526, 0.774),
             ("Cm", 0.556, 0.994), ("Semiángulo entrada [°]", 14.324, 23.673),
             ("L/B", 2.52, 17.935), ("Cwp", 0.662, 0.841)],
    "Van Oortmerssen": [("L [m]", 8.0, 80.0), ("L/B", 3.0, 6.2), ("Cp", 0.50, 0.73),
                        ("LCG/L [%]", -8.0, 2.8), ("Volumen [m3]", 5.0, 3000.0),
                        ("B/T", 1.9, 4.0), ("Cm", 0.70, 0.97),
                        ("Semiángulo entrada [°]", 10.0, 46.0)],
    "Series 60": [("Cb", 0.6, 0.8), ("L/B", 5.5, 8.5), ("B/T", 2.5, 3.5),
                  ("LCG/L [%]", -2.48, 3.51)],
    "Delft I-II": _DELFT,
    "Delft III": _DELFT,
    "Slender Body": [("L/V^1/3", 4.0, None)],
    "Wyman": [],
    "KR Barge": [],
}

# Tipo de casco y lo que el manual indica pero no se puede comprobar aquí.
NOTAS = {
    "Savitsky planeo": "planeo; el manual no da rangos de dimensiones",
    "Blount-Fox": "planeo; LCG/Lcp < 0,46 no comprobable (Maxsurf no da Lcp por COM)",
    "Wyman": "lanchas; da la potencia de motor (Rt = η·P/V); límite de velocidad "
             "según la relación D/L, no comprobado",
    "Delft I-II": "veleros",
    "Delft III": "veleros",
    "Slender Body": "L/V^1/3 mínimo ≈ 4 a Fn 0,2 y ≈ 7,5-8 a Fn 1 (aquí se exige ≥ 4)",
    "KR Barge": "barcazas; el manual no da rangos de dimensiones",
}

# Corrección de correlación (C_A) de cada método, comprobada cambiando
# Vessel.CorrelationAllowance en Maxsurf (Series 60, según el manual: con la RIB
# de prueba no calcula ningún punto). El manual se equivoca con Savitsky pre-planeo.
#   "añadido":   Maxsurf suma C_A·½ρSv² con el C_A que se le pasa.
#   "integrado": el método lleva el suyo y no se puede quitar.
#   "ninguno":   el método no lleva corrección.
CORRELACION_METODO = {
    "Savitsky pre-planeo": ("añadido", "sobre la superficie mojada en reposo"),
    "Savitsky planeo": ("añadido", "sobre la superficie mojada en planeo"),
    "Blount-Fox": ("añadido", "sobre la superficie mojada en planeo"),
    "Lahtiharju": ("añadido", "sobre la superficie mojada en reposo"),
    "Van Oortmerssen": ("añadido", "sobre la superficie mojada en reposo"),
    "Series 60": ("añadido", "según el manual; no comprobado"),
    "Slender Body": ("añadido", "sobre la superficie mojada en reposo"),
    "Holtrop": ("integrado", "regresión propia de Holtrop-Mennen"),
    "Compton": ("integrado", "fijo 0,0004"),
    "Fung": ("integrado", "fijo 0,0005"),
    "Wyman": ("ninguno", ""),
    "Delft I-II": ("ninguno", ""),
    "Delft III": ("ninguno", ""),
    "KR Barge": ("ninguno", ""),
}

LEYENDA_MARCAS = ("C = casco fuera de rango, V = velocidad fuera de rango, "
                  "N = Maxsurf no lo calcula a esta velocidad, ! = resistencia negativa")

# Cómo calcula Maxsurf la potencia (manual de Resistance, pág. 34; Wyman, pág. 5).
LEYENDA_POTENCIA = ("P = Rt·V/η: con η = 1 es la potencia efectiva; con η < 1, la potencia "
                    "necesaria con ese rendimiento. Wyman al revés: su P es potencia de motor "
                    "(no depende de η) y Rt = η·P/V.")


def _tabla(metodo, casco):
    # Lahtiharju tiene rangos distintos con codillo y con pantoque redondo.
    if metodo == "Lahtiharju":
        return metodo + (" (codillo)" if casco["Codillo"] else " (pantoque redondo)")
    return metodo


def _fuera(valor, minimo, maximo):
    return (minimo is not None and valor < minimo) or (maximo is not None and valor > maximo)


def _rango(minimo, maximo):
    return f"[{'-∞' if minimo is None else minimo}, {'∞' if maximo is None else maximo}]"


def texto_correlacion(metodo, ca):
    """Corrección de correlación que lleva el método con el C_A pasado a Maxsurf."""
    tipo, detalle = CORRELACION_METODO[metodo]
    if tipo == "añadido":
        return f"C_A = {ca} ({detalle})" if ca > 0 else "desactivada (C_A = 0)"
    if tipo == "integrado":
        return f"integrada en el método, siempre activa ({detalle})"
    return "el método no lleva corrección"


def texto_rango_velocidad(metodo, casco):
    """Rango de velocidad válido del método."""
    rangos = RANGOS_VELOCIDAD[_tabla(metodo, casco)]
    return "; ".join(f"{tipo} en {_rango(mn, mx)}" for tipo, mn, mx in rangos) or "sin límite numérico"


def avisos_casco(metodo, casco):
    """Parámetros del casco fuera del rango del método."""
    p = parametros(casco)
    return [f"{nombre} = {p[nombre]:.3g} fuera de {_rango(mn, mx)}"
            for nombre, mn, mx in RANGOS_CASCO[_tabla(metodo, casco)]
            if _fuera(p[nombre], mn, mx)]


def avisos_velocidad(metodo, casco, v):
    """Números de Froude fuera del rango del método a v [m/s]."""
    fn = froudes(v, casco)
    return [f"{tipo} = {fn[tipo]:.3g} fuera de {_rango(mn, mx)}"
            for tipo, mn, mx in RANGOS_VELOCIDAD[_tabla(metodo, casco)]
            if _fuera(fn[tipo], mn, mx)]


def marcas(metodo, casco, punto):
    """Avisos de un punto en letras (ver LEYENDA_MARCAS)."""
    s = "C" if avisos_casco(metodo, casco) else ""
    if punto["Rt"] is None:
        return s + "N"
    if avisos_velocidad(metodo, casco, punto["v"]):
        s += "V"
    if punto["Rt"] < 0:
        s += "!"
    return s


def valor_a_velocidad(puntos, v):
    """Valores de la curva a v [m/s].

    Si v es un punto de Maxsurf se devuelve tal cual (Maxsurf guarda las velocidades
    con menos decimales, de ahí la tolerancia); si no, se interpola linealmente y,
    si un vecino no está calculado, resistencia y potencia salen None.
    """
    for p in puntos:
        if abs(p["v"] - v) <= 1e-6 * max(1.0, v):
            return dict(p)
    for a, b in zip(puntos, puntos[1:]):
        if a["v"] <= v <= b["v"]:
            t = (v - a["v"]) / (b["v"] - a["v"])
            return {k: None if a[k] is None or b[k] is None else a[k] + t * (b[k] - a[k])
                    for k in a}
    raise ValueError(f"La velocidad {v:.2f} m/s está fuera del rango calculado.")


def tabla_servicio(metodos, casco, curvas, v, ca):
    """Resumen de cada método a la velocidad v [m/s]: resistencia y potencia para
    cada rendimiento ({η: valor}) y avisos. curvas: {η: {método: puntos}}."""
    filas = []
    for m in metodos:
        puntos = {eta: valor_a_velocidad(c[m], v) for eta, c in curvas.items()}
        filas.append({
            "Método": m,
            "Rt": {eta: p["Rt"] for eta, p in puntos.items()},
            "P": {eta: p["P"] for eta, p in puntos.items()},
            "Marcas": marcas(m, casco, next(iter(puntos.values()))),
            "Corrección": texto_correlacion(m, ca),
            "Casco fuera de rango": "; ".join(avisos_casco(m, casco)),
            "Velocidad fuera de rango": "; ".join(avisos_velocidad(m, casco, v)),
            "Nota": NOTAS.get(m, ""),
        })
    return filas
