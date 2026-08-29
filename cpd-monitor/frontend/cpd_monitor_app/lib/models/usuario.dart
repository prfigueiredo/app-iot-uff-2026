class Usuario {
  final int id;
  final String nome;
  final String usuario;
  final String perfil; // admin | operador | visualizador

  Usuario({required this.id, required this.nome, required this.usuario, required this.perfil});

  factory Usuario.fromJson(Map<String, dynamic> json) {
    return Usuario(
      id: json['id'],
      nome: json['nome'],
      usuario: json['usuario'],
      perfil: json['perfil'],
    );
  }
}
