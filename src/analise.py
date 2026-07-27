import pandas as pd

df = pd.read_parquet("data/produtos.parquet")

# ordena do menor pro maior preço
df_ordenado = df.sort_values("price_per_hour_usd", ascending=True)

print(df_ordenado[["instance_type", "region_code", "vcpu", "memory_gib", "price_per_hour_usd"]].head(20))
