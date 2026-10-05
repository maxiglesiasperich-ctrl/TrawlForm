"""
Relaciones entre todos los parámetros de la base de pesqueros (diseño paramétrico,
lección 2): matriz de Pearson y regresión lineal y = b0 + b1·x para cada pareja.

Ejecutar:  python database/parameter_relations.py
Escribe en output/: pearson_matrix.xlsx, pearson_matrix.png, relations.png y report.txt.
"""

from pathlib import Path

import matplotlib
matplotlib.use("Agg")  # sin ventanas: solo se guardan imágenes
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

CARPETA = Path(__file__).parent
DATABASE_PATH = CARPETA / "input" / "bdds - Fishing Vessels 21-27m.xlsx"
OUTPUT = CARPETA / "output"
SHEET = "FV 21-27m"  # "clean_bbd"

COLUMNS = {
    "LOA": "LengthOverallLOA",                # m
    "L": "LengthBetweenPerpendicularsLBP",    # m
    "B": "Breadth",                           # m
    "D": "Depth",                             # m
    "T": "Draught",                           # m
    "Disp": "Displacement",                   # t
    "DWT": "Deadweight",                      # t
    "GT": "GrossTonnage",
    "V": "Speed",                             # kn
    "P": "TotalHorsepowerofMainEngines",      # hp
}
DISTINCT_RELATIONS = ["L", "B", "D", "T", "Disp"]  # parámetros que definen un diseño distinto
TOP_PAIRS = 10  # parejas con mayor correlación que se destacan en el informe


def load_database(path=DATABASE_PATH, sheet=SHEET):
    """Base con los nombres cortos de COLUMNS; los 0 pasan a NaN (dato que falta en Sea-web)."""
    df = pd.read_excel(path, sheet_name=sheet)
    df.columns = [str(col).strip() for col in df.columns]
    return df[list(COLUMNS.values())].set_axis(list(COLUMNS), axis=1).replace(0, np.nan)


def establish_relations(df):
    """Regresión lineal y = b0 + b1·x para cada pareja de parámetros, como en los apuntes:
    β = (XᵀX)⁻¹XᵀY con X = [1, x]. Devuelve las matrices b0, b1 y r² (fila = y, columna = x)."""
    names = list(df)
    b0, b1, r2 = (pd.DataFrame(np.nan, index=names, columns=names) for _ in range(3))
    for y in names:
        for x in names:
            ok = df[x].notna() & df[y].notna()  # buques con los dos datos
            xs, ys = df[x][ok].to_numpy(), df[y][ok].to_numpy()
            X = np.column_stack([np.ones_like(xs), xs])
            beta = np.linalg.solve(X.T @ X, X.T @ ys)
            residuo = ys - X @ beta
            b0.loc[y, x], b1.loc[y, x] = beta
            r2.loc[y, x] = 1 - np.sum(residuo ** 2) / np.sum((ys - ys.mean()) ** 2)
    return b0, b1, r2


def plot_pearson(r, path):
    """Mapa de colores de la matriz de Pearson."""
    fig, ax = plt.subplots(figsize=(8, 7))
    imagen = ax.imshow(r, cmap="bwr_r", vmin=-1, vmax=1)
    ax.set_xticks(range(len(r)), r.columns)
    ax.set_yticks(range(len(r)), r.index)
    for i in range(len(r)):
        for j in range(len(r)):
            ax.text(j, i, f"{r.iloc[i, j]:.2f}", ha="center", va="center", fontsize=8)
    fig.colorbar(imagen, ax=ax, label="r de Pearson")
    fig.savefig(path, dpi=150, bbox_inches="tight")
    plt.close(fig)


def plot_relations(df, b0, b1, r2, path):
    """Matriz de gráficas: cada celda es y (fila) frente a x (columna) con su recta y r²;
    en la diagonal, el histograma del parámetro."""
    names = list(df)
    n = len(names)
    fig, axes = plt.subplots(n, n, figsize=(2.3 * n, 2.3 * n))
    for i, y in enumerate(names):
        for j, x in enumerate(names):
            ax = axes[i, j]
            if i == j:
                ax.hist(df[x].dropna(), bins=20)
            else:
                ax.scatter(df[x], df[y], s=4, alpha=0.4)
                xs = np.array([df[x].min(), df[x].max()])
                ax.plot(xs, b0.loc[y, x] + b1.loc[y, x] * xs, color="red")
                ax.set_title(f"r² = {r2.loc[y, x]:.2f}", fontsize=8)
            if i == n - 1:
                ax.set_xlabel(x)
            if j == 0:
                ax.set_ylabel(y)
            ax.tick_params(labelsize=6)
    fig.tight_layout()
    fig.savefig(path, dpi=120)
    plt.close(fig)


if __name__ == "__main__":
    OUTPUT.mkdir(exist_ok=True)
    df = load_database()
    r = df.corr()  # Pearson: ρ = cov(X,Y) / (σX·σY), con los buques que tienen los dos datos
    b0, b1, r2 = establish_relations(df)
    stats = df.describe().T

    names = list(df)
    ranking = pd.DataFrame(
        [(a, b, r.loc[a, b], r2.loc[a, b]) for i, a in enumerate(names) for b in names[i + 1:]],
        columns=["Parámetro 1", "Parámetro 2", "r", "r2"],
    ).sort_values("r", key=abs, ascending=False, ignore_index=True)

    with pd.ExcelWriter(OUTPUT / "pearson_matrix.xlsx") as excel:
        r.to_excel(excel, sheet_name="Pearson r")
        r2.to_excel(excel, sheet_name="r2")
        b0.to_excel(excel, sheet_name="b0")
        b1.to_excel(excel, sheet_name="b1")
        ranking.to_excel(excel, sheet_name="Ranking", index=False)
        stats.to_excel(excel, sheet_name="Estadísticas")
    plot_pearson(r, OUTPUT / "pearson_matrix.png")
    plot_relations(df, b0, b1, r2, OUTPUT / "relations.png")

    informe = "\n\n".join([
        f"Base: {DATABASE_PATH.name} (hoja {SHEET})\n"
        f"Buques: {len(df)} · diseños distintos ({', '.join(DISTINCT_RELATIONS)}): "
        f"{len(df[DISTINCT_RELATIONS].drop_duplicates())}",
        "ESTADÍSTICAS DE CADA PARÁMETRO\n" + stats.to_string(float_format="%.2f"),
        "MATRIZ DE PEARSON  ρ = cov(X,Y) / (σX·σY)\n" + r.to_string(float_format="%.2f"),
        f"LAS {TOP_PAIRS} PAREJAS CON MAYOR |r|\n" + ranking.head(TOP_PAIRS).to_string(float_format="%.3f"),
        "RELACIONES  y = b0 + b1·x  (matrices b0, b1 y r²: fila = y, columna = x)\n"
        "r² (en regresión lineal simple, r² = ρ²)\n" + r2.to_string(float_format="%.2f"),
    ])
    (OUTPUT / "report.txt").write_text(informe, encoding="utf-8")
    print(informe)
    print(f"\nResultados guardados en {OUTPUT}")
