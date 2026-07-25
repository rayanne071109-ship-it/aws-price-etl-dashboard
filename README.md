# Pipeline de Dados de Preços EC2 (AWS) — Documentação do Projeto

## 1. Objetivo

Construir um pipeline completo de engenharia de dados (Extract, Transform, Load) usando dados públicos e reais de preços de instâncias EC2 da AWS, finalizando com um dashboard interativo para explorar e comparar preços entre regiões e tipos de instância.

## 2. Fonte dos dados

Os dados vêm da **AWS Price List Bulk API**, um serviço público e gratuito, sem necessidade de conta AWS ou autenticação:

- Índice geral de todos os serviços: `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/index.json`
- Preços do EC2 (todas as regiões): `https://pricing.us-east-1.amazonaws.com/offers/v1.0/aws/AmazonEC2/current/index.json`

O projeto trabalhou com dois arquivos JSON de preços do EC2 — um contendo apenas a região `sa-east-1` (274 MB) e outro com todas as regiões do mundo combinadas (8,4 GB) — além do índice geral de referência.

## 3. Arquitetura do pipeline

```
[JSON bruto da AWS] → Extract → Transform (streaming com ijson) → Load (.parquet) → Dashboard (Streamlit)
```

### 3.1 Extract

Os arquivos JSON foram baixados diretamente da API pública, sem necessidade de chave de acesso.

### 3.2 Transform

Esta foi a etapa mais desafiadora tecnicamente, por dois motivos:

1. **Tamanho dos arquivos**: o arquivo de todas as regiões tem 8,4 GB. Carregá-lo inteiro na memória com `json.load()` não é viável na maioria dos computadores. A solução foi usar a biblioteca `ijson`, que lê o JSON em **streaming** — processando um item de cada vez, sem nunca guardar o arquivo inteiro na RAM.

2. **Dados divididos em duas partes**: o JSON da AWS guarda os **atributos** de cada instância (tipo, vCPU, memória, sistema operacional, região) na seção `products`, e o **preço** de cada uma na seção `terms.OnDemand`, ligados apenas pelo campo `sku`. Foi necessário fazer duas passadas pelo arquivo — uma para extrair os atributos, outra para extrair os preços — e depois unir (`join`) os dois conjuntos pelo `sku`.

O resultado final: **1.161.358 linhas** processadas, cada uma representando uma combinação única de tipo de instância + região + sistema operacional + tenancy + preço.

### 3.3 Load

Os dados tratados foram salvos em formato **Parquet** (`data/produtos.parquet`) — um formato colunar, compacto e rápido de ler, ideal para análise posterior.

### 3.4 Visualização

Um dashboard interativo foi construído com **Streamlit**, permitindo filtrar, ordenar e comparar os dados sem precisar escrever código a cada nova pergunta.

---

## 4. Explicação passo a passo das telas do dashboard

### Imagem 11 — Execução do Transform no terminal

Mostra a saída do script `transform.py` rodando: confirma que **1.161.358 produtos com preço** foram processados com sucesso, com uma amostra das primeiras linhas (SKU, região, preço por hora, memória). Esse print é a evidência de que a etapa de streaming + join funcionou corretamente antes de qualquer visualização ser construída — validar os dados brutos antes de visualizar é uma etapa que não deve ser pulada.

### Imagem 12 — Filtro de região (dropdown)

Mostra o seletor de região do dashboard já filtrado para as regiões comerciais "padrão" da AWS (excluindo regiões de ativação manual, como Malásia ou Israel, e contas separadas como GovCloud/China). Isso garante que a comparação seguinte seja justa, entre regiões que qualquer conta AWS comum tem acesso.

### Imagens 1 a 4 — Tabela de instâncias filtradas por região

Essas quatro imagens mostram a mesma tabela em duas regiões diferentes (`ap-south-1` e `ap-southeast-2`), cada uma ordenada do maior para o menor preço e do menor para o maior:

- **Maior para menor** (imagens 1 e 4): no topo aparecem instâncias `u7in-16tb.224xlarge` — instâncias de altíssima capacidade (896 vCPUs, 16 TB de memória), com preços acima de US$500/hora. Isso mostra o teto de preço da AWS para hardware de ponta (usado, por exemplo, para bancos de dados in-memory gigantescos como SAP HANA).
- **Menor para maior** (imagens 2 e 3): no topo aparecem instâncias `t4g.nano` e `t3a.nano`, a partir de US$0,0028/hora — a "porta de entrada" da AWS, usada para testes, scripts leves ou ambientes de desenvolvimento.

**Conclusão desta seção**: a AWS tem uma amplitude de preço extrema (de frações de centavo a centenas de dólares por hora), o que reforça a importância de sempre filtrar por características específicas (tipo, SO, tenancy) antes de tirar qualquer conclusão sobre "preço médio".

### Imagem 5 — Gráfico de dispersão: Memória vs vCPU

