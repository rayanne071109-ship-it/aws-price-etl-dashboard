import pandas as pd

def buscar_melhor_opcao(vcpu_alvo, memoria_alvo, tolerancia_pct=0.15, so="Linux"):
    df = pd.read_parquet("data/produtos_unificado.parquet")

    # aceita instancias dentro de uma margem de tolerancia (padrao 15%)
    vcpu_min = vcpu_alvo * (1 - tolerancia_pct)
    vcpu_max = vcpu_alvo * (1 + tolerancia_pct)
    mem_min = memoria_alvo * (1 - tolerancia_pct)
    mem_max = memoria_alvo * (1 + tolerancia_pct)

    filtrado = df[
        (df["vcpu"] >= vcpu_min) & (df["vcpu"] <= vcpu_max)
        & (df["memoria_gib"] >= mem_min) & (df["memoria_gib"] <= mem_max)
        & (df["sistema_operacional"].str.contains(so, case=False, na=False))
    ].copy()

    if filtrado.empty:
        print("Nenhuma instancia encontrada nessa faixa. Tente aumentar a tolerancia.")
        return None

    # melhor opcao por provedor
    melhores = (
        filtrado.sort_values("preco_hora_usd")
        .groupby("provedor")
        .first()
        .sort_values("preco_hora_usd")
    )

    print(f"Buscando: {vcpu_alvo} vCPU, {memoria_alvo}GB, {so} (tolerancia {tolerancia_pct:.0%})\n")
    print(melhores[["regiao", "tipo_instancia", "vcpu", "memoria_gib", "preco_hora_usd"]])

    mais_barato = melhores.iloc[0]
    print(f"\n>> Melhor opcao geral: {mais_barato.name.upper()} "
          f"({mais_barato['tipo_instancia']}, {mais_barato['regiao']}) "
          f"a ${mais_barato['preco_hora_usd']:.4f}/hora")

    return melhores

if __name__ == "__main__":
    # exemplo: quero uma maquina com 4 vCPU e 8GB de RAM, Linux
    buscar_melhor_opcao(vcpu_alvo=4, memoria_alvo=8, so="Linux")
