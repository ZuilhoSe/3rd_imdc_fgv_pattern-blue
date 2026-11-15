# Protocolo — calibração dos intervalos do v3 (A, B, C e combinações)

Registrado em 2026-11-11, antes de gerar ou pontuar qualquer variante. Nenhum modelo é retreinado: todas as variantes usam os checkpoints do v3 (`docs/evaluation_protocol_v3.md`).

## Variantes

| Nome | O que muda |
|---|---|
| `v3` | Referência: igual ao `tft_v3` (só `full.ckpt`, curvas lisas) |
| `v3A` | **A — calibração conformal** sobre `v3` |
| `v3B` | **B — ruído de observação** binomial negativa em torno de cada curva sorteada |
| `v3C` | **C — conjunto** de `full.ckpt` e `best.ckpt`, metade dos sorteios de cada |
| `v3AB`, `v3AC`, `v3BC`, `v3ABC` | Combinações; A é sempre aplicada por último |

### A — calibração conformal (CQR assimétrica, escala log1p)

- Para cada nível (UF ou cidade), intervalo k ∈ {50, 80, 90, 95} e valor de `rho`, os escores são `log1p(lower_k) − log1p(y)` e `log1p(y) − log1p(upper_k)`, agrupados em todas as unidades e semanas das temporadas de calibração.
- Os limites são deslocados em log1p pelo quantil `ceil((n+1)(1−α/2))/n` de cada escore, de modo que cada lado erre no máximo α/2.
- A mediana é deslocada pela mediana de `log1p(y) − log1p(pred)`.
- Ao fim, os 9 quantis são cortados em 0 e ordenados.
- **Temporadas de calibração para o corte Y:** só os cortes ≤ Y−2 da mesma variante, a mesma regra do `rho`. Os cortes 2015 e 2016 não têm histórico e ficam sem calibração.

### B — ruído de observação

- Em cada sorteio, os casos semanais de cada município são sorteados como `Poisson(Gamma(k, μ/k))`, onde μ é a curva de Richards sorteada.
- No agregado estadual, o ruído é independente por município antes da soma.
- Um único `k` por corte, estimado por máxima verossimilhança com os casos semanais observados em torno das curvas de Richards ajustadas (`has_fit`). Usa as temporadas que terminam até a EW40 de Y−1, numa amostra de até 4000 temporadas.

### C — conjunto

- Metade dos sorteios vem dos quantis do `full.ckpt` e metade dos do `best.ckpt`, com o total de sorteios mantido.
- No agregado estadual, cada sorteio usa o mesmo checkpoint em todos os municípios.

## Avaliação

- O `rho` de cada variante é escolhido como antes: só cortes ≤ Y−2, em {0,5; 0,8; 1,0}.
- Relatório com as mesmas métricas do v3 para as 8 variantes:
  - razão oficial contra o PROCC (BB) e o LSTM do Eduardo nas 4 validações;
  - cobertura e largura por intervalo;
  - WIS relativo ao B3 na origem móvel;
  - previsão 2026-27.
- **Escolha da variante recomendada:** menor WIS relativo ao B3 nas temporadas 2017-18 a 2021-22, usando a média do log entre UFs e cidades. Essas temporadas não são validações oficiais. A variante escolhida é então relatada nas 4 validações oficiais, que não entram na escolha.
- A origem móvel é relatada em 2015-2024 e em 2017-2024, porque A não altera 2015 e 2016.
