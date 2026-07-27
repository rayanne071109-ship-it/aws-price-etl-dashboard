import streamlit as st
import pandas as pd

st.title("Comparador Multi-Cloud")
st.caption("Escolha a configuração desejada e veja qual nuvem oferece o melhor preço")

@st.cache_data
def carregar_dados():
    return pd.read_parquet("../data/produtos.parquet")


df = carregar_dados()

col1, col2 = st.columns(2)
with col1:
    vcpu_alvo = st.slider("vCPU desejado", min_value=1, max_value=64, value=4)
with col2:
    memoria_alvo = st.slider("Memória desejada (GB)", min_value=1, max_value=256, value=8)

so = st.selectbox("Sistema operacional", ["Linux", "Windows"])
tolerancia_pct = st.slider("Tolerância (%)", min_value=5, max_value=30, value=15) / 100

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
    st.warning("Nenhuma instância encontrada nessa faixa. Tente aumentar a tolerância.")
else:
    melhores = (
        filtrado.sort_values("preco_hora_usd")
        .groupby("provedor")
        .first()
        .sort_values("preco_hora_usd")
    )

    st.subheader("Melhor opção por provedor")
    st.dataframe(
        melhores[["regiao", "tipo_instancia", "vcpu", "memoria_gib", "preco_hora_usd"]],
        use_container_width=True,
        column_config={
            "preco_hora_usd": st.column_config.NumberColumn("Preço/hora (USD)", format="$%.4f"),
        },
    )

    st.subheader("Comparação visual")
    st.bar_chart(melhores["preco_hora_usd"])

    vencedor = melhores.iloc[0]
    st.success(
        f"🏆 Melhor opção geral: **{vencedor.name.upper()}** — "
        f"{vencedor['tipo_instancia']} ({vencedor['regiao']}) "
        f"a **${vencedor['preco_hora_usd']:.4f}/hora**"
    )

    st.subheader("Todas as opções compatíveis (detalhado)")
    st.dataframe(
        filtrado.sort_values("preco_hora_usd")[
            ["provedor", "regiao", "tipo_instancia", "vcpu", "memoria_gib", "preco_hora_usd"]
        ],
        use_container_width=True,
        hide_index=True,
    )
