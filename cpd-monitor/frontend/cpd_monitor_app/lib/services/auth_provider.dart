import 'package:flutter/material.dart';
import '../models/usuario.dart';
import 'api_service.dart';

class AuthProvider extends ChangeNotifier {
  Usuario? _usuario;
  String? _erro;
  bool _carregando = false;

  Usuario? get usuario => _usuario;
  String? get erro => _erro;
  bool get carregando => _carregando;
  bool get logado => _usuario != null;

  Future<bool> login(String usuario, String senha) async {
    _carregando = true;
    _erro = null;
    notifyListeners();
    try {
      _usuario = await ApiService.login(usuario, senha);
      _carregando = false;
      notifyListeners();
      return true;
    } catch (e) {
      _erro = e.toString().replaceFirst('Exception: ', '');
      _carregando = false;
      notifyListeners();
      return false;
    }
  }

  void logout() {
    ApiService.logout();
    _usuario = null;
    notifyListeners();
  }
}
