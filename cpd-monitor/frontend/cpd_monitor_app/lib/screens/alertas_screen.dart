import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/alerta.dart';
import '../services/api_service.dart';
import '../services/auth_provider.dart';

class AlertasScreen extends StatefulWidget {
  const AlertasScreen({super.key});

  @override
  State<AlertasScreen> createState() => _AlertasScreenState();
}

class _AlertasScreenState extends State<AlertasScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<Alerta> _alertas = [];
  List<PerfilAlerta> _perfis = [];
  bool _carregando = true;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _carregar();
  }

  Future<void> _carregar() async {
    setState(() => _carregando = true);
    final alertas = await ApiService.listarAlertas();
    final perfis = await ApiService.listarPerfisAlerta();
    setState(() {
      _alertas = alertas;
      _perfis = perfis;
      _carregando = false;
    });
  }

  Color _corSeveridade(String s) {
    switch (s) {
      case 'alta':
        return Colors.red;
      case 'media':
        return Colors.orange;
      default:
        return Colors.blueGrey;
    }
  }

  Future<void> _abrirNovoPerfil() async {
    final nomeCtrl = TextEditingController();
    final periodoCtrl = TextEditingController();
    final equipeCtrl = TextEditingController();
    final canais = <String>{'push'};

    await showDialog(
      context: context,
      builder: (ctx) => StatefulBuilder(
        builder: (ctx, setDialogState) => AlertDialog(
          title: const Text('Novo perfil de alerta'),
          content: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                TextField(controller: nomeCtrl, decoration: const InputDecoration(labelText: 'Nome (ex.: Plantão de feriado)')),
                TextField(controller: periodoCtrl, decoration: const InputDecoration(labelText: 'Período (ex.: sáb-dom 24h)')),
                TextField(controller: equipeCtrl, decoration: const InputDecoration(labelText: 'Equipe responsável')),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  children: ['sms', 'email', 'push'].map((c) {
                    final ativo = canais.contains(c);
                    return FilterChip(
                      label: Text(c),
                      selected: ativo,
                      onSelected: (v) => setDialogState(() => v ? canais.add(c) : canais.remove(c)),
                    );
                  }).toList(),
                ),
              ],
            ),
          ),
          actions: [
            TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Cancelar')),
            FilledButton(
              onPressed: () async {
                if (nomeCtrl.text.isEmpty || periodoCtrl.text.isEmpty) return;
                await ApiService.criarPerfilAlerta(
                  nome: nomeCtrl.text,
                  periodo: periodoCtrl.text,
                  canais: canais.toList(),
                  equipe: equipeCtrl.text.isEmpty ? 'Não definida' : equipeCtrl.text,
                );
                if (ctx.mounted) Navigator.pop(ctx);
                _carregar();
              },
              child: const Text('Criar'),
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final perfil = context.watch<AuthProvider>().usuario?.perfil ?? 'visualizador';
    final podeGerenciar = perfil == 'admin' || perfil == 'operador';

    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
          child: Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Alertas', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              if (podeGerenciar)
                IconButton(icon: const Icon(Icons.add_circle_outline), tooltip: 'Novo perfil de alerta', onPressed: _abrirNovoPerfil),
            ],
          ),
        ),
        TabBar(
          controller: _tabController,
          tabs: const [Tab(text: 'Recebidos'), Tab(text: 'Perfis')],
        ),
        Expanded(
          child: _carregando
              ? const Center(child: CircularProgressIndicator())
              : TabBarView(
                  controller: _tabController,
                  children: [
                    RefreshIndicator(
                      onRefresh: _carregar,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _alertas.length,
                        itemBuilder: (ctx, i) {
                          final a = _alertas[i];
                          return Card(
                            elevation: 0,
                            margin: const EdgeInsets.only(bottom: 10),
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(12),
                              side: BorderSide(color: _corSeveridade(a.severidade).withValues(alpha: 0.4)),
                            ),
                            child: ListTile(
                              leading: Icon(Icons.warning_amber_rounded, color: _corSeveridade(a.severidade)),
                              title: Text(a.titulo, style: const TextStyle(fontWeight: FontWeight.w600)),
                              subtitle: Text('${a.descricao}\nvia ${a.canal}'),
                              isThreeLine: true,
                            ),
                          );
                        },
                      ),
                    ),
                    RefreshIndicator(
                      onRefresh: _carregar,
                      child: ListView.builder(
                        padding: const EdgeInsets.all(16),
                        itemCount: _perfis.length,
                        itemBuilder: (ctx, i) {
                          final p = _perfis[i];
                          return Card(
                            elevation: 0,
                            margin: const EdgeInsets.only(bottom: 10),
                            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[300]!)),
                            child: ListTile(
                              title: Text(p.nome, style: const TextStyle(fontWeight: FontWeight.w600)),
                              subtitle: Text('${p.periodo}\nEquipe: ${p.equipe} · Canais: ${p.canais.join(", ")}'),
                              isThreeLine: true,
                              trailing: Icon(p.ativo ? Icons.check_circle : Icons.pause_circle, color: p.ativo ? Colors.green : Colors.grey),
                            ),
                          );
                        },
                      ),
                    ),
                  ],
                ),
        ),
      ],
    );
  }
}