Mostra a relação entre memória (GiB) e vCPU de todas as instâncias na região selecionada. É possível observar **faixas horizontais bem definidas** (em torno de 2.000, 4.000, 6.000, 12.000 e 16.000 GiB) — isso reflete o catálogo padronizado da AWS, que oferece combinações fixas de memória por família de instância, em vez de valores aleatórios.

### Imagem 6 — Distribuição por família de instância

Gráfico de barras mostrando quantas instâncias existem em cada categoria (Compute Optimized, General Purpose, Memory Optimized, GPU, Storage Optimized, FPGA, Machine Learning, Micro). **Memory Optimized** e **General Purpose** são as famílias com mais opções disponíveis, enquanto **FPGA** e **Machine Learning** são nichos bem menores — reflexo direto da demanda de mercado por cada tipo de carga de trabalho.

### Imagem 7 — Top 10 tipos de VM mais baratas (Linux, Shared)

Ranking filtrado para eliminar viés de sistema operacional (todas em Linux) e de tenancy (todas compartilhadas). As instâncias da família `t` (burstable, uso geral) dominam o ranking — `t1.micro`, `t2.nano`, `t3.micro`, `t4g.small`, entre outras — todas na faixa de US$0,005 a US$0,022/hora. **Interessante notar** que o `t4g.small` aparece como a mais cara desse grupo (ainda assim barata em termos absolutos), sugerindo que ele oferece mais capacidade que as demais dessa lista.

### Imagem 8 — Comparação de preço médio por região

Aqui fica evidente um viés estatístico importante do dataset: `sa-east-1` (São Paulo) aparece como uma das regiões de **maior** preço médio, e `us-west-1`/`ap-northeast-3` como as mais baratas na média. Isso **não significa** que São Paulo seja cara em todos os tipos de instância — significa que a média está sendo puxada para cima porque a região tem mais linhas de instâncias caras/especializadas na base. Esse é um ponto que foi identificado e discutido durante o desenvolvimento do projeto: **médias agregadas escondem a composição dos dados**.

### Imagens 9 e 10 — Comparação de preço por tipo de instância entre regiões

Essas duas imagens corrigem o problema identificado na Imagem 8, comparando **o mesmo tipo de instância** entre todas as regiões:

- **Imagem 9 (`t3.nano`)**: aqui sim fica claro que `sa-east-1` é a região **mais cara** para essa instância específica (~US$0,017/h), enquanto as demais regiões giram entre US$0,010 e US$0,014/h — uma diferença real e justa de comparar, já que é o mesmo hardware.
- **Imagem 10 (`p6-b300.48xlarge`, instância de GPU de ponta)**: mostra que esse tipo específico só está disponível em duas regiões (`us-east-1` e `us-west-2`), com preços praticamente idênticos (~US$288/h) — evidência de que instâncias de GPU de última geração ainda têm disponibilidade geográfica limitada.

---

## 5. Conclusões

1. **Comparar "preço médio" entre regiões sem contexto é enganoso.** A composição do catálogo de instâncias de cada região distorce a média. A comparação correta é sempre por tipo de instância específico, em igualdade de condições (mesmo SO, mesma tenancy).

2. **`sa-east-1` (São Paulo) é consistentemente mais cara** que a maioria das regiões dos EUA e Ásia para instâncias equivalentes — um dado relevante para empresas brasileiras que decidem entre hospedar localmente (menor latência) ou em regiões mais baratas (menor custo).

3. **Instâncias de última geração (GPU, alta memória) têm disponibilidade geográfica limitada**, concentradas principalmente nos EUA — o que também impacta o custo/benefício de operar cargas de trabalho de IA fora dos EUA.

4. **O maior desafio técnico do projeto não foi a análise, e sim a extração**: processar um arquivo de 8,4 GB exigiu uma abordagem de streaming (via `ijson`) ao invés do carregamento tradicional de JSON — uma decisão de engenharia que reflete um problema real enfrentado em pipelines de dados em produção.

## 6. Considerações finais e próximos passos

- **Possível melhoria 1**: incorporar preços de instâncias **Reservadas** e **Spot**, hoje o projeto usa apenas OnDemand — uma comparação entre os três modelos de compra seria um complemento natural.
- **Possível melhoria 2**: automatizar a atualização dos dados (os preços da AWS mudam), agendando o pipeline para rodar periodicamente (ex: com `cron` ou `Airflow`) — hoje o processo é manual.
- **Possível melhoria 3**: adicionar outros serviços além do EC2 (S3, RDS) para uma visão mais ampla de custo de infraestrutura.
- **Aprendizado central do projeto**: lidar com dados reais, em volume real, expôs decisões de engenharia (streaming, join manual, filtragem de viés estatístico) que datasets didáticos "prontos" geralmente não exigem — isso deu uma experiência mais próxima da rotina real de um profissional de dados.
