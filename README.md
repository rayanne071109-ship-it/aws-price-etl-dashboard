# AWS Price ETL + Dashboard

## 🚀 Visão Geral
Este projeto realiza um **ETL completo** dos preços de instâncias da AWS e disponibiliza um **dashboard interativo** em Streamlit para análise.

- **Extração**: leitura de arquivos JSON da AWS com mais de 1,8 milhão de SKUs.
- **Transformação**: limpeza, normalização e conversão para Parquet.
- **Visualização**: dashboard com filtros por região e gráficos de memória vs vCPU.

---

## 📂 Estrutura
- `src/transform.py`: script ETL que gera `data/produtos.parquet`.
- `src/dashboard.py`: dashboard interativo em Streamlit.
- `data/`: pasta para armazenar dados brutos e transformados.

---

## ⚙️ Instalação
Clone o repositório e instale as dependências:

```bash
git clone https://github.com/seu-usuario/aws-price-etl-dashboard.git
cd aws-price-etl-dashboard
pip install -r requirements.txt
