import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/api_service.dart';
import '../services/auth_provider.dart';
import 'login_screen.dart';

class PerfilScreen extends StatelessWidget {
  const PerfilScreen({super.key});

  String _rotuloPerfil(String perfil) {
    switch (perfil) {
      case 'admin':
        return 'Administrador';
      case 'operador':
        return 'Operador de plantão';
      default:
        return 'Visualizador';
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    final usuario = auth.usuario!;
    final podeSimularAlerta = usuario.perfil == 'admin' || usuario.perfil == 'operador';

    return ListView(
      padding: const EdgeInsets.all(16),
      children: [
        const Text('Perfil', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
        const SizedBox(height: 20),
        Card(
          elevation: 0,
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[300]!)),
          child: ListTile(
            leading: const CircleAvatar(child: Icon(Icons.person)),
            title: Text(usuario.nome, style: const TextStyle(fontWeight: FontWeight.w600)),
            subtitle: Text('${usuario.usuario} · ${_rotuloPerfil(usuario.perfil)}'),
          ),
        ),
        const SizedBox(height: 24),
        if (podeSimularAlerta) ...[
          const Text('Ferramentas de teste', style: TextStyle(fontWeight: FontWeight.bold)),
          const SizedBox(height: 8),
          OutlinedButton.icon(
            icon: const Icon(Icons.campaign),
            label: const Text('Simular um alerta agora'),
            onPressed: () async {
              await ApiService.simularAlerta(
                titulo: 'Alerta de teste',
                descricao: 'Disparado manualmente pela tela de perfil',
                severidade: 'media',
              );
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Alerta simulado enviado')));
              }
            },
          ),
          const SizedBox(height: 24),
        ],
        const Text('Sobre', style: TextStyle(fontWeight: FontWeight.bold)),
        const SizedBox(height: 8),
        Text(
          'App de monitoramento do CPD da STI de Niterói-RJ (TCC). '
          'Todos os dados exibidos são simulados (mock) enquanto não há '
          'integração com o ambiente real do CPD.',
          style: TextStyle(color: Colors.grey[700]),
        ),
        const SizedBox(height: 24),
        OutlinedButton.icon(
          icon: const Icon(Icons.logout, color: Colors.red),
          label: const Text('Sair', style: TextStyle(color: Colors.red)),
          onPressed: () {
            auth.logout();
            Navigator.of(context).pushAndRemoveUntil(MaterialPageRoute(builder: (_) => const LoginScreen()), (route) => false);
          },
        ),
      ],
    );
  }
}
