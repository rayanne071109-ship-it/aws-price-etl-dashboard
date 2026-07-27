import json
import pandas as pd
from pathlib import Path

DATA_DIR = Path("data/vultr")

# A Vultr cobra por mes (monthly_cost), nao por hora diretamente.
# Aproximamos o preco por hora usando 730h/mes (convencao padrao da industria).
# Obs.: planos "Regular"/"High Frequency" tem um teto de 672h faturadas por mes,
# entao na pratica o preco por hora efetivo pode ser um pouco mais alto que essa conta.
HORAS_POR_MES = 730


def carregar_planos():
    with open(DATA_DIR / "plans.json", "r", encoding="utf-8") as f:
        return json.load(f)


def transform():
    planos = carregar_planos()
    print(f"Total de planos carregados: {len(planos)}")

    linhas = []
    for plano in planos:
        monthly_cost = plano.get("monthly_cost")
        vcpu = plano.get("vcpu_count")
        ram_mb = plano.get("ram")

        if not monthly_cost or not vcpu or not ram_mb:
            continue

        preco_hora = monthly_cost / HORAS_POR_MES
        memoria_gib = ram_mb / 1024

        locais = plano.get("locations") or ["global"]
        for regiao in locais:
            linhas.append({
                "provedor": "vultr",
                "regiao": regiao,
                "tipo_instancia": plano.get("id"),
                "familia": plano.get("type"),  # ex.: vc2, vhf, voc, vhp, vbm
                "sistema_operacional": "Linux",
                "vcpu": vcpu,
                "memoria_gib": memoria_gib,
                "preco_hora_usd": preco_hora,
            })

    df = pd.DataFrame(linhas)
    df = df.dropna(subset=["vcpu", "memoria_gib", "preco_hora_usd"])
    df = df[df["preco_hora_usd"] > 0]

    print(f"\nTotal de linhas (planos x regioes): {len(df)}")
    print(df.head(10))

    saida = Path("data")
    saida.mkdir(exist_ok=True)
    df.to_parquet(saida / "produtos_vultr_com_specs.parquet", index=False)
    print(f"\nSalvo em: {saida / 'produtos_vultr_com_specs.parquet'}")

    return df


if __name__ == "__main__":
    transform()
