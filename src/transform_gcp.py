import json
import re
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/gcp")

# GB de RAM por vCPU, por familia (shape "standard" padrao de cada familia)
RATIO_MEMORIA_POR_FAMILIA = {
    "N1": 3.75,
    "N2": 4,
    "N2D": 4,
    "E2": 4,
    "C2": 4,
    "C2D": 4,
    "T2D": 4,
    "T2A": 4,
    "M1": 24,
    "M2": 28,
}

# vCPUs disponiveis no shape "standard" de cada familia
VCPUS_PADRAO_POR_FAMILIA = {
    "N1": [1, 2, 4, 8, 16, 32, 64, 96],
    "N2": [2, 4, 8, 16, 32, 48, 64, 80],
    "N2D": [2, 4, 8, 16, 32, 48, 64, 80, 96],
    "E2": [2, 4, 8, 16, 32],
    "C2": [4, 8, 16, 30, 60],
    "C2D": [2, 4, 8, 16, 32, 56, 112],
    "T2D": [1, 2, 4, 8, 16, 32, 48, 60],
    "T2A": [1, 2, 4, 8, 16, 32, 48],
    "M1": [40, 80, 160],
    "M2": [208, 416],
}

FAMILIAS_CONHECIDAS = sorted(RATIO_MEMORIA_POR_FAMILIA.keys(), key=len, reverse=True)


def identificar_familia(descricao):
    # Sole Tenancy e "Upgrade Premium" sao variantes com preco proprio (mais caro);
    # nao devem contaminar o preco "base" que estamos calculando aqui.
    if "Sole Tenancy" in descricao or "Upgrade Premium" in descricao:
        return None

    # C2 e M1/M2 nao usam a sigla da familia no nome da descricao, entao tratamos
    # esses casos a parte antes de cair no padrao generico "^SIGLA ".
    if descricao.startswith("Compute-optimized"):
        return "C2"
    if descricao.startswith("Memory-optimized"):
        # Nao da pra distinguir M1 de M2 pela descricao (M2 usa um SKU extra de
        # "Upgrade Premium" somado a esse preco base, que ja excluimos acima).
        # Estamos tratando isso como M1 (o preco base, sem o adicional do M2).
        return "M1"

    for familia in FAMILIAS_CONHECIDAS:
        # ex.: "N2D Instance Core running in Americas" / "N1 Predefined Instance Ram ..."
        if re.match(rf"^{familia}\b", descricao):
            return familia
    return None


def preco_unitario_usd(pricing_info):
    if not pricing_info:
        return None
    tiered = pricing_info[0].get("pricingExpression", {}).get("tieredRates", [])
    if not tiered:
        return None
    unit_price = tiered[-1].get("unitPrice", {})  # ultima faixa = preco normal (sem tier gratis)
    units = float(unit_price.get("units", 0))
    nanos = unit_price.get("nanos", 0) / 1e9
    return units + nanos


def carregar_skus():
    with open(DATA_DIR / "compute_engine_skus.json", "r", encoding="utf-8") as f:
        return json.load(f)


def extrair_linhas_cpu_ram(skus):
    linhas = []
    for sku in skus:
        categoria = sku.get("category", {})
        if categoria.get("resourceFamily") != "Compute":
            continue
        if categoria.get("usageType") != "OnDemand":
            continue

        descricao = sku.get("description", "")
        familia = identificar_familia(descricao)
        if not familia:
            continue

        if "Core" in descricao:
            papel = "cpu"
        elif "Ram" in descricao:
            papel = "ram"
        else:
            continue

        preco = preco_unitario_usd(sku.get("pricingInfo"))
        if not preco:
            continue

        for regiao in sku.get("serviceRegions", []):
            linhas.append({
                "familia": familia,
                "regiao": regiao,
                "papel": papel,
                "preco_unitario_usd": preco,
            })

    return pd.DataFrame(linhas)


def montar_instancias(df_precos):
    if df_precos.empty:
        return pd.DataFrame()

    cpu = df_precos[df_precos["papel"] == "cpu"].drop_duplicates(subset=["familia", "regiao"])
    ram = df_precos[df_precos["papel"] == "ram"].drop_duplicates(subset=["familia", "regiao"])

    combinado = cpu.merge(ram, on=["familia", "regiao"], suffixes=("_cpu", "_ram"))

    linhas = []
    for _, row in combinado.iterrows():
        familia = row["familia"]
        gb_por_vcpu = RATIO_MEMORIA_POR_FAMILIA.get(familia)
        vcpus_padrao = VCPUS_PADRAO_POR_FAMILIA.get(familia, [])

        for vcpu in vcpus_padrao:
            memoria_gib = vcpu * gb_por_vcpu
            preco_hora = (
                vcpu * row["preco_unitario_usd_cpu"]
                + memoria_gib * row["preco_unitario_usd_ram"]
            )

            linhas.append({
                "provedor": "gcp",
                "regiao": row["regiao"],
                "tipo_instancia": f"{familia.lower()}-standard-{vcpu}",
                "familia": familia,
                # GCP cobra Linux "de graca" (so paga o hardware); Windows tem SKU de licenca separado,
                # que nao esta sendo somado aqui ainda.
                "sistema_operacional": "Linux",
                "vcpu": vcpu,
                "memoria_gib": memoria_gib,
                "preco_hora_usd": preco_hora,
            })

    return pd.DataFrame(linhas)


def transform():
    skus = carregar_skus()
    print(f"Total de SKUs carregados: {len(skus)}")

    df_precos = extrair_linhas_cpu_ram(skus)
    print(f"Linhas de preco CPU/RAM (OnDemand, explodido por regiao): {len(df_precos)}")

    df_instancias = montar_instancias(df_precos)
    if df_instancias.empty:
        print("Nenhuma instancia foi gerada. Confira o JSON de origem.")
        return df_instancias

    df_instancias = df_instancias.dropna(subset=["preco_hora_usd"])
    df_instancias = df_instancias[df_instancias["preco_hora_usd"] > 0]

    print(f"\nTotal de instancias GCP geradas: {len(df_instancias)}")
    print(df_instancias.head(10))

    saida = Path("data")
    saida.mkdir(exist_ok=True)
    df_instancias.to_parquet(saida / "produtos_gcp_com_specs.parquet", index=False)
    print(f"\nSalvo em: {saida / 'produtos_gcp_com_specs.parquet'}")

    return df_instancias


if __name__ == "__main__":
    transform()
