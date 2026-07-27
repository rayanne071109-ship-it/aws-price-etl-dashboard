import os
import requests
import json
import time
from pathlib import Path

# Compute Engine service id (fixo, publicado pela Google)
SERVICE_ID = "6F81-5844-456A"
BASE_URL = f"https://cloudbilling.googleapis.com/v1/services/{SERVICE_ID}/skus"

# A chave NUNCA fica no código. Defina a variável de ambiente antes de rodar:
#   export GCP_API_KEY="sua_chave_aqui"
API_KEY = os.environ.get("GCP_API_KEY")


def extrair_skus():
    itens = []
    params = {"key": API_KEY, "pageSize": 5000}
    page_token = None

    pagina = 1
    while True:
        if page_token:
            params["pageToken"] = page_token

        print(f"  Pagina {pagina}...")

        for tentativa in range(1, 4):
            resposta = requests.get(BASE_URL, params=params)
            if resposta.status_code == 200:
                break

            print(f"    Erro HTTP {resposta.status_code} (tentativa {tentativa}/3)")
            print(f"    Detalhe da API: {resposta.text[:500]}")

            if tentativa < 3:
                espera = 5 * tentativa
                print(f"    Esperando {espera}s antes de tentar de novo...")
                time.sleep(espera)
        else:
            resposta.raise_for_status()

        resposta.raise_for_status()
        dados = resposta.json()

        itens.extend(dados.get("skus", []))
        page_token = dados.get("nextPageToken")
        pagina += 1

        if not page_token:
            break

        time.sleep(1)

    return itens


def main():
    Path("data/gcp").mkdir(parents=True, exist_ok=True)

    if not API_KEY:
        print("ATENCAO: defina a variavel de ambiente GCP_API_KEY antes de rodar este script.")
        print('  export GCP_API_KEY="sua_chave_aqui"')
        return

    print("Extraindo SKUs do Compute Engine (GCP)...")
    itens = extrair_skus()

    with open("data/gcp/compute_engine_skus.json", "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False)

    print(f"  -> {len(itens)} SKUs salvos\n")


if __name__ == "__main__":
    main()
