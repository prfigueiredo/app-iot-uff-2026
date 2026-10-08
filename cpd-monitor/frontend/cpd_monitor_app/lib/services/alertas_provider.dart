import 'dart:async';
import 'package:flutter/foundation.dart';

import '../models/alerta.dart';

/// Single source of alerts for every screen. REST loads the list, the
/// WebSocket adds new alerts as they happen, and screens only read from here.
class AlertasProvider extends ChangeNotifier {
  final Future<List<Alerta>> Function() buscar;
  final Future<void> Function(int id) marcarLidoNoBackend;

  List<Alerta> _alertas = [];
  bool _carregando = false;
  String? _erro;
  bool _descartado = false;
  StreamSubscription<Alerta>? _assinaturaAlertas;
  StreamSubscription<bool>? _assinaturaConexao;

  AlertasProvider({
    required this.buscar,
    required this.marcarLidoNoBackend,
    required Stream<Alerta> tempoReal,
    Stream<bool>? conectado,
  }) {
    _assinaturaAlertas = tempoReal.listen(_adicionar);
    // After a reconnection, reload to pick up alerts generated while offline.
    _assinaturaConexao = conectado?.listen((ok) {
      if (ok) carregar();
    });
  }

  List<Alerta> get alertas => List.unmodifiable(_alertas);
  bool get carregando => _carregando;
  String? get erro => _erro;
  int get naoLidos => _alertas.where((a) => !a.lido).length;

  Future<void> carregar() async {
    _carregando = true;
    _erro = null;
    notifyListeners();
    try {
      _alertas = await buscar();
    } catch (e) {
      _erro = e.toString().replaceFirst('Exception: ', '');
    }
    // The user may log out while the request is in flight.
    if (_descartado) return;
    _carregando = false;
    notifyListeners();
  }

  void _adicionar(Alerta alerta) {
    // The same alert can arrive by WebSocket and by a reload, so ids are unique here.
    _alertas = [alerta, ..._alertas.where((a) => a.id != alerta.id)];
    notifyListeners();
  }

  Future<void> marcarComoLido(Alerta alerta) async {
    if (alerta.lido) return;
    await marcarLidoNoBackend(alerta.id);
    if (_descartado) return;
    _alertas = [for (final a in _alertas) a.id == alerta.id ? a.marcadoComoLido() : a];
    notifyListeners();
  }

  @override
  void dispose() {
    _descartado = true;
    _assinaturaAlertas?.cancel();
    _assinaturaConexao?.cancel();
    super.dispose();
  }
}
