"""
Maxsurf Modeler: abrir y guardar diseños, hidrostáticas y escalado afín.

Comprobado con Maxsurf 2025:
- Hydrostatics.Calculate(densidad, VCG) da Displacement = Volume·densidad (con 1,025
  sale en t), pero TPC (y MTc) salen 1000 veces menores: se corrigen.
- El VCG de Calculate se mide desde un origen interno y hacia abajo:
  KG = (InternalZero(vertical) - Baseline) - VCG. Hace falta para recuperar GMt,
  GMl y MTc cuando haya pesos (comprobando que h.KG devuelve el KG pedido).
- FrameOfReference da las posiciones respecto al zero pt., que Maxsurf recoloca al
  cambiar una referencia: por eso se fijan respecto al casco (FindAftExt, FindBase).
- LCB y LCF salen como en Data > Calculate Hydrostatics (desde el zero pt., + a proa).
- Design.Path y Design.Name dejan de dar la ruta ~0,3 s después de Open, aunque el
  diseño sigue abierto: el archivo abierto se lee del título de la ventana y se
  guarda con SaveAs y ruta explícita.
"""

import time
from pathlib import Path

from .conexion import ProgramaMaxsurf, cerrar_dialogo, dentro_de, misma_ruta, titulos_ventanas

UNIDADES_LONGITUD = {1: "m", 2: "cm", 3: "mm", 4: "ft", 5: "in", 6: "ft-in"}  # msDimensionUnits
UNIDADES_PESO = {1: "kg", 2: "lb", 3: "t", 4: "LT"}                            # msWeightUnits
VERTICAL = 3                                                                    # msDTVertical


