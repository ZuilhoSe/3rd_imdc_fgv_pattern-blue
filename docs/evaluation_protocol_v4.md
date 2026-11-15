# Protocolo de avaliação — modelo v4

Registrado em 2026-11-11, antes de treinar e de ver qualquer resultado do v4. A avaliação segue `evaluation_protocol_v3.md` em tudo que não está escrito aqui.

## O que muda em relação ao v3

A arquitetura (TFT), a formulação (descritores + Richards), a perda com máscara de forma e o treino em duas etapas continuam iguais, com o mesmo código (`train_v3.py` e `infer_v3.py` configurados por `common_v4.py`).

| Item | v3 | v4 |
|---|---|---|
| Previsão climática | Do mês da semana de decoder | + previsão sazonal emitida em junho: média de jul-set (`fc_pre_*`) e de out-dez (`fc_early_*`), para temperatura, umidade e chuva |
| Temporada em curso | Só a série semanal das últimas 52 semanas | + acumulado da temporada até a semana (casos e incidência, em log) e total da temporada anterior |
| Taxa de aprendizado | 0,003 (ajuste fino 0,0003) | 0,001 (ajuste fino 0,0001) |
| Épocas | Até 25, paciência 5 | Até 50, paciência 8 |

Motivação, registrada antes do treino:
- 10 dos 12 cortes do v3 bateram no limite de 25 épocas ainda melhorando.
- Os outros 2 cortes, e também o `final`, chegaram à melhor época na 2ª a 4ª, sinal de que a taxa de 0,003 é alta para eles.

### Limitações declaradas

- A fonte de previsão climática só vai até 6 meses à frente. Com a emissão de junho, a temporada prevista tem previsão só para out-dez; os meses de pico (fev-mai) ficam sem previsão.
- Em cada ano de treino, todas as amostras usam a emissão de junho, inclusive as com semana de decoder em maio (EW20 a EW22). Isso é um pequeno adiantamento só dentro do treino. Na previsão de cada corte (EW25), a emissão de junho já está disponível.
- As mudanças nos dados (1 e 2) e no treino (taxa e épocas) entram juntas. O v4 não separa o efeito de cada uma; para isso seriam necessárias ablações.

## Avaliação

- **Modelo primário:** `full.ckpt`. O `best.ckpt` é análise de sensibilidade.
- As mesmas métricas do v3, com o v3 ao lado:
  - razão oficial contra o PROCC (BB) e o LSTM do Eduardo nas 4 validações;
  - cobertura e largura por intervalo;
  - WIS relativo ao B3 na origem móvel;
  - previsão 2026-27.
- **Ordem do treino:** primeiro `final` e `test4` a `test1`, depois `cut2021` a `cut2015`. Se a origem móvel completa ainda não tiver terminado, o resultado parcial é declarado como tal.
- **Sem seleção pelo teste:** a configuração acima está congelada. Se o v4 for pior que o v3, os dois resultados são relatados.
