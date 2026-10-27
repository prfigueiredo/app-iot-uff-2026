# CPD Monitor - Backend

API em FastAPI para o app de monitoramento do CPD da STI de Niterói-RJ (TCC).

Não é preciso ter acesso ao ambiente real do CPD para testar. A temperatura
e a umidade do ar-condicionado vêm do sensor simulado em `../sensor_simulado`,
que publica leituras em JSON no FIWARE Orion, de onde o backend as lê. O
combustível do gerador varia sozinho a cada 15s, e os logs (GrayLog) e os
serviços (Zabbix) continuam simulados em memória. Alertas automáticos disparam
quando a temperatura passa de `LIMITE_TEMPERATURA_C` (28°C por padrão).

Os alertas e o histórico (uma média por hora de temperatura e umidade) ficam
num PostgreSQL, que roda no Docker pelo `docker-compose.yml` desta pasta.

## Como rodar localmente

Suba o PostgreSQL (precisa do Docker Desktop aberto). Ele fica na porta 5433:

```bash
docker compose up -d
```

Depois, a API:

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API sobe em `http://127.0.0.1:8000`. Documentação automática (Swagger) em
`http://127.0.0.1:8000/docs` - dá pra testar todas as rotas por lá, sem
precisar do app Flutter.

Sem o PostgreSQL no ar, a API não sobe e explica o motivo. Para rodar sem
banco, com o histórico apagado a cada reinício, use `ARMAZENAMENTO=memoria`.
Para ver médias de 1 minuto em vez de 1 hora numa demonstração, use
`HISTORICO_INTERVALO_MIN=1`.

## Sensor do ar-condicionado via FIWARE

```
sensor simulado ──publica──▶ FIWARE Orion ◀──lê a cada 2s── backend ──▶ app
```

1. Suba o Orion (precisa do Docker): veja `../fiware/README.md`.
2. Suba a API (acima).
3. Em outro terminal, ligue o sensor:

```bash
python ../sensor_simulado/ar_condicionado.py
```

O sensor publica a entidade `urn:ngsi-ld:ArCondicionado:cpd-01` no Orion, e o
backend copia a leitura para `/sensores/atual` (`temperatura_c`,
`temperatura_atualizada_em`, `ar_condicionado_status`). Enquanto nenhum sensor
publicou, esses campos vêm `null`. Para provocar superaquecimento na
demonstração, use `--alvo 31`. Para ver todas as opções, use `--help`.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

Os testes de integração com o FIWARE (`tests/test_integracao_fiware.py`) só
rodam com o Orion no ar, e os testes com o PostgreSQL real
(`tests/test_repositorio.py`) só rodam com o banco no ar. Sem eles, esses
testes aparecem como pulados (`skipped`). Os testes com o PostgreSQL usam um
schema temporário e não tocam nas tabelas de verdade.

## Usuários de teste (perfis de acesso)

| Usuário | Senha | Perfil |
|---|---|---|
| admin | admin123 | Administrador (acesso total) |
| operador | operador123 | Operador (gerencia alertas) |
| visualizador | visual123 | Somente leitura |

## O que já funciona

- Login com JWT e controle de acesso por perfil (RBAC)
- Registro de tentativas de acesso indevido (`/seguranca/tentativas-acesso`, só admin)
- Sensores físicos do CPD: temperatura, umidade, gerador, presença, calor,
  ar-condicionado (`/sensores/atual`)
- Histórico (V3): médias de temperatura e umidade (`/historico/medias`) e
  alertas anteriores (`/historico/alertas`), guardados no PostgreSQL
  (`app/persistencia`)
- Temperatura do ar-condicionado lida do FIWARE Orion (`app/services/fiware.py`)
- Geração de alertas a partir das leituras (`app/services/alertas.py`), com as
  condições registradas na issue #12 do GitHub
- Logs simulando o GrayLog (`/integracoes/graylog/logs`, com filtro por nível)
- Status de serviços simulando o Zabbix (`/integracoes/zabbix/status`)
- Alertas com perfis personalizados (`/alertas`, `/alertas/perfis`),
  simulação manual (`/alertas/simular`) e marcação de lido
  (`POST /alertas/{id}/lido`)
- Push notification em tempo real via WebSocket (`/alertas/ws`). A primeira
  mensagem do cliente deve ser `{"token": "<token de login>"}`
- Dashboard personalizável por usuário (`/dashboard/preferencias`)

## Modo simulação → dados reais

`MODO_SIMULACAO=true` por padrão (ver `app/core/config.py`). Quando o
ambiente real do CPD estiver disponível, os serviços em `app/services/`
passam a chamar as APIs reais do GrayLog e do Zabbix (usando
`GRAYLOG_URL`/`ZABBIX_URL` do `.env`), sem que as rotas ou o app Flutter
precisem mudar - o formato de resposta é o mesmo.

## Estrutura

```
app/
├── api/          # rotas (auth, sensores, alertas, integrações, dashboard, segurança)
├── core/         # config, segurança (JWT), RBAC, base mockada, WebSocket
├── models/       # reservado
├── persistencia/ # alertas e médias: PostgreSQL ou memória
├── schemas/      # reservado para schemas adicionais
├── services/     # FIWARE, regras e geração de alertas, médias do histórico
└── main.py       # ponto de entrada + laço de monitoramento em background
```
