# TrawlForm — Diseño preliminar de embarcaciones con Maxsurf

Programa en Python que **maneja Maxsurf automáticamente** para el diseño preliminar de
una embarcación. A partir de un modelo de Maxsurf (`.msd`) calcula, sin que tengas que
tocar Maxsurf:

- las **hidrostáticas** (desplazamiento, coeficientes de forma, centros, radios
  metacéntricos…) con **Maxsurf Modeler**;
- la **resistencia al avance y la potencia** con los métodos de **Maxsurf Resistance**
  (Savitsky, Holtrop, Van Oortmerssen…), avisando cuando un método no es válido para
  tu casco o tu velocidad;
- y, si quieres, **variantes escaladas** del modelo (más eslora, más manga, otro puntal u
  otro calado) con todos sus resultados.

Los resultados son **los del propio Maxsurf**: el programa no calcula por su cuenta,
le da las órdenes a Maxsurf y recoge lo que este calcula. Al final te deja un informe
de texto, varios Excel, gráficas y los archivos de Maxsurf de cada caso.

> **Este documento es el manual de uso.** La explicación técnica (cómo funciona por
> dentro, qué se ha comprobado y con qué fórmulas) está en
> [`documentacion/Documentacion_tecnica.pdf`](documentacion/Documentacion_tecnica.pdf).

---

## Índice

