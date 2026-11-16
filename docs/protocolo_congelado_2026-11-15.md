# Protocolo congelado — primeiro artigo (Fase 0)

Registrado em 2026-11-15, antes de rodar as sementes novas, de construir os candidatos da Fase 1 e de usar chikungunya como alvo. Vale até a entrega de 2026-11-28. Detalhes de motivação em `plano/PLANO_IMDC_TFT.md` (sumário executivo e B6).

Qualquer mudança depois desta data entra como **emenda** no fim deste arquivo, com data e motivo, e nunca apaga o texto original.

## 1. Conjuntos

| Conjunto | Conteúdo | Status |
|---|---|---|
| Desenvolvimento | Dengue, cortes EW25 de 2015 a 2024 (10 temporadas) e as 4 validações oficiais do IMDC | Já visto. Serve para escolher, nunca para confirmar |
| Confirmatório B | Chikungunya como alvo, nas 27 UFs e nas 10 cidades do desafio | Nunca usado como alvo. Já entrou como covariável no v3 e no v4 (`src/preprocess_v3.py:35-68`) |
| Confirmatório A | Dengue, temporada 2026/27 | Só depósito das previsões; pontuação depois da EW40/2027, fora deste prazo |

Os dados são os de `data/raw/` com os hashes em `reports/manifesto_artefatos_2026-11-15.sha256`. Não se baixa safra nova até 2026-11-28.

## 2. Métricas

- **Primária:** WIS relativo ao B3 (climatologia de parâmetros de Richards) nas UFs, média geométrica das razões de (WIS + 1) por temporada, como em `docs/evaluation_protocol_v3.md`.
- **Secundárias:** WIS relativo nas cidades; razão oficial contra o baseline do IMDC (só dengue); cobertura de 50%, 80%, 90% e 95%; WIS por blocos de horizonte; MAE do log do total da temporada; componentes do WIS (subprevisão, sobreprevisão, dispersão).

## 3. Sementes

- O v3 roda com as sementes 1, 2, 3 e 4, além da 42 já existente, nos 10 cortes de desenvolvimento.
- O "v3" de referência passa a ser a média de quantis das 5 sementes. A semente 42 sozinha é relatada ao lado.
- O desvio entre sementes do WIS relativo é medido por temporada e no agregado.

## 4. Candidatos (lista fechada)

| Id | Candidato | Observação |
|---|---|---|
| C1 | v3, média das 5 sementes | Referência |
| C2 | Média de quantis de B2, B3 e C1 | Ensemble simples, pesos iguais |
| C3 | Total do C1 com forma do B3 | Hipótese da alegação 4 do plano |
| C4 | Gradient boosting para o log do total, com forma do B3 | Mesmas variáveis estáticas e defasadas disponíveis no corte |
| C5 | Modelo de fundação zero-shot sobre a série semanal | Até 2 modelos; escolha por disponibilidade de pesos abertos, registrada em emenda antes de rodar |

Não entram como candidatos: v2, v4, variantes de calibração, Richards com parâmetros oráculo (é diagnóstico, não previsão).

Nenhum hiperparâmetro de C1 a C4 é ajustado olhando os 10 cortes. C4 usa os valores padrão da biblioteca, com número de árvores fixado em emenda antes de rodar.

## 5. Escolha (2026-11-20)

1. Calcular a métrica primária dos candidatos nos 10 cortes de desenvolvimento.
2. O escolhido é o de menor WIS relativo nas UFs. Empate dentro de 0,01: o mais simples (C2 < C3 < C4 < C1 < C5).
3. A escolha é escrita como emenda neste arquivo, com a tabela, **antes** de qualquer previsão de chikungunya.
4. Todos os candidatos são relatados no artigo, não só o escolhido.

## 6. Teste confirmatório em chikungunya

