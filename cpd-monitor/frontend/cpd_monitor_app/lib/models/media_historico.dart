/// Temperature and humidity summary of one stored period (one hour by default).
class MediaHistorico {
  final DateTime inicio;
  final int minutos;
  final int amostras;
  final double temperaturaMedia;
  final double temperaturaMin;
  final double temperaturaMax;
  // Null when the sensor sent no humidity during the period.
  final double? umidadeMedia;
  final double? umidadeMin;
  final double? umidadeMax;

  MediaHistorico({
    required this.inicio,
    required this.minutos,
    required this.amostras,
    required this.temperaturaMedia,
    required this.temperaturaMin,
    required this.temperaturaMax,
    this.umidadeMedia,
    this.umidadeMin,
    this.umidadeMax,
  });

  DateTime get fim => inicio.add(Duration(minutes: minutos));

  factory MediaHistorico.fromJson(Map<String, dynamic> json) {
    double? opcional(String chave) => (json[chave] as num?)?.toDouble();
    return MediaHistorico(
      inicio: DateTime.parse(json['inicio']),
      minutos: json['minutos'],
      amostras: json['amostras'],
      temperaturaMedia: (json['temperatura_media'] as num).toDouble(),
      temperaturaMin: (json['temperatura_min'] as num).toDouble(),
      temperaturaMax: (json['temperatura_max'] as num).toDouble(),
      umidadeMedia: opcional('umidade_media'),
      umidadeMin: opcional('umidade_min'),
      umidadeMax: opcional('umidade_max'),
    );
  }
}

class HistoricoMedias {
  final int intervaloMin;
  final List<MediaHistorico> medias; // oldest first

  HistoricoMedias({required this.intervaloMin, required this.medias});

  factory HistoricoMedias.fromJson(Map<String, dynamic> json) => HistoricoMedias(
        intervaloMin: json['intervalo_min'],
        medias: (json['medias'] as List).map((e) => MediaHistorico.fromJson(e)).toList(),
      );
}
