# Resultados da Fase 1: avaliação com origem móvel

**Resumo:** o TFT completo não superou a climatologia de parâmetros (B3) na comparação primária. O WIS relativo nas UFs foi de 1,19 (IC 95%: 1,08 a 1,33), e valores acima de 1 indicam desempenho pior que o do B3. Em análise exploratória, a perda parece vir da forma da curva prevista: o total previsto pelo TFT, combinado com a forma do B3, empata com o B3.

## Como foi avaliado

O protocolo completo está em [`docs/evaluation_protocol.md`](../../docs/evaluation_protocol.md).

- **Temporadas:** 10, de 2015/16 a 2024/25, com corte na EW25 de cada ano.
- **Unidades:** 26 UFs (sem ES) e as 15 cidades do desafio.
- **Métrica primária:** WIS relativo ao B3 no nível estadual, calculado como média geométrica de `(WIS_modelo + 1) / (WIS_B3 + 1)` por unidade-temporada.
- **Incerteza:** IC de 95% por bootstrap de temporadas.
- **Critério de ganho:** limite superior do IC abaixo de 1.
- **TFT:** um modelo por corte, com uma única semente (42).
- **Agregação estadual:** `rho` escolhido só com temporadas anteriores ao corte. O valor foi 0,5 nos cortes de 2015 e 2016 e 1,0 nos demais, tanto para o TFT quanto para o B3.

## Resultados primários

### WIS relativo ao B3

| Modelo | UFs (IC 95%) | Cidades (IC 95%) |
|---|---|---|
| B3, climatologia de parâmetros | 1,000 (referência) | 1,000 (referência) |
| B2, climatologia de casos | 0,986 (0,948 a 1,032) | 1,021 (0,989 a 1,053) |
| TFT | **1,192 (1,078 a 1,334)** | **1,106 (1,013 a 1,227)** |
| B1, persistência | 1,438 (1,012 a 2,065) | 2,369 (1,652 a 3,506) |

### WIS relativo do TFT ao B3, por temporada

| Temporada | UFs | Cidades |
|---|---|---|
| 2015/16 | 1,052 | 0,978 |
| 2016/17 | 1,813 | 1,628 |
| 2017/18 | 0,973 | 0,965 |
| 2018/19 | 1,312 | 1,199 |
| 2019/20 | 1,230 | 0,978 |
| 2020/21 | 1,022 | 1,084 |
| 2021/22 | 1,193 | 1,055 |
| 2022/23 | 1,392 | 1,180 |
| 2023/24 | 1,055 | 0,931 |
| 2024/25 | 1,077 | 1,207 |

### Componentes do WIS (média semanal) e cobertura

| Nível | Modelo | WIS | Dispersão | Subprevisão | Sobreprevisão | Cob. 50% | Cob. 80% | Cob. 90% | Cob. 95% |
|---|---|---:|---:|---:|---:|---:|---:|---:|---:|
| UFs | B1 | 903,1 | 470,7 | 281,1 | 151,3 | 42% | 74% | 87% | 93% |
| UFs | B2 | 673,8 | 120,7 | 529,2 | 23,9 | 39% | 64% | 72% | 76% |
| UFs | B3 | 711,0 | 100,6 | 586,7 | 23,7 | 34% | 57% | 67% | 73% |
| UFs | TFT | 678,8 | 123,7 | 517,4 | 37,7 | 25% | 47% | 59% | 67% |
| Cidades | B1 | 156,5 | 110,2 | 33,3 | 13,0 | 52% | 83% | 91% | 94% |
| Cidades | B2 | 70,6 | 12,0 | 57,7 | 0,9 | 44% | 70% | 79% | 83% |
| Cidades | B3 | 73,7 | 9,0 | 63,4 | 1,3 | 28% | 48% | 56% | 62% |
| Cidades | TFT | 77,3 | 11,0 | 63,2 | 3,1 | 20% | 39% | 50% | 56% |

- **Subprevisão:** domina o WIS de todos os modelos, exceto o do B1.
- **Cobertura:** fica abaixo do nominal em todos os modelos e níveis, com uma exceção: o B1 nas cidades, na faixa de 50%. O B1 é o que mais se aproxima do nominal, mas com intervalos muito largos e WIS bem pior.
- **Média simples contra métrica primária:** o WIS médio nas UFs favorece o TFT (678,8 contra 711,0), porque é dominado pelas epidemias grandes. A métrica primária dá o mesmo peso a cada UF-temporada.

## Análises exploratórias

Estas análises foram feitas depois de ver o resultado primário, usando as mesmas temporadas. **Não fazem parte do protocolo e servem apenas para gerar hipóteses.**

### Combinações de total e forma

Sem retreino: cada combinação usa quantis já previstos pelo TFT e pelo B3.

| Combinação | UFs (IC 95%) | Cidades (IC 95%) | Cob. 90%, UFs |
|---|---|---|---:|
| Total do TFT + forma do B3 | **0,963 (0,870 a 1,085)** | 0,997 (0,904 a 1,136) | 75% |
| Total e pico do TFT + alfa e beta do B3 | 1,043 (0,949 a 1,169) | 1,023 (0,935 a 1,147) | 69% |
| Total do B3 + forma do TFT | 1,279 (1,194 a 1,359) | 1,122 (1,076 a 1,172) | 53% |

