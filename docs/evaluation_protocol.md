# Protocolo de avaliação — Fase 1

Definido antes de calcular os resultados com origem móvel. Mudanças posteriores devem ser
registradas aqui, com data e motivo.

## Pergunta primária

No nível estadual, o TFT supera a climatologia de parâmetros (B3), que usa a mesma reconstrução
Richards e a mesma agregação, mas com os parâmetros históricos no lugar dos previstos?

- **Métrica primária:** WIS relativo ao B3 no nível estadual. É a média geométrica de
  `(WIS_modelo + 1) / (WIS_B3 + 1)` por UF-temporada, com o WIS calculado semanalmente e promediado
  na temporada.
- **Incerteza:** IC de 95% por bootstrap das temporadas, que são a unidade dependente, não as UFs.
- **Critério:** há evidência de ganho se o limite superior do IC ficar abaixo de 1. Com 10 temporadas
  o poder é limitado, e isso deve ser declarado.

## Conjunto de avaliação

- Cortes EW25/Y para Y = 2015…2024 (temporadas 2015/16 a 2024/25).
- Temporada 2025/26: dados só até EW25/2026; reportada à parte, fora da análise primária.
- Unidades: 26 UFs (sem ES) e as 15 cidades do desafio.

## Regras contra vazamento

- Em cada corte Y, alvos só de temporadas encerradas antes do corte (≤ Y−1); treino ≤ Y−2, early
  stopping = Y−1. Normalizador e imputação de forma usam apenas essas temporadas.
- `rho` da agregação estadual: escolhido por modelo, usando só os cortes ≤ Y−2, cujas temporadas já
  estavam encerradas no corte Y. Para os cortes sem histórico (2015 e 2016), `rho = 0,5`.

## Modelos

| Modelo | Descrição |
|---|---|
| TFT | Modelo global, um por corte. Configuração congelada: sem `time_idx`, lr 0,003, até 8 épocas, paciência 3 |
| B1 | Persistência das últimas 52 semanas, com erro multiplicativo empírico |
| B2 | Climatologia de casos: quantis por semana da temporada, janela de ±2 semanas |
| B3 | Climatologia de parâmetros, com a mesma reconstrução e agregação do TFT |

## Limitações conhecidas (a declarar no artigo)

- **Dados não são safras históricas:** os casos e o clima são os valores atuais, já revisados; não é
  o que estava disponível em cada corte. Isso favorece todos os modelos.
- **Configuração escolhida olhando a temporada 2024/25:** a retirada de `time_idx` e a lr vieram do
  `val_loss` do corte final, cuja validação é essa temporada. Essa temporada está dentro do conjunto
  de avaliação.
- **Ajustes Richards:** vêm de `notebooks/apply_2026.ipynb`, não do Episcanner oficial. O método
  está escrito `diferential_evolution`, e o lmfit cai silenciosamente em Nelder-Mead. Numa amostra
  aleatória de 60 ajustes bem-sucedidos (≥ 200 casos), o resultado foi praticamente igual ao da
  evolução diferencial: |Δpico| mediana de 0,0 semana (p90 = 0,01) e nenhum ajuste com RMSE mais de
  10% pior.
- **Temporadas sem ajuste:** recebem forma imputada. O total observado é mantido, mas a falha não é
  aleatória: atinge grandes cidades (São Paulo, Brasília, Belo Horizonte, Rio) e cobre 24,9% dos
  casos de 2024 e 29,1% dos de 2012. Reajustar essas 10 temporadas com ≥ 1.000 casos fica como
  análise de sensibilidade.
