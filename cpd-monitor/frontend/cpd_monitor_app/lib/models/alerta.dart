class Alerta {
  final int id;
  final String titulo;
  final String descricao;
  final String severidade; // alta | media | baixa
  final String canal; // sms | email | push
  final DateTime data;
  final bool lido;

  Alerta({
    required this.id,
    required this.titulo,
    required this.descricao,
    required this.severidade,
    required this.canal,
    required this.data,
    required this.lido,
  });

  factory Alerta.fromJson(Map<String, dynamic> json) {
    return Alerta(
      id: json['id'] ?? 0,
      titulo: json['titulo'],
      descricao: json['descricao'],
      severidade: json['severidade'] ?? 'media',
      canal: json['canal'] ?? 'push',
      data: json['data'] != null ? DateTime.parse(json['data']) : DateTime.now(),
      lido: json['lido'] ?? false,
    );
  }
}

class PerfilAlerta {
  final int id;
  final String nome;
  final String periodo;
  final List<String> canais;
  final String equipe;
  final bool ativo;

  PerfilAlerta({
    required this.id,
    required this.nome,
    required this.periodo,
    required this.canais,
    required this.equipe,
    required this.ativo,
  });

  factory PerfilAlerta.fromJson(Map<String, dynamic> json) {
    return PerfilAlerta(
      id: json['id'],
      nome: json['nome'],
      periodo: json['periodo'],
      canais: List<String>.from(json['canais']),
      equipe: json['equipe'],
      ativo: json['ativo'] ?? true,
    );
  }
}