1. [Qué necesitas](#1-qué-necesitas)
2. [Instalación (solo la primera vez)](#2-instalación-solo-la-primera-vez)
3. [Uso en 4 pasos](#3-uso-en-4-pasos)
4. [La configuración, variable a variable](#4-la-configuración-variable-a-variable)
5. [Ejemplos de configuración](#5-ejemplos-de-configuración)
6. [Qué resultados obtienes y cómo leerlos](#6-qué-resultados-obtienes-y-cómo-leerlos)
7. [Organización de las carpetas](#7-organización-de-las-carpetas)
8. [Problemas frecuentes](#8-problemas-frecuentes)
9. [Avisos importantes](#9-avisos-importantes)

---

## 1. Qué necesitas

| Necesitas | Detalle |
|---|---|
| **Windows** | 10 u 11. Maxsurf y la automatización que usa el programa solo existen en Windows. |
| **Maxsurf 2025** | Modeler y Resistance, con licencia. Probado con la versión 25.00.00.280 y licencia de estudiante. |
| **Python 3.12 de 64 bits** | El lenguaje en el que está escrito el programa. Otras versiones 3.10 o superiores deberían funcionar. |
| **Tres librerías de Python** | `pywin32` (para hablar con Maxsurf), `openpyxl` (para los Excel) y `matplotlib` (para las gráficas). Se instalan con un solo comando, ver abajo. |

No hace falta saber programar: solo vas a **cambiar unos pocos valores** en un archivo
de texto (`main.py`) y **escribir un comando**.

---

## 2. Instalación (solo la primera vez)

### 2.1 Instalar Python

1. Descarga Python 3.12 (64 bits) de <https://www.python.org/downloads/windows/>.
2. Al instalarlo, **marca la casilla "Add python.exe to PATH"** (abajo, en la primera
   pantalla). Si no la marcas, Windows no encontrará Python desde la terminal.

### 2.2 Abrir una terminal en la carpeta del proyecto

La terminal es una ventana donde se escriben órdenes. Cualquiera de estas dos formas vale:

- **Con VS Code** (recomendado): abre la carpeta del proyecto con *Archivo → Abrir
  carpeta* y luego *Terminal → Nueva terminal*.
- **Con el Explorador de Windows**: entra en la carpeta del proyecto, haz clic derecho
  en un hueco vacío y elige *Abrir en Terminal*.

### 2.3 Instalar las librerías

En la terminal, escribe esto y pulsa Intro:

```
python -m pip install -r requirements.txt
```

Verás cómo se descargan e instalan `pywin32`, `openpyxl` y `matplotlib`. Termina con
un mensaje *Successfully installed…* (o *Requirement already satisfied* si ya estaban).

### 2.4 Comprobar dónde está instalado Maxsurf

El programa busca Maxsurf en **`E:\MAXSURF\bin\win64`**. Si en tu ordenador está en otro
sitio (por ejemplo `C:\Program Files\Bentley\Maxsurf\bin\win64`), abre el archivo
`maxsurf/conexion.py` y cambia esta línea:

```python
CARPETA_MAXSURF = r"E:\MAXSURF\bin\win64"
```

por la ruta de tu instalación (la carpeta donde está `MaxsurfModeler.exe`). Deja la `r`
y las comillas tal cual.

---

## 3. Uso en 4 pasos

**1. Pon tu modelo en `inputs/models/`.**
Copia ahí tu archivo `.msd`. Tu archivo **nunca se modifica**: el programa solo lo lee
(y, en el modo de escalado, trabaja sobre copias).

**2. Configura `main.py`.**
Ábrelo con VS Code o con el Bloc de notas. Al principio hay un bloque marcado como
`CONFIGURACIÓN`: es lo único que tienes que tocar. Como mínimo, pon en `MODELO` el
nombre de tu archivo. Cada variable se explica en el apartado 4.

**3. Ejecuta el programa.** En la terminal:

```
python main.py
```

Qué vas a ver mientras se ejecuta:
- Se **abre Maxsurf Modeler** solo; aparece un instante la ventana de licencia de
  Bentley y **se acepta sola**. Después hace lo mismo **Maxsurf Resistance**.
- Al terminar, **Maxsurf se cierra solo**. No toques las ventanas de Maxsurf mientras
  trabaja.
- Tarda unos **25 segundos por modelo**.
- En la terminal aparece el informe con los resultados y la línea
  `Resultados guardados en …\outputs\…`.

**4. Mira los resultados** en `outputs/<nombre de tu modelo>/` (ver apartado 6).

> Si Maxsurf **ya estaba abierto** cuando lanzas el programa, este lo usa tal cual y
> **no lo cierra** al terminar. Si tienes abierto otro diseño en Maxsurf, el programa
> se para y te pide que lo cierres, para no hacerte perder cambios.

---

## 4. La configuración, variable a variable

Todo se configura en el bloque `CONFIGURACIÓN` de `main.py`. Respeta el formato de los
ejemplos: los textos van **entre comillas**, las listas **entre corchetes `[ ]`** y los
decimales llevan **punto**, no coma (`1.025`, no `1,025`).

| Variable | Qué es | Valores posibles | Ejemplo |
|---|---|---|---|
| `MODO` | Qué hace el programa | `"normal"`: calcula tu modelo tal cual. `"scale"`: crea modelos escalados y los calcula | `"normal"` |
| `MODELO` | Tu archivo de Maxsurf, dentro de `inputs/models/` | Nombre del archivo con su extensión | `"pesquero.msd"` |
| `HIDROSTATICAS` | Calcular las hidrostáticas | `True` (sí) o `False` (no) | `True` |
| `RESISTENCIA` | Calcular resistencia y potencia | `True` o `False` | `True` |
| `FACTORES` | Solo en modo `"scale"`: un modelo escalado por cada grupo de 4 factores (eslora, manga, puntal, calado) | Lista de grupos entre paréntesis | `[(1.20, 1.10, 0.90, 0.90)]` |
| `DENSIDAD` | Densidad del agua, en t/m³ | Agua salada: `1.025` | `1.025` |
| `METODOS` | Métodos de resistencia | `"todos"` o una lista con los nombres exactos | `["Savitsky planeo", "Holtrop"]` |
| `CORRELACION` | Aplicar la corrección modelo-buque (C_A) en los métodos en los que Maxsurf la añade aparte | `True` o `False` | `True` |
| `VEL_SERVICIO` | Velocidad de servicio, en nudos | Mejor un múltiplo de `PASO` | `25.0` |
| `VEL_MAXIMA` | Hasta qué velocidad se calculan las curvas, en nudos | | `35.0` |
| `PASO` | Cada cuántos nudos se calcula un punto de las curvas | `0.5` es un buen valor | `0.5` |
| `RENDIMIENTOS` | Rendimiento η para la potencia, P = Rt·V/η | Lista de valores entre 0 y 1. `1.0` = sin pérdidas (potencia efectiva) | `[1.0, 0.6, 0.5]` |

### Los factores de escala (modo `"scale"`)

Cada factor **multiplica** una dimensión del modelo base: `1.00` = sin cambio,
`1.20` = un 20 % más, `0.90` = un 10 % menos.

| Posición | Factor | Qué hace |
|---|---|---|
| 1.º | Eslora | Alarga o acorta el casco |
| 2.º | Manga | Ensancha o estrecha el casco |
| 3.º | Puntal | Estira o comprime el casco en altura |
| 4.º | Calado | **No cambia el casco**: sube o baja la flotación |

Si el factor de puntal y el de calado son iguales, el resultado es un **escalado
proporcional** (afín) del casco completo. Si son distintos, primero se escala el casco
con el puntal y luego se coloca la flotación en *calado del modelo base × factor de
calado*. Ejemplo: `(1.00, 1.00, 1.00, 1.10)` = el mismo casco con un 10 % más de calado.

### Los métodos de resistencia

Nombres disponibles (escríbelos **exactamente así**, con mayúsculas y guiones):

| Para planeo y semiplaneo | Para buques de desplazamiento | Otros |
|---|---|---|
| `"Savitsky planeo"` | `"Holtrop"` | `"Delft I-II"`, `"Delft III"` (veleros) |
| `"Savitsky pre-planeo"` | `"Van Oortmerssen"` | `"Slender Body"` (método numérico) |
| `"Blount-Fox"` | `"Compton"` | `"KR Barge"` (barcazas) |
| `"Lahtiharju"` | `"Fung"` | |
| `"Wyman"` | `"Series 60"` | |

Elige los que correspondan a tu tipo de barco: **lancha rápida** → Savitsky planeo,
Blount-Fox, Lahtiharju; **pesquero u otro buque de desplazamiento** → Holtrop,
Van Oortmerssen. El informe te dirá si tu casco está dentro del rango de cada método.

---

## 5. Ejemplos de configuración

**Calcular tu modelo tal cual (lo más habitual):**

```python
MODO = "normal"
MODELO = "pesquero.msd"
HIDROSTATICAS = True
RESISTENCIA = True
METODOS = ["Holtrop", "Van Oortmerssen"]
VEL_SERVICIO = 10.0
VEL_MAXIMA = 14.0
PASO = 0.5
RENDIMIENTOS = [1.0]
```

**Una serie de variantes escaladas** (tres modelos: más largo, más ancho, más calado):

```python
MODO = "scale"
MODELO = "pesquero.msd"
FACTORES = [
    (1.10, 1.00, 1.00, 1.00),
    (1.00, 1.10, 1.00, 1.00),
    (1.00, 1.00, 1.00, 1.10),
]
```

**Solo hidrostáticas** (más rápido; no abre Maxsurf Resistance):

```python
HIDROSTATICAS = True
RESISTENCIA = False
```

**Potencia con varios rendimientos** (efectiva y con un 60 % y un 50 % de rendimiento):

```python
RENDIMIENTOS = [1.0, 0.6, 0.5]
```

---

## 6. Qué resultados obtienes y cómo leerlos

Los resultados se guardan **ordenados por modelo base**:

```
outputs/
└── pesquero/                                ← un "caso" por modelo base
    ├── pesquero/                            ← resultados del modo "normal"
    ├── pesquero_L1.10_B1.00_D1.00_T1.00/    ← un modelo escalado (L eslora, B manga, D puntal, T calado)
    ├── pesquero_L1.00_B1.00_D1.00_T1.10/
    └── resumen_serie.xlsx                   ← modo "scale": una fila por modelo escalado
```

Cada vez que vuelves a calcular un modelo, **su carpeta se sobrescribe** con los
resultados nuevos.

### Archivos de cada carpeta

| Archivo | Qué contiene |
|---|---|
| `informe.txt` | Resumen legible de todo: configuración usada, avisos, hidrostáticas y resistencia a la velocidad de servicio. **Empieza por aquí.** |
| `hidrostaticas.xlsx` | Hidrostáticas en la flotación de referencia y datos de referencia (perpendiculares, línea base, flotación). |
| `resistencia.xlsx` | Hoja *Servicio*: todos los métodos a la velocidad de servicio. Hojas de curvas (*Rt*, *P*, *Rf*, *Rr*, una por rendimiento): una fila por velocidad y una columna por método, listas para hacer gráficas. Hojas *Casco* y *Validez*. |
| `escalado.xlsx` | Solo modelos escalados: factores y comprobación del escalado. |
| `resistencia.png` | Gráfica de resistencia total frente a velocidad. |
| `potencia.png` | Gráfica de potencia frente a velocidad. |
| `<modelo>.msd` | Copia del modelo calculado: se abre en Maxsurf Modeler con *File → Open*. |
| `<modelo>.hsd` | Datos medidos por Maxsurf Resistance: se abren en Resistance con *File → Open Measurement Data*. |

Los modelos escalados también se guardan en `inputs/models/scaled_models/<modelo base>/`.

### Las marcas de la tabla de resistencia

En el informe y en el Excel, cada método lleva unas letras que avisan de su validez:

| Marca | Significado |
|---|---|
| (nada) | El casco y la velocidad están dentro del rango del método |
| **C** | El **casco** está fuera del rango de dimensiones del método |
| **V** | La **velocidad** está fuera del rango del método |
| **N** | Maxsurf **no calcula** ese método a esa velocidad (sale "—") |
| **!** | Resistencia **negativa**: resultado sin sentido físico |

Un método con **C** o **V** da un número, pero **no es fiable**: está extrapolando fuera
de los datos con los que se construyó.

### Las gráficas

- **Color = método.** **Tono = rendimiento**: el rendimiento más alto en color fuerte y
  los menores en el mismo color, más claros.
- **Línea continua** = el método es válido; **línea discontinua** = fuera de su rango.
- **Línea vertical** = velocidad de servicio. El eje de arriba da el número de Froude
  de eslora (FnL).

### Qué es la potencia

Maxsurf calcula **P = Rt · V / η**. Con η = 1 es la **potencia efectiva** (la necesaria
para remolcar el casco). Con η < 1 es la potencia necesaria con ese rendimiento, por
ejemplo la potencia al freno si η es el rendimiento propulsivo global.

**Wyman es la excepción**: su fórmula da directamente la **potencia de motor**, que no
cambia con η, y Maxsurf deduce la resistencia como Rt = η·P/V. Por eso en las gráficas
aparece como "Wyman (P de motor)" y, con η = 1, su resistencia sale más alta que la real.

---

## 7. Organización de las carpetas

```
main.py              ← configuración y programa principal (lo único que editas)
README.md            ← este manual
requirements.txt     ← librerías de Python necesarias
maxsurf/             ← todo lo que habla con Maxsurf
    conexion.py      ←   abrir y cerrar Maxsurf, aceptar la licencia
    modeler.py       ←   abrir y guardar modelos, hidrostáticas, escalado
    resistance.py    ←   resistencia y potencia
calculos/            ← cálculos propios, sin Maxsurf
    escalado.py      ←   comprobación del escalado con la teoría
    resistencia.py   ←   rangos de validez de los métodos, números de Froude…
reports/             ← generación de resultados
    texto.py         ←   informe .txt
    excel.py         ←   libros .xlsx
    graficas.py      ←   gráficas .png
inputs/models/       ← tus modelos .msd
    scaled_models/   ←   modelos escalados que genera el programa
outputs/             ← resultados
documentacion/       ← documentación técnica (PDF) y manuales de Maxsurf
CLAUDE.md            ← notas de desarrollo: objetivos, decisiones y particularidades de Maxsurf
```

---

## 8. Problemas frecuentes

| Mensaje o síntoma | Causa y solución |
|---|---|
| `python` no se reconoce como comando | Python no está en el PATH. Reinstálalo marcando *Add python.exe to PATH*. |
| `No module named 'win32com'` (u `openpyxl`, `matplotlib`) | Faltan las librerías: `python -m pip install -r requirements.txt`. |
| `… no ha terminado de arrancar en 120 s. Mira si la ventana de licencia espera respuesta` | Maxsurf no ha podido coger la licencia. Mira la ventana *License Configuration* de Bentley: si la licencia no aparece como "Ok", revísala (conexión, caducidad…). |
| `No existe …\inputs\models\…` | El nombre de `MODELO` no coincide con el archivo: revisa mayúsculas y la extensión `.msd`. |
| `Maxsurf Modeler tiene abierto otro diseño` (o *Resistance*) | Tienes Maxsurf abierto con otro modelo. Guárdalo, ciérralo (*File → Close*) y vuelve a ejecutar. |
| `no se puede escribir … ¿Lo tienes abierto en Excel?` | Hay un Excel de resultados abierto. Ciérralo y vuelve a ejecutar. |
| `METODOS tiene que ser "todos" o una lista entre corchetes` | Has escrito los métodos sin corchetes. Formato correcto: `["Savitsky planeo", "Holtrop"]`. |
| `Métodos desconocidos: …` | Algún nombre está mal escrito. Copia los nombres de la tabla del apartado 4. |
| El programa no encuentra Maxsurf | Maxsurf no está en `E:\MAXSURF`: cambia `CARPETA_MAXSURF` (apartado 2.4). |
| Un método sale con "—" en muchas velocidades | No es un error: Maxsurf no calcula ese método fuera de su rango de velocidades. |
| Aviso: `VEL_SERVICIO no es múltiplo de PASO` | El valor a la velocidad de servicio se ha interpolado. Usa una velocidad múltiplo del paso para tener el valor exacto de Maxsurf. |

---

## 9. Avisos importantes

- **Tu modelo base no se modifica nunca.** El programa solo guarda modelos dentro de
  `inputs/models/scaled_models/`.
- **Revisa siempre las marcas de validez.** Un método fuera de rango da números, pero
  no fiables.
- **El francobordo no se comprueba**: si pones un factor de calado mucho mayor que el de
  puntal, comprueba tú que la flotación queda por debajo de la cubierta.
- **GM y KG**: sin un cálculo de pesos no hay KG real, así que el programa no da GMt,
  GMl ni MTc. Sí da KMt y KMl.
- **Licencia de Maxsurf**: este programa usa la licencia que tengas instalada. Con
  licencia académica, los resultados son solo para uso académico.
- **Manuales de Maxsurf**: los de `documentacion/manuales_maxsurf/` (Modeler y
  Resistance) son propiedad de Bentley Systems. Están en este repositorio privado como
  referencia; no los publiques si algún día el repositorio pasa a ser público.
- **Licencia**: este repositorio no tiene licencia de uso. Todos los derechos están
  reservados: puedes consultar el código, pero no reutilizarlo ni redistribuirlo sin
  permiso del autor.

Para entender cómo funciona por dentro, qué se ha comprobado y de dónde salen las
fórmulas y los rangos de validez, consulta
[`documentacion/Documentacion_tecnica.pdf`](documentacion/Documentacion_tecnica.pdf).
