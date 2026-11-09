
from pathlib import Path
import pandas as pd
from statsmodels.tsa.stattools import adfuller, kpss

# Pastas do projeto
pasta = Path(__file__).resolve().parent
resultados = pasta / "resultados"
resultados.mkdir(exist_ok=True)

# Carregar a base utilizada na regressão
base = pd.read_excel(resultados / "base_regressao.xlsx")

base["data"] = pd.to_datetime(base["data"])
base = base.sort_values("data").reset_index(drop=True)

# Verificar a estrutura das séries
print("\nCOLUNAS DISPONÍVEIS:")
print(base.columns.tolist())

print("\nPERÍODO DA BASE:")
print(base["data"].min(), "até", base["data"].max())

# Testes de estacionariedade
def testar_serie(nome, valores):
    serie = pd.to_numeric(valores, errors="coerce").dropna()

    print(f"\n{'=' * 50}")
    print(f"SÉRIE: {nome}")
    print(f"Observações: {len(serie)}")

    if len(serie) < 15 or serie.nunique() < 2:
        print("Série insuficiente para os testes.")
        return []

    resultados_testes = []

    # Teste ADF
    adf = adfuller(serie, regression="c", autolag="AIC")

    print("\nTESTE ADF")
    print(f"Estatística: {adf[0]:.4f}")
    print(f"Valor-p: {adf[1]:.4f}")

    resultados_testes.append({
        "Serie": nome,
        "Teste": "ADF",
        "Estatistica": adf[0],
        "Valor_p": adf[1]
    })

    # Teste KPSS
    resultado_kpss = kpss(
        serie,
        regression="c",
        nlags="auto"
    )

    print("\nTESTE KPSS")
    print(f"Estatística: {resultado_kpss[0]:.4f}")
    print(f"Valor-p: {resultado_kpss[1]:.4f}")

    resultados_testes.append({
        "Serie": nome,
        "Teste": "KPSS",
        "Estatistica": resultado_kpss[0],
        "Valor_p": resultado_kpss[1]
    })

    return resultados_testes


tabela = []

tabela += testar_serie(
    "Selic defasada em 6 meses",
    base["selic_lag6"]
)

tabela += testar_serie(
    "IPCA acumulado em 12 meses",
    base["ipca_12m"]
)

# ==========================================
# TESTES DAS PRIMEIRAS DIFERENÇAS
# ==========================================

print("\nTESTES DAS PRIMEIRAS DIFERENÇAS")

tabela += testar_serie(
    "Primeira diferença da Selic defasada",
    base["selic_lag6"].diff()
)

tabela += testar_serie(
    "Primeira diferença do IPCA acumulado",
    base["ipca_12m"].diff()
)

# Salvar os resultados
tabela = pd.DataFrame(tabela)

tabela.to_excel(
    resultados / "testes_estacionariedade.xlsx",
    index=False
)

print("\nTestes concluídos!")
print("Resultados salvos em testes_estacionariedade.xlsx")
