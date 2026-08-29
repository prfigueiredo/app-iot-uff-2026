import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../services/auth_provider.dart';
import 'home_shell.dart';

class LoginScreen extends StatefulWidget {
  const LoginScreen({super.key});

  @override
  State<LoginScreen> createState() => _LoginScreenState();
}

class _LoginScreenState extends State<LoginScreen> {
  final _usuarioCtrl = TextEditingController(text: 'admin');
  final _senhaCtrl = TextEditingController(text: 'admin123');

  void _preencherUsuarioTeste(String usuario, String senha) {
    setState(() {
      _usuarioCtrl.text = usuario;
      _senhaCtrl.text = senha;
    });
  }

  Future<void> _entrar() async {
    final auth = context.read<AuthProvider>();
    final ok = await auth.login(_usuarioCtrl.text.trim(), _senhaCtrl.text);
    if (ok && mounted) {
      Navigator.of(context).pushReplacement(MaterialPageRoute(builder: (_) => const HomeShell()));
    }
  }

  @override
  Widget build(BuildContext context) {
    final auth = context.watch<AuthProvider>();
    return Scaffold(
      body: SafeArea(
        child: Center(
          child: SingleChildScrollView(
            padding: const EdgeInsets.all(24),
            child: ConstrainedBox(
              constraints: const BoxConstraints(maxWidth: 400),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  const Icon(Icons.dns_rounded, size: 56, color: Colors.teal),
                  const SizedBox(height: 12),
                  const Text('CPD Monitor', textAlign: TextAlign.center, style: TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
                  Text('STI Niterói-RJ · dados simulados', textAlign: TextAlign.center, style: TextStyle(color: Colors.grey[600])),
                  const SizedBox(height: 32),
                  TextField(
                    controller: _usuarioCtrl,
                    decoration: const InputDecoration(labelText: 'Usuário', border: OutlineInputBorder()),
                  ),
                  const SizedBox(height: 12),
                  TextField(
                    controller: _senhaCtrl,
                    obscureText: true,
                    decoration: const InputDecoration(labelText: 'Senha', border: OutlineInputBorder()),
                    onSubmitted: (_) => _entrar(),
                  ),
                  if (auth.erro != null) ...[
                    const SizedBox(height: 12),
                    Text(auth.erro!, style: const TextStyle(color: Colors.red)),
                  ],
                  const SizedBox(height: 20),
                  FilledButton(
                    onPressed: auth.carregando ? null : _entrar,
                    child: auth.carregando
                        ? const SizedBox(height: 18, width: 18, child: CircularProgressIndicator(strokeWidth: 2))
                        : const Text('Entrar'),
                  ),
                  const SizedBox(height: 24),
                  Text('Usuários de teste (modo simulação):', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
                  const SizedBox(height: 8),
                  Wrap(
                    spacing: 8,
                    runSpacing: 8,
                    children: [
                      ActionChip(label: const Text('admin'), onPressed: () => _preencherUsuarioTeste('admin', 'admin123')),
                      ActionChip(label: const Text('operador'), onPressed: () => _preencherUsuarioTeste('operador', 'operador123')),
                      ActionChip(label: const Text('visualizador'), onPressed: () => _preencherUsuarioTeste('visualizador', 'visual123')),
                    ],
                  ),
                ],
              ),
            ),
          ),
        ),
      ),
    );
  }
}
