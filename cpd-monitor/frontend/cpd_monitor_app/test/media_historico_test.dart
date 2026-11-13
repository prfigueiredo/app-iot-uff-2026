import 'package:flutter_test/flutter_test.dart';

import 'package:cpd_monitor_app/models/media_historico.dart';

void main() {
  test('HistoricoMedias lê a resposta de /historico/medias', () {
    final historico = HistoricoMedias.fromJson({
      'intervalo_min': 60,
      'medias': [
        {
          'inicio': '2026-10-26T10:00:00',
          'minutos': 60,
          'amostras': 720,
          'temperatura_media': 23.4,
          'temperatura_min': 22,
          'temperatura_max': 31.2,
          'amostras_umidade': 720,
          'umidade_media': 48.5,
          'umidade_min': 45.0,
          'umidade_max': 52.0,
        },
      ],
    });

    expect(historico.intervaloMin, 60);
    final media = historico.medias.single;
    expect(media.inicio, DateTime(2026, 10, 26, 10));
    expect(media.fim, DateTime(2026, 10, 26, 11));
    expect(media.amostras, 720);
    expect(media.temperaturaMin, 22.0); // an int in the JSON still becomes a double
    expect(media.temperaturaMax, 31.2);
    expect(media.umidadeMedia, 48.5);
  });

  test('MediaHistorico aceita um período sem umidade', () {
    final media = MediaHistorico.fromJson({
      'inicio': '2026-10-26T10:00:00',
      'minutos': 1,
      'amostras': 12,
      'temperatura_media': 22.0,
      'temperatura_min': 21.5,
      'temperatura_max': 22.5,
      'amostras_umidade': 0,
      'umidade_media': null,
      'umidade_min': null,
      'umidade_max': null,
    });

    expect(media.umidadeMedia, isNull);
    expect(media.fim, DateTime(2026, 10, 26, 10, 1));
  });

  test('HistoricoMedias vazio', () {
    final historico = HistoricoMedias.fromJson({'intervalo_min': 60, 'medias': []});
    expect(historico.medias, isEmpty);
  });
}
