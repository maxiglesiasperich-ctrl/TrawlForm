"""Informe de texto de un modelo: configuración, escalado, hidrostáticas y resistencia."""

from calculos.resistencia import LEYENDA_MARCAS, LEYENDA_POTENCIA, NUDO, froudes, parametros


def _numero(valor, decimales=3):
    """Número con decimales fijos, o un guion si no hay valor."""
    return "—" if valor is None else f"{valor:.{decimales}f}"


def _kilo(valor):
    """N -> kN o W -> kW; None si no está calculado."""
    return None if valor is None else valor / 1000


def informe(r, configuracion):
    """Texto del informe de un modelo (r: resultados de main.calcular_modelo)."""
    t = ["=" * 80,
         f"INFORME: {r['nombre']}",
         f"{r['fecha']:%Y-%m-%d %H:%M} · Maxsurf {r.get('version', '?')}",
         f"Modelo: {r['ruta']}",
         "=" * 80,
         "", "CONFIGURACIÓN"]
    t += [f"  {k:24} {v}" for k, v in configuracion.items()]
    if "factores" in r:
        t.append(f"  {'Factores (L, B, D, T)':24} {', '.join(f'{x:g}' for x in r['factores'])}")
    if r["avisos"]:
        t += ["", "AVISOS"] + [f"  - {a}" for a in r["avisos"]]
    if "control" in r:
        t += _escalado(r["control"])
    if "hidrostaticas" in r:
        t += _hidrostaticas(r)
    if "casco" in r:
        t += _resistencia(r)
    return "\n".join(t)


def _escalado(control):
    t = ["", "CONTROL DEL ESCALADO (Maxsurf frente a la teoría del escalado afín;",
         "eslora, manga y puntal escalados, flotación aún escalada con el puntal)",
         f"  {'':28} {'Base':>10} {'Escalado':>10} {'Teórico':>10} {'Dif.':>8}"]
    for magnitud, base, escalado, teorico, dif in control["filas"]:
        t.append(f"  {magnitud:28} {base:10.4f} {escalado:10.4f} {_numero(teorico, 4):>10} "
                 f"{'' if dif is None else f'{dif:.2%}':>8}")
    t.append("  Resultado: " + ("correcto" if control["correcto"] else "NO CUADRA"))
    base, escalado, final = control["calados"]
    t.append(f"  Calado: base {base:.4f} m -> escalado con el puntal {escalado:.4f} m "
             f"-> final {final:.4f} m")
    return t


def _hidrostaticas(r):
    longitud, peso = r["unidades"]
    t = ["", f"HIDROSTÁTICAS EN LA DWL (unidades del diseño: {longitud}, {peso})"]
    t += [f"  {k:28} {v:12.4f}" for k, v in r["referencias"].items()]
    t.append("")
    t += [f"  {k:28} {v:12.4f}" for k, v in r["hidrostaticas"].items()]
    return t


def _resistencia(r):
    casco, v = r["casco"], r["v_servicio"]
    t = ["", "RESISTENCIA (Maxsurf Resistance)", "  Parámetros del casco:"]
    t += [f"    {k:24} {valor:10.4g}" for k, valor in parametros(casco).items()]
    t.append(f"    {'Tipo de casco':24} {'codillo' if casco['Codillo'] else 'pantoque redondo':>10}")

    fn = froudes(v, casco)
    rendimientos = list(r["curvas"])
    t += ["", f"  A la velocidad de servicio, {v / NUDO:g} kn "
              f"(FnL = {fn['FnL']:.3f}, Fnv = {fn['Fnv']:.3f}, Fnb = {fn['Fnb']:.3f}):",
          f"    {'':20}" + "".join(f"{f'--- η = {eta:g} ---':>19}" for eta in rendimientos),
          f"    {'Método':20}" + f"{'Rt kN':>9}{'P kW':>10}" * len(rendimientos) + "  Marcas"]
    for f in r["servicio"]:
        valores = "".join(f"{_numero(_kilo(f['Rt'][eta]), 2):>9}{_numero(_kilo(f['P'][eta]), 2):>10}"
                          for eta in rendimientos)
        t.append(f"    {f['Método']:20}{valores}  {f['Marcas']}")
    t.append(f"    Marcas: {LEYENDA_MARCAS}")
    t.append(f"    Potencia: {LEYENDA_POTENCIA}")

    t += ["", "  Validez y corrección de correlación de cada método:"]
    for f in r["servicio"]:
        t.append(f"    {f['Método']}" + (f"  ({f['Nota']})" if f["Nota"] else ""))
        t.append(f"      Corrección: {f['Corrección']}")
        if f["Casco fuera de rango"]:
            t.append(f"      Casco fuera de rango: {f['Casco fuera de rango']}")
        if f["Velocidad fuera de rango"]:
            t.append(f"      Velocidad fuera de rango: {f['Velocidad fuera de rango']}")
    t += ["", "  Curvas completas en resistencia.xlsx."]
    return t
