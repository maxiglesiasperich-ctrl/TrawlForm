"""
Escalado afín: nombre del modelo escalado y control frente a la teoría.

Con eslora, manga y alturas multiplicadas por fx, fy, fz en torno al punto
(extremo de popa, crujía, quilla), y la flotación escalada igual, muchas
hidrostáticas cambian de forma exacta; se usan para comprobar que Maxsurf ha
escalado bien. El control se hace antes de mover la flotación al calado pedido.
"""

TOLERANCIA = 0.005  # diferencia máxima admitida con la teoría (0,5 %)


def nombre_escalado(modelo, f_eslora, f_manga, f_puntal, f_calado):
    """Nombre del modelo escalado, p. ej. rib_test_1_L1.20_B1.10_D0.90_T0.95."""
    return f"{modelo}_L{f_eslora:.2f}_B{f_manga:.2f}_D{f_puntal:.2f}_T{f_calado:.2f}"


def prediccion_afin(base, fx, fy, fz):
    """Hidrostáticas teóricas del modelo escalado (solo las de fórmula exacta)."""
    p = {
        "Desplazamiento [t]": base["Desplazamiento [t]"] * fx * fy * fz,
        "Volumen [m3]": base["Volumen [m3]"] * fx * fy * fz,
        "Calado [m]": base["Calado [m]"] * fz,
        "LWL [m]": base["LWL [m]"] * fx,
        "Manga en flotación [m]": base["Manga en flotación [m]"] * fy,
        "Área sección máx. [m2]": base["Área sección máx. [m2]"] * fy * fz,
        "Área flotación [m2]": base["Área flotación [m2]"] * fx * fy,
        "LCB desde popa extrema [m]": base["LCB desde popa extrema [m]"] * fx,
        "LCF desde popa extrema [m]": base["LCF desde popa extrema [m]"] * fx,
        "KB [m]": base["KB [m]"] * fz,
        "BMt [m]": base["BMt [m]"] * fy ** 2 / fz,
        "BMl [m]": base["BMl [m]"] * fx ** 2 / fz,
        "TPC [t/cm]": base["TPC [t/cm]"] * fx * fy,
    }
    for coeficiente in ("Cb", "Cp", "Cm", "Cwp"):
        p[coeficiente] = base[coeficiente]
    p["KMt [m]"] = p["KB [m]"] + p["BMt [m]"]
    p["KMl [m]"] = p["KB [m]"] + p["BMl [m]"]
    return p


def control_escalado(base, escalado, fx, fy, fz, tolerancia=TOLERANCIA):
    """Compara las hidrostáticas del modelo escalado con la teoría.

    Devuelve {"filas": [(magnitud, base, escalado, teórico, diferencia)], "correcto"};
    teórico y diferencia son None en las magnitudes sin fórmula exacta.
    """
    teoria = prediccion_afin(base, fx, fy, fz)
    filas, correcto = [], True
    for magnitud in base:
        teorico, diferencia = teoria.get(magnitud), None
        if teorico is not None:
            diferencia = (escalado[magnitud] - teorico) / teorico
            correcto = correcto and abs(diferencia) <= tolerancia
        filas.append((magnitud, base[magnitud], escalado[magnitud], teorico, diferencia))
    return {"filas": filas, "correcto": correcto}
