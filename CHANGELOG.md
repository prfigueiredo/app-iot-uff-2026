# Registro de modificações

Mudanças relevantes de cada versão do CPD Monitor.

## V2: Alertas

Branch `feature/v2-alertas`.

### Adicionado

- Geração de alertas a partir das leituras do FIWARE, com quatro condições:
  temperatura alta, umidade alta (possível vazamento), ar-condicionado
  desligado e sensor sem comunicação. Ver
  [`docs/v2-condicoes-de-alerta.md`](docs/v2-condicoes-de-alerta.md).
- Um alerta por mudança de nível, com histerese e aviso de normalização.
- Umidade publicada pelo sensor do ar-condicionado no FIWARE.
- Opções `--umidade-alvo` e `--status` no sensor simulado.
- Rota `POST /alertas/{id}/lido` e marcação de lido no app.
- No app: contador de não lidos no menu, lista de alertas atualizada em tempo
  real, data e hora de cada alerta, cores por nível nos cards de temperatura e
  umidade.
- Relatório de testes em [`docs/v2-relatorio-de-testes.md`](docs/v2-relatorio-de-testes.md).

### Corrigido

- Alerta automático não era salvo e chegava ao app sem `id` e sem data.
- Alerta repetido a cada 15s enquanto a temperatura ficava alta.
- WebSocket de alertas aceitava conexão sem login.
- `/alertas/simular` aceitava severidade e canal inválidos.
- WebSocket do app não reconectava após queda.
- Tela de alertas ficava carregando para sempre após erro de rede.
- Notificação com botão "Ver" nunca sumia e travava as seguintes.

### Alterado

- O WebSocket `/alertas/ws` exige `{"token": "<token de login>"}` como
  primeira mensagem e responde `{"tipo": "autenticado"}`.
- `sensor_calor_alerta` passa a seguir o nível crítico de temperatura,
  incluindo a histerese.
- A umidade deixa de ser simulada dentro do backend e passa a vir do FIWARE.
  Ela fica vazia até o sensor publicar.

## V1: Monitoramento dinâmico do ar-condicionado

Branch `feature/sensor-ar-condicionado`.

### Adicionado

- FIWARE Orion e MongoDB em Docker (`cpd-monitor/fiware`).
- Sensor simulado que publica a temperatura do ar-condicionado no Orion.
- Leitura do Orion pelo backend a cada 2s.
- Atualização automática das telas Painel e Sensores a cada 5s.
- Testes automatizados do backend, incluindo integração com o Orion.
- Instruções de execução e testes no README.

### Corrigido

- O app mostrava 21,5°C fixo antes de existir qualquer sensor. Agora mostra
  "Aguardando sensor".
- O card do ar-condicionado mostrava apenas "ligado", sem temperatura.
- O teste do Flutter não compilava (`MyApp` inexistente).
- Arquivos `.pyc` estavam versionados no git.
