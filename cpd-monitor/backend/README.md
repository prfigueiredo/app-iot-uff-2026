# CPD Monitor - Backend

API em FastAPI para o app de monitoramento do CPD da STI de Niterói-RJ (TCC).

**Este é o app completo e funcional, com todos os dados MOCKADOS (simulados)
em memória** - não é necessário instalar PostgreSQL nem ter acesso ao
ambiente real do CPD para testar. Umidade e combustível variam sozinhos a
cada 15s. A temperatura do ar-condicionado vem do sensor simulado em
`../sensor_simulado`, que envia leituras em JSON para o backend. Alertas
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

## Sensor do ar-condicionado

Com a API rodando, em outro terminal:

```bash
python ../sensor_simulado/ar_condicionado.py
```

O sensor envia `{"temperatura_c": 22.3, "status": "ligado"}` para
`POST /sensores/ar-condicionado`, com o cabeçalho `X-Sensor-Key`
(`SENSOR_API_KEY`). Para provocar superaquecimento na demonstração, use
`--alvo 31`. Para ver todas as opções, use `--help`.

## Testes

```bash
pip install -r requirements-dev.txt
python -m pytest tests
```

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
- Recebimento das leituras do sensor do ar-condicionado em JSON
  (`POST /sensores/ar-condicionado`)
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
├── services/     # reservado para integração real com GrayLog/Zabbix
└── main.py       # ponto de entrada + simulador de sensores em background
```
