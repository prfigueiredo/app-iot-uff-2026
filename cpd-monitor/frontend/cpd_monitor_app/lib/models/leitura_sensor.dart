class LeituraSensor {
  // Null until the air conditioning sensor publishes its first reading via FIWARE.
  final double? temperaturaC;
  final DateTime? temperaturaAtualizadaEm;
  final double umidadePct;
  final double combustivelGeradorPct;
  final int pessoasPresentes;
  final bool sensorPresencaAtivo;
  final bool sensorCalorAlerta;
  final String? arCondicionadoStatus;
  final DateTime atualizadoEm;

  LeituraSensor({
    required this.temperaturaC,
    this.temperaturaAtualizadaEm,
    required this.umidadePct,
    required this.combustivelGeradorPct,
    required this.pessoasPresentes,
    this.sensorPresencaAtivo = false,
    this.sensorCalorAlerta = false,
    this.arCondicionadoStatus,
    required this.atualizadoEm,
  });

  factory LeituraSensor.fromJson(Map<String, dynamic> json) {
    return LeituraSensor(
      temperaturaC: (json['temperatura_c'] as num?)?.toDouble(),
      temperaturaAtualizadaEm:
          json['temperatura_atualizada_em'] != null ? DateTime.parse(json['temperatura_atualizada_em']) : null,
      umidadePct: (json['umidade_pct'] as num).toDouble(),
      combustivelGeradorPct: (json['combustivel_gerador_pct'] as num).toDouble(),
      pessoasPresentes: json['pessoas_presentes'] ?? 0,
      sensorPresencaAtivo: json['sensor_presenca_ativo'] ?? false,
      sensorCalorAlerta: json['sensor_calor_alerta'] ?? false,
      arCondicionadoStatus: json['ar_condicionado_status'],
      atualizadoEm: DateTime.parse(json['atualizado_em']),
    );
  }
}
