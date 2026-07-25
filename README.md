# ☁️ Multi-Cloud Price Comparator — AWS vs Azure

Pipeline de ETL + dashboard interativo que compara preços on-demand de máquinas virtuais entre **AWS EC2** e **Azure Virtual Machines**, permitindo encontrar a opção mais barata para uma configuração de vCPU/memória/SO desejada.

![Python](https://img.shields.io/badge/Python-3.10+-blue)
![Streamlit](https://img.shields.io/badge/Streamlit-1.60-red)
![Status](https://img.shields.io/badge/status-lab%20de%20estudo-yellow)

---

## ⚠️ Aviso importante

Este é um **projeto de estudo/portfólio**, construído para praticar ETL, engenharia de dados e visualização com dados públicos reais. Antes de usar:

- Os preços são coletados via **AWS Price List API** e **Azure Retail Prices API**, ambas públicas e de acesso livre, sem necessidade de credenciais.
- Os valores refletem um **snapshot do momento da extração** — preços de nuvem mudam com frequência (região, promoções, reserved instances, etc.) e podem estar desatualizados.
- **Não use os números deste projeto para decisões de compra ou migração real.** Sempre consulte as calculadoras oficiais: [AWS Pricing Calculator](https://calculator.aws) e [Azure Pricing Calculator](https://azure.microsoft.com/pricing/calculator/).
- Este projeto não é afiliado, endossado ou patrocinado pela Amazon Web Services ou Microsoft Azure. Os nomes são usados apenas para fins de referência e identificação das respectivas APIs públicas.
- Algumas specs da Azure (ex. memória de VMs `Standard_B/D/E...`) são **estimadas por família de instância**, não vêm diretamente da API — ver seção "Limitações" abaixo.

---

## 🎯 O que o projeto faz

- Extrai preços on-demand de instâncias Linux/Windows da AWS (via Price List Bulk API) e da Azure (via Retail Prices API), em múltiplas regiões
- Padroniza os dois datasets num schema único (`provedor`, `regiao`, `tipo_instancia`, `vcpu`, `memoria_gib`, `preco_hora_usd`)
- Permite buscar, por vCPU/memória/SO desejados (com margem de tolerância configurável), qual provedor oferece o melhor custo-benefício
- Dashboard interativo em Streamlit com comparação visual, tabela detalhada e destaque do vencedor

---

## 🏗️ Arquitetura

```
Extract                Transform                  Merge              Serve
────────               ─────────                  ─────              ─────
extract_azure.py   →   transform_azure.py    ┐
(Azure Retail API)     + extrair_specs_azure  ├→  merge_clouds.py →  dashboard.py
                                               │   (unifica schema)   pages/1_Comparador_MultiCloud.py
AWS Price List JSON →  transform.py           ┘                     (Streamlit)
(bulk file)
```

**Stack:** Python · pandas · ijson (streaming de JSON grande) · PyArrow/Parquet · Streamlit

---

## 📂 Estrutura do repositório

```
aws-price-etl/
├── src/
│   ├── extract_azure.py          # coleta preços da Azure Retail Prices API
│   ├── transform.py               # parse do bulk JSON da AWS (streaming via ijson)
│   ├── transform_azure.py         # normaliza JSON da Azure
│   ├── extrair_specs_azure.py     # infere vCPU/memória por família de VM (Azure)
│   ├── merge_clouds.py            # unifica os dois datasets num schema comum
│   ├── comparar.py                # busca best-match por CLI
│   ├── analise.py                 # análises exploratórias
│   └── dashboard.py               # dashboard principal (AWS)
├── pages/
│   └── 1_Comparador_MultiCloud.py # página Streamlit: comparador multi-cloud
├── data/                          # dados extraídos e parquets (não versionado)
└── requirements.txt
```

---

## 🚀 Como rodar

```bash
git clone https://github.com/rayanne071109/aws-price-etl.git
cd aws-price-etl
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 1. Extrair dados
python3 src/extract_azure.py
# (o dump da AWS Price List precisa ser baixado separadamente - ver seção Dados)

# 2. Transformar
python3 src/transform.py
python3 src/transform_azure.py
python3 src/extrair_specs_azure.py

# 3. Unificar
python3 src/merge_clouds.py

# 4. Rodar o dashboard
streamlit run src/dashboard.py
```

---

## 📊 Exemplo de resultado

Para uma configuração de **4 vCPU / 8 GB RAM / Linux**, o comparador encontrou:

| Provedor | Instância | Região | Preço/hora |
|---|---|---|---|
| Azure | Standard_B4pls_v2 | eastus | $0.0238 |
| AWS | c6g.xlarge | ap-south-1 | $0.0852 |

---

## ⚠️ Limitações conhecidas

- Memória de VMs Azure é **estimada** a partir da família da SKU (ratio fixo por letra da família), não vem literalmente da API — pode haver imprecisão em famílias menos comuns.
- Comparação é feita apenas com preços **on-demand / consumption**; não considera reserved instances, savings plans, spot ou egress de rede.
- Cobertura de regiões limitada às configuradas nos scripts de extração.

---

## 📄 Licença

Projeto de estudo, uso livre para fins educacionais. Dados de terceiros (AWS/Azure) sujeitos aos termos de uso das respectivas APIs públicas.
