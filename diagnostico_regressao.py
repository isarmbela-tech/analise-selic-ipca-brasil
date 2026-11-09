
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import statsmodels.api as sm
from statsmodels.stats.stattools import durbin_watson
from statsmodels.stats.diagnostic import acorr_ljungbox
from statsmodels.graphics.tsaplots import plot_acf

# Pastas do projeto
pasta = Path(__file__).resolve().parent
resultados = pasta / "resultados"
graficos = pasta / "graficos"

resultados.mkdir(exist_ok=True)
graficos.mkdir(exist_ok=True)

# Base utilizada na regressão anterior
base = pd.read_excel(
    resultados / "base_regressao.xlsx"
)

print("Colunas disponíveis:")
print(base.columns.tolist())
print("\nPrimeiras observações:")
print(base.head())


# ==========================================
# DIAGNÓSTICO DA REGRESSÃO SELIC E IPCA
# ==========================================

# Organizar os dados cronologicamente
base["data"] = pd.to_datetime(base["data"])
base = base.sort_values("data")

# Selecionar variáveis
base = base.dropna(subset=["selic_lag6", "ipca_12m"])

X = sm.add_constant(base["selic_lag6"])
y = base["ipca_12m"]

# Estimar regressão linear
modelo = sm.OLS(y, X).fit()

# Resíduos e valores ajustados
residuos = modelo.resid
ajustados = modelo.fittedvalues

# Testes estatísticos
dw = durbin_watson(residuos)
ljung = acorr_ljungbox(
    residuos, lags=[6, 12], return_df=True
)

print("\n--- DIAGNÓSTICO DO MODELO ---")
print(f"Observações: {len(base)}")
print(f"Durbin-Watson: {dw:.4f}")
print("\nTeste de Ljung-Box:")
print(ljung)

# Criar figura com quatro gráficos
fig, axs = plt.subplots(2, 2, figsize=(14, 10))

# 1. Resíduos versus ajustados
axs[0, 0].scatter(
    ajustados, residuos, color="#2563eb", alpha=0.8
)
axs[0, 0].axhline(0, color="red", linestyle="--")
axs[0, 0].set_title("Resíduos versus valores ajustados")
axs[0, 0].set_xlabel("Valores ajustados")
axs[0, 0].set_ylabel("Resíduos")

# 2. Histograma
axs[0, 1].hist(
    residuos, bins=10,
    color="#2563eb", edgecolor="white"
)
axs[0, 1].set_title("Distribuição dos resíduos")
axs[0, 1].set_xlabel("Resíduos")
axs[0, 1].set_ylabel("Frequência")

# 3. Gráfico Q-Q
sm.qqplot(
    residuos, line="45", ax=axs[1, 0],
    markerfacecolor="#2563eb",
    markeredgecolor="#2563eb"
)
axs[1, 0].set_title("Gráfico Q-Q dos resíduos")

# 4. Autocorrelação
plot_acf(
    residuos, lags=15, ax=axs[1, 1],
    color="#2563eb"
)
axs[1, 1].set_title("Autocorrelação dos resíduos (ACF)")

for ax in axs.flat:
    ax.grid(alpha=0.15)

fig.suptitle(
    "Diagnóstico da regressão: Selic e IPCA",
    fontsize=17, fontweight="bold"
)

plt.tight_layout()

# Salvar em alta qualidade
plt.savefig(
    graficos / "diagnostico_regressao.png",
    dpi=300, bbox_inches="tight"
)
plt.savefig(
    graficos / "diagnostico_regressao.pdf",
    bbox_inches="tight"
)

# Salvar testes estatísticos
with open(
    resultados / "diagnostico_estatistico.txt",
    "w", encoding="utf-8"
) as arquivo:
    arquivo.write(f"Durbin-Watson: {dw:.4f}\n\n")
    arquivo.write("Teste de Ljung-Box:\n")
    arquivo.write(ljung.to_string())

print("\nDiagnóstico salvo com sucesso!")

# ==========================================
# INFERÊNCIA ROBUSTA DE NEWEY-WEST (HAC)
# ==========================================

# Correção robusta com 6 defasagens
modelo_hac = modelo.get_robustcov_results(
    cov_type="HAC",
    maxlags=6,
    use_t=True
)

print("\n--- REGRESSÃO COM CORREÇÃO NEWEY-WEST ---")
print(modelo_hac.summary())

# Comparar resultados
comparacao = pd.DataFrame({
    "Variavel": modelo.params.index,
    "Coeficiente": modelo.params.values,
    "Erro_padrao_MQO": modelo.bse.values,
    "Valor_p_MQO": modelo.pvalues.values,
    "Erro_padrao_HAC": modelo_hac.bse,
    "Valor_p_HAC": modelo_hac.pvalues
})

print("\n--- COMPARAÇÃO MQO E HAC ---")
print(comparacao.to_string(index=False))

# Salvar resultados
comparacao.to_excel(
    resultados / "comparacao_mqo_hac.xlsx",
    index=False
)

with open(
    resultados / "resumo_regressao_hac.txt",
    "w",
    encoding="utf-8"
) as arquivo:
    arquivo.write(modelo_hac.summary().as_text())

print("\nResultados robustos salvos com sucesso!")

plt.show()
