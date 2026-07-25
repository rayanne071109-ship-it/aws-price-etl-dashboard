import requests
import json
from pathlib import Path

BASE_URL = "https://prices.azure.com/api/retail/prices"
REGIOES = ["eastus", "westus2", "brazilsouth", "westeurope"]

def extrair_regiao(regiao):
    itens = []
    url = (
        f"{BASE_URL}?$filter=serviceName eq 'Virtual Machines' "
        f"and armRegionName eq '{regiao}' and priceType eq 'Consumption'"
    )

    pagina = 1
    while url:
        print(f"  Pagina {pagina}...")
        resposta = requests.get(url)
        resposta.raise_for_status()
        dados = resposta.json()

        itens.extend(dados["Items"])
        url = dados.get("NextPageLink")
        pagina += 1

    return itens

def main():
    Path("data/azure").mkdir(parents=True, exist_ok=True)
    for regiao in REGIOES:
        print(f"Extraindo {regiao}...")
        itens = extrair_regiao(regiao)
        with open(f"data/azure/{regiao}.json", "w", encoding="utf-8") as f:
            json.dump(itens, f, ensure_ascii=False)
        print(f"  -> {len(itens)} itens salvos\n")

if __name__ == "__main__":
    main()
