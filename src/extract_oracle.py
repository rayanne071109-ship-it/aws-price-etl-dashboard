import requests
import json
from pathlib import Path

BASE_URL = "https://apexapps.oracle.com/pls/apex/cetools/api/v1/products/"


def extrair_catalogo():
    # API publica, sem autenticacao. Traz todo o catalogo de precos da OCI em USD.
    print("Baixando catalogo completo de precos da Oracle (USD)...")
    resposta = requests.get(BASE_URL, params={"currencyCode": "USD"})
    resposta.raise_for_status()
    dados = resposta.json()
    return dados.get("items", [])


def main():
    Path("data/oracle").mkdir(parents=True, exist_ok=True)

    itens = extrair_catalogo()
    print(f"  -> {len(itens)} produtos salvos\n")

    with open("data/oracle/price_list.json", "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False)


if __name__ == "__main__":
    main()
