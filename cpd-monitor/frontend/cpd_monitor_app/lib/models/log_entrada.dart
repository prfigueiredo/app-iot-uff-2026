class LogEntrada {
  final int id;
  final String nivel;
  final String origem;
  final String mensagem;
  final DateTime data;

  LogEntrada({required this.id, required this.nivel, required this.origem, required this.mensagem, required this.data});

  factory LogEntrada.fromJson(Map<String, dynamic> json) {
    return LogEntrada(
      id: json['id'],
      nivel: json['nivel'],
      origem: json['origem'],
      mensagem: json['mensagem'],
      data: DateTime.parse(json['data']),
    );
  }
}
