
import requests
from pathlib import Path

pasta = Path(__file__).resolve().parent
pasta_dados = pasta / "dados"
pasta_graficos = pasta / "graficos"

pasta_dados.mkdir(exist_ok=True)
pasta_graficos.mkdir(exist_ok=True)

# API do Banco Central - Taxa Selic

url = "https://api.bcb.gov.br/dados/serie/bcdata.sgs.11/dados?formato=json&dataInicial=05/11/2021&dataFinal=05/11/2026"



import requests
from datetime import datetime, timedelta

# API oficial do Banco Central do Brasil
# SGS 11: Taxa Selic diária (% ao dia)

data_final = datetime.today()
data_inicial = datetime(2021, 11, 5)

inicio = data_inicial.strftime("%d/%m/%Y")
fim = data_final.strftime("%d/%m/%Y")

url = (
    "https://api.bcb.gov.br/dados/serie/"
    "bcdata.sgs.11/dados"
)

parametros = {
    "formato": "json",
    "dataInicial": inicio,
    "dataFinal": fim
}

print("Conectando ao Banco Central...")


resposta = requests.get(
    url,
    params=parametros,
    headers={
        "Cache-Control": "no-cache",
        "Pragma": "no-cache"
    },
    timeout=30
)
resposta.raise_for_status()

if resposta.status_code != 200:
    raise SystemExit(
        f"Erro na consulta ao Banco Central. "
        f"Status HTTP: {resposta.status_code}"
    )

if not resposta.content:
    raise SystemExit(
        "O Banco Central retornou uma resposta vazia."
    )

dados = resposta.json()

print("Quantidade de registros recebidos:", len(dados))

if dados:
    print("Primeiro registro:", dados[0])
    print("Último registro:", dados[-1])

datas = [registro["data"] for registro in dados]

quantidade_duplicadas = len(datas) - len(set(datas))

print("Datas duplicadas:", quantidade_duplicadas)

valores_ausentes = sum(
    1
    for registro in dados
    if registro.get("data") in (None, "")
    or registro.get("valor") in (None, "")
)

print("Registros com valores ausentes:", valores_ausentes)

valores_invalidos = 0

for registro in dados:
    try:
        float(registro["valor"])
    except (ValueError, TypeError, KeyError):
        valores_invalidos += 1

print("Valores não numéricos:", valores_invalidos)

datas_invalidas = 0

for registro in dados:
    try:
        datetime.strptime(registro["data"], "%d/%m/%Y")
    except (ValueError, TypeError, KeyError):
        datas_invalidas += 1

print("Datas inválidas:", datas_invalidas)

valores_nao_positivos = sum(
    1
    for registro in dados
    if float(registro["valor"]) <= 0
)

print("Valores não positivos:", valores_nao_positivos)

# Validacao automatica da qualidade dos dados
if (
    quantidade_duplicadas > 0
    or valores_ausentes > 0
    or valores_invalidos > 0
    or datas_invalidas > 0
    or valores_nao_positivos > 0
):
    raise SystemExit(
        "ERRO: Foram encontrados problemas na qualidade dos dados. "
        "A exportacao foi interrompida."
    )

import pandas as pd

print("VALIDACAO APROVADA: dados consistentes.")

# Relatorio de qualidade dos dados
relatorio_qualidade = pd.DataFrame({
    "Indicador": [
        "Total de registros",
        "Datas duplicadas",
        "Registros com valores ausentes",
        "Valores nao numericos",
        "Datas invalidas",
        "Valores nao positivos"
    ],
    "Resultado": [
        len(dados),
        quantidade_duplicadas,
        valores_ausentes,
        valores_invalidos,
        datas_invalidas,
        valores_nao_positivos
    ]
})
# Salvar o relatorio de qualidade em Excel
pasta_resultados = pasta / "resultados"
pasta_resultados.mkdir(exist_ok=True)

relatorio_qualidade.to_excel(
    pasta_resultados / "relatorio_qualidade_selic.xlsx",
    index=False
)

print("Relatorio de qualidade salvo com sucesso!")
print("Conexão realizada com sucesso!")

print("Primeiro registro:", dados[0])
print("Último registro:", dados[-1])

# Transformar os dados em uma tabela
tabela = pd.DataFrame(dados)

# Converter a coluna de datas
tabela["data"] = pd.to_datetime(
    tabela["data"], format="%d/%m/%Y"
)

# Converter os valores para números
tabela["valor"] = pd.to_numeric(tabela["valor"])

# Organizar os dados por data
tabela = tabela.sort_values("data")

# Mostrar a tabela
print("\nTabela organizada:")
print(tabela.to_string(index=False))

# Exportar os dados para Excel
# Validar os dados antes da exportação
if tabela.empty:
    raise ValueError("A tabela está vazia. Exportação cancelada.")

if tabela[["data", "valor"]].isna().any().any():
    raise ValueError("Existem dados ausentes. Exportação cancelada.")

if tabela["data"].duplicated().any():
    raise ValueError("Existem datas duplicadas. Exportação cancelada.")

print("Validação concluída: dados prontos para exportação.")
tabela.to_excel(
    pasta_dados / "dados_selic_atualizado.xlsx",
    index=False
)

print("\nArquivo Excel criado com sucesso!")

print("Data e hora da atualização:", datetime.now().strftime("%d/%m/%Y %H:%M:%S"))
print("Período dos dados:", tabela["data"].min().strftime("%d/%m/%Y"),
      "até", tabela["data"].max().strftime("%d/%m/%Y"))
print("Fonte dos dados: Banco Central do Brasil")
print("Série SGS: 11 - Taxa Selic diária (% ao dia)")
print("Arquivo exportado: dados/dados_selic_atualizado.xlsx")

# ANÁLISE ESTATÍSTICA DA TAXA SELIC

print("\n--- ANÁLISE ESTATÍSTICA ---")

print("Quantidade de registros:", len(tabela))

print("Média:", round(tabela["valor"].mean(), 6))

print("Mediana:", round(tabela["valor"].median(), 6))

print("Valor mínimo:", tabela["valor"].min())

print("Valor máximo:", tabela["valor"].max())

print("Desvio-padrão:", round(tabela["valor"].std(), 6))

print("Dados ausentes:", tabela.isnull().sum().sum())

import matplotlib.pyplot as plt
import matplotlib.dates as mdates

# Criar gráfico de evolução da Selic
fig, ax = plt.subplots(figsize=(13, 6))

ax.plot(
    tabela["data"],
    tabela["valor"],
    color="#1764A0",
    linewidth=2,
    label="Selic diária"
)

ax.set_title(
    f"Evolução da Taxa Selic Diária no Brasil "
    f"({tabela['data'].min():%m/%Y} – {tabela['data'].max():%m/%Y})",
    fontsize=16,
    fontweight="bold",
    pad=20
)

ax.set_xlabel("Ano", fontsize=12)
ax.set_ylabel("Taxa Selic diária (%)", fontsize=12)

ax.xaxis.set_major_locator(mdates.YearLocator())
ax.xaxis.set_major_formatter(mdates.DateFormatter("%Y"))

ax.grid(alpha=0.2)
ax.legend(frameon=False)

plt.tight_layout()

plt.savefig(
    pasta_graficos / "grafico_selic.png",
    dpi=300,
    bbox_inches="tight"
)
plt.show()
