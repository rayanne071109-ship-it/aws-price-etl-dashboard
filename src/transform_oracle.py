import json
import re
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/oracle")

# Proporcao de vCPUs por OCPU. Nas familias x86 (E-series, X-series) 1 OCPU = 2 vCPUs.
# Nas familias Ampere (A1, A2, A4 e variantes "Ax") 1 OCPU = 1 vCPU.
VCPUS_POR_OCPU_X86 = 2
VCPUS_POR_OCPU_AMPERE = 1

# Relacao GB de RAM por OCPU. A Oracle permite escolher de 1 a 64 GB por OCPU
# nos shapes flex; usamos 8GB/OCPU (~4GB por vCPU em x86) como configuracao
# "padrao" equilibrada, pra ficar comparavel com os shapes standard de AWS/Azure/GCP.
GB_POR_OCPU = 8

# Contagens de OCPU comuns pra gerar as instancias sinteticas
OCPUS_PADRAO = [1, 2, 4, 8, 16, 32, 64]

# O catalogo da Oracle mudou de formato: hoje os nomes sao inconsistentes.
# Variacoes observadas no displayName:
#   - com ou sem prefixo "OCI - " / "Oracle Cloud Infrastructure - "
#   - separador entre familia e "OCPU"/"Memory" pode ser " - ", so espaco,
#     ou ate espaco duplo ("E4  - Memory")
#   - familias com sufixo " Ax" (ex.: "X12 Ax", "E6 Ax", "A4 Ax")
# Exemplos reais que a regex abaixo cobre:
#   "Compute - Standard - A2 OCPU"
#   "OCI - Compute - Standard - E6 - OCPU"
#   "OCI - Compute - Standard - X12 Ax - Memory"
#   "Compute - Standard - E4  - Memory"
PREFIXO = r"^(?:OCI - |Oracle Cloud Infrastructure - )?"
FAMILIA = r"(\w+(?: Ax)?)"
SEPARADOR = r"\s*-?\s*"

PADRAO_CPU = re.compile(PREFIXO + r"Compute - Standard - " + FAMILIA + SEPARADOR + r"OCPU$")
PADRAO_MEMORIA = re.compile(PREFIXO + r"Compute - Standard - " + FAMILIA + SEPARADOR + r"Memory$")


def eh_familia_ampere(familia):
    # Ampere = comeca com "A" seguido de digito (A1, A2, A4, A4 Ax, etc.)
    return bool(re.match(r"^A\d", familia))


def vcpus_por_ocpu(familia):
    return VCPUS_POR_OCPU_AMPERE if eh_familia_ampere(familia) else VCPUS_POR_OCPU_X86


def preco_usd(item):
    for loc in item.get("currencyCodeLocalizations", []):
        if loc.get("currencyCode") == "USD":
            precos = loc.get("prices", [])
            if precos:
                return precos[0].get("value")
    return None


def carregar_catalogo():
    with open(DATA_DIR / "price_list.json", "r", encoding="utf-8") as f:
        return json.load(f)


def extrair_linhas_cpu_ram(itens):
    linhas = []
    for item in itens:
        nome = item.get("displayName", "")

        match_ram = PADRAO_MEMORIA.match(nome)
        if match_ram:
            preco = preco_usd(item)
            if preco:
                linhas.append({"familia": match_ram.group(1), "papel": "ram", "preco_unitario_usd": preco})
            continue

        match_cpu = PADRAO_CPU.match(nome)
        if match_cpu:
            preco = preco_usd(item)
            if preco:
                linhas.append({"familia": match_cpu.group(1), "papel": "cpu", "preco_unitario_usd": preco})

    return pd.DataFrame(linhas)


def montar_instancias(df_precos):
    if df_precos.empty:
        return pd.DataFrame()

    cpu = df_precos[df_precos["papel"] == "cpu"].drop_duplicates(subset="familia")
    ram = df_precos[df_precos["papel"] == "ram"].drop_duplicates(subset="familia")

    combinado = cpu.merge(ram, on="familia", suffixes=("_cpu", "_ram"))

    linhas = []
    for _, row in combinado.iterrows():
        familia = row["familia"]
        vcpu_por_ocpu = vcpus_por_ocpu(familia)

        for ocpu in OCPUS_PADRAO:
            vcpu = ocpu * vcpu_por_ocpu
            memoria_gib = ocpu * GB_POR_OCPU
            preco_hora = ocpu * row["preco_unitario_usd_cpu"] + memoria_gib * row["preco_unitario_usd_ram"]

            linhas.append({
                "provedor": "oracle",
                # a API publica nao traz preco por regiao (preco e global/uniforme em USD)
                "regiao": "global",
                "tipo_instancia": f"VM.Standard.{familia.replace(' ', '')}.Flex-{ocpu}",
                "familia": familia,
                "sistema_operacional": "Linux",
                "vcpu": vcpu,
                "memoria_gib": memoria_gib,
                "preco_hora_usd": preco_hora,
            })

    return pd.DataFrame(linhas)


def transform():
    itens = carregar_catalogo()
    print(f"Total de produtos carregados: {len(itens)}")

    df_precos = extrair_linhas_cpu_ram(itens)
    print(f"Linhas de preco CPU/RAM (Standard): {len(df_precos)}")
    if not df_precos.empty:
        familias_encontradas = sorted(df_precos["familia"].unique())
        print(f"Familias encontradas: {familias_encontradas}")

    df_instancias = montar_instancias(df_precos)
    if df_instancias.empty:
        print("Nenhuma instancia foi gerada. Confira o JSON de origem / os padroes de nome.")
        return df_instancias

    df_instancias = df_instancias.dropna(subset=["preco_hora_usd"])
    df_instancias = df_instancias[df_instancias["preco_hora_usd"] > 0]

    print(f"\nTotal de instancias Oracle geradas: {len(df_instancias)}")
    print(df_instancias.head(10))

    saida = Path("data")
    saida.mkdir(exist_ok=True)
    df_instancias.to_parquet(saida / "produtos_oracle_com_specs.parquet", index=False)
    print(f"\nSalvo em: {saida / 'produtos_oracle_com_specs.parquet'}")

    return df_instancias


if __name__ == "__main__":
    transform()
