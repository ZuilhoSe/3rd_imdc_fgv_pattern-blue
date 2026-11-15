# Protocolo de avaliação — modelo v3

Registrado em 2026-11-05, antes de treinar e de ver qualquer resultado do v3.

## O que muda em relação ao modelo submetido

A arquitetura (TFT) e a formulação (descritores da temporada + reconstrução Richards) são as mesmas.

| Item | Modelo submetido | v3 |
|---|---|---|
| Variáveis observadas | Casos, incidência, temperatura, chuva e umidade médias | + mínimos e máximos, pressão, amplitude térmica, dias de chuva, ENSO, IOD, PDO, chikungunya, acessos Afya |
| Previsão climática | Temperatura e chuva | + umidade |
| Categóricas | UF, Köppen, bioma, macrorregião | + região de saúde |
| Alvos de forma | Treina também em valores imputados | Perda de forma só em temporadas com ajuste Richards |
| Ajustes Richards | Sem as 10 temporadas grandes que falharam | 9 das 10 reajustadas; a de Cruzeiro do Sul em 2014 (R² = 0,37) segue sem ajuste |
| Épocas | Até 8, de 400 lotes | Até 25, paciência 5 |
| Última temporada | Fora do treino | Ajuste fino de 3 épocas com todos os dados do corte, com taxa de 0,0003 |

A máscara da perda de forma foi motivada pela análise exploratória da Fase 1, que usou as mesmas temporadas de teste. Isso deve ser declarado.

## Modelo primário e comparações

- **Modelo primário:** `full.ckpt`, treinado com todos os dados do corte. `best.ckpt` (só etapa 1) é análise de sensibilidade.
- **Dados de avaliação:** casos observados oficiais de `Mosqlimate-project/3rd_IMDC_results` (`data/dengue_state.csv.gz` e `data/dengue_city.csv.gz`), que chegam a 2026-09-27. Não entram como variáveis: todo corte continua limitado à EW25.
- **Comparação oficial, nas 4 validações (2022-23 a 2025-26):** razão `R_v = WIS_modelo / WIS_baseline` por unidade e validação, resumida pela média geométrica, como no desafio.
  - UFs: baseline PROCC (BB), sem ES.
  - Cidades: baseline EMAp LSTM (`3rd_imdc_emap_lstm_muni`).
- **Comparação com origem móvel:** WIS relativo ao B3 em 2015/16 a 2024/25, como em `evaluation_protocol.md`.
- **Agregação estadual:** `rho` escolhido só com cortes ≤ Y−2, em {0,5; 0,8; 1,0}; 0,5 onde não há histórico.
- **Sem seleção pelo teste:** configuração e épocas ficam congeladas. Variantes extras são relatadas como exploratórias.