- **Cortes:** EW25 de cada ano de 2017 a 2024, com a temporada EW41 a EW40 seguinte. Se os dados não sustentarem algum corte (série com menos de 2 temporadas completas antes do corte), o corte é retirado por regra, antes de rodar qualquer modelo, e a retirada é registrada em emenda.
- **Pipeline:** o mesmo do escolhido, sem mudar hiperparâmetros. Ajustes de Richards de chikungunya pelo mesmo procedimento de dengue. O B3 de chikungunya é a climatologia dos parâmetros ajustados de chikungunya.
- **Variáveis:** a série de chikungunya ocupa o lugar da de dengue; a de dengue ocupa o lugar da covariável de chikungunya. O resto não muda.
- **Sementes:** 3 (1, 2, 3) quando o escolhido tiver rede treinada.
- **Pontuação:** uma única vez. Não se roda segunda versão depois de ver o resultado.

### Critério de ganho

O escolhido tem ganho em chikungunya se as três condições valerem nas UFs:

1. WIS relativo ao B3 menor que 1;
2. teste de permutação de sinais, unilateral, sobre o log da razão por temporada, com p < 0,10;
3. a distância até 1 maior que o desvio entre sementes.

As cidades são secundárias e não mudam a decisão.

## 7. Regra de parada (2026-11-22)

- **Com ganho:** a tese do artigo é positiva, restrita ao que o escolhido é (por exemplo, "combinar com climatologia ajuda", se for C2 ou C3).
- **Sem ganho ou inconclusivo:** a tese é a de diagnóstico, na estrutura de A4 do plano.
- Nos dois casos o artigo relata desenvolvimento e confirmatório com o mesmo destaque e declara o baixo poder de um teste com 8 temporadas ou menos.

## 8. Depósito 2026/27

Até 2026-11-27, as previsões 2026/27 de todos os candidatos vão para `reports/deposito_2026_27/`, com SHA-256 num manifesto e commit com tag datada.

## 9. Registro

Cada execução, inclusive as que falharem, ganha uma linha em `reports/registro_experimentos.csv`.

## Emendas

### E1 — 2026-11-15, antes de rodar qualquer semente: hardware das sementes

As sementes do v3 rodam no servidor `multigpu` (A100), não na RTX 3050 local. Como a mesma semente em GPUs diferentes não reproduz bit a bit, a semente 42 também é refeita no servidor (`<corte>_s42`), e o C1 passa a ser a média de quantis das 5 sementes rodadas no servidor (1, 2, 3, 4 e 42). A rodada original da semente 42 na RTX 3050 é relatada ao lado como sensibilidade ao hardware. Hiperparâmetros iguais aos de `src/run_v3.sh`; só `NUM_WORKERS` e o paralelismo mudam, e nenhum dos dois altera o modelo. Lista de tags em `hpc/tags_sementes_v3.txt`.

### E2 — 2026-11-16, antes de rodar o C4: biblioteca, variáveis e número de árvores

Feita depois de ver o resultado do C1 (WIS relativo 0,995 nas UFs) e antes de rodar o C4 em qualquer corte. Código em `src/c4_boosting.py`.

- **Biblioteca:** `sklearn.ensemble.HistGradientBoostingRegressor` (scikit-learn 1.9.0), `loss="quantile"`, um modelo por nível de `common.QUANTILE_LEVELS`, com os quantis ordenados depois para não cruzarem.
- **Hiperparâmetros:** os padrões da biblioteca, incluindo o número de árvores (`max_iter=100`) e a parada antecipada automática. A semente é fixa (`random_state=0`).
- **Alvo:** log(1 + casos totais) da temporada EW41/Y a EW40/Y+1, por município.
- **Variáveis, todas conhecidas na EW25/Y:**
  - log do total das 4 últimas temporadas completas;
  - mediana e máximo do log do total das temporadas completas, e quantas há;
  - log dos casos da temporada corrente até a EW25/Y;
  - log dos casos das últimas 8 semanas;
  - log da população;
  - UF, Köppen, bioma e macrorregião como categóricas. A regional ficou de fora porque tem 439 categorias e a biblioteca aceita até 255.
