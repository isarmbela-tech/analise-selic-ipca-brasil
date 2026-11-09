
import requests
import pandas as pd

# API do Banco Central - IPCA mensal (série 433)
url = (
    "https://api.bcb.gov.br/dados/serie/bcdata.sgs.433/dados"
    "?formato=json&dataInicial=01/01/2021&dataFinal=31/10/2026"
)

print("Conectando ao Banco Central...")

resposta = requests.get(url, timeout=30)
resposta.raise_for_status()

dados = resposta.json()

# Transformar os dados em tabela
tabela = pd.DataFrame(dados)

# Converter datas e valores
tabela["data"] = pd.to_datetime(
    tabela["data"], format="%d/%m/%Y"
)
tabela["valor"] = pd.to_numeric(tabela["valor"])

# Organizar por data
tabela = tabela.sort_values("data")

# Salvar na pasta dados
tabela.to_excel("dados/dados_ipca.xlsx", index=False)

print("\nColeta realizada com sucesso!")
print("Quantidade de registros:", len(tabela))
print(tabela.tail(10).to_string(index=False))
print("\nArquivo Excel salvo na pasta dados!")
