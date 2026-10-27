# Registro de modificações

Mudanças relevantes de cada versão do CPD Monitor.

## V3: Histórico

Branch `feature/v3-historico`.

### Adicionado

- PostgreSQL em Docker (`cpd-monitor/backend/docker-compose.yml`), na porta
  5433 e aceitando conexões só do próprio computador.
- Alertas guardados no PostgreSQL. Eles sobrevivem ao reinício do backend
  (issue [#17](https://github.com/prfigueiredo/app-iot-uff-2026/issues/17)).
- Média por hora da temperatura e da umidade, com mínimo, máximo e número de
  leituras de cada período. Períodos sem leitura ficam como lacuna, sem valor
  inventado.
- Rotas `GET /historico/medias?horas=` e `GET /historico/alertas?dias=&condicao=`.
- No app: seção Histórico na tela Sensores, com gráfico (média, mínimo e
  máximo), tabela de registros e escolha entre 24 h, 7 dias e 30 dias.
- No app: aba Histórico na tela Alertas, com filtros de período e de condição.
- Variáveis `ARMAZENAMENTO` (`postgres` ou `memoria`) e
  `HISTORICO_INTERVALO_MIN` (médias de 1 minuto para demonstrações).
- Variável `ORION_PORTA` para subir o Orion em outra porta quando a 1026 está
  ocupada.
- Testes do armazenamento rodando nas versões em memória e PostgreSQL, testes
  do cálculo das médias e testes das rotas de histórico.

### Corrigido

- Rota antiga de envio direto do sensor ainda existia e respondia com erro 500.
- Alerta repetido após reiniciar o backend com um problema ainda em andamento.
  Agora o nível de cada condição é recuperado do último alerta guardado.
- Tela Sensores ficava carregando para sempre após erro de rede.
- Links quebrados para a pasta `docs`, que agora apontam para as issues
  [#12](https://github.com/prfigueiredo/app-iot-uff-2026/issues/12),
  [#15](https://github.com/prfigueiredo/app-iot-uff-2026/issues/15) e
  [#16](https://github.com/prfigueiredo/app-iot-uff-2026/issues/16).

### Alterado

- O backend não sobe sem o PostgreSQL e explica o motivo. Para rodar sem banco,
  use `ARMAZENAMENTO=memoria`.
- O histórico simulado de `/sensores/historico` e os alertas de exemplo foram
  removidos. O histórico vem só de leituras reais do sensor.
- O Orion passa a aceitar conexões só do próprio computador
  (issue [#19](https://github.com/prfigueiredo/app-iot-uff-2026/issues/19)).

## V2: Alertas

Branch `feature/v2-alertas`.

### Adicionado

- Geração de alertas a partir das leituras do FIWARE, com quatro condições:
  temperatura alta, umidade alta (possível vazamento), ar-condicionado
  desligado e sensor sem comunicação. Ver a issue [#12](https://github.com/prfigueiredo/app-iot-uff-2026/issues/12).
- Um alerta por mudança de nível, com histerese e aviso de normalização.
- Umidade publicada pelo sensor do ar-condicionado no FIWARE.
- Opções `--umidade-alvo` e `--status` no sensor simulado.
- Rota `POST /alertas/{id}/lido` e marcação de lido no app.
- No app: contador de não lidos no menu, lista de alertas atualizada em tempo
  real, data e hora de cada alerta, cores por nível nos cards de temperatura e
  umidade.
- Testes e defeitos registrados nas issues [#15](https://github.com/prfigueiredo/app-iot-uff-2026/issues/15) e [#16](https://github.com/prfigueiredo/app-iot-uff-2026/issues/16).

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
