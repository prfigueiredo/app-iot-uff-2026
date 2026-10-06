class Alerta {
  final int id;
  final String titulo;
  final String descricao;
  final String severidade; // alta | media | baixa
  final String canal; // sms | email | push
  // temperatura | umidade | ar_desligado | sem_comunicacao, or null for manual alerts.
  final String? condicao;
  final DateTime data;
  final bool lido;

  Alerta({
    required this.id,
    required this.titulo,
    required this.descricao,
    required this.severidade,
    required this.canal,
    this.condicao,
    required this.data,
    required this.lido,
  });

  factory Alerta.fromJson(Map<String, dynamic> json) {
    return Alerta(
      id: json['id'],
      titulo: json['titulo'],
      descricao: json['descricao'],
      severidade: json['severidade'],
      canal: json['canal'],
      condicao: json['condicao'],
      data: DateTime.parse(json['data']),
      lido: json['lido'],
    );
  }

  Alerta marcadoComoLido() => Alerta(
        id: id,
        titulo: titulo,
        descricao: descricao,
        severidade: severidade,
        canal: canal,
        condicao: condicao,
        data: data,
        lido: true,
      );
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
