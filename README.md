# CPD Monitor (app-iot-uff-2026)

Aplicativo de monitoramento do CPD, evoluído na disciplina de Gerência de
Projeto e Manutenção de Software (GPMS) da UFF, 2026.2.

O protótipo original usa dados simulados em memória. O projeto substitui essas
partes, em três versões incrementais, por dados dinâmicos integrados ao
FIWARE.

| Versão | Escopo | Situação |
|---|---|---|
| V1 | Temperatura do ar-condicionado dinâmica via FIWARE | Concluída |
| V2 | Alertas a partir dos dados monitorados | Concluída |
| V3 | Histórico da temperatura e dos alertas | Concluída |

## Arquitetura

```
sensor simulado ──publica──▶ FIWARE Orion ◀──lê a cada 2s── backend (FastAPI) ──▶ app (Flutter)
                                                                  │
                                                                  ▼
                                                     PostgreSQL (alertas e médias)
```

- O **sensor simulado** publica a temperatura do ar-condicionado no Orion.
- O **FIWARE Orion** é o broker intermediário. Um sensor novo só precisa
  publicar uma entidade, sem mudança no backend.
- O **backend** lê a entidade do Orion e entrega ao app em `/sensores/atual`.
  A cada leitura, verifica as condições de alerta e envia os alertas ao app
  em tempo real por WebSocket.
- O **PostgreSQL** guarda os alertas e uma média por hora da temperatura e da
  umidade (média, mínimo e máximo). O histórico sobrevive ao reinício do
  backend.
- O **app** mostra temperatura e umidade, se atualiza sozinho a cada 5s,
  exibe os alertas assim que são gerados e permite consultar o histórico.

| Pasta | Conteúdo |
|---|---|
| [`cpd-monitor/fiware`](cpd-monitor/fiware/README.md) | Orion + MongoDB em Docker |
| [`cpd-monitor/sensor_simulado`](cpd-monitor/sensor_simulado/ar_condicionado.py) | Sensor simulado do ar-condicionado |
| [`cpd-monitor/backend`](cpd-monitor/backend/README.md) | API em FastAPI e PostgreSQL do histórico em Docker |
| [`cpd-monitor/frontend/cpd_monitor_app`](cpd-monitor/frontend/cpd_monitor_app/README.md) | App em Flutter |

## Pré-requisitos

