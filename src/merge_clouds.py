import pandas as pd

def merge():
    aws = pd.read_parquet("data/produtos.parquet")
    azure = pd.read_parquet("data/produtos_azure_com_specs.parquet")

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

    unificado = pd.concat([aws_padronizado, azure_padronizado], ignore_index=True)
    unificado = unificado.dropna(subset=["vcpu", "memoria_gib", "preco_hora_usd"])

    print(f"Total unificado: {len(unificado)} linhas")
    print(unificado["provedor"].value_counts())
    print()
    print(unificado.head())

    unificado.to_parquet("data/produtos_unificado.parquet", index=False)
    print("\nSalvo em: data/produtos_unificado.parquet")

if __name__ == "__main__":
    merge()
