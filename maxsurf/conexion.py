"""
Arranque y conexión COM con los programas de Maxsurf (común a Modeler y Resistance).

Comprobado con Maxsurf 2025 y licencia de estudiante:
- Si es COM quien arranca el programa, su ventana de licencia queda oculta y nunca
  llega a estar listo: se lanza el .exe y se espera a su ventana principal.
- Al arrancar, Bentley muestra "License Configuration". En los procesos que lanzamos
  nosotros se pulsa OK si la licencia está en estado "Ok" (p. ej. "Ok, Student").
- Modeler muestra además el asistente "Design Quickstart" ~2 s después de arrancar;
  se cierra con Cancel (ver Modeler.conectar).
- Si el programa ya estaba abierto, COM se conecta a esa ventana y no se cierra.
- Tras Exit() el proceso no termina mientras Python retenga el objeto COM.
- Con Modeler y Resistance abiertos a la vez, Modeler no termina de cerrarse:
  se usan uno detrás de otro.
- IsInitializedCorrectly da False aunque todo funciona: no se usa.
"""

import csv
import gc
import os
import subprocess
import time

import win32con
import win32gui
import win32process
from win32com.client import gencache

CARPETA_MAXSURF = r"E:\MAXSURF\bin\win64"


def misma_ruta(a, b):
    """True si a y b son el mismo archivo."""
    return os.path.normcase(os.path.abspath(a)) == os.path.normcase(os.path.abspath(b))


def dentro_de(ruta, carpeta):
    """True si ruta está dentro de carpeta."""
    ruta = os.path.normcase(os.path.abspath(ruta))
    carpeta = os.path.normcase(os.path.abspath(carpeta))
    try:
        return os.path.commonpath([ruta, carpeta]) == carpeta
    except ValueError:  # unidades de disco distintas
        return False


def titulos_ventanas(exe):
    """Títulos de ventana de los procesos abiertos con ese ejecutable."""
    salida = subprocess.run(
        ["tasklist", "/V", "/FO", "CSV", "/NH", "/FI", f"IMAGENAME eq {exe}"],
        capture_output=True, text=True).stdout
    return [fila[-1] for fila in csv.reader(salida.splitlines())
            if fila and fila[0].lower() == exe.lower()]


def _ventana(pid, titulo):
    """Ventana visible del proceso pid cuyo título empieza por 'titulo', o None."""
    ventanas = []

    def buscar(hwnd, _):
        if (win32gui.IsWindowVisible(hwnd)
                and win32process.GetWindowThreadProcessId(hwnd)[1] == pid
                and win32gui.GetWindowText(hwnd).startswith(titulo)):
            ventanas.append(hwnd)
        return True

    win32gui.EnumWindows(buscar, None)
    return ventanas[0] if ventanas else None


def _controles(hwnd):
    """Controles de una ventana: lista de (clase, texto, hwnd)."""
    controles = []

    def anotar(h, _):
        controles.append((win32gui.GetClassName(h), win32gui.GetWindowText(h), h))
        return True

    win32gui.EnumChildWindows(hwnd, anotar, None)
    return controles


def _pulsar(controles, texto):
    """Pulsa el botón con ese texto; True si existe."""
    botones = [h for clase, t, h in controles if clase == "Button" and t == texto]
    if botones:
        win32gui.PostMessage(botones[0], win32con.BM_CLICK, 0, 0)
    return bool(botones)


def _aceptar_licencia(pid):
    """Pulsa OK en la ventana de licencia del proceso pid si la licencia está "Ok".

    Devuelve "sin ventana", "aceptada" o el texto de la ventana (licencia aún no lista).
    """
    hwnd = _ventana(pid, "License Configuration")
    if hwnd is None:
        return "sin ventana"
    controles = _controles(hwnd)
    licencia_ok = any(clase == "Static" and t.startswith("Ok") for clase, t, _ in controles)
    if licencia_ok and _pulsar(controles, "OK"):
        return "aceptada"
    return " | ".join(t for _, t, _ in controles if t.strip())


def cerrar_dialogo(pid, titulo, boton, espera_s):
    """Espera hasta espera_s a que el proceso pid muestre el diálogo 'titulo', pulsa
    'boton' y espera a que se cierre. True si lo ha cerrado."""
    inicio = time.time()
    while time.time() - inicio < espera_s:
        hwnd = _ventana(pid, titulo)
        if hwnd is not None and _pulsar(_controles(hwnd), boton):
            while _ventana(pid, titulo) is not None and time.time() - inicio < espera_s + 10:
                time.sleep(0.5)
            return True
        time.sleep(0.5)
    return False


class ProgramaMaxsurf:
    """Conexión con un programa de Maxsurf, para usar con `with`.

    Si ya estaba abierto se conecta a él y lo deja abierto; si no, lo abre y lo cierra.
    """

    PROGID = None   # identificador COM
    EXE = None      # ejecutable, en CARPETA_MAXSURF
    TITULO = None   # texto del título de su ventana principal

    def __init__(self):
        self.app = None
        self._proceso = None  # solo si lo hemos lanzado nosotros

    def __enter__(self):
        self.conectar()
        return self

    def __exit__(self, *_):
        self.cerrar()

    @property
    def version(self):
        return self.app.Version

    def _listo(self):
        # Título "Maxsurf Xxx [...]" o "archivo.msd - Maxsurf Xxx [...]".
        return any(self.TITULO in t for t in titulos_ventanas(self.EXE))

    def conectar(self, espera_max_s=120):
        """Se conecta al programa, abriéndolo si hace falta."""
        if not titulos_ventanas(self.EXE):
            self._proceso = subprocess.Popen([os.path.join(CARPETA_MAXSURF, self.EXE)])

        inicio = time.time()
        licencia = "sin ventana"
        while not self._listo():
            if time.time() - inicio > espera_max_s:
                detalle = "" if licencia in ("sin ventana", "aceptada") else f" Dice: {licencia}"
                raise TimeoutError(f"{self.EXE} no ha terminado de arrancar en {espera_max_s} s. "
                                   f"Mira si la ventana de licencia espera respuesta.{detalle}")
            if self._proceso is not None:
                licencia = _aceptar_licencia(self._proceso.pid)
                if licencia == "aceptada":
                    time.sleep(2)  # tiempo para que se cierre la ventana
            time.sleep(1)
        self.app = gencache.EnsureDispatch(self.PROGID)

    def cerrar(self):
        """Suelta la conexión y, si lo abrimos nosotros, cierra el programa y espera a
        que termine (si no termina en 60 s se fuerza: es nuestro y ya se le pidió salir)."""
        app, self.app = self.app, None
        if app is not None and self._proceso is not None:
            app.Exit()
            del app
            gc.collect()
            try:
                self._proceso.wait(timeout=60)
            except subprocess.TimeoutExpired:
                self._proceso.kill()
