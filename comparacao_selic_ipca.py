
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Localizar os arquivos do projeto
pasta = Path(__file__).resolve().parent

selic = pd.read_excel(pasta / "dados" / "dados_selic.xlsx")
ipca = pd.read_excel(pasta / "dados" / "dados_ipca.xlsx")

# Preparar as datas
selic["data"] = pd.to_datetime(selic["data"])
ipca["data"] = pd.to_datetime(ipca["data"])

selic = selic.sort_values("data")
ipca = ipca.sort_values("data")

# Série 11 do BCB: Selic diária em percentual
# Anualização equivalente, considerando 252 dias úteis
selic["selic_anual"] = (
    (1 + selic["valor"] / 100) ** 252 - 1
) * 100

# Selecionar o último registro de cada mês
selic_mensal = (
    selic.set_index("data")["selic_anual"]
    .resample("ME").last()
)

# Calcular o IPCA acumulado em 12 meses
ipca_12m = (
    (1 + ipca.set_index("data")["valor"] / 100)
    .rolling(12, min_periods=12)
    .apply(np.prod, raw=True)
    .sub(1)
    .mul(100)
)

# Organizar ambas as séries por mês
comparacao = pd.concat(
    [
        selic_mensal.rename("Selic anualizada"),
        ipca_12m.resample("ME").last().rename("IPCA 12 meses")
    ],
    axis=1
).dropna()

# Criar o gráfico
fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(
    comparacao.index,
    comparacao["Selic anualizada"],
    color="#174EA6",
    linewidth=2.5,
    label="Selic anualizada equivalente"
)

ax.plot(
    comparacao.index,
    comparacao["IPCA 12 meses"],
    color="#D62828",
    linewidth=2.5,
    label="IPCA acumulado em 12 meses"
)

ax.set_title(
    "Brasil: evolução comparativa da Selic e da inflação (2021–2026)",
    fontsize=16,
    fontweight="bold",
    pad=20
)

ax.set_ylabel("Taxa (%)", fontsize=12)
ax.set_xlabel("Ano", fontsize=12)

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

ax.grid(alpha=0.2)
ax.legend(frameon=False, fontsize=11)

plt.tight_layout()

# Salvar o gráfico
saida = pasta / "graficos"
saida.mkdir(exist_ok=True)

plt.savefig(
    saida / "comparacao_selic_ipca.png",
    dpi=300,
    bbox_inches="tight"
)

plt.savefig(
    saida / "comparacao_selic_ipca.pdf",
    bbox_inches="tight"
)

print("Gráfico comparativo salvo com sucesso!")
print("Meses comparados:", len(comparacao))

plt.show()