- **Treino do corte Y:** todas as temporadas completas até Y-1, com as variáveis montadas como se o corte fosse o da temporada correspondente.
- **Forma:** alpha, beta e pico vêm do B3 do mesmo corte. A agregação para UF usa a mesma escolha de rho dos outros modelos.
- **Esclarecimento, antes de qualquer resultado do C4:** a temporada 2010 está incompleta na base, que começa em janeiro de 2010. Por isso ela não conta como temporada completa, e o treino começa na temporada 2012, a primeira cuja parcial até a EW25 está inteira na base. Defasagens que não existem em nenhum exemplo de treino de um corte ficam fora do modelo desse corte. A biblioteca não aceita coluna vazia.

### E3 — 2026-11-16, antes de rodar o C5: modelo de fundação

Feita depois de ver C1 a C4 e antes de rodar o C5 em qualquer corte. Código em `src/c5_chronos.py`.

- **Modelo:** um só, `amazon/chronos-bolt-small` (pesos abertos, Hugging Face), via `chronos-forecasting` 2.3.2. Foi escolhido por ter pesos abertos, ser pequeno o bastante para rodar na CPU e já vir com previsão por quantil. Fica aberto um segundo modelo, se for registrado em outra emenda antes de rodar.
- **Uso:** zero-shot, sem treino nem ajuste. O contexto é a série semanal de casos de cada UF e de cada cidade do desafio até a EW25/Y. O modelo prevê até a EW40/Y+1, e ficam as semanas da temporada.
- **Quantis:** os 9 níveis exigidos pelo desafio. O Chronos-Bolt só foi treinado de 0,1 a 0,9, então os intervalos de 90% e 95% saem iguais ao de 80%. Isso fica como publicado, sem correção.
- **Agregação:** previsão direta por UF e por cidade, como B1 e B2, sem rho.

### E4 — 2026-11-16, antes de qualquer previsão de chikungunya: escolha do candidato

Feita com os 5 candidatos pontuados nos 10 cortes de desenvolvimento, 4 dias antes da data da seção 5. A regra é a da seção 5, sem mudança. Nenhuma previsão nem ajuste de chikungunya como alvo foi feito até aqui.

WIS relativo ao B3 nos cortes EW25 de 2015 a 2024 (`reports/v3/rolling_relative.csv`; IC 95% por bootstrap de temporadas; "melhor" é a fração das unidade-temporadas em que o candidato bate o B3):

| Id | Candidato | UFs | IC 95% (UFs) | Melhor (UFs) | Cidades |
|---|---|---|---|---|---|
| C1 | v3, média das 5 sementes | 0,995 | 0,929–1,066 | 47% | 0,970 |
| **C2** | **Média de quantis de B2, B3 e C1** | **0,939** | **0,907–0,974** | **66%** | 0,973 |
| C3 | Total do C1 com forma do B3 | 0,950 | 0,886–1,010 | 50% | 0,959 |
| C4 | Boosting do log do total, forma do B3 | 0,976 | 0,912–1,049 | 46% | 0,949 |
| C5 | Chronos-Bolt Small, zero-shot | 1,009 | 0,849–1,179 | 50% | 1,008 |

- **Escolhido: C2.** Tem o menor WIS relativo nas UFs. A distância para o segundo (C3) é 0,011, fora da faixa de empate de 0,01; e, se fosse empate, o C2 venceria por ser o mais simples.
- **Pipeline em chikungunya (seção 6):** B2 e B3 de chikungunya e o C1 de chikungunya, este como média de quantis das sementes 1, 2 e 3, combinados com pesos iguais, como no desenvolvimento. Hiperparâmetros do TFT os de `src/run_v3.sh`, no mesmo servidor da E1.
- Os 5 candidatos continuam relatados no artigo (seção 5, item 4). Commits dos resultados: `bcee534` (C1), `415e13f` (C2 a C4) e `df11912` (C5).

