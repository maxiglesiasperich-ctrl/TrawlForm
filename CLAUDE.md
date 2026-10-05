# Herramienta de diseño paramétrico para pesquero de menos de 24 m

## Objetivo
Aplicación en Python con una interfaz de deslizadores que, partiendo de un
diseño base ya modelado en Maxsurf, permita variar las dimensiones principales
(eslora, manga, calado, puntal) y ver cómo cambian: desplazamiento, Cb, Cp, Cm,
Cwp, LCB, KB, BM, resistencia, potencia y peso muerto.
El diseño base no se modifica nunca: siempre se trabaja sobre una copia.

## Sobre mí
Conozco la teoría de ingeniería naval y manejo Maxsurf y Rhino, pero no he
programado nunca. Explícame cada paso en español y con lenguaje sencillo, dime
exactamente qué ejecutar y qué resultado debo esperar.

## Entorno
- Windows, Python de 64 bits, librería pywin32.
- Maxsurf 2025 (25.00.00.280) con licencia académica (solo uso académico).
- Rhino y Grasshopper con licencia, disponibles como alternativa.

## Diseño base
- Archivo: [ruta al .msd]
- Eslora: [ ] m, manga: [ ] m, calado: [ ] m, puntal: [ ] m
- Desplazamiento: [ ] t, peso en rosca: [ ] t
- Velocidad de servicio: [ ] nudos

## Enfoque
Python controla Maxsurf mediante su interfaz de automatización COM (win32com),
de modo que los resultados son los del propio Maxsurf.
Todo el código que habla con Maxsurf va en un único módulo, separado de los
cálculos y de la interfaz.

## Fases (una cada vez)
1. Probar la conexión COM con Maxsurf Modeler. Identificadores candidatos:
   "BentleyModeler.Application", "Maxsurf.Application",
   "MAXSURF Modeller.Application".
2. Leer las hidrostáticas del diseño base y comprobar que coinciden con las
   que muestra Maxsurf.
3. Escalado afín (factores de eslora, manga y calado) sobre una copia y
   recálculo de hidrostáticas.
4. Resistencia: con Maxsurf Resistance por COM si es posible; si no, programar
   Van Oortmerssen y Holtrop-Mennen en Python.
5. Pesos: peso en rosca escalado desde el diseño base por grupos (acero,
   maquinaria, equipo). Peso muerto = desplazamiento - peso en rosca.
6. Interfaz con deslizadores (Streamlit) que muestre base y variante lado a lado.
7. Más adelante: variar Cb y LCB (transformación paramétrica o Lackenby) y
   estabilidad inicial (GM).

## Reglas
- No inventes nombres de métodos ni propiedades COM. Inspecciona la librería de
  tipos con win32com (makepy / gencache) o consulta ModelerAutomation.chm, que
  está en la carpeta de documentación de Maxsurf.
- No pases a la fase siguiente hasta que yo confirme que la actual funciona.
- Valida siempre con el casco base sin transformar antes de fiarte de un cálculo.
- Unidades: metros, toneladas, nudos, agua salada 1,025 t/m3.
- Los métodos empíricos deben avisar cuando una variante se salga de su rango
  de validez.
- Si la automatización COM no funciona con mi licencia, dímelo y pasamos al
  plan B: exportar la cartilla de trazado y calcular las hidrostáticas en
  Python, o hacerlo en Grasshopper.

