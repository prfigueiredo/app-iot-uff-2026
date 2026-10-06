# CPD Monitor (app-iot-uff-2026)

Aplicativo de monitoramento do CPD, evoluído na disciplina de Gerência de
Projeto e Manutenção de Software (GPMS) da UFF, 2026.2.

O protótipo original usa dados simulados em memória. O projeto substitui essas
partes, em três versões incrementais, por dados dinâmicos integrados ao
FIWARE.

| Versão | Escopo | Situação |
|---|---|---|
| V1 | Temperatura do ar-condicionado dinâmica via FIWARE | Backend pronto e testado. Validação do app em andamento |
| V2 | Alertas a partir dos dados monitorados | Não iniciada |
| V3 | Histórico da temperatura e dos alertas | Não iniciada |

## Arquitetura

```
sensor simulado ──publica──▶ FIWARE Orion ◀──lê a cada 2s── backend (FastAPI) ──▶ app (Flutter)
```

- O **sensor simulado** publica a temperatura do ar-condicionado no Orion.
- O **FIWARE Orion** é o broker intermediário. Um sensor novo só precisa
  publicar uma entidade, sem mudança no backend.
- O **backend** lê a entidade do Orion e entrega ao app em `/sensores/atual`.
- O **app** mostra a temperatura e se atualiza sozinho a cada 5s.

| Pasta | Conteúdo |
|---|---|
| [`cpd-monitor/fiware`](cpd-monitor/fiware/README.md) | Orion + MongoDB em Docker |
| [`cpd-monitor/sensor_simulado`](cpd-monitor/sensor_simulado/ar_condicionado.py) | Sensor simulado do ar-condicionado |
| [`cpd-monitor/backend`](cpd-monitor/backend/README.md) | API em FastAPI |
| [`cpd-monitor/frontend/cpd_monitor_app`](cpd-monitor/frontend/cpd_monitor_app/README.md) | App em Flutter |

## Pré-requisitos

- Python 3.10 ou mais novo
- Docker Desktop, para o FIWARE
- Flutter SDK, para o app ([guia oficial](https://docs.flutter.dev/get-started))
- Chrome ou Edge, para rodar o app no navegador

## Como rodar

Todos os comandos partem da raiz do repositório. Use um terminal para cada
parte e deixe todos abertos.

### 1. FIWARE

Com o Docker Desktop aberto:

```bash
docker compose -f cpd-monitor/fiware/docker-compose.yml up -d
```

Para conferir, `http://127.0.0.1:1026/version` deve responder com a versão do
Orion.

### 2. Backend

```bash
cd cpd-monitor/backend
python -m venv venv
./venv/Scripts/python -m pip install -r requirements-dev.txt
./venv/Scripts/python -m uvicorn app.main:app --port 8000
```

No Linux ou macOS, troque `./venv/Scripts/python` por `./venv/bin/python`.

A API fica em `http://127.0.0.1:8000`, com a documentação interativa em
`http://127.0.0.1:8000/docs`. Enquanto nenhum sensor publicou, o log mostra
`FIWARE: aguardando o sensor publicar`.

### 3. Sensor simulado

```bash
python cpd-monitor/sensor_simulado/ar_condicionado.py --intervalo 2
```

Cada linha deve terminar em `Orion HTTP 204`. Opções úteis:

- `--alvo 31` faz a temperatura subir até 31°C, para provocar o alerta de
  calor (o limite é 28°C).
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

O teste de integração (`tests/test_integracao_fiware.py`) cobre o fluxo
sensor → FIWARE → backend → resposta do app. Ele só roda com o Orion no ar. Sem
o Orion, aparece como pulado (`skipped`).

App, dentro de `cpd-monitor/frontend/cpd_monitor_app`:

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

## Configuração

O backend lê as configurações de **variáveis de ambiente**. O arquivo
[`.env.example`](cpd-monitor/backend/.env.example) só documenta os valores
padrão. Ele não é carregado automaticamente.

| Variável | Padrão | Uso |
|---|---|---|
| `FIWARE_URL` | `http://127.0.0.1:1026` | Endereço do Orion |
| `FIWARE_ENTIDADE_AR_CONDICIONADO` | `urn:ngsi-ld:ArCondicionado:cpd-01` | Entidade lida pelo backend |
| `FIWARE_INTERVALO_S` | `2` | Segundos entre leituras do Orion |
| `LIMITE_TEMPERATURA_C` | `28` | Acima disso, o sensor de calor dispara |

## Problemas conhecidos

- **Use `127.0.0.1` em vez de `localhost` nos scripts.** No Windows, cada
  requisição para `localhost` levou cerca de 2s, porque o sistema tenta o IPv6
  antes e o servidor só escuta no IPv4. Com `127.0.0.1` levou cerca de 1 ms.
- **Emulador Android:** o app aponta para `localhost`. No emulador, troque por
  `10.0.2.2` em `lib/services/api_service.dart`.
- **O Orion não tem autenticação.** Qualquer máquina na rede consegue publicar
  leituras. O FIWARE resolve isso com componentes próprios de segurança, que
  estão fora do escopo atual.
- **O app mostra apenas o ar-condicionado `cpd-01`.** Outros sensores já
  conseguem publicar no Orion, mas exibir vários na tela exige mudar o modelo
  de dados.
- **Alerta de calor repetido.** Enquanto a temperatura passa de 28°C, o app
  recebe uma notificação nova a cada 15s. Isso vem do protótipo e será tratado
  na V2.

## Branches

O repositório segue GitFlow: `main` para produção, `develop` para
homologação, e `feature/*`, `release/*` e `hotfix/*` para o trabalho do dia a
dia. Novas funcionalidades saem de `develop` e voltam para ela por pull
request.

## Links

- Quadro de atividades: https://github.com/users/prfigueiredo/projects/2
