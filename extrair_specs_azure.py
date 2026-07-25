import re
import pandas as pd

RATIO_MEMORIA_POR_FAMILIA = {
    "D": 4, "DC": 4,
    "E": 8, "EC": 8,
    "F": 2, "FX": 2,
    "B": 2,
    "M": 16,
    "L": 8,
    "N": 4, "NC": 4, "ND": 4, "NV": 4,
    "H": 8, "HB": 8, "HC": 8, "HX": 8,
    "G": 4, "GS": 4,
    "A": 2,
}

def extrair_vcpu_familia(nome_sku):
    match = re.match(r"^(?:Standard|Basic)_([A-Z]{1,2})(\d+)(?:-(\d+))?([a-z]*)(?:_v(\d+))?", nome_sku)
    if not match:
        return None, None, None

    familia, base, constrained, _sufixo, _versao = match.groups()
    base = int(base)
    vcpu_real = int(constrained) if constrained else base
    memoria = base * RATIO_MEMORIA_POR_FAMILIA.get(familia, 4)

    return familia, vcpu_real, memoria

def processar():
    df = pd.read_parquet("data/produtos_azure.parquet")

    resultados = df["tipo_instancia"].apply(extrair_vcpu_familia)
    df["familia_vm"] = resultados.apply(lambda x: x[0])
    df["vcpu"] = resultados.apply(lambda x: x[1])
    df["memoria_gib_estimada"] = resultados.apply(lambda x: x[2])

    total = len(df)
    sem_match = df["vcpu"].isna().sum()
    print(f"Total de linhas: {total}")
    print(f"Sem vCPU identificado: {sem_match} ({sem_match/total:.1%})")

    df = df[df["vcpu"].notna()]
    print(f"Linhas finais (com specs completas): {len(df)}")

    print()
    print("Exemplos:")
    print(df[["tipo_instancia", "familia_vm", "vcpu", "memoria_gib_estimada"]].head(10))

    df.to_parquet("data/produtos_azure_com_specs.parquet", index=False)
    print("\nSalvo em: data/produtos_azure_com_specs.parquet")

if __name__ == "__main__":
    processar()