### E5 — 2026-11-16, antes de qualquer previsão de chikungunya: desvio entre sementes do C2

A seção 6 pede, no critério 3, que a distância até 1 seja maior que o desvio entre sementes, mas não diz como medir esse desvio num ensemble. Para o C2 fica assim:

- Para cada semente s em {1, 2, 3}, monta-se o C2 da semente s: média de quantis, com pesos iguais, de B2, B3 e do TFT da semente s sozinha, com a mesma agregação para UF (escolha de rho) do C2.
- Calcula-se a métrica primária (WIS relativo ao B3 nas UFs, agregado nos cortes) de cada um dos 3.
- O desvio entre sementes é o desvio padrão amostral (ddof = 1) desses 3 valores, como em `dp_sementes` de `src/evaluate_v3.py`.
- O critério 3 vale se 1 − WIS relativo do C2 (com o C1 das 3 sementes) for maior que esse desvio.

Escolhido por medir a variação do que está sendo testado, e não a do TFT sozinho, que a média com B2 e B3 amortece. Registrado antes de qualquer resultado de chikungunya.

### E6 — 2026-11-16, antes de qualquer previsão de chikungunya: dados, cortes e verdade do confirmatório

Feita depois do pré-processamento de chikungunya (`src/preprocess_chik.py`, que só monta tabelas) e antes de qualquer baseline, treino ou previsão. Nada de chikungunya foi pontuado.

- **Início da série:** a série de chikungunya do FTP começa na EW01/2014 (domingo 2013-12-29) nos 5.570 municípios. As semanas anteriores saem da base em vez de virar zero. A temporada 2014 fica incompleta e não vira alvo; a primeira temporada completa é a 2015.
- **Cortes (seção 6):** cada corte de 2017 a 2024 tem pelo menos 2 temporadas completas antes dele (o de 2017 tem 2015 e 2016). Nenhum corte é retirado: são 8 temporadas.
- **Ajustes de Richards:** os do episcanner para `disease == "chikungunya"` (`data/processed/episcanner_results_2026.csv`), temporadas 2015 a 2025, 2.885 municípios-temporada. A regra de reajuste do v3 (temporadas com 50 casos ou mais sem ajuste, aceito se R² ≥ 0,95) não encontrou nenhuma temporada para reajustar. O B3 usa esses ajustes, como o B3 de dengue usa os do episcanner.
- **Troca das séries (seção 6):** casos e incidência passam a ser de chikungunya; `log_casos_chik` passa a ser o log dos casos de dengue. O resto da base não muda.
- **Cidades:** as 10 do Optional Challenge 3 (https://sprint.mosqlimate.org/instructions/, consultado em 2026-11-16): 2211001 Teresina, 2931350 Teixeira de Freitas, 3143302 Montes Claros, 3119401 Coronel Fabriciano, 1721000 Palmas, 1716109 Paraíso do Tocantins, 4104808 Cascavel, 4219507 Xanxerê, 5103403 Cuiabá e 5102637 Campo Novo do Parecis.
- **Verdade:** os casos de chikungunya de `data/raw/` (os mesmos hashes da seção 1). Em dengue a avaliação usou os observados oficiais do IMDC (`data/external/imdc_results/`), que não existem localmente para chikungunya; a seção 1 proíbe baixar dados novos até 2026-11-28. Nas UFs, a verdade é a soma dos municípios, sem o ES.
- **rho:** a mesma regra do desenvolvimento (cortes ≤ Y-2, grade 0,5, 0,8 e 1,0, padrão 0,5), aplicada só aos cortes de chikungunya. Os cortes de 2017 e 2018 ficam com 0,5.
- **Código:** `src/confirmatorio_chik.py` (B2, B3, combinações, pontuação única e critério); TFT pelo `src/train_v3.py` e `src/infer_v3.py` com `DOENCA=chik`, tags em `hpc/tags_chik.txt`.