A melhor combinação não é superior ao B3, porque o IC inclui 1. O que se pode dizer é que a forma do TFT piora o resultado, e o total do TFT não.

### Descritores da temporada, por município

Médias das 10 temporadas, com todos os municípios.

| Descritor | B3 | TFT |
|---|---:|---:|
| Viés do total (log) | -0,507 | -0,228 |
| MAE do total (log) | 1,491 | 1,343 |
| MAE do total (log), municípios com ≥ 200 casos | 2,374 | 1,927 |
| Cobertura de 80% do total | 61% | 66% |
| Largura do intervalo de 80% (log) | 2,716 | 2,955 |
| MAE do pico (semanas), com ajuste Richards | 4,995 | 4,744 |
| MAE do pico (semanas), com ajuste e ≥ 200 casos | 4,499 | 4,452 |

O TFT teve MAE do total menor que o do B3 em 9 das 10 temporadas; a exceção é 2016/17.

### Soma das medianas municipais contra casos observados

A soma das medianas não é a mediana da soma; serve só para dar a ordem de grandeza.

| Temporada | B3 | TFT | Observado |
|---|---:|---:|---:|
| 2015/16 | 555.302 | 713.104 | 1.614.673 |
| 2016/17 | 574.573 | 932.041 | 252.205 |
| 2017/18 | 650.102 | 465.997 | 243.368 |
| 2018/19 | 474.484 | 496.937 | 1.522.444 |
| 2019/20 | 409.507 | 963.102 | 1.015.474 |
| 2020/21 | 431.387 | 352.753 | 497.788 |
| 2021/22 | 438.606 | 753.613 | 1.385.993 |
| 2022/23 | 401.684 | 478.317 | 1.620.229 |
| 2023/24 | 425.537 | 481.580 | 6.858.892 |
| 2024/25 | 441.738 | 543.559 | 1.802.625 |

Nenhum dos dois modelos antecipou a epidemia de 2023/24.

### WIS relativo do TFT ao B3, por intensidade da temporada

Intensidade = casos da unidade na temporada divididos pela mediana da própria unidade nas 10 temporadas. Como usa os casos observados, este corte só existe depois da temporada.

| Intensidade | UFs | n | Cidades | n |
|---|---:|---:|---:|---:|
| Abaixo de 0,5 vez | 0,979 | 64 | 1,196 | 42 |
| De 0,5 a 1,5 vez | 1,357 | 116 | 1,170 | 60 |
| De 1,5 a 4 vezes | 1,274 | 57 | 1,105 | 20 |
| Acima de 4 vezes | 0,906 | 23 | 0,872 | 28 |

### Temporada 2025/26

Dados só até a EW25/2026, por isso fora da análise primária. WIS mediano:

| Nível | B1 | B2 | B3 | TFT |
|---|---:|---:|---:|---:|
| UFs | 170,1 | 127,9 | 125,1 | 96,2 |
| Cidades | 130,6 | 18,6 | 17,2 | 17,2 |

## Limitações

- **Uma semente:** ainda não se sabe quanto das diferenças vem da variação do treino.
- **Poucas temporadas:** com 10, o poder estatístico é limitado.
- **Dados não são safras históricas:** casos e clima são os valores atuais, já revisados, o que favorece todos os modelos.
- **Configuração do TFT:** a retirada de `time_idx` e a taxa de aprendizado foram escolhidas olhando a temporada 2024/25, que está no conjunto de avaliação.
- **Ajustes Richards:** vêm de `notebooks/apply_2026.ipynb`, não do Episcanner oficial. O método está escrito `diferential_evolution` e cai em Nelder-Mead. Numa amostra de 60 ajustes, o resultado foi praticamente igual ao da evolução diferencial.
- **Temporadas sem ajuste:** recebem forma imputada, e a falha se concentra em grandes cidades (24,9% dos casos de 2024 e 29,1% dos de 2012). Isso pode afetar justamente a forma, onde está a perda do TFT. O reajuste não foi feito.
- **README:** ainda atribui os parâmetros ao Episcanner, o que precisa ser corrigido.
- **Submissão ao IMDC:** a previsão 2026-27 enviada usa o TFT completo, não uma combinação.

## O que ainda não foi feito

- Rodar sementes adicionais.
- Reajustar as temporadas grandes sem ajuste Richards.
- Medir por que a forma do TFT piora o resultado. A hipótese de quantis de forma estreitos demais não foi testada.
- Comparar com os resultados oficiais do IMDC.

## Arquivos

- **Tabelas primárias:** `relative_wis.csv`, `median_wis_by_season.csv`, `components_coverage.csv` e `rho_by_cut.csv`, nesta pasta.
- **Análises exploratórias:** os scripts e as combinações estão apenas na pasta temporária da sessão, e não no repositório. Os valores acima foram copiados da saída desses scripts.
