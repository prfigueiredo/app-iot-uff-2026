import 'package:flutter_test/flutter_test.dart';

import 'package:cpd_monitor_app/models/leitura_sensor.dart';

void main() {
  test('LeituraSensor reads the air conditioning fields sent by the backend', () {
    final leitura = LeituraSensor.fromJson({
      'temperatura_c': 28.5,
      'umidade_pct': 48,
      'combustivel_gerador_pct': 82.0,
      'pessoas_presentes': 1,
      'sensor_calor_alerta': true,
      'ar_condicionado_status': 'ligado',
      'atualizado_em': '2026-10-05T21:24:45.123456',
    });

    expect(leitura.temperaturaC, 28.5);
    expect(leitura.umidadePct, 48.0);
    expect(leitura.sensorCalorAlerta, isTrue);
    expect(leitura.arCondicionadoStatus, 'ligado');
    expect(leitura.atualizadoEm.second, 45);
  });
}
