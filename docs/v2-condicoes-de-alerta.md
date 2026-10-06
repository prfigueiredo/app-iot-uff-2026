# V2: condições de alerta

Este documento define quais situações geram alerta no CPD Monitor (atividade
4.1 da EAP). Os valores abaixo são uma **proposta para validação do PO**.
Todos podem ser alterados por variável de ambiente, sem mudar o código.

## Condições

| Condição | Atenção (severidade média) | Crítico (severidade alta) | Volta ao normal |
|---|---|---|---|
| Temperatura do ar-condicionado | acima de 26°C | acima de 28°C | abaixo de 25,5°C |
| Umidade perto do ar-condicionado | acima de 60% | acima de 70% | abaixo de 58% |
| Ar-condicionado desligado | | status `desligado` | status `ligado` |
| Sensor sem comunicação | | nenhuma leitura há mais de 60s | nova leitura |

A umidade alta perto do ar-condicionado foi incluída porque pode indicar
vazamento de água do equipamento.

Como referência para a temperatura e a umidade, a diretriz térmica da ASHRAE
para data centers (TC 9.9) recomenda até 27°C e até 60% de umidade relativa.
Essa referência é do nosso conhecimento prévio da diretriz e não foi conferida
no documento original para este projeto. Os limites finais são decisão do PO.

## Como os alertas são gerados

**Um alerta por mudança de nível, nunca um por leitura.** Cada condição tem
um nível: normal, atenção ou crítico. O sistema compara o nível novo com o
anterior a cada leitura (a cada 2s):

| Mudança | Alerta gerado |
|---|---|
| normal → atenção | "Temperatura em atenção" / "Umidade elevada" (média) |
| normal ou atenção → crítico | "Temperatura crítica", "Umidade crítica", "Ar-condicionado desligado" ou "Sensor sem comunicação" (alta) |
| qualquer nível → normal | aviso de normalização (baixa) |
| crítico → atenção | nenhum, porque o problema continua |
| nível igual | nenhum |

Sem essa regra, uma temperatura que fica acima do limite geraria um alerta a
cada leitura. No protótipo original eram cerca de 240 alertas por hora.

**Histerese.** O nível só cai depois que o valor fica um pouco abaixo do
limite (0,5°C para temperatura, 2 pontos para umidade). Sem isso, uma
temperatura oscilando entre 27,9°C e 28,1°C geraria um par "crítico" e
"normalizado" a cada oscilação.

**Sensor sem comunicação.** Conta o tempo desde a última leitura publicada
pelo sensor no FIWARE. Se o backend acabou de iniciar e nunca recebeu leitura,
conta desde o início do monitoramento. Esse alerta também dispara quando o
próprio FIWARE está fora do ar.

## Configuração

| Variável | Padrão |
|---|---|
| `TEMPERATURA_ATENCAO_C` | 26 |
| `LIMITE_TEMPERATURA_C` | 28 |
| `HISTERESE_TEMPERATURA_C` | 0.5 |
| `UMIDADE_ATENCAO_PCT` | 60 |
| `UMIDADE_CRITICA_PCT` | 70 |
| `HISTERESE_UMIDADE_PCT` | 2 |
| `SENSOR_SEM_COMUNICACAO_S` | 60 |

## Onde está no código

- Regras: `cpd-monitor/backend/app/services/regras_alerta.py`
- Geração, textos e envio: `cpd-monitor/backend/app/services/alertas.py`
- Laço de monitoramento: `_loop_monitoramento` em `cpd-monitor/backend/app/main.py`

## Fora do escopo da V2

- Perfis de alerta por horário, plantão ou feriado (RF04). Hoje todos os
  alertas vão para todos os usuários, pelo canal `push` do app.
- Envio real por SMS ou e-mail.
- Estado de "lido" por usuário. Hoje, quando um usuário marca um alerta como
  lido, ele fica lido para todos.
- Alertas guardados em banco de dados. Os alertas ficam em memória e somem ao
  reiniciar o backend. Isso é escopo da V3 (histórico).
