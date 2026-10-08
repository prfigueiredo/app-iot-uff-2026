import 'dart:async';
import 'package:flutter_test/flutter_test.dart';

import 'package:cpd_monitor_app/models/alerta.dart';
import 'package:cpd_monitor_app/services/alertas_provider.dart';

Alerta alerta(int id, {bool lido = false, String severidade = 'alta'}) => Alerta(
      id: id,
      titulo: 'Alerta $id',
      descricao: 'descrição',
      severidade: severidade,
      canal: 'push',
      condicao: 'temperatura',
      data: DateTime(2026, 10, 6, 12, 0, id),
      lido: lido,
    );

void main() {
  late StreamController<Alerta> tempoReal;
  late StreamController<bool> conectado;
  late List<Alerta> doBackend;
  late List<int> marcadosNoBackend;
  late int buscas;
  late AlertasProvider provider;

  setUp(() {
    tempoReal = StreamController<Alerta>.broadcast();
    conectado = StreamController<bool>.broadcast();
    doBackend = [alerta(2), alerta(1, lido: true)];
    marcadosNoBackend = [];
    buscas = 0;
    provider = AlertasProvider(
      buscar: () async {
        buscas++;
        return List.of(doBackend);
      },
      marcarLidoNoBackend: (id) async => marcadosNoBackend.add(id),
      tempoReal: tempoReal.stream,
      conectado: conectado.stream,
    );
  });

  tearDown(() {
    provider.dispose();
    tempoReal.close();
    conectado.close();
  });

  test('carrega a lista e conta os não lidos', () async {
    await provider.carregar();
    expect(provider.alertas.map((a) => a.id), [2, 1]);
    expect(provider.naoLidos, 1);
  });

  test('alerta em tempo real entra no topo sem recarregar', () async {
    await provider.carregar();
    tempoReal.add(alerta(3));
    await pumpEventQueue();
    expect(provider.alertas.map((a) => a.id), [3, 2, 1]);
    expect(provider.naoLidos, 2);
    expect(buscas, 1);
  });

  test('o mesmo alerta chegando duas vezes não duplica', () async {
    await provider.carregar();
    tempoReal.add(alerta(2));
    await pumpEventQueue();
    expect(provider.alertas.map((a) => a.id), [2, 1]);
  });

  test('marcar como lido avisa o backend e atualiza o contador', () async {
    await provider.carregar();
    await provider.marcarComoLido(provider.alertas.first);
    expect(marcadosNoBackend, [2]);
    expect(provider.naoLidos, 0);
  });

  test('alerta já lido não chama o backend de novo', () async {
    await provider.carregar();
    await provider.marcarComoLido(provider.alertas.last);
    expect(marcadosNoBackend, isEmpty);
  });

  test('ao reconectar, recarrega para pegar alertas perdidos', () async {
    await provider.carregar();
    doBackend = [alerta(5), ...doBackend];
    conectado.add(true);
    await pumpEventQueue();
    expect(buscas, 2);
    expect(provider.alertas.first.id, 5);
  });

  test('erro ao carregar fica disponível para a tela', () async {
    final comErro = AlertasProvider(
      buscar: () async => throw Exception('Backend fora do ar'),
      marcarLidoNoBackend: (_) async {},
      tempoReal: const Stream.empty(),
    );
    await comErro.carregar();
    expect(comErro.erro, 'Backend fora do ar');
    expect(comErro.carregando, isFalse);
    comErro.dispose();
  });

  test('Alerta.fromJson lê o formato enviado pelo backend', () {
    final a = Alerta.fromJson({
      'id': 7,
      'titulo': 'Umidade elevada',
      'descricao': 'Verifique se há vazamento de água.',
      'severidade': 'media',
      'canal': 'push',
      'condicao': 'umidade',
      'data': '2026-10-06T12:00:05.123456',
      'lido': false,
    });
    expect(a.id, 7);
    expect(a.condicao, 'umidade');
    expect(a.data.second, 5);
    expect(a.marcadoComoLido().lido, isTrue);
  });
}