## Estructura del código (reestructurado el 2026-10-05 a petición del usuario)
Se ejecuta `python main.py`. El usuario solo edita la CONFIGURACIÓN de main.py.
```
main.py             configuración + pipeline completo (sin módulo de "pasos" aparte)
maxsurf/            todo lo que habla con Maxsurf por COM (conexion, modeler, resistance)
calculos/           cálculos propios sin Maxsurf (escalado, resistencia)
reports/            informe .txt (texto.py), libros .xlsx (excel.py, con openpyxl) y
                    gráficas .png (graficas.py, con matplotlib)
inputs/models/      modelos .msd del usuario (nunca se modifican)
inputs/models/scaled_models/<modelo base>/   modelos generados por el modo "scale",
                                             una carpeta por caso (como en outputs)
outputs/<modelo base>/                 una carpeta por caso (modelo base)
    <modelo base>/                     resultados del modo "normal"
    <modelo base>_L.._B.._H../         resultados de cada modelo escalado (mismo nivel)
    resumen_serie.xlsx                 modo "scale"
  Cada carpeta de resultados: informe.txt, hidrostaticas.xlsx, resistencia.xlsx,
  escalado.xlsx (si es escalado) y los archivos de Maxsurf (petición del usuario):
  <modelo>.msd (copia del diseño analizado) y <modelo>.hsd (Resistance
  MeasurementsSaveAs: datos medidos del casco + densidad y C_A; se abre con File >
  Open Measurement Data; no guarda resultados, que solo están en los Excel).
```
- Documentación (2026-10-05): README.md = manual de uso para no programadores (en
  castellano); documentacion/Documentacion_tecnica.pdf = parte técnica (generado con
  reportlab desde un script temporal, no está en el repo; si cambia el programa hay
  que actualizar README y PDF); documentacion/manuales_maxsurf/ = ModelerManual.pdf y
  ResistanceManual.pdf (copyright de Bentley; incluidos porque el repo es privado:
  no publicarlos si pasa a ser público). requirements.txt: pywin32, openpyxl, matplotlib.
- Repositorio git (2026-10-05): proyecto movido a la carpeta TrawlForm/, clon del repo
  PRIVADO de GitHub maxiglesiasperich-ctrl/TrawlForm (rama main). Se unieron el
  "Initial commit" de GitHub y el historial local (merge de historias no relacionadas;
  .gitignore = plantilla Python de GitHub + sección propia; README propio con título
  TrawlForm). gh CLI no instalado. Decisiones del usuario:
  commits con maxiglesiasperich@gmail.com (config local del repo; la global es la de
  la UPC), SIN licencia (todos los derechos reservados, indicado en README),
  CLAUDE.md y manuales de Maxsurf INCLUIDOS, rib_test_1.msd incluido como ejemplo.
  .gitignore propio: .vscode/ (por si VS Code la recrea), outputs/ e
  inputs/models/scaled_models/.
- Modos: "normal" (pipeline del MODELO de inputs/models) y "scale" (un modelo
  escalado por cada juego de FACTORES = (eslora, manga, puntal, calado), nombre
  <modelo>_L1.20_B1.10_D0.90_T0.95).
- Puntal y calado independientes (2026-10-05): escalado afín con (eslora, manga,
  puntal), con la DWL escalada con el puntal y control teórico en ese estado; después
  Modeler.fijar_calado coloca la DWL en calado_base × f_calado sobre la línea base.
  No se comprueba el francobordo (el programa no sabe dónde está la cubierta).
- No se comparan modelos: cada ejecución calcula todos los parámetros de cada modelo.
- Las carpetas de outputs/<modelo>/ se sobrescriben en cada ejecución (decisión del
  usuario).
- Modeler y Resistance se usan uno detrás de otro: con los dos abiertos a la vez,
  Modeler no termina de cerrarse.
- Solo se guarda con Modeler dentro de scaled_models/ (Modeler.guardar lo exige).
- Design.Path y Design.Name dejan de dar la ruta ~0,3 s después de Design.Open
  (el diseño sigue abierto y el título de la ventana lo muestra): el archivo abierto
  se lee del título y se guarda con SaveAs(ruta, True), comprobando la fecha del archivo.
- Modeler muestra el asistente "Design Quickstart" ~2 s tras arrancar: si lo hemos
  abierto nosotros se cierra con Cancel.
- Si falla el escalado, se borra la copia de scaled_models (no queda un "escalado"
  sin escalar).
- Tras la reestructuración, resultados comparados con la versión anterior: idénticos
  (hidrostáticas, control de escalado y curvas de los 14 métodos).
