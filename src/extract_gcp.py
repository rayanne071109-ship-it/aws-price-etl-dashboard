import requests
import json
import time
from pathlib import Path

# Compute Engine service id (fixo, publicado pela Google)
SERVICE_ID = "6F81-5844-456A"
BASE_URL = f"https://cloudbilling.googleapis.com/v1/services/{SERVICE_ID}/skus"

# Gere em: console.cloud.google.com -> APIs & Services -> Credentials
# (precisa habilitar a "Cloud Billing API" no projeto antes)
API_KEY = "AIzaSyBHnp4a-TeR1WA82UGnkSR9haHqjp4LVsk"


def extrair_skus():
    itens = []
    params = {"key": API_KEY, "pageSize": 5000}
    page_token = None

    pagina = 1
    while True:
        if page_token:
            params["pageToken"] = page_token

        print(f"  Pagina {pagina}...")

        # Tenta ate 3 vezes essa pagina, com espera crescente entre tentativas
        # (ajuda quando o erro e rate limit / instabilidade momentanea).
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
            resposta.raise_for_status()  # esgotou as tentativas, agora sim estoura o erro

        resposta.raise_for_status()
        dados = resposta.json()

        itens.extend(dados.get("skus", []))
        page_token = dados.get("nextPageToken")
        pagina += 1

        if not page_token:
            break

        time.sleep(1)  # pequena pausa entre paginas pra nao estourar rate limit

    return itens


def main():
    Path("data/gcp").mkdir(parents=True, exist_ok=True)

    if API_KEY == "SUA_API_KEY_AQUI":
        print("ATENCAO: defina sua API_KEY do Google Cloud antes de rodar este script.")
        return

    print("Extraindo SKUs do Compute Engine (GCP)...")
    itens = extrair_skus()

    with open("data/gcp/compute_engine_skus.json", "w", encoding="utf-8") as f:
        json.dump(itens, f, ensure_ascii=False)

    print(f"  -> {len(itens)} SKUs salvos\n")


if __name__ == "__main__":
    main()
