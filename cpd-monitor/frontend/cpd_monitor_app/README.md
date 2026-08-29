# CPD Monitor - App Flutter

App completo de monitoramento do CPD (TCC), consumindo o backend mockado.

## Como rodar

Este projeto foi montado manualmente (lib/ + pubspec.yaml). Para virar um
projeto Flutter completo (com pastas android/ios/etc.), rode na raiz desta
pasta:

```bash
flutter create . --org br.rj.niteroi.sti --project-name cpd_monitor_app
flutter pub get
flutter run
```

O comando `flutter create .` preenche as pastas de plataforma sem sobrescrever
o `lib/` que já está pronto.

**Importante:** rode o backend (`cpd-monitor/backend`) antes de abrir o app -
veja o README dele. Sem o backend rodando, as telas mostram erro de conexão.

## Conectando ao backend

Por padrão o app aponta para `http://localhost:8000` (ver
`lib/services/api_service.dart`, constantes `baseUrl` e `wsUrl`).

- Emulador Android: troque `localhost` por `10.0.2.2`.
- Celular físico na mesma Wi-Fi: troque por `http://<IP-da-sua-máquina>:8000`.
- iOS Simulator / Web / Desktop: `localhost` funciona normalmente.

## Telas

- **Login** - com atalhos para os 3 usuários de teste
- **Painel** - dashboard personalizável (escolha quais métricas aparecem)
- **Sensores** - leituras atuais + gráficos de histórico (temperatura/umidade)
- **Serviços** - status estilo UptimeRobot dos serviços monitorados (Zabbix)
- **Logs** - logs do GrayLog com filtro por nível
- **Alertas** - alertas recebidos + perfis de alerta personalizados (criação
  restrita a admin/operador) + push notification em tempo real via WebSocket
- **Perfil** - dados do usuário, botão de simular alerta (admin/operador), logout

## Status

App completo com dados mockados - pronto para ser testado por usuários.
Próxima etapa: modelagem de banco de dados real e integração real com
GrayLog/Zabbix/sensores, sem alterar as telas.
