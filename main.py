"""
Herramienta de diseño preliminar con Maxsurf.

Configura los datos de abajo y ejecuta:  python main.py

MODO "normal": calcula el modelo MODELO de inputs/models.
MODO "scale":  por cada juego de FACTORES crea un modelo escalado en
               inputs/models/scaled_models/<modelo>/ y lo calcula.

Resultados agrupados por modelo base (se sobrescriben en cada ejecución):
    outputs/<modelo>/<modelo>/                 modo "normal"
    outputs/<modelo>/<modelo>_L.._B.._H../     cada modelo escalado
    outputs/<modelo>/resumen_serie.xlsx        modo "scale"
Cada carpeta de resultados lleva informe.txt, hidrostaticas.xlsx, resistencia.xlsx,
escalado.xlsx (si es un modelo escalado), las gráficas resistencia.png (Rt-V) y
potencia.png (P-V) y los archivos de Maxsurf: <modelo>.msd (Modeler) y <modelo>.hsd
(datos medidos de Resistance).
"""

import shutil
from datetime import datetime
from pathlib import Path

from calculos.escalado import control_escalado, nombre_escalado
from calculos.resistencia import NUDO, tabla_servicio
from maxsurf.modeler import Modeler
from maxsurf.resistance import CA_MAXSURF, Resistance
from maxsurf.resistance import METODOS as METODOS_DISPONIBLES
from reports import excel
from reports.graficas import guardar_graficas
from reports.texto import informe

# ═══════════════════════════════ CONFIGURACIÓN ═══════════════════════════════

MODO = "scale"               # "normal" o "scale"
MODELO = "rib_test_1.msd"     # archivo de inputs/models

HIDROSTATICAS = True
RESISTENCIA = True

# Modo "scale": un modelo por cada (eslora, manga, puntal, calado).
# El puntal escala la geometría en altura; el calado solo mueve la flotación.
# Con puntal = calado es un escalado afín puro.
FACTORES = [
    (1.20, 1.10, 0.90, 0.90),
]

DENSIDAD = 1.025              # t/m3 (agua salada)

# Métodos: "todos" o una lista entre corchetes, p. ej. ["Savitsky planeo", "Holtrop"].
# Disponibles: Savitsky pre-planeo, Savitsky planeo, Blount-Fox, Lahtiharju, Holtrop,
# Compton, Fung, Van Oortmerssen, Series 60, Delft I-II, Delft III, Slender Body,
# Wyman, KR Barge.
METODOS = ["Savitsky planeo", "Savitsky pre-planeo", "Holtrop", "Wyman"]
CORRELACION = True            # corrección modelo-buque (C_A) donde Maxsurf la añade aparte
VEL_SERVICIO = 25.0           # kn (múltiplo de PASO para tener el valor exacto de Maxsurf)
VEL_MAXIMA = 35.0             # kn
PASO = 0.5                    # kn
# Rendimiento η para la potencia, P = Rt·V/η: 1 = sin pérdidas (potencia efectiva);
# se pueden poner varios, p. ej. [1.0, 0.6, 0.5]. Wyman da potencia de motor y Rt = η·P/V.
RENDIMIENTOS = [1.0]

# ═════════════════════════════════ PIPELINE ══════════════════════════════════

CARPETA = Path(__file__).parent
MODELOS = CARPETA / "inputs" / "models"
ESCALADOS = MODELOS / "scaled_models"
SALIDAS = CARPETA / "outputs"
ARCHIVOS_SALIDA = ("informe.txt", "escalado.xlsx", "hidrostaticas.xlsx", "resistencia.xlsx",
                   "resistencia.png", "potencia.png")