- Estilo pedido: nombres en español y coherentes, comentarios breves e incidentes,
  sin redundancias. Sin archivos __init__.py (el usuario no los quiere): se importa
  directamente del archivo, p. ej. `from maxsurf.modeler import Modeler`.

## Estado actual
Fases 1, 2, 3 y 4 CONFIRMADAS por el usuario (2026-10-05).
Fases 5, 6 y 7 EN ESPERA (decisión del usuario, 2026-10-05): con las fases 1-4 le
basta para el diseño preliminar; se retomarán más adelante. No empezarlas sin que
el usuario lo pida. Al retomar la fase 5 quedaron pendientes dos preguntas: el
reparto del peso en rosca (acero/maquinaria/equipo) y la ley de escala de cada grupo.
Diseño de prueba provisional: inputs/models/rib_test_1.msd (RIB de ~8 m creada con
las formas predefinidas de Maxsurf; el pesquero real vendrá después).

### Conexión con Maxsurf (fase 1) - maxsurf/conexion.py
- Maxsurf 2025 (25.00.00.280), exes en E:\MAXSURF\bin\win64. Ayudas COM (.chm) y
  manuales (.pdf) en E:\MAXSURF.
- ProgIDs: "BentleyModeler.Application", "BentleyResistance.Application" (los otros
  candidatos no existen). También está BentleyStability.Application.
- pywin32 312 instalado el 2026-10-05 (no estaba).
- Si COM arranca el programa, la ventana de licencia queda oculta y nunca está
  listo: se lanza el .exe normal y se espera a la ventana "Maxsurf Xxx [".
  Con un diseño abierto el título es "archivo.msd - Maxsurf Xxx [...]".
