class ServicoZabbix {
  final int id;
  final String nome;
  final String tipo;
  final String status; // up | warning | down
  final double uptimePct;

  ServicoZabbix({required this.id, required this.nome, required this.tipo, required this.status, required this.uptimePct});

  factory ServicoZabbix.fromJson(Map<String, dynamic> json) {
    return ServicoZabbix(
      id: json['id'],
      nome: json['nome'],
      tipo: json['tipo'],
      status: json['status'],
      uptimePct: (json['uptime_pct'] as num).toDouble(),
    );
  }
}
