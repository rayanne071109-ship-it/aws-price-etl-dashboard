import requests
import json
from pathlib import Path

BASE_URL = "https://api.vultr.com/v2/plans"


def extrair_planos():
    planos = []
    cursor = None
    pagina = 1

    while True:
        params = {"per_page": 500}
        if cursor:
            params["cursor"] = cursor

        print(f"  Pagina {pagina}...")
        resposta = requests.get(BASE_URL, params=params)
        resposta.raise_for_status()
        dados = resposta.json()

        planos.extend(dados.get("plans", []))

        cursor = dados.get("meta", {}).get("links", {}).get("next")
        pagina += 1

        if not cursor:
            break

    return planos


def main():
    Path("data/vultr").mkdir(parents=True, exist_ok=True)

    print("Extraindo planos da Vultr (endpoint publico, sem autenticacao)...")
    planos = extrair_planos()

    with open("data/vultr/plans.json", "w", encoding="utf-8") as f:
        json.dump(planos, f, ensure_ascii=False)

    print(f"  -> {len(planos)} planos salvos\n")


if __name__ == "__main__":
    main()
