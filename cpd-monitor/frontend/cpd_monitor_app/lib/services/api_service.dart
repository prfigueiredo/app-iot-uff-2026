// Serviço central de comunicação HTTP/WebSocket com o backend.
import 'dart:convert';
import 'package:http/http.dart' as http;

import '../models/leitura_sensor.dart';
import '../models/log_entrada.dart';
import '../models/servico_zabbix.dart';
import '../models/alerta.dart';
import '../models/usuario.dart';

class ApiService {
  // Em emulador Android, use 10.0.2.2 no lugar de localhost.
  // Em celular físico na mesma rede, troque pelo IP local da sua máquina.
  static const String baseUrl = 'http://localhost:8000';
  static const String wsUrl = 'ws://localhost:8000';

  static String? _token;

  static void definirToken(String? token) => _token = token;

  static Map<String, String> get _headers => {
        'Content-Type': 'application/json',
        if (_token != null) 'Authorization': 'Bearer $_token',
      };

  static Future<bool> healthCheck() async {
    try {
      final response = await http.get(Uri.parse('$baseUrl/health'));
      if (response.statusCode == 200) {
        final data = jsonDecode(response.body);
        return data['status'] == 'ok';
      }
      return false;
    } catch (_) {
      return false;
    }
  }

  /// Faz login e guarda o token para as próximas requisições.
  /// Retorna o Usuario logado, ou lança uma exceção com a mensagem do backend.
  static Future<Usuario> login(String usuario, String senha) async {
    final response = await http.post(
      Uri.parse('$baseUrl/auth/login'),
      headers: {'Content-Type': 'application/x-www-form-urlencoded'},
      body: {'username': usuario, 'password': senha},
    );
    if (response.statusCode != 200) {
      final erro = jsonDecode(response.body);
      throw Exception(erro['detail'] ?? 'Falha no login');
    }
    final data = jsonDecode(response.body);
    _token = data['access_token'];
    return Usuario.fromJson(data['usuario']);
  }

  static void logout() => _token = null;

  static Future<LeituraSensor> leituraAtual() async {
    final r = await http.get(Uri.parse('$baseUrl/sensores/atual'), headers: _headers);
    _verificarErro(r);
    return LeituraSensor.fromJson(jsonDecode(r.body));
  }

  static Future<List<LeituraSensor>> historicoSensores({int limite = 48}) async {
    final r = await http.get(Uri.parse('$baseUrl/sensores/historico?limite=$limite'), headers: _headers);
    _verificarErro(r);
    final lista = jsonDecode(r.body) as List;
    return lista.map((e) => LeituraSensor.fromJson(e)).toList();
  }

  static Future<List<LogEntrada>> logsGraylog({String? nivel}) async {
    final query = nivel != null ? '?nivel=$nivel' : '';
    final r = await http.get(Uri.parse('$baseUrl/integracoes/graylog/logs$query'), headers: _headers);
    _verificarErro(r);
    final data = jsonDecode(r.body);
    final lista = data['logs'] as List;
    return lista.map((e) => LogEntrada.fromJson(e)).toList();
  }

  static Future<List<ServicoZabbix>> statusZabbix() async {
    final r = await http.get(Uri.parse('$baseUrl/integracoes/zabbix/status'), headers: _headers);
    _verificarErro(r);
    final data = jsonDecode(r.body);
    final lista = data['servicos'] as List;
    return lista.map((e) => ServicoZabbix.fromJson(e)).toList();
  }

  static Future<List<Alerta>> listarAlertas() async {
    final r = await http.get(Uri.parse('$baseUrl/alertas'), headers: _headers);
    _verificarErro(r);
    final lista = jsonDecode(r.body) as List;
    return lista.map((e) => Alerta.fromJson(e)).toList();
  }

  static Future<List<PerfilAlerta>> listarPerfisAlerta() async {
    final r = await http.get(Uri.parse('$baseUrl/alertas/perfis'), headers: _headers);
    _verificarErro(r);
    final lista = jsonDecode(r.body) as List;
    return lista.map((e) => PerfilAlerta.fromJson(e)).toList();
  }

  static Future<PerfilAlerta> criarPerfilAlerta({
    required String nome,
    required String periodo,
    required List<String> canais,
    required String equipe,
  }) async {
    final r = await http.post(
      Uri.parse('$baseUrl/alertas/perfis'),
      headers: _headers,
      body: jsonEncode({'nome': nome, 'periodo': periodo, 'canais': canais, 'equipe': equipe, 'ativo': true}),
    );
    _verificarErro(r);
    return PerfilAlerta.fromJson(jsonDecode(r.body));
  }

  static Future<void> simularAlerta({required String titulo, required String descricao, String severidade = 'media'}) async {
    final r = await http.post(
      Uri.parse('$baseUrl/alertas/simular'),
      headers: _headers,
      body: jsonEncode({'titulo': titulo, 'descricao': descricao, 'severidade': severidade, 'canal': 'push'}),
    );
    _verificarErro(r);
  }

  static Future<Map<String, dynamic>> obterPreferenciasDashboard() async {
    final r = await http.get(Uri.parse('$baseUrl/dashboard/preferencias'), headers: _headers);
    _verificarErro(r);
    return jsonDecode(r.body);
  }

  static Future<void> salvarPreferenciasDashboard(Map<String, dynamic> preferencias) async {
    final r = await http.put(
      Uri.parse('$baseUrl/dashboard/preferencias'),
      headers: _headers,
      body: jsonEncode(preferencias),
    );
    _verificarErro(r);
  }

  static void _verificarErro(http.Response r) {
    if (r.statusCode >= 400) {
      try {
        final erro = jsonDecode(r.body);
        throw Exception(erro['detail'] ?? 'Erro ${r.statusCode}');
      } catch (_) {
        throw Exception('Erro ${r.statusCode} ao comunicar com o backend');
      }
    }
  }
}
