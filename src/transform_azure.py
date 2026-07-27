import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path.home() / "Documentos" / "aws-price-etl" / "data" / "azure"

def carregar_itens(caminho):
    with open(caminho, "r", encoding="utf-8") as f:
        conteudo = json.load(f)

    if isinstance(conteudo, list):
        return conteudo

    if isinstance(conteudo, dict) and "Items" in conteudo:
        return conteudo["Items"]

    print(f"  Aviso: formato inesperado em {caminho}, pulando.")
    return []

def transform():
    arquivos = list(DATA_DIR.glob("*.json"))
    print(f"Encontrados {len(arquivos)} arquivos em {DATA_DIR}")

    linhas = []
    for arquivo in arquivos:
        itens = carregar_itens(arquivo)
        print(f"  {arquivo.name}: {len(itens)} itens")
        for item in itens:
            linhas.append({
                "provedor": "azure",
                "regiao": item.get("armRegionName"),
                "tipo_instancia": item.get("armSkuName"),
                "nome_produto": item.get("productName"),
                "sistema_operacional": "Windows" if "windows" in (item.get("productName") or "").lower() else "Linux",
                "unidade": item.get("unitOfMeasure"),
                "tipo_preco": item.get("type"),
                "preco_hora_usd": item.get("retailPrice"),
                "moeda": item.get("currencyCode"),
            })

    df = pd.DataFrame(linhas)
    df = df.drop_duplicates()
    df = df[df["preco_hora_usd"] > 0]
    df = df[df["tipo_preco"] == "Consumption"]

    print(f"\nTotal de linhas: {len(df)}")
    print(df.head())

    saida = Path("data")
    saida.mkdir(exist_ok=True)
    df.to_parquet(saida / "produtos_azure.parquet", index=False)
    print(f"Salvo em: {saida / 'produtos_azure.parquet'}")

    return df

if __name__ == "__main__":
    transform()