class Modeler(ProgramaMaxsurf):
    PROGID = "BentleyModeler.Application"
    EXE = "MaxsurfModeler.exe"
    TITULO = "Maxsurf Modeler ["

    def conectar(self, espera_max_s=120):
        """Si lo abrimos nosotros, cierra además el asistente "Design Quickstart"
        (Cancel), que aparece ~2 s después de arrancar y se queda delante."""
        super().conectar(espera_max_s)
        if self._proceso is not None:
            cerrar_dialogo(self._proceso.pid, "Design Quickstart", "Cancel", espera_s=15)

    def _archivo_abierto(self):
        """Nombre del archivo que muestra el título de Modeler ('' si no hay diseño)."""
        for titulo in titulos_ventanas(self.EXE):
            if " - " + self.TITULO in titulo:
                return titulo.split(" - " + self.TITULO)[0]
        return ""

    def abrir(self, ruta, carpeta_propia, recargar=False):
        """Carga el diseño sin modificarlo; con recargar=True lo relee del disco
        aunque ya esté cargado.

        En un Modeler que abrió el usuario, si tiene otro diseño abierto que no es de
        carpeta_propia, se detiene para no perder cambios suyos.
        """
        d = self.app.Design
        actual = d.Path
        if actual and misma_ruta(actual, ruta) and not recargar:
            return
        abierto = self._archivo_abierto()
        if abierto and self._proceso is None and not (actual and dentro_de(actual, carpeta_propia)):
            raise RuntimeError(f"Maxsurf Modeler tiene abierto otro diseño ({actual or abierto}). "
                               "Guárdalo, ciérralo (File > Close) y vuelve a ejecutar.")
        if abierto:
            d.Close(False)
        d.Open(str(ruta), False, False)
        for _ in range(10):  # el título se actualiza enseguida, pero por si acaso
            if self._archivo_abierto() == Path(ruta).name:
                return
            time.sleep(0.5)
        raise RuntimeError(f"Maxsurf Modeler no ha podido abrir {ruta}")

    def descartar(self):
        """Cierra el diseño cargado sin guardar."""
        self.app.Design.Close(False)

    def guardar(self, ruta, carpeta_permitida):
        """Guarda el diseño cargado en 'ruta', solo si está en carpeta_permitida y es el
        archivo abierto en Modeler, y comprueba que el archivo se ha escrito."""
        ruta = Path(ruta)
        if not dentro_de(ruta, carpeta_permitida):
            raise RuntimeError(f"No se guarda {ruta}: solo se guardan modelos de {carpeta_permitida}")
        if self._archivo_abierto() != ruta.name:
            raise RuntimeError(f"No se guarda: Modeler no tiene abierto {ruta.name}")
        antes = ruta.stat().st_mtime
        self.app.Design.SaveAs(str(ruta), True)
        if ruta.stat().st_mtime == antes:
            raise RuntimeError(f"Maxsurf no ha guardado {ruta}")

    def unidades(self):
        """Unidades del diseño: (longitud, peso)."""
        p = self.app.Preferences
        return UNIDADES_LONGITUD.get(p.DimensionUnits, "?"), UNIDADES_PESO.get(p.WeightUnits, "?")

    def referencias(self):
        """Perpendiculares, maestra, línea base y DWL, desde el zero pt."""
        f = self.app.Design.FrameOfReference
        return {
            "Perpendicular de popa [m]": f.AftPerp,
            "Maestra [m]": f.Midships,
            "Perpendicular de proa [m]": f.FwdPerp,
            "Línea base [m]": f.Baseline,
            "Flotación DWL [m]": f.DatumWL,
        }

    def hidrostaticas(self, densidad):
        """Hidrostáticas en la DWL (densidad en t/m3).

        Calculate pide un VCG, pero sin pesos no hay KG real: se calcula con KG = 0 y
        no se devuelven GMt, GMl ni MTc, que son los únicos valores que dependen de él.
        """
        f = self.app.Design.FrameOfReference
        h = self.app.Design.Hydrostatics
        h.Calculate(densidad, f.InternalZero(VERTICAL) - f.Baseline)  # VCG para KG = 0
        return {
            "Desplazamiento [t]": h.Displacement,
            "Volumen [m3]": h.Volume,
            "Calado [m]": h.Draft,
            "LWL [m]": h.LWL,
            "Manga en flotación [m]": h.BeamWL,
            "Superficie mojada [m2]": h.WSA,
            "Área sección máx. [m2]": h.MaxCrossSectArea,
            "Área flotación [m2]": h.WaterplaneArea,
            "Cb": h.Cb,
            "Cp": h.Cp,
            "Cm": h.Cm,
            "Cwp": h.Cwp,
            "LCB desde zero pt. [m]": h.LCB,
            "LCF desde zero pt. [m]": h.LCF,
            "LCB desde popa extrema [m]": h.LCB - f.FindAftExt,
            "LCF desde popa extrema [m]": h.LCF - f.FindAftExt,
            "KB [m]": h.KB,
            "BMt [m]": h.BMt,
            "BMl [m]": h.BMl,
            "KMt [m]": h.KMt,
            "KMl [m]": h.KMl,
            "TPC [t/cm]": h.TPC * 1000,
        }

    def escalar(self, fx, fy, fz):
        """Escalado afín: eslora × fx, manga × fy, alturas × fz, con punto fijo en
        (extremo de popa, crujía, quilla). Escala también perpendiculares, línea base y DWL."""
        d = self.app.Design
        f = d.FrameOfReference
        superficies = list(d.Surfaces)
        bloqueadas = [s.Name for s in superficies if s.Locked]
        if bloqueadas:
            raise RuntimeError(f"Superficies bloqueadas (Locked): {bloqueadas}. "
                               "Desbloquéalas en el modelo base.")

        popa, quilla = f.FindAftExt, f.FindBase
        # propiedad: (distancia al casco ya escalada, punto del casco desde el que se mide)
        objetivos = {
            "AftPerp": (fx * (f.AftPerp - popa), "FindAftExt"),
            "FwdPerp": (fx * (f.FwdPerp - popa), "FindAftExt"),
            "Baseline": (fz * (f.Baseline - quilla), "FindBase"),
            "DatumWL": (fz * (f.DatumWL - quilla), "FindBase"),
        }

        # La ayuda no documenta el sistema del centro de ReScale: se escala en torno a
        # (0, 0, 0) y luego se devuelve el casco a su sitio.
        for s in superficies:
            s.ReScale(fx, fy, fz, 0.0, 0.0, 0.0)
        dx, dz = popa - f.FindAftExt, quilla - f.FindBase
        for s in superficies:
            s.Move(dx, 0.0, dz, False, 0)
        if abs(f.FindAftExt - popa) > 1e-4 or abs(f.FindBase - quilla) > 1e-4:
            raise RuntimeError("El casco no ha quedado en su sitio tras el escalado.")
        self._colocar(objetivos)  # la maestra la recoloca Maxsurf a mitad de las perpendiculares

    def fijar_calado(self, calado):
        """Coloca la flotación DWL a 'calado' metros sobre la línea base (el casco no cambia)."""
        self._colocar({"DatumWL": (calado, "Baseline")})

    def _colocar(self, objetivos):
        """Coloca referencias de FrameOfReference a una distancia de otra referencia:
        {propiedad: (distancia, referencia)}. Cada cambio puede mover el zero pt., así
        que se fija, se relee y se repite si hace falta."""
        f = self.app.Design.FrameOfReference

        def error(prop):
            distancia, punto = objetivos[prop]
            return getattr(f, prop) - getattr(f, punto) - distancia

        for prop, (distancia, punto) in objetivos.items():
            for _ in range(5):
                setattr(f, prop, getattr(f, punto) + distancia)
                if abs(error(prop)) < 1e-5:
                    break
        mal = [p for p in objetivos if abs(error(p)) > 1e-5]
        if mal:
            raise RuntimeError(f"No se han podido colocar las referencias {mal}.")
