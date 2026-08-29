// Conecta ao canal de push notifications do backend (/alertas/ws) e expõe
// um Stream com cada novo alerta recebido em tempo real.
import 'dart:async';
import 'dart:convert';
import 'package:web_socket_channel/web_socket_channel.dart';

import 'api_service.dart';

class AlertaWebSocketService {
  WebSocketChannel? _channel;
  final _controller = StreamController<Map<String, dynamic>>.broadcast();

  Stream<Map<String, dynamic>> get alertas => _controller.stream;

  void conectar() {
    _channel = WebSocketChannel.connect(Uri.parse('${ApiService.wsUrl}/alertas/ws'));
    _channel!.stream.listen(
      (mensagem) {
        final data = jsonDecode(mensagem);
        if (data['tipo'] == 'novo_alerta') {
          _controller.add(data['alerta']);
        }
      },
      onError: (_) {},
      onDone: () {},
    );
  }

  void desconectar() {
    _channel?.sink.close();
  }
}
