
from pathlib import Path
import numpy as np
import pandas as pd
import statsmodels.api as sm
import matplotlib.pyplot as plt

from statsmodels.tsa.stattools import adfuller, kpss
from statsmodels.stats.diagnostic import breaks_cusumolsresid

# ==========================================
# 1. CONFIGURAR PASTAS
# ==========================================

pasta = Path(__file__).resolve().parent
resultados = pasta / "resultados"
graficos = pasta / "graficos"

resultados.mkdir(exist_ok=True)
graficos.mkdir(exist_ok=True)

# ==========================================
# 2. CARREGAR E PREPARAR OS DADOS
# ==========================================

base = pd.read_excel(
    resultados / "base_regressao.xlsx"
)

base["data"] = pd.to_datetime(base["data"])
base = base.sort_values("data").reset_index(drop=True)

base = base[
    ["data", "selic_lag6", "ipca_12m"]
].copy()

for coluna in ["selic_lag6", "ipca_12m"]:
    base[coluna] = pd.to_numeric(
        base[coluna], errors="coerce"
    )

if base.isna().any().any():
    raise ValueError("Existem dados ausentes na base.")

meses = base["data"].dt.to_period("M")

if meses.duplicated().any():
    raise ValueError("Existem meses duplicados.")

periodo = pd.period_range(
    meses.min(), meses.max(), freq="M"
)

if len(periodo.difference(pd.PeriodIndex(meses))) > 0:
    raise ValueError("Existem meses ausentes na série.")

# ==========================================
# 3. RECONSTRUIR O MODELO DINÂMICO
# ==========================================

base["ipca_lag1"] = base["ipca_12m"].shift(1)
base = base.dropna().reset_index(drop=True)

y = base["ipca_12m"]

X = sm.add_constant(
    base[["selic_lag6", "ipca_lag1"]]
)

modelo = sm.OLS(y, X).fit()

residuos = modelo.resid

print("\n=== MODELO DINÂMICO ===")
print(modelo.summary())

# ==========================================
# 4. TESTE ADF DOS RESÍDUOS
# ==========================================

adf = adfuller(
    residuos,
    regression="c",
    autolag="AIC"
)

print("\n=== ADF DOS RESÍDUOS ===")
print(f"Estatística: {adf[0]:.6f}")
print(f"Valor-p: {adf[1]:.6f}")

# ==========================================
# 5. TESTE KPSS DOS RESÍDUOS
# ==========================================

kpss_resultado = kpss(
    residuos,
    regression="c",
    nlags="auto"
)

print("\n=== KPSS DOS RESÍDUOS ===")
print(f"Estatística: {kpss_resultado[0]:.6f}")
print(f"Valor-p: {kpss_resultado[1]:.6f}")

# ==========================================
# 6. TESTE CUSUM DE ESTABILIDADE
# ==========================================

cusum = breaks_cusumolsresid(
    residuos,
    ddof=int(modelo.df_model + 1)
)

print("\n=== TESTE CUSUM ===")
print(f"Estatística: {cusum[0]:.6f}")
print(f"Valor-p: {cusum[1]:.6f}")

# ==========================================
# 7. GRÁFICOS DOS RESÍDUOS
# ==========================================

fig, ax = plt.subplots(
    2, 1, figsize=(12, 8)
)

ax[0].plot(
    base["data"],
    residuos,
    color="#1459A6",
    linewidth=2
)

ax[0].axhline(
    0, color="red", linestyle="--"
)

ax[0].set_title(
    "Resíduos do modelo dinâmico"
)

ax[0].set_ylabel("Resíduos")
ax[0].grid(alpha=0.2)

# Soma acumulada padronizada ilustrativa
residuos_padronizados = (
    residuos / residuos.std(ddof=1)
)

soma_acumulada = (
    residuos_padronizados.cumsum()
    / np.sqrt(len(residuos))
)

ax[1].plot(
    base["data"],
    soma_acumulada,
    color="#1459A6",
    linewidth=2
)

ax[1].axhline(
    0, color="red", linestyle="--"
)

ax[1].set_title(
    "Soma acumulada dos resíduos padronizados"
)

ax[1].set_ylabel("Soma acumulada")
ax[1].set_xlabel("Período")
ax[1].grid(alpha=0.2)

plt.suptitle(
    "Diagnóstico complementar do modelo dinâmico",
    fontsize=15,
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    graficos / "validacao_modelo_dinamico.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    graficos / "validacao_modelo_dinamico.pdf",
    bbox_inches="tight"
)

plt.show()

# ==========================================
# 8. SALVAR RESULTADOS
# ==========================================

tabela = pd.DataFrame([
    {
        "Teste": "ADF dos resíduos",
        "Estatistica": adf[0],
        "Valor_p": adf[1]
    },
    {
        "Teste": "KPSS dos resíduos",
        "Estatistica": kpss_resultado[0],
        "Valor_p": kpss_resultado[1]
    },
    {
        "Teste": "CUSUM",
        "Estatistica": cusum[0],
        "Valor_p": cusum[1]
    }
])

tabela.to_excel(
    resultados / "validacao_modelo_dinamico.xlsx",
    index=False
)

print("\nValidação concluída com sucesso!")
print("Resultados e gráficos salvos.")