def comprobar_configuracion():
    """Revisa la configuración y devuelve la lista de métodos de resistencia."""
    if MODO not in ("normal", "scale"):
        raise ValueError('MODO tiene que ser "normal" o "scale".')
    if not (isinstance(HIDROSTATICAS, bool) and isinstance(RESISTENCIA, bool)):
        raise ValueError("HIDROSTATICAS y RESISTENCIA tienen que ser True o False.")
    if isinstance(METODOS, str) and METODOS != "todos":
        raise ValueError('METODOS tiene que ser "todos" o una lista entre corchetes, '
                         'p. ej. ["Savitsky planeo", "Holtrop"].')
    if not (MODELOS / MODELO).is_file():
        raise FileNotFoundError(f"No existe {MODELOS / MODELO}")
    if MODO == "normal" and not (HIDROSTATICAS or RESISTENCIA):
        raise ValueError("No hay nada que calcular: HIDROSTATICAS y RESISTENCIA son False.")
    if MODO == "scale" and not FACTORES:
        raise ValueError("FACTORES está vacío.")
    if MODO == "scale" and any(len(f) != 4 or min(f) <= 0 for f in FACTORES):
        raise ValueError("Cada juego de FACTORES tiene que ser (eslora, manga, puntal, calado), "
                         "todos mayores que 0.")
    if PASO <= 0:
        raise ValueError("PASO tiene que ser mayor que 0.")
    if not RENDIMIENTOS or any(not 0 < eta <= 1 for eta in RENDIMIENTOS):
        raise ValueError("RENDIMIENTOS tiene que tener al menos un valor, todos entre 0 y 1.")
    if len(set(RENDIMIENTOS)) != len(RENDIMIENTOS):
        raise ValueError("RENDIMIENTOS tiene valores repetidos.")
    metodos =list(METODOS_DISPONIBLES) if METODOS == "todos" else list(METODOS)
    desconocidos = [m for m in metodos if m not in METODOS_DISPONIBLES]
    if desconocidos:
        raise ValueError(f"Métodos desconocidos: {desconocidos}. "
                         f"Disponibles: {', '.join(METODOS_DISPONIBLES)}")
    return metodos


def configuracion():
    """Configuración que se copia en el informe."""
    return {
        "Modo": MODO,
        "Modelo base": MODELO,
        "Densidad [t/m3]": DENSIDAD,
        "Métodos": METODOS,
        "Corrección C_A": CORRELACION,
        "V servicio [kn]": VEL_SERVICIO,
        "V máxima [kn]": VEL_MAXIMA,
        "Paso [kn]": PASO,
        "Rendimientos η": ", ".join(f"{eta:g}" for eta in RENDIMIENTOS),
    }


def nuevo_resultado(ruta, factores=None):
    """Datos de partida de un modelo; los pasos del pipeline le van añadiendo resultados."""
    r = {"nombre": ruta.stem, "ruta": ruta, "fecha": datetime.now(), "avisos": [],
         "densidad": DENSIDAD, "carpeta": SALIDAS / Path(MODELO).stem / ruta.stem}
    if factores:
        r["factores"] = factores
    return r


def preparar_carpeta(r):
    """Crea la carpeta de resultados del modelo y borra los de la ejecución anterior."""
    r["carpeta"].mkdir(parents=True, exist_ok=True)
    for archivo in ARCHIVOS_SALIDA + (f"{r['nombre']}.msd", f"{r['nombre']}.hsd"):
        (r["carpeta"] / archivo).unlink(missing_ok=True)


def crear_modelo_escalado(modeler, base, r):
    """Copia el modelo base, lo escala (eslora, manga, puntal), comprueba el escalado
    con la teoría, coloca la flotación en el calado pedido y lo guarda.
    Si algo falla, borra la copia para que no quede un "escalado" sin escalar."""
    f_eslora, f_manga, f_puntal, f_calado = r["factores"]
    r["ruta"].parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(base, r["ruta"])
    try:
        modeler.abrir(r["ruta"], ESCALADOS, recargar=True)
        antes = modeler.hidrostaticas(DENSIDAD)
        modeler.escalar(f_eslora, f_manga, f_puntal)  # la flotación escala con el puntal
        escalado = modeler.hidrostaticas(DENSIDAD)
        r["control"] = control_escalado(antes, escalado, f_eslora, f_manga, f_puntal)
        if not r["control"]["correcto"]:
            raise RuntimeError(f"El escalado {r['factores']} no cuadra con la teoría: no se guarda.")

        calado = antes["Calado [m]"] * f_calado
        modeler.fijar_calado(calado)
        final = modeler.hidrostaticas(DENSIDAD)["Calado [m]"]
        if abs(final - calado) > 1e-4:
            raise RuntimeError(f"Maxsurf da un calado de {final:.4f} m en lugar de {calado:.4f} m.")
        r["control"]["calados"] = (antes["Calado [m]"], escalado["Calado [m]"], final)
        modeler.guardar(r["ruta"], ESCALADOS)
    except Exception:
        modeler.descartar()
        r["ruta"].unlink(missing_ok=True)
        raise


