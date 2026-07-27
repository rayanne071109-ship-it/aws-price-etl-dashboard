# ☁️ Multi-Cloud Price Comparator — AWS · Azure · GCP · Oracle · Vultr

Pipeline de ETL + dashboard interativo que compara preços on-demand de máquinas virtuais entre **5 provedores de nuvem** (AWS, Azure, GCP, Oracle Cloud e Vultr), permitindo encontrar a opção mais barata para uma configuração de vCPU/memória/SO desejada.

![Python](https://img.shields.io/badge/Python-3.10+-blue) ![Streamlit](https://img.shields.io/badge/Streamlit-1.60-red) ![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)

---

## ⚠️ Aviso importante

Este é um **projeto de estudo/portfólio**, construído para praticar ETL, engenharia de dados e visualização com dados públicos reais. Antes de usar:

- Os preços são coletados via APIs públicas e de acesso livre, sem necessidade de credenciais: **AWS Price List API**, **Azure Retail Prices API**, **Google Cloud Billing Catalog API**, **Oracle Cloud Price List API** e **Vultr API**.
- Os valores refletem um **snapshot do momento da extração** — preços de nuvem mudam com frequência (região, promoções, reserved instances, etc.) e podem estar desatualizados.
- **Não use os números deste projeto para decisões de compra ou migração real.** Sempre consulte as calculadoras oficiais de cada provedor.
- Este projeto não é afiliado, endossado ou patrocinado por nenhum dos provedores de nuvem citados. Os nomes são usados apenas para fins de referência e identificação das respectivas APIs públicas.
- Algumas specs são **estimadas**, não vêm literalmente da API — ver seção "Limitações" abaixo.

---

## 🎯 O que o projeto faz

- Extrai preços on-demand de instâncias Linux/Windows de 5 provedores diferentes, em múltiplas regiões (quando a API disponibiliza essa granularidade)
- Padroniza todos os datasets num schema único (`provedor`, `regiao`, `tipo_instancia`, `vcpu`, `memoria_gib`, `preco_hora_usd`, `sistema_operacional`)
- Permite buscar, por vCPU/memória/SO desejados (com margem de tolerância configurável), qual provedor oferece o melhor custo-benefício
- Dashboard interativo em Streamlit com comparação visual, tabela detalhada e destaque do vencedor
- Mais de **780 mil linhas** de dados processadas e unificadas numa única fonte comparável

---

## 🏗️ Arquitetura

```
Extract                    Transform                       Merge                Serve
────────                   ─────────                       ─────                ─────
extract_aws.py         →   transform_aws.py            ┐
extract_azure.py       →   transform_azure.py          │
extract_gcp.py         →   transform_gcp.py             ├→  merge_clouds.py  →  1_Comparador_MultiCloud.py
extract_oracle.py      →   transform_oracle.py          │   (unifica schema)    (Streamlit)
extract_vultr.py       →   transform_vultr.py           ┘
```

**Stack:** Python · pandas · requests · regex · PyArrow/Parquet · Streamlit

---

## 📂 Estrutura do repositório

```
aws-price-etl-dashboard/
├── src/
│   ├── extract_aws.py             # coleta bulk price list da AWS
│   ├── transform_aws.py           # parse do bulk JSON da AWS
│   ├── extract_azure.py           # coleta preços via Azure Retail Prices API
│   ├── transform_azure.py         # normaliza JSON da Azure
│   ├── extract_gcp.py             # coleta preços via GCP Billing Catalog API
│   ├── transform_gcp.py           # normaliza catálogo da GCP
│   ├── extract_oracle.py          # coleta catálogo público de preços da Oracle
│   ├── transform_oracle.py        # parse do catálogo Oracle (regex flexível p/
│   │                               #   variações de nomenclatura) + geração de
│   │                               #   instâncias sintéticas por família/OCPU
│   ├── extract_vultr.py           # coleta preços via Vultr API
│   ├── transform_vultr.py         # normaliza catálogo da Vultr
│   └── merge_clouds.py            # unifica os 5 datasets num schema comum
├── pages/
│   └── 1_Comparador_MultiCloud.py # dashboard Streamlit: comparador multi-cloud
├── data/                          # dados extraídos e parquets (não versionado)
└── requirements.txt
```

> Os nomes exatos de alguns scripts de extração/transformação (GCP, Vultr, AWS)
> podem variar conforme a versão local do projeto — ajuste esta árvore se algum
> arquivo tiver nome diferente no seu repositório.

---

## 🚀 Como rodar

```bash
git clone https://github.com/rayanne071109-ship-it/aws-price-etl-dashboard.git
cd aws-price-etl-dashboard
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. Extrair dados de cada provedor
python3 src/extract_aws.py
python3 src/extract_azure.py
python3 src/extract_gcp.py
python3 src/extract_oracle.py
python3 src/extract_vultr.py

# 2. Transformar (padronizar schema)
python3 src/transform_aws.py
python3 src/transform_azure.py
python3 src/transform_gcp.py
python3 src/transform_oracle.py
python3 src/transform_vultr.py

# 3. Unificar tudo num único parquet
python3 src/merge_clouds.py

# 4. Rodar o dashboard
streamlit run pages/1_Comparador_MultiCloud.py
```

---

## 📊 Exemplo de resultado

Para uma configuração de **4 vCPU / 16 GB RAM / Linux** (tolerância 30%):

| Provedor | Instância            | Região       | vCPU | Memória (GiB) | Preço/hora |
|----------|-----------------------|--------------|------|----------------|------------|
| Azure    | Standard_D4pls_v6      | westus2      | 4    | 16             | $0.0229    |
| Oracle   | VM.Standard.E4.Flex-2   | global       | 4    | 16             | $0.0740    |
| AWS      | t4g.xlarge              | ap-south-1   | 4    | 16             | $0.0896    |
| Vultr    | vhp-4c-12gb-amd         | dfw          | 4    | 12             | $0.0986    |
| GCP      | t2d-standard-4          | asia-south1  | 4    | 16             | $0.1115    |

---

## 🧩 Desafios técnicos ao longo do projeto

- **Catálogo da Oracle mudou de formato em produção**: nomes de produtos passaram a ter prefixos opcionais, espaçamento inconsistente (inclusive espaço duplo) e sufixos de família não documentados. Foi necessário reescrever a extração com regex mais flexível e tolerante a variações.
- **Diferença de arquitetura de CPU**: famílias Ampere (A1/A2/A4, ARM) usam 1 OCPU = 1 vCPU, enquanto famílias x86 (E/X-series) usam 1 OCPU = 2 vCPUs — essa proporção precisou ser tratada por família, não de forma genérica.
- **Volume desbalanceado entre provedores**: a AWS sozinha responde por ~95% das linhas do dataset unificado (preço por região × tipo de instância), enquanto a Oracle expõe preços globais (sem variação por região) — o que exigiu cuidado na hora de comparar "maçãs com maçãs" no dashboard.

---

## ⚠️ Limitações conhecidas

- Memória de VMs Azure é **estimada** a partir da família da SKU (ratio fixo por letra da família), não vem literalmente da API — pode haver imprecisão em famílias menos comuns.
- Instâncias Oracle são **geradas sinteticamente** (combinação de OCPU × família), já que a API pública não expõe uma lista fixa de "tipos de instância" como AWS/Azure/GCP — o preço por OCPU/GB é real, a combinação é calculada.
- Comparação é feita apenas com preços **on-demand / consumption**; não considera reserved instances, savings plans, spot ou egress de rede.
- Cobertura de regiões limitada às configuradas nos scripts de extração (e, no caso da Oracle, o preço público é global, sem variação regional).

---

## 📄 Licença

Projeto de estudo, uso livre para fins educacionais. Dados de terceiros (AWS/Azure/GCP/Oracle/Vultr) sujeitos aos termos de uso das respectivas APIs públicas.
