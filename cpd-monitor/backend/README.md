# CPD Monitor - Backend

API em FastAPI para o app de monitoramento do CPD da STI de Niterói-RJ (TCC).

**Este é o app completo e funcional, com todos os dados MOCKADOS (simulados)
em memória** - não é necessário instalar PostgreSQL nem ter acesso ao
ambiente real do CPD para testar. Umidade e combustível variam sozinhos a
cada 15s. A temperatura do ar-condicionado vem do sensor simulado em
`../sensor_simulado`, que publica leituras em JSON no FIWARE Orion, de onde o
backend as lê. Alertas
automáticos disparam quando a temperatura passa de `LIMITE_TEMPERATURA_C`
(28°C por padrão).

## Como rodar localmente

```bash
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
uvicorn app.main:app --reload
```

A API sobe em `http://localhost:8000`. Documentação automática (Swagger) em
`http://localhost:8000/docs` - dá pra testar todas as rotas por lá, sem
precisar do app Flutter.

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

O teste de integração (`tests/test_integracao_fiware.py`) só roda com o Orion
no ar. Sem ele, o teste é pulado.

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
  ar-condicionado (`/sensores/atual`, `/sensores/historico`)
- Temperatura do ar-condicionado lida do FIWARE Orion (`app/services/fiware.py`)
- Logs simulando o GrayLog (`/integracoes/graylog/logs`, com filtro por nível)
- Status de serviços simulando o Zabbix (`/integracoes/zabbix/status`)
- Alertas com perfis personalizados (`/alertas`, `/alertas/perfis`) e
  simulação manual (`/alertas/simular`)
- Push notification em tempo real via WebSocket (`/alertas/ws`)
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
├── models/       # reservado para modelos de banco real (próxima etapa)
├── schemas/      # reservado para schemas adicionais
├── services/     # integrações externas (FIWARE hoje, GrayLog/Zabbix depois)
└── main.py       # ponto de entrada + simulador de sensores em background
```
