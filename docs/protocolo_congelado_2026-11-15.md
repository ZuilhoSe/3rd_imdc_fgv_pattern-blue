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

(nenhuma)
