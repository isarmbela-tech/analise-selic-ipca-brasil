
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from pathlib import Path

# Localizar os dados do projeto
pasta = Path(__file__).resolve().parent
arquivo = pasta / "dados" / "dados_ipca.xlsx"

# Ler os dados coletados
df = pd.read_excel(arquivo)

# Preparar os dados
df["data"] = pd.to_datetime(df["data"])
df["valor"] = pd.to_numeric(df["valor"])
df = df.sort_values("data")

# Calcular o IPCA acumulado em 12 meses
df["ipca_12m"] = (
    (1 + df["valor"] / 100)
    .rolling(window=12, min_periods=12)
    .apply(lambda x: x.prod(), raw=True)
    .sub(1)
    .mul(100)
)

df = df.dropna(subset=["ipca_12m"])

# Identificar os valores extremos da inflação
indice_max = df["ipca_12m"].idxmax()
indice_min = df["ipca_12m"].idxmin()

pico = df.loc[indice_max]
minimo = df.loc[indice_min]
ultimo = df.iloc[-1]

print("\n--- INDICADORES DO IPCA ---")

print(
    f"Maior inflação: {pico['ipca_12m']:.2f}% "
    f"em {pico['data']:%m/%Y}"
)

print(
    f"Menor inflação: {minimo['ipca_12m']:.2f}% "
    f"em {minimo['data']:%m/%Y}"
)

print(
    f"Último resultado: {ultimo['ipca_12m']:.2f}% "
    f"em {ultimo['data']:%m/%Y}"
)


# Metas centrais anuais
metas = {
    2021: 3.75,
    2022: 3.50,
    2023: 3.25,
    2024: 3.00,
    2025: 3.00,
    2026: 3.00
}

df["meta"] = df["data"].dt.year.map(metas)
df["limite_superior"] = df["meta"] + 1.5
df["limite_inferior"] = df["meta"] - 1.5

# Criar o gráfico
fig, ax = plt.subplots(figsize=(14, 7))

ax.plot(
    df["data"],
    df["ipca_12m"],
    color="#175CD3",
    linewidth=2.5,
    label="IPCA acumulado em 12 meses"
)

ax.plot(
    df["data"],
    df["meta"],
    color="#D92D20",
    linestyle="--",
    linewidth=1.8,
    label="Meta central"
)

ax.fill_between(
    df["data"],
    df["limite_inferior"],
    df["limite_superior"],
    color="#12B76A",
    alpha=0.12,
    label="Faixa de tolerância"
)

ax.set_title(
    "Inflação no Brasil: IPCA acumulado em 12 meses",
    fontsize=18,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Ano", fontsize=12)
ax.set_ylabel("IPCA acumulado (%)", fontsize=12)

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

ax.grid(alpha=0.2)
ax.legend(frameon=False, loc="upper right")


# Destacar os principais indicadores no gráfico
indicadores = [
    (pico, "Pico", "#C62828", (15, 15)),
    (minimo, "Mínimo", "#16803C", (15, -35)),
    (ultimo, "Último", "#175CD3", (-110, 20))
]

for registro, nome, cor, deslocamento in indicadores:
    ax.scatter(
        registro["data"],
        registro["ipca_12m"],
        color=cor,
        s=75,
        zorder=5
    )

    ax.annotate(
        f"{nome}: {registro['ipca_12m']:.2f}%\n"
        f"{registro['data']:%m/%Y}",
        xy=(registro["data"], registro["ipca_12m"]),
        xytext=deslocamento,
        textcoords="offset points",
        fontsize=10,
        fontweight="bold",
        color=cor,
        arrowprops=dict(arrowstyle="-", color=cor)
    )


plt.tight_layout()

# Salvar na pasta de gráficos
saida = pasta / "graficos"
saida.mkdir(exist_ok=True)

plt.savefig(
    saida / "grafico_ipca_acumulado.png",
    dpi=300,
    bbox_inches="tight"
)

print("Gráfico do IPCA acumulado salvo com sucesso!")

plt.show()
