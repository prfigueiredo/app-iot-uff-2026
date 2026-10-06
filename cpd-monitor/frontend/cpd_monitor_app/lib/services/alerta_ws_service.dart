// Conecta ao canal de push notifications do backend (/alertas/ws) e expõe
// um Stream com cada novo alerta recebido em tempo real.
import 'dart:async';
import 'dart:convert';
import 'dart:math';
import 'package:web_socket_channel/web_socket_channel.dart';

import '../models/alerta.dart';
import 'api_service.dart';

class AlertaWebSocketService {
  final String Function() obterToken;
  final _alertas = StreamController<Alerta>.broadcast();
  final _conectado = StreamController<bool>.broadcast();

  WebSocketChannel? _channel;
  Timer? _timerReconexao;
  int _tentativas = 0;
  bool _ativo = false;

  AlertaWebSocketService({required this.obterToken});

  Stream<Alerta> get alertas => _alertas.stream;

  /// Emits true once the backend confirms the subscription and false when the
  /// connection drops, so the app can reload anything missed while offline.
  Stream<bool> get conectado => _conectado.stream;

  void conectar() {
    _ativo = true;
    _abrir();
  }

  void dispose() {
    desconectar();
    _alertas.close();
    _conectado.close();
  }

  Future<void> _abrir() async {
    final channel = WebSocketChannel.connect(Uri.parse('${ApiService.wsUrl}/alertas/ws'));
    _channel = channel;
    try {
      await channel.ready;
    } catch (_) {
      _agendarReconexao();
      return;
    }
    if (!_ativo) {
      channel.sink.close();
      return;
    }
    // The token goes in the first message, not in the URL, so it never lands in access logs.
    channel.sink.add(jsonEncode({'token': obterToken()}));
    channel.stream.listen(
      (mensagem) {
        final data = jsonDecode(mensagem);
        if (data['tipo'] == 'autenticado') {
          _tentativas = 0;
          _conectado.add(true);
        } else if (data['tipo'] == 'novo_alerta') {
          _alertas.add(Alerta.fromJson(data['alerta']));
        }
      },
      // With cancelOnError, an error ends the subscription without calling
      // onDone, so both paths must schedule the reconnection.
      onError: (_) => _agendarReconexao(),
      onDone: _agendarReconexao,
      cancelOnError: true,
    );
  }

  // Waits 1, 2, 4... up to 30 seconds between attempts, so a backend that is
  // down is not flooded with connections.
  void _agendarReconexao() {
    if (!_ativo) return;
    _conectado.add(false);
    final espera = Duration(seconds: min(30, pow(2, _tentativas).toInt()));
    _tentativas++;
    _timerReconexao = Timer(espera, _abrir);
  }

  void desconectar() {
    _ativo = false;
    _timerReconexao?.cancel();
    _channel?.sink.close();
  }
}
