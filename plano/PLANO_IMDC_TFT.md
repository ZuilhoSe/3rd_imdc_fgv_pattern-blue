# Plano IMDC 2026 — Pattern Blue: auditoria, publicação e roadmap

Data: 2026-11-14. Escopo: auditar, criticar e planejar. Nenhum código foi escrito e nenhum experimento foi rodado para este documento; só leitura do repositório e consultas de dados já existentes.

**Marcação usada em todo o texto**

- **[F]** fato verificado no material, com arquivo e linha ou tabela.
- **[I]** inferência minha a partir dos fatos.
- **[O]** opinião ou recomendação.
- **(a verificar)** vem de literatura ou da web e eu não li a fonte primária. A única fonte externa que li por inteiro foi a página de instruções do IMDC 2026 (https://sprint.mosqlimate.org/instructions/).

**O que não recebi.** O pedido tinha campos em branco: detalhes do edital, caminho do "plano do Richards", comentários dos orientadores e tabelas extras. Usei a página oficial de instruções e o repositório. Onde isso muda a conclusão, está na lista de perguntas (B7.4).

---

## Sumário executivo

1. **O modelo submetido foi mal.** Nas 4 validações oficiais ficou com razão de WIS 1,612 contra o baseline PROCC nas UFs (20º de 28 modelos oficiais) e 1,161 nas cidades (6º de 10). Cobertura de 95% nas UFs: 56% [F: `reports/v3/report_v4_full.txt:34,49,79`].
2. **Nenhuma versão do TFT supera, com evidência, uma climatologia.** Na origem móvel de 10 temporadas, o WIS relativo ao B3 (climatologia de parâmetros) nas UFs foi 1,19 (v2), 1,005 (v3) e 1,17 (v4); só o do v2 tem IC que exclui 1, e para pior [F: `report_v4_full.txt:118-121`]. Uma climatologia de casos por semana (B2) empata com o B3 e ganha de todos os TFTs na razão oficial das UFs [F: idem, linhas 13, 24-27].
3. **O gargalo é a magnitude da temporada, não a arquitetura.** Nas UFs, a subprevisão responde por 62% a 90% do WIS de todos os modelos, menos a persistência; no baseline oficial são 82% [F: `report_v4_full.txt:48-60`]. Nenhum modelo antecipou 2023/24 [F: `reports/rolling/resultados_fase1.md:106-109`].
4. **O que dá para publicar agora** é um relato honesto com resultado negativo e diagnóstico: formulação por descritores de Richards, avaliação com origem móvel, decomposição total contra forma e o conflito entre calibração e WIS relativo. Alegar ganho do TFT não se sustenta.
5. **Antes de GNN e TNN**, três testes baratos decidem se vale construir: autocorrelação espacial dos resíduos, defasagens espaciais como variáveis e o teto do Richards com parâmetros oráculo. Sem sinal nesses testes, a sequência GNN → TNN é capacidade extra num problema limitado por informação.
6. **O conjunto de teste está gasto.** As 10 temporadas e as 4 validações já orientaram v3, a calibração e o v4. O único teste limpo que resta é a temporada 2026/27, prospectiva, e a transferência para chikungunya.

### Decisão registrada em 2026-11-14: esperar ganho

Você escolheu não publicar o resultado negativo agora e esperar um resultado positivo para o primeiro artigo. A recomendação original (preprint de diagnóstico) fica nas seções A3 e A4 como plano de contingência. O que muda:

1. **"Ganho" só vale nos testes confirmatórios.** Qualquer melhora nos cortes de 2015 a 2025 é desenvolvimento (item 6). O artigo positivo depende de chikungunya (disponível já, pontuada uma única vez) ou da temporada 2026/27 (fecha na EW40/2027).
2. **Datas mais cedo possíveis** [I]: início de 2027 com chikungunya, depois das Fases 0, 1, 2 e 2b; fim de 2027 com o prospectivo.
3. **A Fase 0 continua obrigatória** e passa a ser o primeiro trabalho: sem versionamento e sem sementes, um ganho futuro não se distingue de ruído.
4. **O protocolo congelado (B6) precisa de data pública antes da Fase 1** (tag no git ou depósito no OSF/Zenodo). Sem isso, esperar ganho vira busca até achar, e o revisor não tem como separar as duas coisas.
5. **Regra de parada** [O]: se ao fim das Fases 2 e 2b nenhum candidato superar o B3 pelo critério de B6, o artigo volta a ser o de diagnóstico. Sugiro fixar a data-limite agora, com os orientadores.
7. **Prazo de duas semanas (pedido em 2026-11-14, entrega até 2026-11-28):** ver o bloco seguinte, que substitui as datas do item 2 e fixa a regra de parada do item 5 em 2026-11-22.
6. **Custo aceito** [O]: nada fixa a prioridade da formulação e do diagnóstico até lá, e o artigo coletivo do IMDC 2026 pode publicar parte dos achados (subprevisão geral, conflito entre calibração e ranking) antes.

### Plano de duas semanas (2026-11-14 a 2026-11-28)

Premissa [I]: "terminar" é ter o primeiro artigo pronto para os orientadores. Em duas semanas cabe **um** teste confirmatório (chikungunya) e nenhuma arquitetura nova. O artigo sai com o resultado que esse teste der; é isso que torna o prazo compatível com "esperar ganho".

| Dias | Trabalho | GPU local (estimativa) | Pronto quando |
|---|---|---|---|
| 14–15/11 | Versionar tudo; protocolo congelado com tag datada; refazer as tabelas exploratórias por script | — | `git status` limpo; tag publicada |
| 15–19/11 | 4 sementes novas do v3 nos 10 cortes (a 42 já existe) | ~80 h | Desvio entre sementes medido |
| 15–18/11 | Candidatos baratos, sem rede nova: ensemble de quantis (B2, B3, v3), total do v3 com forma do B3, boosting para o total, Richards oráculo, 2 modelos de fundação zero-shot | < 10 h | Uma linha por candidato na tabela primária |
| 15–20/11 | Revisão bibliográfica pelos prompts de A5, em paralelo | — | Matriz verificada |
| 20/11 | Escolher **um** candidato pelo critério de B6, por escrito, antes de abrir chikungunya | — | Registro com data |
| 20–22/11 | Chikungunya: pré-processar como alvo, treinar o que o candidato exigir (3 sementes), pontuar uma vez | ~50 h | Tabela confirmatória |
| 22/11 | **Regra de parada:** ganho em chikungunya define a tese positiva; sem ganho, a tese é a de diagnóstico | — | Tese fixada |
| 23–27/11 | Escrita na estrutura de A4; depósito das previsões 2026/27 dos candidatos | — | Cada número rastreável a um CSV |
| 28/11 | Envio aos orientadores | — | — |

**Fica de fora:** GNN, rede topológica, blocos novos de dados (imunidade, ENSO, defasagens espaciais no TFT), sementes do v2, simulação de atraso de notificação, o resultado prospectivo de 2026/27 (só o depósito).

**Riscos do prazo** [O]:

- A folga de GPU é pequena: ~140 h de ~330 h de relógio, sem margem para um treino que falhe duas vezes. Se o HPC estiver acessível, usar.
- Os candidatos com chance real são combinações (ensemble, total do v3 com forma do B3: 0,957 no desenvolvimento, IC inclui 1). Se um deles ganhar, a tese honesta é "combinar com climatologia ajuda", não "o TFT ganha".
- Chikungunya tem menos temporadas úteis que dengue; o poder do teste confirmatório é baixo e isso vai declarado no artigo.
- Com um único teste confirmatório e 3 sementes, o resultado mais provável é inconclusivo. Nesse caso vale a regra de parada.

---

# Parte A — Publicar o primeiro avanço

## A1. Mapa do que existe

### Dados e variáveis

| Item | O que há | Evidência |
|---|---|---|
| Casos | Dengue semanal, 5.570 municípios, 2010-01-03 a 2026-06-21 (EW25/2026) | [F] consulta a `data/processed/base_weekly.parquet`; `src/preprocess.py:26,43-52` |
| Clima observado | ERA5 via Mosqlimate: temperatura, chuva, umidade (v2); mínimos, máximos, pressão, amplitude, dias de chuva (v3) | [F] `preprocess.py:55-63`; `preprocess_v3.py:19-32` |
| Previsão climática | Emissões mensais, 1 a 6 meses à frente; v2/v3 usam a média de todas as emissões para o mês-alvo; v4 acrescenta a emissão de junho (jul-set e out-dez) | [F] `preprocess.py:66-78`; `preprocess_v4.py:20-31`; consulta aos arquivos brutos (leads 1 a 6) |
| Índices oceânicos | ENSO, IOD, PDO semanais; fora do v2, dentro do v3 | [F] `preprocess.py:99-104`; `common_v3.py:22-24` |
| Outras séries | Chikungunya e acessos Afya (2021+), com indicador `has_access` | [F] `preprocess_v3.py:35-51,70-76` |
| Estáticas | UF, Köppen, bioma, macrorregião; região de saúde no v3 | [F] `common.py:53`; `common_v3.py:25` |
| Alvos | `log_total_cases`, `alpha`, `beta`, `peak_week` por município-temporada; 83.550 linhas, temporadas 2011 a 2025 | [F] `common.py:44`; consulta a `season_targets_v3.parquet` |
| Ajustes de Richards | Só 27% dos municípios-temporada têm ajuste (9% em 2017, 59% em 2024); os demais recebem forma imputada por medianas | [F] consulta a `season_targets_v3.parquet`; `common.py:83-96` |
| Grafo | Arestas de adjacência, GraphML, embeddings espectrais de 16 dimensões; não entram em nenhum modelo avaliado | [F] `src/graph_embedding.py`; `README.md:155-156` |
| TDA | Entropia e amplitude de persistência H0/H1 em configuração antiga; abandonadas | [F] `data/processed/tft_config.json:19-22`; `README.md:155-156` |

### Formulação e configuração do TFT

- **Tarefa** [F: `common.py:4-13`]: janela de 52 semanas, 1 passo de decoder, 4 alvos com 7 quantis cada. O modelo prevê descritores da temporada seguinte; não prevê casos semanais.
- **Reconstrução** [F: `src/imdc_submission.py:46-61`]: curva de Richards normalizada para somar o total previsto.
- **Incerteza** [F: `imdc_submission.py:65-89`]: Monte Carlo sobre as marginais de cada parâmetro, com interpolação linear dos 7 quantis; caudas além de 2% e 98% ficam presas no último quantil (linha 72); os 4 parâmetros são sorteados de forma independente dentro do município.
- **Agregação estadual** [F: `imdc_submission.py:120-130`]: soma das curvas municipais por sorteio, com cópula gaussiana de um fator por UF (`rho`).
- **Arquitetura** [F: `src/train.py:58-63`]: `hidden_size=32`, 2 cabeças de atenção, dropout 0,1; 113 mil parâmetros no v2 e 172 mil no v3 [F: `src/outputs/train_rolling.log:5`; `v3_train.log:6`].
- **Treino v2** [F: `train.py:33-37,51-52`]: lr 0,003, 400 lotes de 256 por época, decoders nas EW20 a EW32, alvos ≤ Y−2, parada antecipada na temporada Y−1.
- **Treino v3** [F: `src/train_v3.py:64-66,88-94`; `common_v3.py:29-42`]: perda de forma só em temporadas com ajuste; segunda etapa de 3 épocas com todos os dados do corte (`full.ckpt`).
- **v4** [F: `docs/evaluation_protocol_v4.md:9-14`]: mais variáveis, lr 0,001, até 50 épocas.
- **Sementes** [F: `common.py:32`; `resultados_fase1.md:14`]: uma única, 42, em todas as versões.

### Validação

| Esquema | Conteúdo | Evidência |
|---|---|---|
| Origem móvel | Cortes EW25/Y, Y = 2015 a 2024; um modelo por corte; 26 UFs e 15 cidades | [F] `docs/evaluation_protocol.md:18-22` |
| Métrica primária | WIS relativo ao B3 nas UFs, média geométrica de `(WIS+1)/(WIS_B3+1)`; IC por bootstrap de temporadas | [F] `evaluation_protocol.md:11-16`; `src/rolling_eval.py:205-219` |
| Oficial | Razão de WIS contra PROCC (UFs) e LSTM EMAp (cidades) nas 4 validações, com casos oficiais até 2026-09-27 | [F] `docs/evaluation_protocol_v3.md:24-27`; `src/evaluate_v3.py:31,41-46` |
| Baselines próprios | B1 persistência, B2 climatologia de casos, B3 climatologia de parâmetros | [F] `rolling_eval.py:64-104` |
| Calibração | Conformal (A), ruído binomial negativo (B), conjunto de checkpoints (C), protocolo registrado antes | [F] `docs/evaluation_protocol_v3_calib.md` |

### Resultados

**Origem móvel, 2015/16 a 2024/25, WIS relativo ao B3** [F: `report_v4_full.txt:104-123`]

| Modelo | UFs (IC 95%) | Cidades (IC 95%) |
|---|---|---|
| B2, climatologia de casos | 0,986 (0,949 a 1,035) | 1,021 (0,989 a 1,053) |
| TFT v2 | 1,192 (1,079 a 1,343) | 1,106 (1,014 a 1,233) |
| TFT v3 | 1,005 (0,836 a 1,203) | 0,994 (0,821 a 1,258) |
| TFT v4 | 1,171 (0,962 a 1,446) | 1,081 (0,898 a 1,273) |
| Total do v3 + forma do B3 | 0,957 (0,807 a 1,143) | 0,980 (0,810 a 1,236) |
| B1, persistência | 1,438 (1,021 a 2,062) | 2,369 (1,652 a 3,506) |

**Razão oficial nas 4 validações** [F: `report_v4_full.txt:3-43,62-84`]

| Modelo | UFs, contra PROCC | Cidades, contra LSTM EMAp |
|---|---:|---:|
| Melhor oficial | 0,889 (LNCC ARP) | 0,944 (EMAp Prophet) |
| B2 | 1,014 | 1,061 |
| B3 | 1,054 | 1,027 |
| Total do v3 + forma do B3 | 1,164 | 0,996 |
| TFT v4 | 1,187 | 1,033 |
| TFT v3 | 1,213 | 1,014 |
| TFT v2 | 1,240 | 1,081 |
| Submetido (`3rd_imdc_fgv_pattern-blue`) | 1,612 | 1,161 |

**Cobertura e componentes, UFs, 4 validações** [F: `report_v4_full.txt:45-60`]

| Modelo | Cob. 50% | Cob. 95% | WIS | Subprevisão | Sobreprevisão |
|---|---:|---:|---:|---:|---:|
| PROCC (baseline oficial) | 47,5 | 92,0 | 1116 | 920 | 46 |
| Submetido | 22,3 | 56,4 | 1305 | 815 | 387 |
| TFT v3 | 36,6 | 85,2 | 1188 | 1031 | 18 |
| TFT v3 + conformal (v3A) | 55,0 | 95,3 | 1065 | 520 | 63 |
| B3 | 39,9 | 81,1 | 1242 | 1113 | 4 |

**O que não existe** [F, por ausência nos relatórios]:

- **Por horizonte.** Todos os relatórios dão a média da temporada. Não há WIS por semana de antecedência (16 a 68 semanas após o corte) nem por fase (subida, pico, descida).
- **Por região.** Não há tabela por macrorregião ou por UF para v2, v3 ou v4.
- **Relatórios antigos.** `reports/capitais_*.csv`, `eval_metrics.csv` e `top100_*.csv` são de 1º de julho e mostram a mesma curva em todas as temporadas (por exemplo, `eval_metrics.csv:2-4`: total previsto de 841 e pico na EW15 para Cruzeiro do Sul nos três testes). [I] São do pipeline v1, com os erros listados em `preprocess.py:8-16`, e não devem ser citados.

### Submissões

- **Validações** [F: `src/outputs/upload_manifest.csv`, de 1º de julho]: enviadas no prazo de 1º de julho com o pipeline v1.
- **Correção** [F: `git log`, commit `dc24fc9` de 2026-09-23; `upload_manifest_v2.csv` só com `final`]: o pipeline corrigido e a previsão 2026-27 são de 23 de setembro; o prazo oficial da previsão era 10 de setembro [F: página de instruções, seção 9].
- [I] O que o IMDC pontuou nas validações foi o v1, com erros de junção e de semana de pico. O 1,612 mede esses erros, não a formulação. Se a previsão final aceita foi a v1 ou a v2 é pergunta para você (B7.4).

---

## A2. Auditoria de robustez

Ordenada por impacto. Severidade: **crítico** invalida uma alegação; **importante** muda o tamanho ou a confiança; **menor** deve ser declarado.

### Críticos

**C1. O conjunto de avaliação orientou o desenho, três vezes.**
- [F] A configuração do v2 (sem `time_idx`, lr) foi escolhida pelo `val_loss` do corte final, cuja validação é 2024/25 (`evaluation_protocol.md:44-46`).
- [F] A máscara da perda de forma do v3 veio da análise exploratória nas mesmas 10 temporadas (`evaluation_protocol_v3.md:19`).
- [F] O v4 foi motivado pelo comportamento do v3 nos mesmos cortes (`evaluation_protocol_v4.md:16-18`).
- [F] O `rho` da submissão foi ajustado nas próprias 4 validações (`src/evaluate.py:71-87`; `src/outputs/state_rho.json`).
- [I] Mecanismo: cada decisão tomada depois de ver o teste reduz o erro aparente sem reduzir o erro real. A melhora de 1,19 para 1,005 entre v2 e v3 mistura efeito real com adaptação ao teste, e não há como separar com os dados atuais.
- [O] Tratar 2015 a 2025 como conjunto de desenvolvimento daqui em diante e dizer isso no artigo.

**C2. Uma semente.**
- [F] Todos os resultados usam a semente 42 (`common.py:32`).
- [F] No mesmo corte, `best.ckpt` e `full.ckpt` do v3 diferem em 0,04 no WIS relativo (1,046 contra 1,005) e os do v4 têm ICs que divergem (`report_v4_full.txt:119-122`).
- [I] A diferença entre v3 e v4 (0,17) pode ser da mesma ordem que a variação entre sementes. Sem medir essa variação, nenhuma comparação entre versões do TFT é interpretável.

**C3. Dados revisados, não safras.**
- [F] Casos e clima são os valores atuais (`evaluation_protocol.md:42-43`; `preprocess.py:48-50`).
- [I] Na EW25/Y, as últimas semanas do SINAN ainda estão incompletas por atraso de notificação. O encoder do retrospecto vê a contagem final; o da previsão real vê a contagem parcial. O viés favorece o retrospecto e pode explicar parte da subprevisão em produção. Atinge todos os modelos próprios, mas não necessariamente os dos outros times.
- [O] Se o Mosqlimate guardar safras, usar; se não, simular o atraso truncando as últimas semanas com um perfil empírico.

**C4. A comparação que sustentaria "o TFT agrega valor" é negativa ou nula.**
- [F] Tabelas de A1. O único resultado com IC fora de 1 é contra o TFT (v2 nas UFs e cidades; `v4_best` nas UFs).
- [F] Com 10 temporadas e IC de 0,84 a 1,20, o v3 não distingue ganho de 15% de perda de 20%.

### Importantes

**I1. Normalizador com a temporada de validação e com o próprio alvo.**
- [F] `fit_normalizer` usa todas as temporadas ≤ Y−1 (`common.py:160-165`; `train.py:45`), o que inclui a temporada de parada antecipada (Y−1) e o próprio alvo de cada amostra de treino. `add_target_scales=True` entrega centro e escala ao modelo como variável estática (`common.py:177`).
- [I] Não há vazamento da temporada de teste. Mas, no treino, o centro por município contém cerca de 1/n do alvo (n ≤ 15 temporadas), e no teste não. O resíduo de treino fica sistematicamente menor que o de teste, o que empurra os quantis para estreitos. É um mecanismo candidato para a subcobertura (cobertura de 80% do total: 66%; `resultados_fase1.md:85`). Não foi testado.
- [O] Teste: normalizador ajustado deixando de fora a temporada da amostra, ou escalas só com temporadas anteriores ao decoder.

**I2. Forma imputada em 73% dos alvos.**
- [F] 27% dos municípios-temporada têm ajuste; o resto recebe medianas (`common.py:83-96`). O v2 treinou a forma nesses valores; o v3 mascara.
- [F] A falha não é aleatória: atinge grandes cidades e 24,9% dos casos de 2024 (`evaluation_protocol.md:52-55`); o v3 reajustou 9 de 10 (`evaluation_protocol_v3.md:15`).
- [I] O B3 usa as mesmas formas imputadas; a comparação é justa entre os dois, mas a forma de ambos é, em boa parte, a mediana regional.

**I3. Ajustes de Richards fora do Episcanner oficial.**
- [F] Vêm de `notebooks/apply_2026.ipynb`, com `method="diferential_evolution"` (linha 421), que o lmfit não reconhece e troca por Nelder-Mead (`evaluation_protocol.md:47-51`). O `README.md:18,127` ainda os atribui ao Episcanner.
- [F] O reajuste do v3 restringe o pico a 5 ≤ t ≤ 35 e `gamma` a 0,30–0,33 (`preprocess_v3.py:101-105`).
- [I] Picos antes de meados de novembro ou depois de junho são truncados no alvo.

**I4. Scores incompletos.**
- [F] Há WIS, componentes, cobertura e largura (`rolling_eval.py:124-142`). Não há PIT, log score nem CRPS, nem WIS por horizonte.
- [F] O WIS relativo próprio soma 1 antes da razão (`rolling_eval.py:213`); o oficial não (`evaluation_protocol_v3.md:25`).
- [I] Com 9 quantis, o WIS já aproxima o CRPS; o log score não é recuperável sem densidade e eu não o perseguiria. O que falta de fato é o histograma PIT por horizonte e a tabela por horizonte.

**I5. A métrica muda o vencedor.**
- [F] O conformal (v3A) melhora o WIS médio das UFs (1065 contra 1188) e leva a cobertura de 95% a 95,3%, mas piora a razão oficial de 1,21 para 2,17 (`reports/v3_calib/intervals_state.csv:5`; `official_ratio_state.csv:14`).
- [F] O WIS médio simples favorece o TFT v2 sobre o B3 (678,8 contra 711,0) e a média geométrica faz o contrário (`resultados_fase1.md:58`).
- [I] Mecanismo: a média geométrica por unidade dá o mesmo peso a Roraima e a São Paulo. Alargar intervalos em log1p custa muito em unidades pequenas e de temporada fraca, e rende pouco onde a epidemia foi grande. A calibração conformal agrupada por nível não respeita essa heterogeneidade.
- [O] Este é um achado publicável por si só (A3, alegação 6).

**I6. Baselines.**
- [F] Existem persistência, climatologia de casos e climatologia de parâmetros. Faltam SARIMA, gradient boosting, um modelo direto do total sem Richards e um ensemble.
- [F] Os arquivos oficiais trazem Prophet, SARIMAX, XGBoost e LSTM de outros times (`report_v4_full.txt:8,18,21,29`), já pontuados.
- [I] Comparar com modelos de terceiros nas 4 validações é legítimo, mas eles usaram suas próprias decisões de dados. Não substitui baselines rodados no mesmo protocolo de 10 temporadas.

**I7. Significância.**
- [F] IC percentil por bootstrap de 10 médias de temporada (`rolling_eval.py:214-217`).
- [I] A unidade independente é a temporada, e são 10. Diebold–Mariano sobre semanas não se aplica bem: os erros de uma previsão de 52 semanas emitida de uma só origem são um único evento correlacionado, e a correção HAC não resolve com 10 origens.
- [O] Usar, sobre o log da razão por temporada, teste de permutação de sinais (exato, 2¹⁰ combinações) e Wilcoxon pareado, além do bootstrap. Declarar o menor efeito detectável: com o desvio observado entre temporadas, só diferenças da ordem de 15% a 20% seriam detectadas.

**I8. Ablações confundidas.**
- [F] O v3 muda variáveis, categóricas, perda, ajustes, épocas e etapa de ajuste fino ao mesmo tempo (`evaluation_protocol_v3.md:9-17`). O v4 muda dados e treino juntos, e declara isso (`evaluation_protocol_v4.md:24`).
- [I] Não se sabe o que causou a melhora do v2 para o v3 nem a piora do v3 para o v4.

**I9. Reprodutibilidade.**
- [F] Todo o código de v3, v4, origem móvel, protocolos e relatórios está fora do controle de versão (`git status`: `docs/`, `reports/rolling/`, `reports/v3*/`, `src/*_v3.py`, `src/*_v4.py`, `src/rolling_eval.py`).
- [F] Os scripts das análises exploratórias ficaram numa pasta temporária e os números foram copiados à mão (`resultados_fase1.md:152`).
- [F] `pyproject.toml` não lista `mosqlient` nem `python-dotenv`, citados no `README.md:98-99`, e lista `giotto-tda` e `torch-geometric`, que nenhum script usa.
- [F] Treino em `bf16-mixed` (`train.py:71`), não determinístico entre máquinas.
- [F] O protocolo do v4 diz que 10 dos 12 cortes do v3 bateram no limite de 25 épocas (`evaluation_protocol_v4.md:17`); o log mostra 8 (`v3_train.log`: `test1` e `cut2015` a `cut2021`). Conferir.

### Menores

- **Imputação com dados futuros.** Buracos de clima são preenchidos com a média da série inteira do município (`preprocess.py:127-128`; `preprocess_v3.py:62-63`) e, no v4, com `bfill` (`preprocess_v4.py:43`). [I] Efeito pequeno, mas é informação posterior ao corte.
- **Disponibilidade da previsão climática.** O decoder usa a média das emissões para o mês-alvo (`common.py:134-141`). [I] Depende de a emissão de junho estar publicada até a EW25; o protocolo do v4 assume que sim (`evaluation_protocol_v4.md:23`). Confirmar a data de publicação da fonte.
- **População.** A de 2026 repete a de 2025 (`preprocess.py:115`). [I] A estimativa do ano Y pode não existir na EW25/Y nos cortes antigos.
- **Acessos Afya.** Só existem a partir de 2021 (`preprocess_v3.py:42-51`). [I] Nos cortes de 2015 a 2020 a variável é constante; o modelo de cada corte vê um conjunto efetivo diferente de variáveis.
- **Decoders de treino depois da EW25.** Amostras com decoder nas EW26 a EW32 têm encoder com semanas que não existiriam no corte (`common.py:56`). [I] É aumento de dados, não vazamento, mas o treino vê a temporada um pouco mais adiantada que a inferência.
- **Temporada 2025/26.** Parcial na origem móvel (base até EW25/2026) e quase completa na oficial (casos até 2026-09-27). Os dois números não são comparáveis.
- **README.** E-mail com erro de digitação, nome do líder e sobrenome da orientadora inconsistentes (`README.md:35-42`).

### Covariáveis: disponível no momento da previsão?

| Variável | Papel | Disponível na EW25/Y? | Observação |
|---|---|---|---|
| Casos, incidência | observada | Sim, mas com atraso de notificação | Ver C3 |
| Clima ERA5 | observada | Sim, com poucos dias de atraso (a verificar) | Preenchimento usa média futura |
| Previsão climática mensal | conhecida | Depende da data de emissão (a verificar) | Só 6 meses; não cobre fev-mai |
| ENSO, IOD, PDO | observada | Sim | Valor realizado, não previsto |
| População | conhecida | Incerto para o ano corrente | Efeito pequeno |
| Chikungunya | observada | Sim, com o mesmo atraso dos casos | |
| Acessos Afya | observada | Só de 2021 em diante | Não estacionária por construção |
| Acumulado e total anterior (v4) | observada | Sim | `preprocess_v4.py:45-51` |
| Escalas do alvo | estática | Sim, mas incluem Y−1 e o próprio alvo no treino | Ver I1 |

---

## A3. Alegações publicáveis

| # | Alegação | Evidência | Força | Ameaça principal | O que falta | Destino |
|---|---|---|---|---|---|---|
| 1 | Formulação: TFT global prevê descritores de Richards; reconstrução por Monte Carlo; agregação por cópula | Código e README | Descritiva | Novidade frente ao Episcanner e a híbridos existentes | Revisão bibliográfica (A5) | **Publicar** como método |
| 2 | O TFT supera a climatologia de parâmetros | v2: 1,19 (IC > 1); v3: 1,005 (IC inclui 1); v4: 1,17 | Contra | C1, C2 | Nada resolve a curto prazo | **Cortar.** Reformular: "não supera" |
| 3 | Previsões de temporada inteira subpreveem e subcobrem, em todos os modelos menos a persistência, inclusive no baseline oficial | Componentes do WIS nas 4 validações e nas 10 temporadas | Forte | Dados revisados favorecem todos | Tabela por horizonte e por intensidade com script versionado | **Publicar** |
| 4 | O valor do TFT está no total, e a forma prevista atrapalha | Total TFT + forma B3: 0,96 (IC inclui 1); total B3 + forma TFT: 1,28 (IC > 1), só no v2; MAE do total menor em 9 de 10 temporadas | Moderada para "a forma do v2 atrapalha"; fraca para "o total ajuda" | Exploratória, scripts perdidos, uma semente; nas 4 validações oficiais o híbrido (1,164) perde para o B3 (1,054) nas UFs | Refazer com sementes e script no repositório; relatar o conflito com as validações oficiais | **Reformular** como hipótese |
| 5 | Mascarar a perda de forma e ajustar com a última temporada melhora o modelo (v2 → v3) | 1,19 → 1,005 | Fraca | Seis mudanças juntas, escolhidas olhando o teste | Ablação uma a uma, com sementes | **Reformular** como observação |
| 6 | Calibração conformal corrige a cobertura e piora o WIS relativo; ruído binomial negativo melhora a cobertura nas cidades sem custo | `reports/v3_calib/*`; protocolo registrado antes | Moderada a forte | Conformal agrupado por nível; uma semente | Conformal estratificado por porte como contraprova | **Publicar** |
| 7 | Mais variáveis e mais épocas não ajudaram (v3 → v4) | 1,005 → 1,171 nas UFs | Fraca | Confundida; uma semente | Sementes | **Citar com cautela** |
| 8 | Corrigir o pipeline levou a razão oficial de 1,61 para 1,24 | `report_v4_full.txt:27,34` | Forte, mas não é ciência | — | — | **Declarar** em uma frase, sem alegar mérito |
| 9 | Posição entre os times | 20º de 28 (UFs), 6º de 10 (cidades) com o submetido; o v3 ficaria em 15º e 4º | Forte | O v3 foi feito depois de ver os resultados | — | **Publicar** o submetido; o v3 só como pós-hoc |

**Obrigatório antes de qualquer preprint**

1. Versionar todo o código, protocolos e relatórios; refazer as tabelas exploratórias com scripts no repositório.
2. Rodar pelo menos 5 sementes do v2 e do v3 nos 10 cortes e reportar média e desvio entre sementes.
3. Tabela de WIS e cobertura por horizonte (blocos de 4 a 8 semanas) e por macrorregião.
4. Teste de permutação de sinais ao lado do bootstrap; declarar o efeito mínimo detectável.
5. Corrigir o README: origem dos ajustes de Richards, variáveis de cada versão, nomes.
6. Seção de limitações com C1, C3, I1, I2 e I3 por extenso.

**Desejável**

- Baselines no mesmo protocolo: SARIMA sazonal por UF, gradient boosting para o total, ensemble simples (média de quantis de B2, B3 e TFT).
- Histograma PIT por horizonte.
- Teste do normalizador sem a temporada da amostra (I1).
- Richards com parâmetros oráculo (B3).
- Simulação de atraso de notificação (C3).

---

## A4. Estratégia de publicação

### Tipo de artigo

> **Decisão de 2026-11-14:** a peça 1 abaixo não será publicada agora. O plano ativo é um único artigo de método (peça 2), condicionado aos testes confirmatórios de B6. A peça 1, a estrutura do preprint e o plano de escrita ficam como contingência, acionada pela regra de parada do sumário executivo. O material de diagnóstico (seções 6 e 7 da estrutura) entra no artigo de método de qualquer forma.

[O] **Recomendação original: duas peças, nesta ordem.**

1. **Preprint curto agora (medRxiv ou arXiv), como relato de participação com avaliação retrospectiva.** Tese: prever a temporada inteira a partir da EW25 é um problema dominado pela magnitude; um modelo profundo por descritores paramétricos não supera climatologias; a calibração e a métrica de ranking entram em conflito. Um resultado negativo bem medido é útil para os outros 27 times e para os organizadores.
2. **Artigo de método depois da Fase 2 do roadmap**, só se algum componente passar no teste prospectivo ou na transferência para chikungunya.

[O] Não recomendo artigo de método agora. A alegação central ("o TFT com Richards melhora a previsão") tem evidência contrária.

**Artigo coletivo do IMDC.** [F] As instruções preveem "technical reports and scientific publications" (seção 8). A edição de 2024 gerou artigo coletivo (medRxiv, doi:10.1101/2025.05.12.25327419; versão na PNAS segundo fontes secundárias, DOI não localizado; a verificar). [O] Perguntar ao Flávio se há artigo coletivo de 2026, qual descrição do modelo entra e se há restrição a publicar antes.

### Periódicos e eventos candidatos

Todos os requisitos e prazos abaixo estão **a verificar** nas páginas oficiais.

| Destino | Por que cabe | Risco | Prazo |
|---|---|---|---|
| medRxiv / arXiv (stat.AP, cs.LG) | Sem barreira; fixa a data | Nenhum | Contínuo |
| Royal Society Open Science | Publicou o Episcanner (doi:10.1098/rsos.241261); aceita resultado negativo sólido | Taxa de publicação | Contínuo |
| Epidemics | Público de previsão epidemiológica | Pede contribuição epidemiológica clara | Contínuo |
| PLOS Computational Biology | Tradição em avaliação de previsões (WIS) | Exige novidade de método; resultado negativo é difícil | Contínuo |
| Infectious Disease Modelling | Edição especial sobre modelagem guiada por dados; prazo de 1º de novembro de 2026 já passou | Verificar se houve extensão | Contínuo fora da edição |
| Tropical Medicine and Infectious Disease (MDPI) | Edição especial sobre vigilância sensível ao clima, prazo 31 de dezembro de 2026 | Prestígio menor | 2026-12-31 |
| SBCAS 2027 (SBC) | Evento brasileiro de computação em saúde; já publicou GNN para dengue em capitais | Artigo curto | A verificar; submissões costumam fechar no primeiro trimestre |
| International Journal of Forecasting | Casa do TFT original; interesse em avaliação probabilística | Público menos epidemiológico | Contínuo |

### Estrutura do preprint

| Seção | Conteúdo | Figuras e tabelas |
|---|---|---|
| 1. Introdução | O IMDC, a tarefa de temporada inteira, a pergunta: um modelo profundo de descritores supera climatologias? | — |
| 2. Dados | Fontes, cortes, safras contra dados revisados | T1: variáveis por versão e disponibilidade no corte |
| 3. Método | Alvos, Richards, TFT, Monte Carlo, cópula, baselines B1 a B3 | F1: esquema corte → descritores → curva → agregação |
| 4. Protocolo | Origem móvel, métrica primária, regra do `rho`, o que foi fixado antes e o que não foi | T2: linha do tempo das decisões e o que cada uma viu |
| 5. Resultados primários | WIS relativo, razão oficial, posição | T3: tabela de A1; F2: razão por temporada com variação entre sementes |
| 6. Diagnóstico | Componentes, cobertura, por horizonte, por intensidade; total contra forma | F3: componentes do WIS; F4: WIS por horizonte; F5: previsto contra observado do total por temporada |
| 7. Calibração | A, B, C; conflito entre cobertura e WIS relativo | T4: cobertura e razão por variante; F6: WIS médio contra razão geométrica |
| 8. Discussão | Limite de informação na magnitude; o que o Richards impõe; o que faria diferença | — |
| 9. Limitações | C1 a C4, I1 a I3 | — |
| Suplemento | Tabelas por UF, PIT, lista de ajustes refeitos | — |

### Plano de escrita

| Semana | Entrega | Critério de pronto |
|---|---|---|
| 1 | Repositório versionado; scripts exploratórios refeitos | `git status` limpo; um comando regenera cada tabela |
| 1–3 | 5 sementes de v2 e v3 em 10 cortes (HPC) | Tabela com média e desvio entre sementes |
| 2 | Tabelas por horizonte e região; permutação de sinais | CSVs em `reports/` |
| 2–3 | Revisão bibliográfica (A5) | Matriz de extração preenchida e verificada |
| 3 | Seções 2 a 4 e 9 | Revisão sua |
| 4 | Seções 5 a 7 com os números finais | Cada número do texto rastreável a um CSV |
| 5 | Introdução, discussão, resumo; envio aos orientadores | — |
| 6 | Preprint | — |

---

## A5. Revisão bibliográfica

### Lacunas por seção

| Seção | Lacuna | Pergunta |
|---|---|---|
| Introdução | Estado da previsão de dengue de temporada inteira | Que antecedência e que habilidade os estudos relatam para previsão sazonal, e contra qual baseline? |
| Introdução | Lições dos desafios | O que os desafios de dengue (NOAA 2015, IMDC 2024 e 2025) concluíram sobre ensembles e baselines? |
| Método | Híbridos paramétricos | Quem já previu parâmetros de curvas epidêmicas (Richards, logística, SIR) com redes neurais? |
| Método | TFT em arboviroses | Onde o TFT foi usado em dengue, com que horizonte e que avaliação probabilística? |
| Protocolo | Avaliação | Como comparar previsões com poucas temporadas; WIS relativo; testes pareados |
| Calibração | Conformal em epidemiologia | Há relatos de calibração conformal piorando scores relativos? |
| Roadmap | GNN espaço-temporal em dengue | Quais grafos (adjacência, mobilidade) deram ganho, e em que horizonte? |
| Roadmap | Redes topológicas | Há aplicação de redes simpliciais ou celulares a previsão epidemiológica? |
| Roadmap | Modelos de fundação | Como se saem em séries epidêmicas, com que cuidado contra vazamento de pré-treino? |

### Ponto de partida (tudo a verificar; não li as fontes)

- Araujo et al. 2025, Episcanner, *R. Soc. Open Sci.* doi:10.1098/rsos.241261; arXiv:2407.21286.
- IMDC 2024, "Leveraging probabilistic forecasts for dengue preparedness and control", medRxiv doi:10.1101/2025.05.12.25327419. Relatórios dos sprints: Zenodo doi:10.5281/zenodo.13929005 e https://zenodo.org/records/17516518.
- Johansson et al. 2019, desafio aberto de dengue, *PNAS* doi:10.1073/pnas.1909865116.
- Mosqlimate, arXiv:2410.18945.
- Lim et al. 2021, TFT, *Int. J. Forecast.* doi:10.1016/j.ijforecast.2021.03.012.
- Bracher et al. 2021, WIS, *PLoS Comput. Biol.* doi:10.1371/journal.pcbi.1008618.
- Wang, Wu, Yang 2012, Richards e SIR, *J. Theor. Biol.* doi:10.1016/j.jtbi.2012.07.024.
- Romano, Patterson, Candès 2019, regressão quantílica conformal, arXiv:1905.03222.
- Chen e Moraga 2025, LSTM com mobilidade para dengue no Brasil, medRxiv doi:10.1101/2025.03.02.25323168.
- "Previsão de Casos de Dengue em Capitais Brasileiras com Redes Neurais Espaço-Temporais em Grafos", SBCAS, https://sol.sbc.org.br/index.php/sbcas_estendido/article/view/43841.
- TFT para malária e dengue (África do Sul e Vietnã), *IJERPH* 23(1):75, https://www.mdpi.com/1660-4601/23/1/75.
- Su et al. 2026, "How (Not) to Hybridize Neural and Mechanistic Models for Epidemiological Forecasting", arXiv:2602.06323.
- "Forecasting Seasonal Influenza Epidemics with Physics-Informed Neural Networks", arXiv:2506.03897.
- EpiCastBench, arXiv:2605.11598; "Foundation time series models for forecasting and policy evaluation in infectious disease epidemics", medRxiv doi:10.1101/2025.02.24.25322795; "Zero-shot forecasting of epidemics", workshop NeurIPS 2025, https://neurips.cc/virtual/2025/130450.
- Redes topológicas: Hajij et al., arXiv:2206.00606; ModernSASST, arXiv:2604.15833; TopoPrimer, arXiv:2605.15035.

### Strings de busca

Bases: PubMed, Scopus ou Web of Science, arXiv, medRxiv, SciELO, SBC OpenLib. Período: 2015 a 2026.

1. `dengue AND (forecast* OR predict*) AND (seasonal OR "season-ahead" OR "long-lead" OR "months ahead") AND (probabilistic OR interval OR "weighted interval score" OR CRPS)`
2. `dengue AND ("temporal fusion transformer" OR transformer OR "deep learning") AND forecast* AND (Brazil OR municipality OR state)`
3. `(Richards OR logistic OR "growth curve" OR "epidemic curve") AND (parameter* NEAR/5 (predict* OR learn*)) AND ("neural network" OR "deep learning") AND epidemic`
4. `dengue AND ("graph neural network" OR "spatio-temporal graph" OR GCN OR "graph attention") AND forecast*`
5. `("simplicial" OR "cell complex" OR "hypergraph" OR "topological deep learning") AND ("spatio-temporal" OR forecast*) AND (epidemic OR disease OR traffic)`
6. `("foundation model" OR Chronos OR TimesFM OR Moirai OR TiRex OR Toto) AND (epidemic OR "infectious disease" OR dengue OR influenza) AND forecast*`
7. `(conformal OR recalibrat*) AND (epidemic OR "infectious disease") AND forecast* AND (coverage OR "interval score")`
8. `("forecast evaluation" OR "forecast comparison") AND (epidemic OR "forecast hub") AND ("small sample" OR "few seasons" OR "Diebold-Mariano" OR permutation)`

### Critérios

- **Inclusão:** previsão fora da amostra de incidência de dengue ou de arbovirose próxima; horizonte ≥ 4 semanas; comparação com pelo menos um baseline; revisado por pares ou preprint com código ou dados. Para as lacunas de método (3, 5, 6, 7, 8), qualquer doença ou domínio.
- **Exclusão:** só ajuste dentro da amostra; só classificação de surto sem contagem; sem DOI, PMID ou identificador arXiv; revisões narrativas sem dados (guardar à parte, como contexto).

### Matriz de extração

Uma linha por estudo: identificador (DOI, PMID ou arXiv) · ano · país e escala espacial · doença · horizonte · alvo (semanal, total, pico) · modelo · variáveis · esquema de validação (origens, temporadas) · baselines · métrica · resultado contra o melhor baseline, com número · dados na data real ou revisados · código disponível · observação sobre vazamento · quem extraiu · quem verificou.

### Prompts autocontidos para agentes

**Prompt 1 — Busca e extração** (um agente por string; trocar `<STRING>` e `<LACUNA>`)

```
Tarefa: revisão bibliográfica sobre <LACUNA>. Trabalhe só com o que encontrar e abrir; não use memória.

1. Rode a busca "<STRING>" no PubMed, no arXiv, no medRxiv e no Google Scholar, restrita a 2015–2026.
   Registre, por base, a string exata usada e o número de resultados.
2. Triagem pelo título e resumo. Critérios de inclusão: previsão fora da amostra; horizonte de 4 semanas ou mais
   (para temas de método, qualquer horizonte); pelo menos um baseline de comparação. Exclua estudos só de ajuste
   dentro da amostra e os sem identificador.
3. Para cada estudo incluído (máximo 25, os mais relevantes), ABRA o texto ou o resumo na página do DOI e preencha:
   identificador (DOI, PMID ou arXiv) | ano | país e escala | doença | horizonte | alvo | modelo | variáveis |
   validação (número de origens e temporadas) | baselines | métrica | resultado contra o melhor baseline, com número |
   dados em tempo real ou revisados | código disponível (URL) | trecho literal de até 15 palavras que sustenta o resultado.
4. Regras obrigatórias:
   - Todo estudo precisa de DOI, PMID ou identificador arXiv que você abriu e conferiu. Sem identificador, não entra.
   - Não invente número, autor, periódico ou ano. Campo que você não leu recebe "não lido".
   - Marque em cada linha: "texto completo lido", "só resumo lido" ou "só metadados".
5. Entregue: (a) tabela em Markdown; (b) lista dos excluídos, com o motivo; (c) três frases sobre o que a literatura
   diz a respeito de <LACUNA>, cada uma apontando para linhas da tabela.
```

**Prompt 2 — Verificação independente** (agente diferente, sem acesso ao raciocínio do primeiro)

```
Tarefa: verificar uma tabela de extração bibliográfica feita por outra pessoa. Suponha que ela pode conter erros
e referências inexistentes.

Entrada: a tabela abaixo.
<TABELA>

Para cada linha:
1. Resolva o identificador em https://doi.org/<DOI>, em https://pubmed.ncbi.nlm.nih.gov/<PMID>/ ou em
   https://arxiv.org/abs/<ID>. Se não resolver, marque "IDENTIFICADOR INVÁLIDO".
2. Confira título, primeiro autor, ano e periódico contra a página aberta. Divergência: marque "METADADOS DIVERGEM"
   e escreva o valor correto.
3. Procure na página (resumo ou texto) o resultado numérico e o trecho literal citados. Marque "CONFIRMADO",
   "NÃO ENCONTRADO" ou "CONTRADITO", copiando o trecho que você viu.
4. Não corrija por suposição. Se não conseguiu abrir a fonte, marque "NÃO VERIFICÁVEL".

Entregue: a tabela com uma coluna "verificação" e um resumo com a contagem de cada marca.
Linhas que não estejam "CONFIRMADO" não podem ser citadas no artigo.
```

**Prompt 3 — Síntese por seção** (só depois da verificação)

```
Entrada: tabela verificada, apenas as linhas "CONFIRMADO".
<TABELA>

Escreva, em português, um parágrafo de trabalhos relacionados para a seção "<SEÇÃO>" de um artigo sobre previsão
de dengue de temporada inteira no Brasil. Regras: cada afirmação cita o identificador entre colchetes; nenhuma
afirmação sem linha correspondente na tabela; relate os resultados com os números da tabela; ao final, liste em
uma frase o que a literatura NÃO responde. Não elogie nem critique os estudos além do que os números mostram.
```

---

# Parte B — Roadmap

## B1. Crítica da sequência GNN → TFT → atenção/convolução → TNN

### O problema que a sequência não ataca

- [F] O erro é dominado pela subprevisão da magnitude (A1). Trocar a forma do TFT pela do B3 melhora; trocar o total piora (`resultados_fase1.md:68-74`).
- [F] A previsão sai na EW25 e cobre da EW41 à EW40 seguinte: 16 a 68 semanas de antecedência (instruções, seção 4).
- [I] Grafos espaciais capturam propagação entre vizinhos, que opera em semanas. A 4 a 16 meses, o que decide a magnitude é o que ainda não aconteceu: sorotipo circulante, imunidade acumulada, clima do verão. A adjacência informa pouco sobre isso. O que o espaço pode dar a essa distância é outra coisa: **suavização** de alvos ruidosos por agrupamento e **memória regional** de suscetíveis (o vizinho teve epidemia grande no ano passado).
- [O] A sequência proposta aumenta a capacidade do modelo. A evidência diz que falta informação e sobra variância. A ordem deveria ser: informação e alvo primeiro, arquitetura depois.

### Riscos concretos

| Risco | Mecanismo | Evidência no material | Mitigação |
|---|---|---|---|
| Poucos ciclos independentes | 1 milhão de janelas de treino, mas só 15 temporadas; municípios da mesma temporada compartilham sorotipo e clima. Há 13 janelas quase idênticas por alvo (EW20 a EW32) | `v3_train.log:5`; `common.py:56`; `val_loss` oscila de 2,2 a 5,9 entre cortes | Contar o tamanho efetivo em temporadas; regularizar para a climatologia; não ler o `val_loss` de uma temporada como sinal |
| Mais variáveis, pior resultado | Cada variável nova tem 15 realizações sazonais para mostrar efeito | v3 → v4: 1,005 → 1,171 | Blocos, uma entrada por vez, com sementes (B2) |
| Vazamento espacial | Embeddings ou normalizações de grafo calculados com a série inteira; mensagem de vizinhos com dados posteriores ao corte | `graph_embedding.py` usa só a adjacência, que é estática: sem vazamento hoje | Tudo que depender de casos (pesos de aresta, mobilidade estimada) calculado por corte |
| Agregação que mascara o ganho | A UF é soma de municípios; o `rho` da cópula já absorve a correlação intraestadual | `rho` escolhido entre 0,8 e 1,0 em quase todos os cortes (`reports/v3_calib/rho_by_cut.csv`) | [I] `rho` perto de 1 indica que um fator comum por UF explica quase tudo; uma GNN municipal precisa superar isso |
| Atraso de notificação | O encoder do retrospecto vê as últimas semanas completas; o da produção, não | C3 | Safras ou truncamento simulado antes de qualquer arquitetura nova |
| Não estacionariedade | Troca de sorotipo, vacinação a partir de 2024, expansão para o Sul, pandemia em 2020/21 | 2023/24: 6,9 milhões observados contra cerca de 0,5 milhão previsto | Variáveis de sorotipo e imunidade; aceitar que parte é imprevisível e calibrar a cauda |
| Pico único do Richards | Temporadas com dois picos ou platô; soma estadual de curvas com picos diferentes | Pico restrito a 5–35 no reajuste (`preprocess_v3.py:103`); 73% das formas imputadas | Teste do oráculo (B3) |
| Complexidade sem ablação | GNN + TFT + atenção + convolução + TNN em sequência, sem medir cada parte | v3 e v4 já sofrem disso (I8) | Um módulo por vez (B6) |
| Custo | v4: 46 horas para 12 cortes, uma semente, GPU local | `v4_train.log` | Orçamento em B6 |

### Sobre "GNN seguida de TFT, com atenção e convolução"

- [I] O TFT já tem atenção temporal e seleção de variáveis. Somar convolução temporal e atenção espacial sem hipótese sobre o que cada uma captura é busca de arquitetura com 10 pontos de avaliação.
- [O] Desenho mínimo defensável: um codificador espacial que produz, por município e semana, um resumo da vizinhança (uma ou duas camadas de convolução de grafo sobre incidência e acumulado), entregue ao TFT como variável observada. Isso isola a pergunta: a vizinhança ajuda? A resposta barata vem antes, com defasagens espaciais calculadas à mão (B6, Fase 2).

---

## B2. Plano de dados e variáveis

### Catálogo

Prioridade por valor esperado para o problema dominante (magnitude da temporada) dividido pelo custo. Fontes externas e suas defasagens estão a verificar. Pela regra do desafio, dado extra precisa ser aberto, atualizável e cobrir todos os estados [F: instruções, seção 2].

| # | Variável | Fonte | Resolução | Defasagem na EW25 | Custo | Prioridade | Racional |
|---|---|---|---|---|---|---|---|
| 1 | Imunidade acumulada: incidência acumulada em 2, 3 e 5 temporadas, própria e da região | Derivada dos casos | Município, anual | Nenhuma | Baixo | **Alta** | Proxy de suscetíveis; atua na escala de anos, que é a do problema |
| 2 | Defasagens espaciais: incidência da última temporada nos vizinhos e na região de saúde | Derivada + `adjacencia_edges.csv` | Município | Nenhuma | Baixo | **Alta** | Testa o valor do grafo sem GNN |
| 3 | Previsão de ENSO (probabilidade de El Niño no verão) | IRI/CPC | Global, mensal | Emissão de junho | Baixo | **Alta** | Única informação climática que alcança fev-mai |
| 4 | Sorotipo predominante e troca recente | Ministério da Saúde (vigilância laboratorial) | UF, anual ou mensal | Meses; cobertura desigual | Médio a alto | **Alta se existir aberta** | Candidata mais forte para 2023/24; risco de não cumprir a regra de dados |
| 5 | Previsão sazonal de mais longo alcance | C3S, SEAS5 | Grade, 6 a 7 meses | Emissão de junho | Médio | Média | Estende pouco além do que já há |
| 6 | Cobertura vacinal (Qdenga) | Ministério da Saúde | Município, 2024+ | Meses | Médio | Média | Série curta; efeito pequeno até aqui |
| 7 | Mobilidade pendular e hierarquia urbana | IBGE (Censo, REGIC) | Par de municípios, estática | Nenhuma | Médio | Média | Arestas melhores que adjacência; só vale se o item 2 der sinal |
| 8 | Fluxo aéreo | ANAC | Aeroporto, mensal | 1 a 2 meses | Médio | Baixa | Importação entre regiões; efeito de semanas |
| 9 | Infestação (LIRAa) | Ministério da Saúde | Município, irregular | Irregular | Alto | Baixa | Cobertura incompleta; provavelmente fora da regra |
| 10 | Socioeconômicas (saneamento, densidade, altitude) | Censo 2022 | Município, estática | Nenhuma | Baixo | Baixa | O modelo já tem efeito fixo por município via escalas do alvo |
| 11 | Já no v3: clima estendido, índices oceânicos, chikungunya, Afya | FTP | — | — | Zero | **Reavaliar** | Entraram juntas, sem ablação |

### Contra "o máximo de variáveis"

[O] Regras, a fixar no protocolo antes de rodar:

1. **Blocos, não variáveis.** Agrupar por mecanismo (imunidade, espaço, clima realizado, clima previsto, sinais digitais) e testar bloco a bloco.
2. **Ordem fixada antes**, pela tabela acima.
3. **Critério de entrada.** O bloco fica se melhorar a métrica primária, na média das sementes, em mais que um desvio-padrão entre sementes, e não piorar em mais de 6 das 10 temporadas.
4. **Critério de saída.** Depois de montar o conjunto, retirar cada bloco uma vez. O que não fizer falta sai.
5. **Triagem barata primeiro.** Para o total da temporada, gradient boosting quantílico com os mesmos blocos roda em minutos. Bloco que não ajuda ali dificilmente ajuda no TFT.
6. **Pesos de seleção do TFT não são evidência.** Importância por permutação entre temporadas, sim.
7. **Encolhimento para a climatologia.** Prever o desvio em relação ao B3 em vez do nível. Com 15 temporadas, a hipótese nula certa para cada variável é "não muda nada".

---

## B3. Papel do Richards

### Interpretações possíveis do "plano paramétrico"

Não recebi o plano. O material sustenta quatro leituras:

| # | Papel | Como seria | Estado hoje |
|---|---|---|---|
| a | **Decodificador**: a rede prevê os parâmetros e a curva sai da fórmula | É o que o v2, o v3 e o v4 fazem | [F] Implementado |
| b | **Estrutura prévia**: a rede prevê casos semanais, com penalidade ou base de Richards (resíduo sobre a curva) | Decoder de 52 passos; Richards como média a priori | Não existe |
| c | **Covariável**: parâmetros ajustados de temporadas passadas (ou seus quantis) entram como entrada | B3 como variável de entrada | Parcial: as escalas do alvo já carregam média e desvio por município (`common.py:177`) |
| d | **Baseline**: só o B3 | Climatologia de parâmetros | [F] Implementado |

### O que a evidência já diz

- [F] A forma prevista pelo TFT v2 piora o resultado; a forma do B3 é melhor (`resultados_fase1.md:68-74`).
- [F] O MAE do pico é de quase 5 semanas tanto no B3 quanto no TFT (`resultados_fase1.md:87-88`).
- [I] Os três parâmetros de forma, a essa antecedência, são quase imprevisíveis além da climatologia local. O papel (a), com forma aprendida, gasta três das quatro saídas num alvo sem sinal e com 73% de rótulos imputados.
- [O] Hipótese de trabalho: Richards como (d) para a forma e a rede só para o total (e talvez para o deslocamento do pico). É o `v3total_b3forma`, que já existe como exploratório.

### Testes que decidem

| Teste | Pergunta | Resultado que decide | Custo |
|---|---|---|---|
| **T1. Oráculo** | Com os parâmetros ajustados reais e o total observado, qual é o WIS da reconstrução? | Se o oráculo, nas UFs, não ficar bem abaixo do B2, a forma paramétrica é o teto e (b) passa a valer a pena | Minutos; sem treino |
| **T2. Pico único** | Que fração dos casos está em temporadas com ajuste ruim (R² < 0,95) ou com dois picos? | Acima de 20% dos casos: Richards de um pico é inadequado para UFs grandes; testar soma de duas curvas | Minutos |
| **T3. Total direto** | Gradient boosting quantílico só para o total, com forma do B3, contra TFT total + forma do B3 | Se empatar, o TFT não se justifica para o total | Horas |
| **T4. Curva direta** | TFT com decoder semanal (sem Richards) contra o papel (a) | Se a curva direta ganhar com folga maior que a variação entre sementes, Richards vira só baseline | 1 a 2 dias de GPU |
| **T5. Dependência entre parâmetros** | Sortear os parâmetros com a correlação empírica em vez de independentes | Mudança de cobertura acima de 5 pontos: corrigir o sorteio | Minutos |
| **T6. Desvio da climatologia** | Alvo = desvio em relação ao quantil do B3 | Se reduzir a variância entre sementes sem perder WIS, adotar | 1 dia de GPU |

T1 e T2 vêm primeiro: são baratos e definem se o resto do roadmap mantém o Richards no centro.

---

## B4. Modelos de fundação de séries temporais

### Panorama (novembro de 2026; fontes secundárias, a verificar nos cartões dos modelos)

| Modelo | Origem | Estado | Covariáveis | Licença | Nota |
|---|---|---|---|---|---|
| Chronos-2 | Amazon | 120 milhões de parâmetros, só codificador | Passadas e futuras; multivariado | Aberta (a verificar) | Saída em quantis |
| TimesFM 2.5 / TimesFM-3 | Google | O 3 teria saído em 31 de agosto de 2026, com 330 milhões de parâmetros | O 3: passadas e futuras | Pesos do 3 com licença não comercial | Conferir se a licença atende à exigência de reprodutibilidade do desafio |
| Moirai 2.0 | Salesforce | Só decodificador (arXiv:2511.11698) | Univariado na versão 2.0 (a verificar) | Aberta (a verificar) | |
| Toto 2.0 | Datadog | Maio de 2026; de 4 milhões a 2,5 bilhões de parâmetros | Multivariado | Apache 2.0 | Treinado sobretudo em telemetria |
| TiRex / TiRex-2 | NXAI | xLSTM, 35 milhões; o 2 aceita covariáveis | O 2: passadas e futuras | A verificar | Bom em zero-shot num estudo com epidemias |
| Lag-Llama | — | 2023–2024; superado nos comparativos recentes (a verificar) | Não | Aberta | Só como referência histórica |
| TimeGPT | Nixtla | API fechada | Sim | Fechada | Fora: não reprodutível |

Em séries epidêmicas (a verificar): EpiCastBench (arXiv:2605.11598) aponta TimesFM e Chronos-2 com os menores erros medianos, e modelos clássicos ganhando em séries curtas e com muitos zeros; medRxiv doi:10.1101/2025.02.24.25322795 relata bom desempenho sem retreino. Nenhuma das fontes que vi reporta WIS.

### Onde entram

| Uso | Como | Opinião |
|---|---|---|
| **Baseline zero-shot** | 26 UFs e 15 cidades, contexto até a EW25, horizonte de 68 semanas, quantis diretos | **Fazer primeiro.** Barato, e responde se o TFT próprio faz sentido |
| Com covariáveis | Chronos-2 ou TiRex-2 com semana da temporada e previsão climática | Segundo passo, só se o zero-shot for competitivo |
| Ajuste fino | Nas séries de UF e de município | Só com go; alto risco de sobreajuste com 15 temporadas |
| Extrator de representações | Embedding da série como entrada do modelo do total | Especulativo; baixa prioridade |
| Membro de ensemble | Média de quantis com B2, B3 e TFT | Provável melhor uso |

### Dois cuidados

1. **Horizonte.** [I] Esses modelos foram treinados sobretudo para horizontes curtos, e 68 semanas pode exceder o horizonte nativo de alguns (a verificar). Em previsão autorregressiva longa, a incerteza tende a degenerar.
2. **Vazamento de pré-treino.** [I] Modelos lançados em 2025 e 2026 podem ter visto séries públicas de dengue do Brasil até 2024 ou 2025. A avaliação retrospectiva não é limpa para eles. A comparação honesta é a temporada 2026/27, prospectiva; no retrospecto, declarar o risco e comparar com a climatologia, que também "conhece" a história.

### Go / no-go

- **Go para covariáveis e ensemble:** zero-shot com WIS relativo ao B3 ≤ 1,05 nas UFs nas 10 temporadas e cobertura de 90% ≥ 75%.
- **Go para ajuste fino:** a versão com covariáveis melhora o zero-shot em mais que a variação entre temporadas (teste de permutação de sinais, p < 0,1).
- **No-go:** zero-shot acima de 1,20, ou intervalos que explodem depois de 30 semanas. Fica só como linha de tabela.
- **Em qualquer caso:** se o zero-shot empatar com o TFT v3, isso entra no artigo.

---

## B5. Rede neural topológica

### O que "seguindo a mesma ideia" pode significar

| Construção | Células | O que acrescenta à GNN |
|---|---|---|
| **Complexo de cliques** sobre a adjacência | Nós, arestas, triângulos de municípios mutuamente vizinhos | Pouco: num grafo planar de fronteiras, triângulos são abundantes e não têm significado epidemiológico próprio |
| **Complexo celular ou combinatório administrativo** | Município ⊂ região de saúde ⊂ macrorregião ⊂ UF como células de ordem crescente | Mensagens entre níveis da hierarquia; é a estrutura que os dados já têm (`map_regional_health.csv`) e é a agregação que o desafio pontua |
| **Hipergrafo de mobilidade** | Hiperaresta = região de influência de um polo (REGIC) ou área metropolitana | Interação de grupo: um polo que sincroniza seus satélites |
| **Sinais em arestas** (Laplaciano de Hodge) | Fluxos de mobilidade como sinal na aresta | Separa componentes de gradiente e de circulação do fluxo; exige dado de fluxo |

- [O] A leitura mais útil aqui é a **hierarquia administrativa como complexo combinatório**: é a única em que a célula de ordem superior tem significado e alvo observado (a UF).
- [F] As variáveis de TDA (persistência H0/H1) já foram testadas e abandonadas (`tft_config.json:19-22`; `README.md:155-156`). [I] Persistência como variável e rede topológica são coisas diferentes; o abandono da primeira não diz nada sobre a segunda, mas mostra que topologia por si não trouxe sinal antes.

### O que ganharia sobre a GNN

- [I] Uma GNN com agregação por região (pooling hierárquico) já aproxima o complexo administrativo. O ganho específico da rede topológica seria capturar efeitos que não se decompõem em pares: o comportamento do grupo não é a soma das influências par a par.
- [I] Em epidemiologia, o candidato é a sincronização por polo: quando o polo regional tem epidemia, todos os satélites têm, independentemente da adjacência entre eles.

### Experimento que mostra se há interação de ordem superior

Antes de treinar qualquer rede topológica:

1. **Resíduo de grupo.** Ajustar, por temporada, o desvio do total municipal em relação à climatologia com (i) médias dos vizinhos par a par e (ii) (i) mais o termo de grupo (média da região de saúde, do polo). Se (ii) não reduzir o erro fora da amostra, entre temporadas, não há estrutura de ordem superior a explorar.
2. **Controle por permutação.** Se (ii) ajudar, repetir com as células embaralhadas (mesmos tamanhos, municípios trocados dentro da UF). Se o ganho persistir com células aleatórias, é efeito de suavização, que uma GNN com pooling também captura. Não é topologia.
3. **Só então** comparar a rede topológica com a GNN, com o mesmo número de parâmetros e as mesmas variáveis.

### Critério de parada

- **Não começar** se a GNN (Fase 3) não superar o TFT com defasagens espaciais.
- **Não começar** se o passo 1 não mostrar ganho, ou se o passo 2 mostrar que células aleatórias dão o mesmo.
- **Parar** se, com 5 sementes, a rede topológica não superar a GNN de mesmo tamanho em mais que um desvio-padrão entre sementes na métrica primária.
- [O] Probabilidade subjetiva de a rede topológica passar nos três: baixa, da ordem de 10% a 20%. Vale como capítulo exploratório de dissertação, não como aposta para o próximo desafio.

---

## B6. Desenho experimental

### Protocolo congelado

Escrever em `docs/` e registrar com data antes da Fase 1.

- **Desenvolvimento:** cortes de 2015 a 2025. Todos já foram vistos.
- **Confirmatório A:** temporada 2026/27, prospectiva, pontuada quando fechar (EW40/2027). As previsões de cada candidato são geradas e depositadas agora (hash e data).
- **Confirmatório B:** chikungunya, UFs e as 10 cidades do desafio, com o mesmo pipeline e sem ajuste de hiperparâmetros. Os dados já estão em `data/raw/` e nunca foram usados como alvo [F: `preprocess_v3.py:35-39` usa só como variável].
- **Métrica primária:** WIS relativo ao B3 nas UFs, como hoje. **Secundárias:** razão oficial, cobertura de 50%, 80%, 90% e 95%, WIS por horizonte, MAE do log do total.
- **Sementes:** 5 por configuração; reportar média e desvio.
- **Comparação:** permutação de sinais sobre o log da razão por temporada, com bootstrap ao lado. Diferença só é "ganho" se superar o desvio entre sementes e tiver p < 0,1; com 10 temporadas, declarar o poder.
- **Dados:** os mesmos do envio ao IMDC como base; cada bloco novo entra como variante nomeada.
- **Registro:** uma linha por experimento num CSV (configuração, semente, commit, métricas), inclusive os que falharem.

### Fases

| Fase | Conteúdo | Depende de | Critério de pronto verificável | Esforço seu | GPU |
|---|---|---|---|---|---|
| **0. Base** | Versionar tudo; refazer tabelas exploratórias; 5 sementes de v2 e v3; por horizonte e região; permutação | — | Um comando regenera cada tabela; desvio entre sementes medido | 1 semana | ~200 h local, ou ~80 h na A100 (estimativa) |
| **1. Diagnóstico sem rede** | T1, T2 e T5 do Richards; baselines (SARIMA, boosting do total, ensemble B2+B3); normalizador sem a temporada da amostra; atraso de notificação simulado | 0 | Tabela com o teto do oráculo; decisão escrita sobre o papel do Richards | 1 a 2 semanas | < 20 h |
| **2. Informação** | Blocos 1 a 3 do catálogo (imunidade, defasagens espaciais, previsão de ENSO), primeiro em boosting, depois no TFT; Moran dos resíduos por temporada | 1 | Cada bloco com entrada ou saída decidida pelo critério de B2 | 2 semanas | ~150 h |
| **2b. Modelos de fundação** (em paralelo) | Zero-shot de 2 ou 3 modelos nas UFs e cidades | 0 | Linha na tabela primária; decisão go/no-go | 3 dias | < 10 h |
| **3. GNN** (condicional) | Codificador espacial mínimo antes do TFT | 2 com sinal espacial | Supera o TFT com defasagens espaciais pelo critério do protocolo | 3 a 4 semanas | ~300 h |
| **4. Rede topológica** (condicional) | Passos 1 e 2 de B5; depois a rede | 3 com ganho | Critérios de B5 | 4 semanas ou mais | ~300 h |
| **5. Ensemble e artigo 2** | Combinação dos que passaram; confirmatório B; depósito das previsões 2026/27 | 2, 2b | Previsões depositadas; chikungunya pontuada uma única vez | 2 semanas | < 20 h |

**Condição de entrada na Fase 3:** resíduos com autocorrelação espacial além do fator comum por UF (Moran significativo em pelo menos 7 das 10 temporadas depois de remover a média da UF) **e** ganho das defasagens espaciais na Fase 2. Sem as duas, pular para a Fase 5.

### Orçamento computacional

- [F] v3: cerca de 2 horas por corte com 25 épocas; 12 cortes em 22 horas (`v3_train.log`, de 2026-11-05 00:48 a 22:40). v4: 5 horas por corte com 50 épocas; 12 cortes em 46 horas (`v4_train.log`).
- [F] `num_workers=0` em todos os treinos (`run_v3.sh:5`). [I] No Windows, o carregamento de dados provavelmente limita a GPU; no HPC, com vários processos de carga, o tempo por corte deve cair bastante. Medir um corte antes de planejar.
- [I] Uma configuração completa (10 cortes × 5 sementes) custa cerca de 100 horas de GPU local no regime do v3. O roadmap inteiro, com as fases condicionais, fica na ordem de 1.000 horas locais; sem as condicionais, cerca de 400.
- [O] Reduzir o custo por experimento antes de multiplicar experimentos: uma janela por alvo em vez de 13 (ou 3), e triagem em boosting.

---

## B7. Decisões, delegação, riscos e perguntas

### B7.1 Decisões suas

1. **Tese do primeiro artigo:** decidido em 2026-11-14, esperar um resultado positivo (minha recomendação era resultado negativo com diagnóstico). Falta fixar a data-limite da regra de parada.
2. **Tratar 2015–2025 como desenvolvimento** e aceitar que a confirmação só vem em 2027 ou por chikungunya.
3. **Papel do Richards** depois de T1 e T2: decodificador, só forma climatológica, ou baseline.
4. **GNN e rede topológica condicionais** aos testes baratos, ou objetivos de formação independentes do resultado. Se a dissertação exige a rede topológica, o enquadramento muda: vira estudo exploratório com critério de parada, não aposta de desempenho.
5. **Dados externos** (sorotipo, vacinação) e a regra de dados abertos do desafio.
6. **Onde publicar** e se o preprint sai antes do artigo coletivo do IMDC.

### B7.2 Tarefas delegáveis a modelos menores

Cada prompt é autocontido. Entregue-os com o repositório aberto.

**D1 — Tabela por horizonte**

```
Repositório: Pattern-Blue. Leia src/rolling_eval.py e src/evaluate_v3.py para entender o formato dos scores.
Os scores semanais estão em src/outputs/rolling/scores/*.parquet (colunas: unit, date, casos, pred, wis, dispersion,
under, over, cov50, cov80, cov90, cov95, model, cut_year, level, rho).
Tarefa: criar src/report_by_horizon.py que
1. carrega os scores e aplica a mesma seleção de rho de rolling_eval.load_selected();
2. calcula o horizonte em semanas desde o corte EW25 do cut_year (use common.cut_date);
3. agrupa em blocos de 8 semanas e, para cut_year de 2015 a 2024, salva em reports/rolling/by_horizon.csv:
   level, model, bloco, WIS médio, WIS relativo ao b3 (média geométrica de (wis+1)/(wis_b3+1) por unidade-temporada),
   cobertura de 50/80/90/95.
Não altere nenhum arquivo existente. Não retreine nada. Rode o script e mostre a tabela.
Verificação: a média ponderada dos blocos precisa reproduzir reports/rolling/components_coverage.csv com erro
menor que 0,5%. Mostre essa conferência.
```

**D2 — Teste de permutação de sinais**

```
Repositório: Pattern-Blue. Em src/rolling_eval.py, a função relative_table calcula o log da razão de WIS por
temporada (variável `by`) e um IC por bootstrap.
Tarefa: criar src/sign_permutation.py que, para cada nível e modelo, pega esse vetor de 10 valores por temporada
e calcula (a) o p-valor bilateral exato do teste de permutação de sinais (2^10 combinações, estatística = média),
(b) o p-valor de Wilcoxon pareado (scipy.stats.wilcoxon). Salve em reports/rolling/significance.csv.
Não altere rolling_eval.py; importe as funções dele. Mostre a tabela e confirme que a coluna wis_rel coincide
com reports/rolling/relative_wis.csv.
```

**D3 — Oráculo do Richards (T1)**

```
Repositório: Pattern-Blue. Leia src/imdc_submission.py (weekly_curves), src/common.py (season_targets_for_cut)
e src/rolling_eval.py (score_frame, load_truth).
Tarefa: criar src/oracle_richards.py. Para cada temporada de 2015/16 a 2024/25:
1. pegue de data/processed/season_targets_v3.parquet os parâmetros REAIS da própria temporada (obs_total, alpha,
   beta, peak_idx), só municípios com has_fit; para os demais use o total observado e a forma imputada como em
   season_targets_for_cut, mas calculada com as temporadas anteriores;
2. reconstrua a curva semanal por município com weekly_curves e some por UF (sem incerteza: os 9 quantis iguais);
3. pontue com score_frame contra load_truth() para UFs e para as 15 cidades de build_submissions.DENGUE_CITIES.
Saída: reports/rolling/oracle.csv com o erro absoluto médio semanal por nível e temporada, ao lado do erro
absoluto da mediana do B2 e do B3 (use a coluna ae dos scores existentes).
Isto é um teto: usa informação do futuro de propósito. Escreva isso no cabeçalho do script. Não retreine nada.
```

**D4 — Autocorrelação espacial dos resíduos**

```
Repositório: Pattern-Blue. Parâmetros previstos: src/outputs/params/v3/params_<tag>_full.parquet (TFT v3) e
src/outputs/params/params_b3_<ano>.parquet (B3); colunas geocode, q, total_cases. Alvos:
data/processed/season_targets_v3.parquet (obs_total por geocode e season; a temporada do corte Y é season = Y+1).
Arestas: data/processed/adjacencia_edges.csv (source_geocode, target_geocode). Mapa de tags: common.SEASON_TAGS.
Tarefa: criar src/residual_moran.py. Para cada corte de 2015 a 2024 e cada modelo:
1. resíduo = log1p(obs_total) − log1p(mediana prevista, q = 0.5) por município;
2. subtraia a média do resíduo da UF (2 primeiros dígitos do geocode);
3. calcule o I de Moran com pesos de adjacência normalizados por linha e p-valor por 999 permutações.
Salve reports/rolling/residual_moran.csv (modelo, corte, I antes e depois de remover a média da UF, p-valores).
Não retreine nada. Mostre a tabela.
```

**D5 — Baseline zero-shot com modelo de fundação**

```
Repositório: Pattern-Blue. Leia src/rolling_eval.py (b2_frames, score_frame, load_truth) para o formato esperado.
Tarefa: criar src/fm_zeroshot.py que, para cada corte EW25/Y, Y de 2015 a 2024, e para cada UF (exceto ES) e
cada uma das 15 cidades:
1. monta a série semanal de casos até common.cut_date(Y), sem nenhum dado posterior;
2. pede a um modelo de fundação de séries temporais de pesos abertos (comece pelo Chronos-2; consulte o cartão
   do modelo antes de escrever a chamada e anote a versão exata e o horizonte máximo suportado) os quantis
   0.025, 0.05, 0.10, 0.25, 0.50, 0.75, 0.90, 0.95, 0.975 para as semanas até a EW40 de Y+1;
3. recorta a temporada EW41/Y–EW40/Y+1, grava em src/outputs/rolling/direct/fm_<Y>_<level>.parquet no mesmo
   formato de b1/b2 (use imdc_submission.build_df).
Depois rode `python rolling_eval.py score` e `python rolling_eval.py report` e mostre a linha do modelo.
Se o horizonte nativo for menor que o necessário, pare e relate; não improvise previsão em cadeia sem avisar.
Registre no cabeçalho: "o pré-treino do modelo pode incluir estas séries; resultado retrospectivo não é limpo".
```

**D6 — README**

```
Repositório: Pattern-Blue. O README.md descreve o modelo submetido, mas tem erros conhecidos, listados em
reports/rolling/resultados_fase1.md (seção Limitações) e em docs/evaluation_protocol.md.
Tarefa: corrigir só fatos, sem reescrever o estilo: (1) os parâmetros de Richards vêm de
notebooks/apply_2026.ipynb, não do Episcanner oficial; (2) e-mail e nomes da seção "Team and Contributors"
(perguntar ao usuário a grafia correta antes de alterar); (3) acrescentar a seção "Avaliação posterior",
com ligação para reports/rolling/resultados_fase1.md e a tabela de WIS relativo. Mostre o diff antes de salvar.
```

Revisão bibliográfica: prompts 1 a 3 de A5.

### B7.3 Dez maiores riscos

| # | Risco | Probabilidade | Impacto | Resposta |
|---|---|---|---|---|
| 1 | Nenhuma arquitetura supera a climatologia porque a magnitude não é previsível com estes dados | Alta | Alto | Enquadrar o trabalho como medida desse limite; buscar informação (B2) antes de capacidade |
| 2 | Continuar ajustando o modelo às mesmas 10 temporadas e publicar um ganho que não se repete | Alta | Alto | Protocolo congelado; confirmatórios A e B |
| 3 | Diferenças entre versões serem ruído de semente | Alta | Alto | Fase 0 |
| 4 | Atraso de notificação derrubar o desempenho em produção | Média | Alto | Truncamento simulado na Fase 1 |
| 5 | Sorotipo e vacinação não existirem como dado aberto para todos os estados | Média | Médio | Verificar antes de planejar em cima; usar a imunidade acumulada como substituto |
| 6 | Custo de GPU estourar com sementes × cortes × variantes | Média | Médio | Triagem em boosting; menos janelas por alvo |
| 7 | Revisor rejeitar por falta de novidade ou por resultado negativo | Média | Médio | Preprint primeiro; periódico que aceita resultado negativo; contribuição = protocolo e diagnóstico |
| 8 | Modelo de fundação zero-shot empatar com o TFT e esvaziar o artigo de método | Média | Médio | Descobrir cedo (Fase 2b) e incorporar ao enredo |
| 9 | Rede topológica consumir meses sem ganho mensurável | Alta, se iniciada sem os testes | Médio | Critério de parada de B5 |
| 10 | Perda de resultados por código fora do controle de versão | Já ocorreu (`resultados_fase1.md:152`) | Médio | Primeiro item da Fase 0 |

### B7.4 Perguntas que só você pode responder

1. **Previsão final:** o IMDC registrou a previsão 2026-27 do pipeline v1 ou a corrigida de 23 de setembro, enviada depois do prazo de 10 de setembro?
2. **Plano do Richards:** existe um documento? Qual das quatro leituras de B3 é a dos orientadores?
3. **Comentários da Iasmim e do Flávio:** o que eles esperam como "primeiro avanço": o modelo submetido, o v3 ou o diagnóstico?
4. **Artigo coletivo do IMDC 2026:** vai existir? Há restrição a preprint independente antes dele?
5. **Vínculo acadêmico:** isto é dissertação ou tese? A GNN e a rede topológica são requisito do projeto ou hipótese?
6. **Prazo real:** há data de defesa, relatório ou evento que fixe o cronograma?
7. **HPC:** qual a cota na A100, o tempo máximo por tarefa e a fila típica?
8. **Safras:** o Mosqlimate ou o Infodengue guardam os dados como estavam em cada EW25? O Flávio saberia.
9. **Dados externos:** vocês têm acesso a sorotipo por UF e ano em formato aberto?
10. **Próximo desafio:** o objetivo é ir melhor no IMDC 2027 ou publicar método? As duas metas pedem ordens diferentes de trabalho: para o desafio, ensemble de climatologias com calibração rende mais que arquitetura.
11. **Grafia dos nomes** no README: "Iasmim Almeida" ou "Iasmim Ferreira"?

---

## Apêndice — Fontes externas consultadas

Li por inteiro apenas a primeira. As demais vieram de resultados de busca e estão a verificar.

- Instruções do 3º IMDC: https://sprint.mosqlimate.org/instructions/
- IMDC 2024, medRxiv: https://www.medrxiv.org/content/10.1101/2025.05.12.25327419.full.pdf
- Relatórios dos sprints: https://zenodo.org/records/13929005 e https://zenodo.org/records/17516518
- Episcanner: https://www.ncbi.nlm.nih.gov/pmc/articles/PMC12115816/ e https://arxiv.org/abs/2407.21286
- Mosqlimate: https://arxiv.org/html/2410.18945v1
- Johansson et al. 2019: https://repository.library.noaa.gov/view/noaa/29091
- Chen e Moraga 2025: https://www.medrxiv.org/content/10.1101/2025.03.02.25323168.full.pdf
- GNN em capitais (SBCAS): https://sol.sbc.org.br/index.php/sbcas_estendido/article/view/43841
- TFT para malária e dengue: https://www.mdpi.com/1660-4601/23/1/75
- Híbridos neurais e mecanísticos: https://arxiv.org/abs/2602.06323v1 e https://arxiv.org/html/2506.03897v1
- Modelos de fundação em epidemias: https://arxiv.org/pdf/2605.11598, https://www.medrxiv.org/content/10.1101/2025.02.24.25322795.full.pdf e https://neurips.cc/virtual/2025/130450
- Moirai 2.0: https://arxiv.org/pdf/2511.11698
- TimesFM-3 (fontes secundárias): https://datanorth.ai/news/google-releases-timesfm-3 e https://pypi.org/project/timesfm/
- Comparativos de modelos de fundação (blogs): https://www.turingpost.com/p/time-series-llms-fms e https://pasqualepillitteri.it/en/news/26634/time-series-ai-compared-timesfm-chronos-timestral
- Redes topológicas: https://arxiv.org/html/2604.15833 e https://arxiv.org/pdf/2605.15035
- Edições especiais: https://www.keaipublishing.com/en/journals/infectious-disease-modelling/call-for-papers/special-issue-on-data-driven-biomathematical-modelling-and-stochastic-analysis-for-infectious-diseases-from-mechanisms-to-public-health-action/
