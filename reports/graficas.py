"""Gráficas de resistencia y potencia frente a la velocidad (matplotlib)."""

import math

import matplotlib
matplotlib.use("Agg")  # sin ventanas: solo se guardan imágenes
import matplotlib.pyplot as plt
from matplotlib.colors import to_rgb
from matplotlib.lines import Line2D

from calculos.resistencia import G, NUDO, avisos_casco, avisos_velocidad

ACLARADO_MAX = 0.65  # cuánto se aclara el color del rendimiento más bajo (0 = nada, 1 = blanco)


def guardar_graficas(carpeta, r, v_max):
    """resistencia.png (Rt-V) y potencia.png (P-V) del modelo, hasta v_max [m/s]."""
    _grafica(r, v_max, "Rt", "Resistencia total", "Rt [kN]", carpeta / "resistencia.png")
    _grafica(r, v_max, "P", "Potencia, P = Rt·V/η", "P [kW]", carpeta / "potencia.png")


def _tono(color, aclarado):
    """Mezcla el color con blanco (aclarado 0 = color original)."""
    return tuple(c + (1 - c) * aclarado for c in to_rgb(color))


def _kilo_o_nan(valor):
    """N -> kN o W -> kW; NaN (hueco en la curva) si no está calculado."""
    return math.nan if valor is None else valor / 1000


def _iguales(a, b):
    return all((math.isnan(x) and math.isnan(y)) or abs(x - y) <= 1e-9 * max(1.0, abs(x))
               for x, y in zip(a, b))


def _grafica(r, v_max, clave, titulo, eje_y, ruta):
    """Una curva por método y rendimiento: color = método, tono = rendimiento (el
    mayor, color fuerte); continua = dentro de rango, discontinua = fuera de rango."""
    casco, curvas = r["casco"], r["curvas"]
    rendimientos = sorted(curvas, reverse=True)
    aclarado = {eta: ACLARADO_MAX * i / max(1, len(rendimientos) - 1)
                for i, eta in enumerate(rendimientos)}
    metodos = list(curvas[rendimientos[0]])

    fig, ax = plt.subplots(figsize=(11, 6.5))
    leyenda_metodos, hay_tonos = [], False
    for i, m in enumerate(metodos):
        color = plt.cm.tab10(i % 10)
        casco_valido = not avisos_casco(m, casco)
        primera = None
        for eta in rendimientos:
            puntos = [p for p in curvas[eta][m] if p["v"] <= v_max * (1 + 1e-9)]
            y = [_kilo_o_nan(p[clave]) for p in puntos]
            if primera is None:
                primera = y
            elif _iguales(y, primera):
                continue  # igual que con el rendimiento mayor (la Rt casi nunca depende de η)
            else:
                hay_tonos = True
            x = [p["v"] / NUDO for p in puntos]
            valido = [casco_valido and not avisos_velocidad(m, casco, p["v"]) for p in puntos]
            tono = _tono(color, aclarado[eta])
            ax.plot(x, y, color=tono, linestyle="--", linewidth=1.2)
            ax.plot(x, [yi if ok else math.nan for yi, ok in zip(y, valido)],
                    color=tono, linewidth=2.2)
        nombre = m + (" (P de motor)" if m == "Wyman" else "")
        leyenda_metodos.append(Line2D([], [], color=color, linewidth=2.2, label=nombre))

    v_servicio = r["v_servicio"] / NUDO
    ax.axvline(v_servicio, color="0.3", linestyle="-.", linewidth=1.3)

    ax.set_xlim(0, v_max / NUDO)
    ax.set_ylim(bottom=min(0, ax.get_ylim()[0]))
    ax.set_xlabel("V [kn]")
    ax.set_ylabel(eje_y)
    ax.set_title(f"{r['nombre']} — {titulo}", pad=14)
    ax.grid(alpha=0.3)
    froude = NUDO / math.sqrt(G * casco["LWL"])  # FnL por nudo
    ax.secondary_xaxis("top", functions=(lambda kn: kn * froude, lambda fn: fn / froude)
                       ).set_xlabel("FnL")

    claves = [Line2D([], [], color="0.2", linewidth=2.2, label="dentro de rango"),
              Line2D([], [], color="0.2", linewidth=1.2, linestyle="--", label="fuera de rango"),
              Line2D([], [], color="0.3", linewidth=1.3, linestyle="-.",
                     label=f"V servicio = {v_servicio:g} kn")]
    if hay_tonos:
        claves += [Line2D([], [], color=_tono("0.1", aclarado[eta]), linewidth=2.2,
                          label=f"η = {eta:g}") for eta in rendimientos]
    leyenda = ax.legend(handles=leyenda_metodos, title="Método", loc="upper left",
                        bbox_to_anchor=(1.01, 1))
    ax.add_artist(leyenda)
    ax.legend(handles=claves, title="Líneas", loc="lower left", bbox_to_anchor=(1.01, 0))

    # bbox_extra_artists: sin él, el recorte "tight" deja fuera parte de la primera leyenda.
    fig.savefig(ruta, dpi=150, bbox_inches="tight", bbox_extra_artists=(leyenda,))
    plt.close(fig)
