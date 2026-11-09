
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Carregar os dados oficiais do IPCA
df = pd.read_excel("dados/dados_ipca.xlsx")

df["data"] = pd.to_datetime(df["data"])
df = df.sort_values("data")

# Criar a média móvel de 12 meses
df["media_movel_12m"] = df["valor"].rolling(12).mean()

# Calcular o IPCA acumulado em 12 meses
df["ipca_acumulado_12m"] = (
    (1 + df["valor"] / 100)
    .rolling(window=12)
    .apply(lambda x: x.prod(), raw=True)
    .sub(1)
    .mul(100)
)

# Mostrar os últimos resultados
print("\nIPCA acumulado em 12 meses:")
print(
    df[["data", "ipca_acumulado_12m"]]
    .tail(12)
    .to_string(index=False)
)

# Configurar o gráfico
fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(
    df["data"], df["valor"],
    color="#2563EB",
    linewidth=1.8,
    marker="o",
    markersize=3,
    label="IPCA mensal"
)

ax.plot(
    df["data"], df["media_movel_12m"],
    color="#DC2626",
    linewidth=2.5,
    label="Média móvel de 12 meses"
)

ax.axhline(
    0, color="gray",
    linewidth=0.8,
    linestyle="--"
)

ax.set_title(
    "Evolução da Inflação Mensal no Brasil (2021–2026)",
    fontsize=17,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Ano", fontsize=12)
ax.set_ylabel("Variação mensal do IPCA (%)", fontsize=12)

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

ax.grid(alpha=0.2)
ax.legend(frameon=False)

plt.tight_layout()

# Salvar na pasta de gráficos
plt.savefig("graficos/grafico_ipca.png", dpi=300)

plt.show()
