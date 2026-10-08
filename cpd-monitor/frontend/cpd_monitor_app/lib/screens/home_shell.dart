import 'dart:async';
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/alerta.dart';
import '../services/api_service.dart';
import '../services/auth_provider.dart';
import '../services/alerta_ws_service.dart';
import '../services/alertas_provider.dart';
import '../widgets/severidade.dart';
import 'dashboard_screen.dart';
import 'sensores_screen.dart';
import 'servicos_screen.dart';
import 'logs_screen.dart';
import 'alertas_screen.dart';
import 'perfil_screen.dart';
import 'login_screen.dart';

class HomeShell extends StatefulWidget {
  const HomeShell({super.key});

  @override
  State<HomeShell> createState() => _HomeShellState();
}

class _HomeShellState extends State<HomeShell> {
  static const _abaAlertas = 4;

  int _abaAtual = 0;
  late final AlertaWebSocketService _wsService;
  late final AlertasProvider _alertasProvider;
  StreamSubscription<Alerta>? _assinaturaNotificacoes;

  final _telas = const [
    DashboardScreen(),
    SensoresScreen(),
    ServicosScreen(),
    LogsScreen(),
    AlertasScreen(),
    PerfilScreen(),
  ];

  @override
  void initState() {
    super.initState();
    _wsService = AlertaWebSocketService(obterToken: () => ApiService.token ?? '');
    _alertasProvider = AlertasProvider(
      buscar: ApiService.listarAlertas,
      marcarLidoNoBackend: ApiService.marcarAlertaLido,
      tempoReal: _wsService.alertas,
      conectado: _wsService.conectado,
    );
    _assinaturaNotificacoes = _wsService.alertas.listen(_notificar);
    _alertasProvider.carregar();
    _wsService.conectar();
  }

  void _notificar(Alerta alerta) {
    if (!mounted) return;
    final snackBar = SnackBar(
      // A SnackBar with an action persists by default, which would block
      // every later alert behind it.
      persist: false,
      backgroundColor: corDaSeveridade(alerta.severidade),
      content: Row(
        children: [
          Icon(iconeDaSeveridade(alerta.severidade), color: Colors.white),
          const SizedBox(width: 12),
          Expanded(child: Text(alerta.titulo)),
        ],
      ),
      action: SnackBarAction(
        label: 'Ver',
        textColor: Colors.white,
        onPressed: () => setState(() => _abaAtual = _abaAlertas),
      ),
      duration: const Duration(seconds: 5),
    );
    // The newest alert replaces the one on screen instead of waiting in a queue.
    ScaffoldMessenger.of(context)
      ..hideCurrentSnackBar()
      ..showSnackBar(snackBar);
  }

  @override
  void dispose() {
    _assinaturaNotificacoes?.cancel();
    _alertasProvider.dispose();
    _wsService.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    if (!auth.logado) {
      // Sessão perdida (ex.: token expirado) - volta para o login.
      WidgetsBinding.instance.addPostFrameCallback((_) {
        Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const LoginScreen()));
      });
      return const SizedBox.shrink();
    }

    return ChangeNotifierProvider<AlertasProvider>.value(
      value: _alertasProvider,
      child: Scaffold(
        body: SafeArea(child: _telas[_abaAtual]),
        bottomNavigationBar: Consumer<AlertasProvider>(
          builder: (context, alertas, _) => NavigationBar(
            selectedIndex: _abaAtual,
            onDestinationSelected: (i) => setState(() => _abaAtual = i),
            destinations: [
              const NavigationDestination(icon: Icon(Icons.dashboard_outlined), selectedIcon: Icon(Icons.dashboard), label: 'Painel'),
              const NavigationDestination(icon: Icon(Icons.sensors_outlined), selectedIcon: Icon(Icons.sensors), label: 'Sensores'),
              const NavigationDestination(icon: Icon(Icons.dns_outlined), selectedIcon: Icon(Icons.dns), label: 'Serviços'),
              const NavigationDestination(icon: Icon(Icons.article_outlined), selectedIcon: Icon(Icons.article), label: 'Logs'),
              NavigationDestination(
                icon: Badge.count(
                  count: alertas.naoLidos,
                  isLabelVisible: alertas.naoLidos > 0,
                  child: const Icon(Icons.notifications_outlined),
                ),
                selectedIcon: Badge.count(
                  count: alertas.naoLidos,
                  isLabelVisible: alertas.naoLidos > 0,
                  child: const Icon(Icons.notifications),
                ),
                label: 'Alertas',
              ),
              const NavigationDestination(icon: Icon(Icons.person_outline), selectedIcon: Icon(Icons.person), label: 'Perfil'),
            ],
          ),
        ),
      ),
    );
  }
}
