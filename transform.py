import ijson
import pandas as pd
from pathlib import Path

DATA_DIR = Path.home() / "Documentos" / "aws-price-etl" / "data"

def extract_products():
    produtos = {}
    arquivos = list(DATA_DIR.glob("*.json"))
    print(f"Encontrados {len(arquivos)} arquivos JSON em {DATA_DIR}")

    for arquivo in arquivos:
        print(f"Lendo produtos de {arquivo} ...")
        with open(arquivo, "rb") as f:
            for sku, produto in ijson.kvitems(f, "products"):
                if produto.get("productFamily") != "Compute Instance":
                    continue
                attrs = produto.get("attributes", {})
                if not attrs.get("instanceType"):
                    continue
                produtos[sku] = {
                    "sku": sku,
                    "region_code": attrs.get("regionCode"),
                    "location": attrs.get("location"),
                    "instance_type": attrs.get("instanceType"),
                    "instance_family": attrs.get("instanceFamily"),
                    "vcpu": attrs.get("vcpu"),
                    "memory": attrs.get("memory"),
                    "operating_system": attrs.get("operatingSystem"),
                    "tenancy": attrs.get("tenancy"),
                    "current_generation": attrs.get("currentGeneration"),
                }
    return produtos

def extract_ondemand_prices(skus_validos):
    precos = {}
    arquivos = list(DATA_DIR.glob("*.json"))

    for arquivo in arquivos:
        print(f"Lendo preços de {arquivo} ...")
        with open(arquivo, "rb") as f:
            for sku, termo in ijson.kvitems(f, "terms.OnDemand"):
                if sku not in skus_validos:
                    continue  # pula o que a gente nem guardou em products
                for t in termo.values():
                    for dim in t.get("priceDimensions", {}).values():
                        usd = dim.get("pricePerUnit", {}).get("USD")
                        if usd:
                            try:
                                valor = float(usd)
                                if valor > 0:
                                    precos[sku] = valor
                            except ValueError:
                                pass
    print(f"Preços encontrados: {len(precos)}")
    return precos

def transform():
    produtos = extract_products()
    precos = extract_ondemand_prices(set(produtos.keys()))

    # junta preço com produto, descartando quem não tem preço OnDemand
    for sku, preco in precos.items():
        if sku in produtos:
            produtos[sku]["price_per_hour_usd"] = preco

    df = pd.DataFrame.from_dict(produtos, orient="index")
    df = df[df["price_per_hour_usd"].notna()]  # remove quem ficou sem preço

    df["vcpu"] = pd.to_numeric(df["vcpu"], errors="coerce")
    df["memory_gib"] = df["memory"].str.replace(" GiB", "").astype(float)
    df["current_generation"] = df["current_generation"].map({"Yes": True, "No": False})

    print(f"\nTotal final de produtos com preço: {len(df)}")
    print(df.head())

    output_dir = Path("data")
    output_dir.mkdir(parents=True, exist_ok=True)

    output_file = output_dir / "produtos.parquet"
    df.to_parquet(output_file, engine="pyarrow", index=False)
    print(f"Arquivo salvo em: {output_file}")

    return df

if __name__ == "__main__":
    transform()