- Al arrancar sale la ventana "License Configuration" (registro: HKCU\Software\
  Bentley\MaxsurfAndMultiframeCommonLicense2500, "Show At Startup" = 1, "Remember
  license selection" = 1). A petición del usuario (2026-10-05), conectar() pulsa OK
  automáticamente, solo en procesos lanzados por el script (por su PID) y solo si
  la licencia está en estado "Ok" (p. ej. "Ok, Student"); si no, avisa al agotar
  el tiempo con el texto de la ventana. Probado en Modeler y Resistance.
- Si el programa ya está abierto, COM se conecta a esa ventana: NUNCA llamar a Exit
  sobre una instancia que no hemos abierto nosotros.
- IsInitializedCorrectly da False aunque todo funciona: no usarlo como comprobación.
- Tras Exit() el proceso no termina mientras Python retenga el objeto COM: se suelta
  y se espera al proceso (si no termina en 60 s, se fuerza; es nuestro).

### Hidrostáticas (fase 2) - maxsurf/modeler.py
- Hydrostatics.Calculate(densidad, VCG): Displacement = Volume * densidad (con 1.025
  sale en t). TPC y MTc salen /1000 con esa densidad: se multiplican por 1000.
- LCB/LCF por COM = los de la ventana de Maxsurf ("from zero pt., +ve fwd").
- dVCG de Calculate: KG = (InternalZero(vertical) - Baseline) - dVCG.
- Sin pesos no hay KG real: se calcula con KG = 0 y NO se dan GMt, GMl ni MTc
  (decisión del usuario, 2026-10-05; con KG = 0 saldría GM = KM, sin sentido
  físico). Para recuperarlos hará falta un KG real, que en modo "scale" debería
  escalarse (KG × factor de alturas), y comprobar que h.KG devuelve el KG pedido.
- Comparado con Data > Calculate Hydrostatics (KG fluid = 0): coinciden todos los
  valores (Δ, V, T, LWL, B, WSA, áreas, Cb, Cp, Cm, Cwp, LCB, LCF, KB, BMt, BMl,
  GMt, GMl, KMt, KMl, TPC, MTc).

### Escalado afín (fase 3) - maxsurf/modeler.py, calculos/escalado.py
- Surface.ReScale + Move sobre una copia en scaled_models. Con 1.2/1.1/0.9 todas las
  magnitudes coinciden con la predicción teórica al 0,00 %; si no cuadra, no se guarda.
- FrameOfReference: sus valores van respecto al zero pt., que Maxsurf recoloca al
  cambiar una referencia (aquí: maestra y DWL). Fijar siempre respecto al casco
  (FindAftExt, FindBase) y releer. La maestra se recoloca sola.

### Resistencia (fase 4) - maxsurf/resistance.py, calculos/resistencia.py
- Los 14 métodos de Maxsurf Resistance (hsMethodType 1-14) se eligen por nombre
  con la variable METODOS de main.py ("todos" o una lista).
- Rangos de validez (velocidad con FnL/Fnv/Fnb y dimensiones):
  ResistanceManual.pdf, Appendix B (págs. 51-53), en calculos/resistencia.py.
- Maxsurf solo acepta Velocities.Low/High y da 81 puntos equiespaciados. La
  variable PASO (kn) fija el paso: se calcula por tramos de 80·PASO, así que toda
  velocidad múltiplo de PASO es un punto exacto de Maxsurf (comprobado: diferencia
  0 frente a Maxsurf directo). Solo se interpola si VEL_SERVICIO no es múltiplo de
  PASO, y el informe avisa. El usuario prefiere dejarlo así (2026-10-05).
- Fuera de su rango de velocidad muchos métodos devuelven 0 y también v = 0 en
  Item(): se tratan como "no calculado" y la velocidad se toma de Velocity(i).
- Correlación modelo-buque (C_A): variable CORRELACION (True/False); el script fija
  siempre Vessel.CorrelationAllowance (0.0004 = valor de Maxsurf, o 0). Comprobado:
  lo añaden aparte Savitsky pre-planeo, Lahtiharju, Van Oortmerssen, Slender Body
  (superficie en reposo) y Savitsky planeo, Blount-Fox (superficie en planeo);
  Holtrop, Compton y Fung lo llevan integrado (el usuario decidió no tocarlos);
  Wyman, Delft y KR Barge no llevan. El manual se equivoca con Savitsky pre-planeo.
  La opción "19th ITTC modified formula" no existe por COM.
- Al salir pregunta "Save measured data?" y se cuelga: cerrar antes con
  MeasurementsClose() y DesignClose().
- Potencia (manual pág. 34): P = R·V/η con un único η (Efficiency, en %). Variable
  RENDIMIENTOS de main.py (lista, 0 < η ≤ 1; 1 = potencia efectiva): Maxsurf calcula
  una vez por cada η; Excel e informe muestran Rt y P por η (columna "P", ya no "PE").
  Wyman es al revés (manual pág. 5, comprobado): su fórmula da potencia de motor, que
  no depende de η, y Maxsurf deduce Rt = η·P/V; con η = 1 su Rt está sobrestimada.
- Gráficas (reports/graficas.py, matplotlib 3.10): resistencia.png (Rt-V) y
  potencia.png (P-V) en cada carpeta de resultados. Color = método (tab10), tono =
  rendimiento (η mayor fuerte, menores más claros); continua = dentro de rango,
  discontinua = fuera de rango (casco o velocidad); línea vertical en V servicio; eje
  superior FnL. En Rt solo se dibujan los η que cambian la curva (en la práctica, Wyman).
  El usuario normalmente usará 2-3 métodos.
- Velocidad de servicio provisional: 25 kn, máxima 35 kn, paso 0,5 kn (RIB de
  prueba, lancha rápida: los métodos adecuados son Savitsky planeo / Blount-Fox).
- Con la RIB, Holtrop y Van Oortmerssen quedan fuera de rango; Van Oortmerssen
  llega a dar resistencias negativas (extrapolación de la regresión).

### Pendiente para más adelante (decidido por el usuario el 2026-10-05)
- Poder introducir tanto factores como medidas objetivo (eslora, manga, calado...).
- Posible: aviso de francobordo (calado mayor que el puntal) si se sabe la cubierta.