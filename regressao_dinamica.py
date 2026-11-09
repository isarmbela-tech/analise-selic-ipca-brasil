
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm

from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.graphics.tsaplots import plot_acf

# ==========================================
# 1. CONFIGURAR PASTAS
# ==========================================

pasta = Path(__file__).resolve().parent
resultados = pasta / "resultados"
graficos = pasta / "graficos"

resultados.mkdir(exist_ok=True)
graficos.mkdir(exist_ok=True)

# ==========================================
# 2. CARREGAR DADOS DA REGRESSÃO ANTERIOR
# ==========================================

base = pd.read_excel(
    resultados / "base_regressao.xlsx"
)

base["data"] = pd.to_datetime(base["data"])
base = base.sort_values("data").reset_index(drop=True)

colunas = ["data", "selic_lag6", "ipca_12m"]
base = base[colunas].copy()

# ==========================================
# 3. CRIAR A INFLAÇÃO DEFASADA
# ==========================================

# Conferir se os meses são consecutivos
meses = base["data"].dt.to_period("M")

if meses.duplicated().any():
    raise ValueError("Existem meses duplicados na base.")

# Identificar os meses ausentes
periodo_completo = pd.period_range(
    start=meses.min(),
    end=meses.max(),
    freq="M"
)

meses_ausentes = periodo_completo.difference(meses)

print("\n--- VERIFICAÇÃO DA SÉRIE TEMPORAL ---")
print("Primeiro mês:", meses.min())
print("Último mês:", meses.max())
print("Quantidade de meses ausentes:", len(meses_ausentes))

print("\nMeses ausentes:")
for mes in meses_ausentes:
    print(mes)

if len(meses_ausentes) > 0:
    raise ValueError(
        "A análise foi interrompida para corrigir "
        "as lacunas da série temporal."
    )

base["ipca_lag1"] = base["ipca_12m"].shift(1)

base = base.dropna().reset_index(drop=True)

print("\nObservações utilizadas:", len(base))

# ==========================================
# 4. ESTIMAR OS MODELOS
# ==========================================

y = base["ipca_12m"]

# Modelo simples
X1 = sm.add_constant(base[["selic_lag6"]])

modelo_simples = sm.OLS(y, X1).fit()

# Modelo dinâmico
X2 = sm.add_constant(
    base[["selic_lag6", "ipca_lag1"]]
)

modelo_dinamico = sm.OLS(y, X2).fit()

# Erros robustos HAC - Newey-West
modelo_hac = modelo_dinamico.get_robustcov_results(
    cov_type="HAC",
    maxlags=6
)

print("\n--- MODELO DINÂMICO ---")
print(modelo_dinamico.summary())

print("\n--- MODELO DINÂMICO COM HAC ---")
print(modelo_hac.summary())

# ==========================================
# 5. COMPARAR MODELOS
# ==========================================

comparacao = pd.DataFrame({
    "Modelo": ["Simples", "Dinâmico"],
    "R2": [
        modelo_simples.rsquared,
        modelo_dinamico.rsquared
    ],
    "R2_ajustado": [
        modelo_simples.rsquared_adj,
        modelo_dinamico.rsquared_adj
    ],
    "AIC": [
        modelo_simples.aic,
        modelo_dinamico.aic
    ],
    "BIC": [
        modelo_simples.bic,
        modelo_dinamico.bic
    ]
})

print("\n--- COMPARAÇÃO DOS MODELOS ---")
print(comparacao.to_string(index=False))

comparacao.to_excel(
    resultados / "comparacao_modelos_dinamicos.xlsx",
    index=False
)

# ==========================================
# 6. TABELA DE COEFICIENTES ROBUSTOS
# ==========================================

coeficientes = pd.DataFrame({
    "Variavel": X2.columns,
    "Coeficiente": modelo_hac.params,
    "Erro_padrao_HAC": modelo_hac.bse,
    "Valor_p_HAC": modelo_hac.pvalues,
    "IC95_inferior": modelo_hac.conf_int()[:, 0],
    "IC95_superior": modelo_hac.conf_int()[:, 1]
})

coeficientes.to_excel(
    resultados / "coeficientes_dinamicos_hac.xlsx",
    index=False
)

print("\n--- COEFICIENTES HAC ---")
print(coeficientes.to_string(index=False))

# ==========================================
# 7. DIAGNÓSTICO DE AUTOCORRELAÇÃO
# ==========================================

residuos = modelo_dinamico.resid

ljung = acorr_ljungbox(
    residuos,
    lags=[6, 12],
    return_df=True
)

print("\n--- TESTE DE LJUNG-BOX ---")
print(ljung)

ljung.to_excel(
    resultados / "ljung_box_dinamico.xlsx"
)

# ==========================================
# 8. GRÁFICO: VALORES OBSERVADOS E AJUSTADOS
# ==========================================

plt.rcParams.update({
    "font.size": 11,
    "axes.spines.top": False,
    "axes.spines.right": False
})

fig, ax = plt.subplots(figsize=(13, 6))

ax.plot(
    base["data"],
    y,
    color="#1558B0",
    linewidth=2.5,
    label="IPCA observado"
)

ax.plot(
    base["data"],
    modelo_dinamico.fittedvalues,
    color="#D62728",
    linewidth=2.3,
    linestyle="--",
    label="IPCA ajustado"
)

ax.set_title(
    "Brasil: inflação observada e ajustada pelo modelo dinâmico",
    fontsize=16,
    fontweight="bold",
    pad=18
)

ax.set_xlabel("Período")
ax.set_ylabel("IPCA acumulado em 12 meses (%)")
ax.grid(alpha=0.18)
ax.legend(frameon=False)

plt.tight_layout()

plt.savefig(
    graficos / "regressao_dinamica_ajuste.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    graficos / "regressao_dinamica_ajuste.pdf",
    bbox_inches="tight"
)

plt.show()

# ==========================================
# 9. GRÁFICO: DIAGNÓSTICO DOS RESÍDUOS
# ==========================================

fig, axes = plt.subplots(
    1, 2, figsize=(14, 5)
)

axes[0].scatter(
    modelo_dinamico.fittedvalues,
    residuos,
    color="#2563EB",
    alpha=0.8
)

axes[0].axhline(
    0, color="#D62728", linestyle="--"
)

axes[0].set_title("Resíduos versus valores ajustados")
axes[0].set_xlabel("Valores ajustados")
axes[0].set_ylabel("Resíduos")
axes[0].grid(alpha=0.15)

plot_acf(
    residuos,
    lags=min(15, len(residuos) - 1),
    ax=axes[1],
    color="#1558B0"
)

axes[1].set_title("Autocorrelação dos resíduos")
axes[1].set_xlabel("Defasagem (meses)")

fig.suptitle(
    "Diagnóstico do modelo de regressão dinâmica",
    fontsize=16,
    fontweight="bold"
)

plt.tight_layout()

plt.savefig(
    graficos / "diagnostico_modelo_dinamico.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    graficos / "diagnostico_modelo_dinamico.pdf",
    bbox_inches="tight"
)

plt.show()

print("\nAnálise dinâmica concluída com sucesso!")
print("Resultados e gráficos salvos nas pastas do projeto.")
