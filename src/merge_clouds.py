import pandas as pd
from pathlib import Path

def merge():
    aws = pd.read_parquet("data/produtos.parquet")
    azure = pd.read_parquet("data/produtos_azure_com_specs.parquet")

    gcp_path = Path("data/produtos_gcp_com_specs.parquet")
    gcp = pd.read_parquet(gcp_path) if gcp_path.exists() else None

    oracle_path = Path("data/produtos_oracle_com_specs.parquet")
    oracle = pd.read_parquet(oracle_path) if oracle_path.exists() else None

    vultr_path = Path("data/produtos_vultr_com_specs.parquet")
    vultr = pd.read_parquet(vultr_path) if vultr_path.exists() else None

    aws_padronizado = pd.DataFrame({
        "provedor": "aws",
        "regiao": aws["region_code"],
        "tipo_instancia": aws["instance_type"],
        "familia": aws["instance_family"],
        "sistema_operacional": aws["operating_system"],
        "vcpu": pd.to_numeric(aws["vcpu"], errors="coerce"),
        "memoria_gib": aws["memory_gib"],
        "preco_hora_usd": aws["price_per_hour_usd"],
    })

    azure_padronizado = pd.DataFrame({
        "provedor": "azure",
        "regiao": azure["regiao"],
        "tipo_instancia": azure["tipo_instancia"],
        "familia": azure["familia_vm"],
        "sistema_operacional": azure["sistema_operacional"],
        "vcpu": azure["vcpu"],
        "memoria_gib": azure["memoria_gib_estimada"],
        "preco_hora_usd": azure["preco_hora_usd"],
    })

    dataframes = [aws_padronizado, azure_padronizado]

    if gcp is not None:
        gcp_padronizado = pd.DataFrame({
            "provedor": "gcp",
            "regiao": gcp["regiao"],
            "tipo_instancia": gcp["tipo_instancia"],
            "familia": gcp["familia"],
            "sistema_operacional": gcp["sistema_operacional"],
            "vcpu": gcp["vcpu"],
            "memoria_gib": gcp["memoria_gib"],
            "preco_hora_usd": gcp["preco_hora_usd"],
        })
        dataframes.append(gcp_padronizado)
    else:
        print("Aviso: data/produtos_gcp_com_specs.parquet nao encontrado, seguindo so com AWS + Azure.")

    if oracle is not None:
        oracle_padronizado = pd.DataFrame({
            "provedor": "oracle",
            "regiao": oracle["regiao"],
            "tipo_instancia": oracle["tipo_instancia"],
            "familia": oracle["familia"],
            "sistema_operacional": oracle["sistema_operacional"],
            "vcpu": oracle["vcpu"],
            "memoria_gib": oracle["memoria_gib"],
            "preco_hora_usd": oracle["preco_hora_usd"],
        })
        dataframes.append(oracle_padronizado)
    else:
        print("Aviso: data/produtos_oracle_com_specs.parquet nao encontrado, seguindo sem Oracle.")

    if vultr is not None:
        vultr_padronizado = pd.DataFrame({
            "provedor": "vultr",
            "regiao": vultr["regiao"],
            "tipo_instancia": vultr["tipo_instancia"],
            "familia": vultr["familia"],
            "sistema_operacional": vultr["sistema_operacional"],
            "vcpu": vultr["vcpu"],
            "memoria_gib": vultr["memoria_gib"],
            "preco_hora_usd": vultr["preco_hora_usd"],
        })
        dataframes.append(vultr_padronizado)
    else:
        print("Aviso: data/produtos_vultr_com_specs.parquet nao encontrado, seguindo sem Vultr.")

    unificado = pd.concat(dataframes, ignore_index=True)
    unificado = unificado.dropna(subset=["vcpu", "memoria_gib", "preco_hora_usd"])

    print(f"Total unificado: {len(unificado)} linhas")
    print(unificado["provedor"].value_counts())
    print()
    print(unificado.head())

    unificado.to_parquet("data/produtos_unificado.parquet", index=False)
    print("\nSalvo em: data/produtos_unificado.parquet")

if __name__ == "__main__":
    merge()
