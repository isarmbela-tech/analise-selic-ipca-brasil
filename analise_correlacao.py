
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from pathlib import Path

# 1. Pastas do projeto
pasta = Path(__file__).resolve().parent
dados = pasta / "dados"
graficos = pasta / "graficos"
resultados = pasta / "resultados"

graficos.mkdir(exist_ok=True)
resultados.mkdir(exist_ok=True)

# 2. Carregar os dados
selic = pd.read_excel(dados / "dados_selic.xlsx")
ipca = pd.read_excel(dados / "dados_ipca.xlsx")

for df in (selic, ipca):
    df["data"] = pd.to_datetime(df["data"])
    df["valor"] = pd.to_numeric(df["valor"], errors="coerce")
    df.dropna(subset=["data", "valor"], inplace=True)
    df.sort_values("data", inplace=True)

# 3. Selic acumulada em 12 meses
# Série 11: taxa percentual diária, em dias úteis.
# Produto dos fatores nos últimos 12 meses corridos.
selic = selic.drop_duplicates("data")
selic["fator"] = 1 + selic["valor"] / 100
selic["log_fator"] = np.log(selic["fator"])

# Acumulação móvel por janela temporal de 365 dias
selic_diaria = selic.set_index("data")["log_fator"]
selic_12m = (
    np.exp(selic_diaria.rolling("365D").sum()) - 1
) * 100

# Excluir observações sem histórico completo de 12 meses
inicio_selic = selic["data"].min()
selic_12m = selic_12m[
    selic_12m.index >= inicio_selic + pd.DateOffset(months=12)
]

selic_mensal = selic_12m.resample("ME").last()

# 4. IPCA acumulado em 12 meses
ipca = ipca.drop_duplicates("data")
ipca = ipca.set_index("data")["valor"]

ipca_12m = (
    (1 + ipca / 100)
    .rolling(12, min_periods=12)
    .apply(np.prod, raw=True)
    .sub(1)
    .mul(100)
)

ipca_12m.index = ipca_12m.index.to_period("M").to_timestamp("M")

# 5. Base mensal
base = pd.concat(
    [
        selic_mensal.rename("selic_12m"),
        ipca_12m.rename("ipca_12m")
    ],
    axis=1,
    sort=False
).dropna()

base = base.sort_index()

# 6. Correlações com defasagens
defasagens = [0, 1, 3, 6, 12]
linhas = []

for lag in defasagens:
    # Selic anterior versus inflação observada depois
    pares = pd.DataFrame({
        "selic": base["selic_12m"].shift(lag),
        "ipca": base["ipca_12m"]
    }).dropna()

    r = pares["selic"].corr(pares["ipca"])

    linhas.append({
        "defasagem_meses": lag,
        "correlacao_pearson": r,
        "observacoes": len(pares)
    })

tabela = pd.DataFrame(linhas)

print("\nCORRELAÇÕES SELIC x IPCA")
print(tabela.to_string(index=False))

# 7. Salvar tabelas
base.to_excel(resultados / "base_selic_ipca.xlsx")
tabela.to_excel(
    resultados / "correlacoes_selic_ipca.xlsx",
    index=False
)

# 8. Gráfico
fig, ax = plt.subplots(figsize=(11, 6))

cores = [
    "#174EA6" if r >= 0 else "#D62828"
    for r in tabela["correlacao_pearson"]
]

barras = ax.bar(
    tabela["defasagem_meses"].astype(str),
    tabela["correlacao_pearson"],
    color=cores,
    width=0.65
)

ax.axhline(0, color="black", linewidth=0.9)

ax.set_title(
    "Correlação entre Selic e IPCA por defasagem temporal",
    fontsize=15,
    fontweight="bold",
    pad=18
)

ax.set_xlabel("Defasagem da Selic (meses)")
ax.set_ylabel("Coeficiente de correlação de Pearson")

ax.set_ylim(-1.1, 1.1)
ax.grid(axis="y", alpha=0.2)

for barra in barras:
    altura = barra.get_height()
    ax.annotate(
        f"{altura:.3f}",
        (barra.get_x() + barra.get_width()/2, altura),
        xytext=(0, 5 if altura >= 0 else -15),
        textcoords="offset points",
        ha="center",
        fontsize=10,
        fontweight="bold"
    )

plt.tight_layout()

plt.savefig(
    graficos / "correlacao_selic_ipca.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    graficos / "correlacao_selic_ipca.pdf",
    bbox_inches="tight"
)

print("\nArquivos salvos com sucesso!")
print("Meses disponíveis:", len(base))

plt.show()
