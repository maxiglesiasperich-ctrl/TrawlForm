"""
Maxsurf Resistance: resistencia al avance con sus 14 métodos.

Comprobado con Maxsurf 2025:
- Solo admite Velocities.Low/High y calcula siempre 81 puntos equiespaciados.
- Fuera de su rango muchos métodos dan 0 (y también v = 0 en Item): "no calculado".
- Por defecto usa densidad 1025,9 kg/m3 y C_A = 0,0004: se fijan siempre desde aquí.
- Potencia (manual, pág. 34): P = R·V/η, con un único rendimiento η para todas las
  velocidades. Wyman es al revés: su fórmula da la potencia de motor, que no depende
  de η, y Maxsurf deduce R = η·P/V (comprobado: con η = 0,5 su R se reduce a la mitad).
- Al salir pregunta "Save measured data?" si antes no se cierran mediciones y diseño.
"""

import math
from pathlib import Path

from .conexion import ProgramaMaxsurf, dentro_de, misma_ruta

# Nombre -> código del enumerado hsMethodType.
METODOS = {
    "Savitsky pre-planeo": 1,
    "Savitsky planeo": 2,
    "Blount-Fox": 3,
    "Lahtiharju": 4,
    "Holtrop": 5,
    "Compton": 6,
    "Fung": 7,
    "Van Oortmerssen": 8,
    "Series 60": 9,
    "Delft I-II": 10,
    "Delft III": 11,
    "Slender Body": 12,
    "Wyman": 13,
    "KR Barge": 14,
}
CA_MAXSURF = 0.0004  # Vessel.CorrelationAllowance por defecto
CODILLO = 1          # hsCTHardChine


class Resistance(ProgramaMaxsurf):
    PROGID = "BentleyResistance.Application"
    EXE = "MaxsurfResistance.exe"
    TITULO = "Maxsurf Resistance ["

    def abrir(self, ruta, carpeta_propia):
        """Carga el diseño leyéndolo del disco (Resistance no modifica la geometría).
        Otro diseño abierto solo se cierra si está en carpeta_propia."""
        d = self.app.Design
        actual = d.DesignPath
        if actual:
            if not dentro_de(actual, carpeta_propia):
                raise RuntimeError(f"Maxsurf Resistance tiene abierto otro diseño ({actual}). "
                                   "Ciérralo (File > Close) y vuelve a ejecutar.")
            d.MeasurementsClose()
            d.DesignClose()
        d.DesignOpen(str(ruta))
        if not misma_ruta(d.DesignPath, ruta):
            raise RuntimeError(f"Maxsurf Resistance no ha podido abrir {ruta}")

    def calcular(self, metodos, v_max, paso, densidad, correlacion, rendimientos):
        """Resistencia y potencia de 0 a v_max [m/s] con los métodos dados, una vez
        por cada rendimiento η de 'rendimientos' (0 < η ≤ 1).

        Cada múltiplo de 'paso' [m/s] es un punto calculado por Maxsurf (sin
        interpolar). densidad en t/m3; correlacion es el C_A que Maxsurf añade en los
        métodos que lo usan aparte.
        Devuelve (casco, curvas): datos medidos del casco y, por rendimiento y método,
        una lista de puntos {v, Fn, Rt, Rf, Rr, P} en m/s, N y W (None = no calculado).
        """
        d = self.app.Design
        d.MeasureHull()
        d.Methods.SelectAll = False
        for m in metodos:
            d.Methods.Select(METODOS[m], True)
        d.Vessel.WaterDensity = densidad * 1000  # en kg/m3
        d.Vessel.CorrelationAllowance = correlacion

        curvas = {}
        for eta in rendimientos:
            d.Efficiency.Efficiency = eta * 100  # en %
            curvas[eta] = self._curvas(metodos, v_max, paso)
        d.Efficiency.Efficiency = 100  # valor por defecto de Maxsurf

        v = d.Vessel
        casco = {
            "LWL": v.LWL,
            "B": v.Beam,
            "T": v.Draft,
            "Volumen": v.DisplacedVolume,
            "Sup. mojada": v.WettedArea,
            "Cp": v.PrismaticCoeff,
            "Cwp": v.WaterplaneAreaCoeff,
            "Área sección máx.": v.MaxSectArea,
            "Cm": v.MaxSectArea / (v.Beam * v.Draft),
            "Semiángulo entrada": v.HalfAngleOfEntrance,
            "LCG desde maestra": v.LCGFromMidships,
            "Área espejo": v.TransomArea if v.TransomArea > 1e-9 else 0.0,  # ~1e-28 = ruido
            "Astilla muerta": v.Deadrise,
            "Codillo": v.ChineType == CODILLO,
        }
        return casco, curvas

    def _curvas(self, metodos, v_max, paso):
        """Curvas de cada método de 0 a v_max con los ajustes actuales de Maxsurf.

        Maxsurf calcula como máximo 80 pasos de velocidad (81 puntos) en cada cálculo;
        si hacen falta más, se calcula en varias veces (0-80 pasos, 80-160...) y se unen.
        """
        d = self.app.Design
        curvas = {m: [] for m in metodos}
        tramo = 80 * paso
        for k in range(max(1, math.ceil(v_max / tramo - 1e-9))):
            d.Velocities.Low = k * tramo
            d.Velocities.High = (k + 1) * tramo
            d.CalculateResistance()
            r = d.ResistanceResults
            # Índices de 1 a 81; el primer punto de cada cálculo repite el último del anterior.
            for i in range(1 if k == 0 else 2, r.Count + 1):
                for m in metodos:
                    res = r.Item(METODOS[m], i)
                    p = {"v": r.Velocity(i), "Fn": res.Fn, "Rt": res.Rt,
                         "Rf": res.Rf, "Rr": res.Rr, "P": res.Power}
                    if p["v"] > 0 and p["Rt"] == 0:
                        p.update(Fn=None, Rt=None, Rf=None, Rr=None, P=None)
                    curvas[m].append(p)
        return curvas

    def guardar_mediciones(self, ruta):
        """Guarda los datos medidos del casco y los ajustes (densidad, C_A...) en un
        .hsd, que se abre en Resistance con File > Open Measurement Data."""
        self.app.Design.MeasurementsSaveAs(str(ruta))
        if not Path(ruta).is_file():
            raise RuntimeError(f"Maxsurf Resistance no ha guardado {ruta}")

    def cerrar(self):
        """Cierra antes mediciones y diseño para que no pregunte "Save measured data?"."""
        if self.app is not None and self._proceso is not None:
            self.app.Design.MeasurementsClose()
            self.app.Design.DesignClose()
        super().cerrar()