- Python 3.10 ou mais novo
- Docker Desktop, para o FIWARE e o PostgreSQL
- Flutter SDK, para o app ([guia oficial](https://docs.flutter.dev/get-started))
- Chrome ou Edge, para rodar o app no navegador

## Como rodar

Todos os comandos partem da raiz do repositório. Use um terminal para cada
parte e deixe todos abertos.

### 1. FIWARE e PostgreSQL

Com o Docker Desktop aberto:

```bash
docker compose -f cpd-monitor/fiware/docker-compose.yml up -d
docker compose -f cpd-monitor/backend/docker-compose.yml up -d
```

Para conferir, `http://127.0.0.1:1026/version` deve responder com a versão do
Orion. O PostgreSQL fica na porta **5433**, para não conflitar com um
PostgreSQL instalado direto no computador, que costuma usar a 5432. Os dois só
aceitam conexões do próprio computador.

Se a porta 1026 já estiver ocupada (veja "Problemas conhecidos"), suba o Orion
em outra porta e avise o backend e o sensor:

```bash
ORION_PORTA=11026 docker compose -f cpd-monitor/fiware/docker-compose.yml up -d
```

No PowerShell, defina a variável antes: `$env:ORION_PORTA = "11026"`. O
backend usa `FIWARE_URL=http://127.0.0.1:11026`, e o sensor usa
`--orion http://127.0.0.1:11026`.

### 2. Backend

```bash
cd cpd-monitor/backend
python -m venv venv
./venv/Scripts/python -m pip install -r requirements-dev.txt
./venv/Scripts/python -m uvicorn app.main:app --port 8000
```

No Linux ou macOS, troque `./venv/Scripts/python` por `./venv/bin/python`.

A API fica em `http://127.0.0.1:8000`, com a documentação interativa em
`http://127.0.0.1:8000/docs`. O log deve mostrar `Armazenamento: postgres`.
Enquanto nenhum sensor publicou, ele mostra `FIWARE: aguardando o sensor
publicar`.

Sem o PostgreSQL no ar, o backend **não sobe** e explica o motivo. Isso é de
propósito: rodar sem banco perderia o histórico sem avisar. Para rodar sem
banco (o histórico some ao reiniciar), use `ARMAZENAMENTO=memoria`.

**Para demonstrações**, as médias podem ser de 1 minuto em vez de 1 hora, para
o histórico aparecer sem esperar:

```bash
HISTORICO_INTERVALO_MIN=1 ./venv/Scripts/python -m uvicorn app.main:app --port 8000
```

No PowerShell: `$env:HISTORICO_INTERVALO_MIN = "1"` antes de subir o backend.

### 3. Sensor simulado

```bash
python cpd-monitor/sensor_simulado/ar_condicionado.py --intervalo 2
```

Cada linha deve terminar em `Orion HTTP 204`. Opções úteis:

- `--alvo 31` faz a temperatura subir até 31°C (alertas de temperatura).
- `--umidade-alvo 75` faz a umidade subir até 75% (alertas de umidade).
- `--status desligado` informa o ar-condicionado como desligado.
- `Ctrl+C` para o sensor. Depois de 60s sem leituras, o backend gera o alerta
  "Sensor sem comunicação".
- `--id urn:ngsi-ld:ArCondicionado:cpd-02` publica como outro sensor.
- `--help` lista todas as opções.

### 4. App

```bash
cd cpd-monitor/frontend/cpd_monitor_app
flutter pub get
flutter run -d chrome
```

Sem o Chrome, use `flutter run -d edge`.

### Usuários de teste

| Usuário | Senha | Perfil |
|---|---|---|
| admin | admin123 | Acesso total |
| operador | operador123 | Gerencia alertas |
| visualizador | visual123 | Somente leitura |

## Testes automatizados

Backend, dentro de `cpd-monitor/backend`:

```bash
./venv/Scripts/python -m pytest tests
```

Com o FIWARE e o PostgreSQL no ar, o resultado esperado é **108 passed**.
Alguns testes dependem desses serviços e aparecem como pulados (`skipped`)
quando eles estão desligados:

- `tests/test_integracao_fiware.py` (2 testes) cobre os fluxos sensor → FIWARE
  → backend → app e sensor → FIWARE → alerta → app.
- `tests/test_repositorio.py` roda os mesmos testes de armazenamento duas
  vezes: na versão em memória e no PostgreSQL real (11 testes). No PostgreSQL,
  cada execução usa um schema temporário, apagado no final, e nunca toca nas
  tabelas de verdade.

App, dentro de `cpd-monitor/frontend/cpd_monitor_app` (resultado esperado: 13
testes):

```bash
flutter test
```

## Roteiro de testes manuais da V1

Com as quatro partes rodando, registre se cada caso passou ou falhou.

O Orion guarda a última leitura mesmo depois de reiniciar. Para o CT01 começar
do zero, apague a leitura salva antes de subir o backend:

```bash
docker compose -f cpd-monitor/fiware/docker-compose.yml down -v
docker compose -f cpd-monitor/fiware/docker-compose.yml up -d
```

| # | Ação | Resultado esperado |
|---|---|---|
| CT01 | Antes de ligar o sensor, faça login com `admin` | No Painel, o card de temperatura mostra "-" e "Aguardando sensor" |
| CT02 | Ligue o sensor e observe o Painel sem mexer em nada | A temperatura e a hora mudam sozinhas a cada ~5s |
| CT03 | Abra a aba Sensores | O card "Ar-condicionado" mostra a temperatura em °C, o status e a hora da leitura |
| CT04 | Reinicie o sensor com `--alvo 31` | Ao passar de 28°C, o card fica vermelho e mostra "Acima do limite" |
| CT05 | Pare o sensor com `Ctrl+C` | O valor e a hora congelam. O app não quebra |
| CT06 | Ligue o sensor com `--alvo 22` | A temperatura cai e o card volta ao normal |
| CT07 | Pare o Orion: `docker compose -f cpd-monitor/fiware/docker-compose.yml stop orion` | O valor e a hora congelam. O backend registra um único aviso no log |
| CT08 | Religue o Orion: `docker compose -f cpd-monitor/fiware/docker-compose.yml start orion` | A atualização volta sozinha, sem reiniciar o backend |

## Roteiro de testes manuais da V2

Os resultados e os defeitos encontrados estão registrados nas issues
[#15](https://github.com/prfigueiredo/app-iot-uff-2026/issues/15) e [#16](https://github.com/prfigueiredo/app-iot-uff-2026/issues/16). Resumo:

| # | Ação | Resultado esperado |
|---|---|---|
| CT-V2-01 | Sensor com `--alvo 31` | Acima de 26°C: notificação laranja e card "Atenção". Acima de 28°C: um único alerta crítico e card vermelho |
| CT-V2-02 | Sensor com `--umidade-alvo 80` | Acima de 60%: "Umidade elevada". Acima de 70%: "Umidade crítica" |
| CT-V2-03 | Sensor com `--status desligado` | "Ar-condicionado desligado" |
| CT-V2-04 | Sensor com valores normais e ligado | Avisos de normalização |
| CT-V2-05 | Pare o sensor por mais de 60s | "Sensor sem comunicação" |
| CT-V2-06 | Toque num alerta não lido | Alerta fica cinza e o contador do sino diminui |

## Roteiro de testes manuais da V3

Suba o backend com `HISTORICO_INTERVALO_MIN=1` e o sensor com `--alvo 30`.

| # | Ação | Resultado esperado |
|---|---|---|
| CT-V3-01 | Espere 2 minutos e abra Sensores → Histórico | Gráfico com a média (linha cheia), o mínimo e o máximo (tracejadas), e a tabela com data, hora, valores e número de leituras de cada período |
| CT-V3-02 | Troque o período entre 24 h, 7 dias e 30 dias | O gráfico e a tabela mostram só os períodos do intervalo escolhido |
| CT-V3-03 | Pare o sensor por 3 minutos e ligue de novo | O gráfico mostra uma lacuna, e a tabela não tem registros desses minutos |
| CT-V3-04 | Abra Alertas → Histórico e use os filtros de período e de condição | Só aparecem os alertas do período e da condição escolhidos |
| CT-V3-05 | Com a temperatura crítica, reinicie o backend | Os alertas e as médias continuam lá, e nenhum alerta repetido é gerado para o problema que continua |
| CT-V3-06 | Pare o PostgreSQL (`docker compose -f cpd-monitor/backend/docker-compose.yml stop`) e suba o backend | O backend se recusa a subir e diz onde procurou o banco |

## Configuração

O backend lê as configurações de **variáveis de ambiente**. O arquivo
[`.env.example`](cpd-monitor/backend/.env.example) só documenta os valores
padrão. Ele não é carregado automaticamente.

| Variável | Padrão | Uso |
|---|---|---|
| `DATABASE_URL` | `postgresql://cpd_user:cpd_pass@127.0.0.1:5433/cpd_monitor` | Endereço do PostgreSQL |
| `ARMAZENAMENTO` | `postgres` | `postgres` ou `memoria` (sem banco, o histórico some ao reiniciar) |
| `HISTORICO_INTERVALO_MIN` | `60` | Minutos de cada média do histórico. Precisa dividir o dia em partes iguais (1, 5, 15, 30, 60...) |
| `FIWARE_URL` | `http://127.0.0.1:1026` | Endereço do Orion |
| `FIWARE_ENTIDADE_AR_CONDICIONADO` | `urn:ngsi-ld:ArCondicionado:cpd-01` | Entidade lida pelo backend |
| `FIWARE_INTERVALO_S` | `2` | Segundos entre leituras do Orion |
| `TEMPERATURA_ATENCAO_C` | `26` | Alerta de atenção de temperatura |
| `LIMITE_TEMPERATURA_C` | `28` | Alerta crítico de temperatura e sensor de calor |
| `HISTERESE_TEMPERATURA_C` | `0.5` | Quanto abaixo do limite a temperatura volta ao normal |
| `UMIDADE_ATENCAO_PCT` | `60` | Alerta de atenção de umidade |
| `UMIDADE_CRITICA_PCT` | `70` | Alerta crítico de umidade |
| `HISTERESE_UMIDADE_PCT` | `2` | Quanto abaixo do limite a umidade volta ao normal |
| `SENSOR_SEM_COMUNICACAO_S` | `60` | Segundos sem leitura até o alerta de sensor sem comunicação |

As condições e os valores estão registrados na issue [#12](https://github.com/prfigueiredo/app-iot-uff-2026/issues/12).

A porta do Orion no computador é definida por `ORION_PORTA` (padrão `1026`),
lida pelo `docker-compose.yml` do FIWARE, e não pelo backend.

## Problemas conhecidos

- **Use `127.0.0.1` em vez de `localhost` nos scripts.** No Windows, cada
  requisição para `localhost` levou cerca de 2s, porque o sistema tenta o IPv6
  antes e o servidor só escuta no IPv4. Com `127.0.0.1` levou cerca de 1 ms.
- **Emulador Android:** o app aponta para `localhost`. No emulador, troque por
  `10.0.2.2` em `lib/services/api_service.dart`.
- **O Orion não tem autenticação.** Hoje ele só aceita conexões do próprio
  computador, mas qualquer programa nele consegue publicar leituras. O FIWARE
  resolve isso com componentes próprios de segurança, que estão fora do
  escopo atual ([#19](https://github.com/prfigueiredo/app-iot-uff-2026/issues/19)).
- **Porta 1026 ocupada no Windows.** O serviço de Filas de Mensagens do
  Windows (MSMQ, `mqsvc.exe`) pode pegar a porta 1026 ao ligar o computador,
  e o Orion fica inacessível. Para ver quem usa a porta, rode
  `netstat -ano | findstr :1026`. Use `ORION_PORTA` (veja "Como rodar") ou,
  se o MSMQ não for usado, desative-o nos Recursos do Windows.
- **O app mostra apenas o ar-condicionado `cpd-01`.** Outros sensores já
  conseguem publicar no Orion, mas exibir vários na tela exige mudar o modelo
  de dados.
- **O período em andamento não aparece no histórico.** Cada média é gravada
  quando o seu período termina. Se o backend parar no meio do período, a média
  parcial é gravada e mesclada com o restante depois.
- **Usuários, perfis de alerta e tentativas de acesso indevido continuam em
  memória** e voltam ao estado inicial quando o backend reinicia.
- **Estado de "lido" compartilhado.** Quando um usuário marca um alerta como
  lido, ele fica lido para todos.
- **Arquivos gerados do Flutter.** Rodar `flutter pub get` ou `flutter build`
  no Windows faz o git mostrar 7 arquivos de `linux/`, `macos/` e `windows/`
  como modificados. A diferença é só o final de linha. Para descartar, use
  `git checkout -- linux macos windows` dentro da pasta do app.

## Branches

O repositório segue GitFlow: `main` para produção, `develop` para
homologação, e `feature/*`, `release/*` e `hotfix/*` para o trabalho do dia a
dia. Novas funcionalidades saem de `develop` e voltam para ela por pull
request.

## Links

- Quadro de atividades: https://github.com/users/prfigueiredo/projects/2
- Issues: https://github.com/prfigueiredo/app-iot-uff-2026/issues
