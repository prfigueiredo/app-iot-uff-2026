# V2: relatório de testes

Atividade 4.4 da EAP (realizar testes e correções da Versão 2).
Executado em 05/10/2026 na branch `feature/v2-alertas`.

Ambiente: Windows 11, Python 3.10, Flutter 3.47.6 (Dart 3.13.5), FIWARE Orion
4.5.0 com MongoDB 8.0 em Docker, app compilado para web e aberto no navegador.

## Critérios de aceitação da V2

| Critério (plano, seção 2.1.5) | Resultado | Evidência |
|---|---|---|
| Forem definidas as condições que geram um alerta | ✅ | [`v2-condicoes-de-alerta.md`](v2-condicoes-de-alerta.md), pendente de validação do PO |
| O sistema identificar quando uma dessas condições ocorrer | ✅ | Testes de regras e de monitor, CT-V2-01 a CT-V2-08 |
| O alerta for gerado e exibido na interface | ✅ | CT-V2-01 a CT-V2-10, verificados no app rodando |
| O funcionamento dos alertas for validado por testes | ✅ | 58 testes no backend, 10 no app, roteiro manual abaixo |

## Testes automatizados

| Conjunto | Testes | Resultado |
|---|---|---|
| Backend (`python -m pytest tests`) | 58 | 58 passaram |
| App (`flutter test`) | 10 | 10 passaram |
| Análise estática do app (`flutter analyze`) | | nenhum problema |

O backend inclui dois testes de integração com o Orion real: sensor → FIWARE
→ backend → app, e sensor → FIWARE → alerta → app.

**Teste de mutação.** Para conferir se os testes pegam defeitos de verdade,
quatro defeitos foram reintroduzidos de propósito, um de cada vez:

| Defeito reintroduzido | Testes que falharam |
|---|---|
| Alertar a cada leitura acima do limite (comportamento do protótipo) | 3 |
| Remover a histerese | 2 |
| Não salvar o alerta gerado (comportamento do protótipo) | 2 |
| Usar `>=` em vez de `>` no limite | 1 |

Todos os quatro foram detectados.

## Roteiro manual (app rodando no navegador)

| # | Ação | Esperado | Resultado |
|---|---|---|---|
| CT-V2-01 | Sensor sobe de 25°C para 31°C | Ao passar de 26°C, notificação laranja "Temperatura em atenção" e card de temperatura laranja, "Atenção" | ✅ |
| CT-V2-02 | Temperatura continua subindo | Ao passar de 28°C, um único alerta "Temperatura crítica" e card vermelho, "Crítico" | ✅ |
| CT-V2-03 | Temperatura fica acima de 28°C por vários ciclos | Nenhum alerta novo | ✅ Dois alertas de temperatura no total |
| CT-V2-04 | Umidade sobe de 58% para 80% | "Umidade elevada" acima de 60%, "Umidade crítica" acima de 70% | ✅ |
| CT-V2-05 | Sensor publica status `desligado` | "Ar-condicionado desligado" (alta) | ✅ |
| CT-V2-06 | Temperatura e umidade voltam ao normal | "Temperatura normalizada" e "Umidade normalizada" (baixa) | ✅ |
| CT-V2-07 | Sensor para de publicar | "Sensor sem comunicação" cerca de 60s depois da última leitura | ✅ 62s |
| CT-V2-08 | Sensor volta a publicar, ligado | "Sensor voltou a comunicar" e "Ar-condicionado religado" | ✅ |
| CT-V2-09 | Tocar num alerta não lido | Alerta fica cinza, contador do sino diminui | ✅ |
| CT-V2-10 | Notificação na tela quando chega outra | A nova substitui a antiga, e cada uma some sozinha | ✅ |

No cenário completo foram gerados exatamente 10 alertas, um por transição,
com o sensor publicando a cada 2s.

## Defeitos do protótipo corrigidos na V2

| Defeito | Correção |
|---|---|
| Alerta automático era enviado ao app mas nunca salvo, então não aparecia na lista | Uma única função cria, salva e envia todo alerta |
| Alerta repetido a cada 15s enquanto a temperatura ficava alta | Alerta só na mudança de nível, com histerese |
| Alerta automático sem `id` e sem data. O app escondia isso com `id ?? 0` | O registro é sempre completo e o app não usa mais valores de reserva |
| Condição de alerta praticamente impossível de ocorrer numa demonstração | O sensor simulado aceita `--alvo`, `--umidade-alvo` e `--status` |
| WebSocket de alertas aceitava conexão sem login | O token é exigido na primeira mensagem, e tentativas inválidas ficam registradas |
| `/alertas/simular` aceitava qualquer severidade e título vazio | Validação dos campos |
| Não havia como marcar alerta como lido | Rota `POST /alertas/{id}/lido` e toque no alerta no app |
| Lista de alertas não atualizava ao chegar alerta novo | Fonte única de alertas no app (`AlertasProvider`), alimentada pelo WebSocket |
| WebSocket do app não reconectava e ignorava erros | Reconexão com espera crescente e recarga da lista ao reconectar |
| Tela de alertas girava para sempre em caso de erro de rede | Estados de erro com "Tentar novamente" |
| Card de alerta não mostrava data e hora | Data e hora em cada alerta |

## Defeitos encontrados durante os testes da V2

| Defeito | Como foi encontrado | Correção |
|---|---|---|
| Card dizia "Normal" com 26,8°C enquanto o alerta dizia "atenção" | App rodando | O backend envia ao app os níveis calculados pelo monitor, e os cards usam esses níveis |
| Notificação com botão "Ver" nunca sumia e travava as seguintes na fila | App rodando, confirmado no código do Flutter (`persist = persist ?? action != null`) | `persist: false` e a notificação nova substitui a antiga |
| Teste do WebSocket podia perder o alerta enviado logo após autenticar | Revisão do teste | O servidor confirma a inscrição com `{"tipo": "autenticado"}` |
| Erro de conexão do WebSocket no app não disparava reconexão | Revisão do código | Reconexão agendada tanto no erro quanto no fechamento |

## Limitações conhecidas

- Os alertas ficam em memória e somem ao reiniciar o backend (escopo da V3).
- O estado de "lido" é compartilhado entre todos os usuários.
- O Orion não tem autenticação.
- O teste no app foi feito no navegador. Android e iOS não foram testados.
