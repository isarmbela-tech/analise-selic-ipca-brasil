
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import statsmodels.api as sm
from pathlib import Path

# ==========================================
# 1. ORGANIZAÇÃO DO PROJETO
# ==========================================

pasta = Path(__file__).resolve().parent
resultados = pasta / "resultados"
graficos = pasta / "graficos"

graficos.mkdir(exist_ok=True)
resultados.mkdir(exist_ok=True)

# ==========================================
# 2. CARREGAR A BASE
# ==========================================

df = pd.read_excel(
    resultados / "base_selic_ipca.xlsx",
    index_col=0,
    parse_dates=True
)

df = df.sort_index()

# ==========================================
# 3. DEFINIR DEFASAGEM DE 6 MESES
# ==========================================

df["selic_lag6"] = df["selic_12m"].shift(6)

base = df[
    ["selic_lag6", "ipca_12m"]
].dropna().copy()

print("Observações utilizadas:", len(base))

# ==========================================
# 4. ESTIMAR REGRESSÃO LINEAR
# ==========================================

X = sm.add_constant(base["selic_lag6"])
y = base["ipca_12m"]

modelo = sm.OLS(y, X).fit()

print("\nRESULTADOS DA REGRESSÃO")
print(modelo.summary())

# ==========================================
# 5. PREVISÕES E INTERVALOS
# ==========================================

grade = np.linspace(
    base["selic_lag6"].min(),
    base["selic_lag6"].max(),
    200
)

X_grade = sm.add_constant(
    pd.DataFrame({"selic_lag6": grade}),
    has_constant="add"
)

previsao = modelo.get_prediction(X_grade)

intervalos = previsao.summary_frame(alpha=0.05)

# ==========================================
# 6. GRÁFICO CIENTÍFICO
# ==========================================

fig, ax = plt.subplots(figsize=(12, 7))

ax.scatter(
    base["selic_lag6"],
    base["ipca_12m"],
    color="#174EA6",
    s=65,
    alpha=0.75,
    edgecolor="white",
    linewidth=0.8,
    label="Observações mensais"
)

ax.plot(
    grade,
    intervalos["mean"],
    color="#D62828",
    linewidth=2.5,
    label="Regressão linear (MQO)"
)

ax.fill_between(
    grade,
    intervalos["mean_ci_lower"],
    intervalos["mean_ci_upper"],
    color="#D62828",
    alpha=0.15,
    label="IC de 95% da média estimada"
)

# Estatísticas do modelo
beta = modelo.params["selic_lag6"]
r2 = modelo.rsquared
pvalor = modelo.pvalues["selic_lag6"]

texto = (
    f"Coeficiente β = {beta:.3f}\n"
    f"R² = {r2:.3f}\n"
    f"p-valor = {pvalor:.4f}\n"
    f"n = {len(base)}"
)

ax.text(
    0.03, 0.97,
    texto,
    transform=ax.transAxes,
    fontsize=11,
    va="top",
    bbox=dict(
        boxstyle="round,pad=0.6",
        facecolor="#F2F5FA",
        edgecolor="#D0D7E2"
    )
)

ax.set_title(
    "Relação entre Selic defasada e inflação no Brasil",
    fontsize=16,
    fontweight="bold",
    pad=20
)

ax.set_xlabel(
    "Selic acumulada em 12 meses, defasada em 6 meses (%)",
    fontsize=12
)

ax.set_ylabel(
    "IPCA acumulado em 12 meses (%)",
    fontsize=12
)

ax.grid(alpha=0.2)
ax.legend(loc="best", frameon=False)

plt.tight_layout()

# ==========================================
# 7. SALVAR RESULTADOS
# ==========================================

plt.savefig(
    graficos / "regressao_selic_ipca.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    graficos / "regressao_selic_ipca.pdf",
    bbox_inches="tight"
)

with open(
    resultados / "resumo_regressao.txt",
    "w",
    encoding="utf-8"
) as arquivo:
    arquivo.write(modelo.summary().as_text())

base.to_excel(
    resultados / "base_regressao.xlsx"
)

print("\nRegressão executada com sucesso!")
print("Gráfico e resultados salvos.")

plt.show()