def calcular_hidrostaticas(modeler, r):
    """Hidrostáticas en la DWL con Maxsurf Modeler."""
    modeler.abrir(r["ruta"], ESCALADOS)
    r["version"] = modeler.version
    r["unidades"] = modeler.unidades()
    if r["unidades"] != ("m", "t"):
        r["avisos"].append("El diseño no está en metros y toneladas: "
                           "las unidades indicadas en las hidrostáticas no valen.")
    r["referencias"] = modeler.referencias()
    r["hidrostaticas"] = modeler.hidrostaticas(DENSIDAD)


def calcular_resistencia(resistance, r, metodos):
    """Curvas de resistencia y resumen a la velocidad de servicio con Maxsurf Resistance."""
    ca = CA_MAXSURF if CORRELACION else 0.0
    resistance.abrir(r["ruta"], MODELOS)
    r["version"] = resistance.version
    r["casco"], r["curvas"] = resistance.calcular(
        metodos, VEL_MAXIMA * NUDO, PASO * NUDO, DENSIDAD, ca, RENDIMIENTOS)
    r["v_servicio"] = VEL_SERVICIO * NUDO
    r["servicio"] = tabla_servicio(metodos, r["casco"], r["curvas"], r["v_servicio"], ca)
    resistance.guardar_mediciones(r["carpeta"] / f"{r['nombre']}.hsd")
    if abs(VEL_SERVICIO / PASO - round(VEL_SERVICIO / PASO)) > 1e-9:
        r["avisos"].append(f"VEL_SERVICIO no es múltiplo de PASO: los valores a "
                           f"{VEL_SERVICIO} kn están interpolados.")


def guardar_resultados(r):
    """Escribe informe.txt, los Excel y una copia del .msd en la carpeta del modelo."""
    carpeta = r["carpeta"]
    shutil.copy2(r["ruta"], carpeta / r["ruta"].name)
    texto = informe(r, configuracion())
    (carpeta / "informe.txt").write_text(texto, encoding="utf-8")
    if "control" in r:
        excel.guardar_escalado(carpeta / "escalado.xlsx", r)
    if "hidrostaticas" in r:
        excel.guardar_hidrostaticas(carpeta / "hidrostaticas.xlsx", r)
    if "casco" in r:
        excel.guardar_resistencia(carpeta / "resistencia.xlsx", r, VEL_MAXIMA * NUDO)
        guardar_graficas(carpeta, r, VEL_MAXIMA * NUDO)
    print(texto)
    print(f"\nResultados guardados en {carpeta}\n")


def main():
    metodos = comprobar_configuracion()
    base = MODELOS / MODELO
    if MODO == "normal":
        resultados = [nuevo_resultado(base)]
    else:
        resultados = [nuevo_resultado(ESCALADOS / base.stem / f"{nombre_escalado(base.stem, *f)}.msd", f)
                      for f in FACTORES]
    for r in resultados:
        preparar_carpeta(r)

    # Modeler y Resistance se usan uno detrás de otro: si están abiertos a la vez,
    # Modeler no termina de cerrarse.
    if MODO == "scale" or HIDROSTATICAS:
        with Modeler() as modeler:
            for r in resultados:
                if "factores" in r:
                    crear_modelo_escalado(modeler, base, r)
                if HIDROSTATICAS:
                    calcular_hidrostaticas(modeler, r)

    if RESISTENCIA:
        with Resistance() as resistance:
            for r in resultados:
                calcular_resistencia(resistance, r, metodos)

    for r in resultados:
        guardar_resultados(r)
    if MODO == "scale":
        ruta = SALIDAS / base.stem / "resumen_serie.xlsx"
        excel.guardar_resumen_serie(ruta, resultados)
        print(f"Resumen de la serie en {ruta}")


if __name__ == "__main__":
    try:
        main()
    except PermissionError as e:
        print(f"\nERROR: no se puede escribir {e.filename}. "
              "¿Lo tienes abierto en Excel? Ciérralo y vuelve a ejecutar.")
    except Exception as e:
        print(f"\nERROR: {e}")
