import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import '../models/alerta.dart';
import '../services/alertas_provider.dart';
import '../services/api_service.dart';
import '../services/auth_provider.dart';
import '../widgets/severidade.dart';

class AlertasScreen extends StatefulWidget {
  const AlertasScreen({super.key});

  @override
  State<AlertasScreen> createState() => _AlertasScreenState();
}

class _AlertasScreenState extends State<AlertasScreen> with SingleTickerProviderStateMixin {
  late TabController _tabController;
  List<PerfilAlerta> _perfis = [];
  bool _carregandoPerfis = true;
  String? _erroPerfis;

  @override
  void initState() {
    super.initState();
    _tabController = TabController(length: 2, vsync: this);
    _carregarPerfis();
  }

  @override
  void dispose() {
    _tabController.dispose();
    super.dispose();
  }

  Future<void> _carregarPerfis() async {
    setState(() {
      _carregandoPerfis = true;
      _erroPerfis = null;
    });
    try {
      final perfis = await ApiService.listarPerfisAlerta();
      if (!mounted) return;
      setState(() => _perfis = perfis);
    } catch (e) {
      if (!mounted) return;
      setState(() => _erroPerfis = e.toString().replaceFirst('Exception: ', ''));
    }
    if (mounted) setState(() => _carregandoPerfis = false);
  }

  Future<void> _marcarComoLido(Alerta alerta) async {
    try {
      await context.read<AlertasProvider>().marcarComoLido(alerta);
    } catch (e) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(content: Text('Não foi possível marcar como lido: ${e.toString().replaceFirst('Exception: ', '')}')),
      );
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
                _carregarPerfis();
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
    final alertas = context.watch<AlertasProvider>();

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
          tabs: [
            Tab(text: alertas.naoLidos > 0 ? 'Recebidos (${alertas.naoLidos})' : 'Recebidos'),
            const Tab(text: 'Perfis'),
          ],
        ),
        Expanded(
          child: TabBarView(
            controller: _tabController,
            children: [
              _ListaComEstado(
                carregando: alertas.carregando && alertas.alertas.isEmpty,
                erro: alertas.erro,
                vazia: alertas.alertas.isEmpty,
                mensagemVazia: 'Nenhum alerta até agora',
                aoAtualizar: alertas.carregar,
                itemCount: alertas.alertas.length,
                itemBuilder: (ctx, i) => _CardAlerta(
                  alerta: alertas.alertas[i],
                  aoTocar: () => _marcarComoLido(alertas.alertas[i]),
                ),
              ),
              _ListaComEstado(
                carregando: _carregandoPerfis,
                erro: _erroPerfis,
                vazia: _perfis.isEmpty,
                mensagemVazia: 'Nenhum perfil cadastrado',
                aoAtualizar: _carregarPerfis,
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
            ],
          ),
        ),
      ],
    );
  }
}

class _CardAlerta extends StatelessWidget {
  final Alerta alerta;
  final VoidCallback aoTocar;
  const _CardAlerta({required this.alerta, required this.aoTocar});

  String _formatarData(DateTime d) {
    String dois(int n) => n.toString().padLeft(2, '0');
    return '${dois(d.day)}/${dois(d.month)} ${dois(d.hour)}:${dois(d.minute)}:${dois(d.second)}';
  }

  @override
  Widget build(BuildContext context) {
    final cor = corDaSeveridade(alerta.severidade);
    return Card(
      elevation: 0,
      margin: const EdgeInsets.only(bottom: 10),
      color: alerta.lido ? null : cor.withValues(alpha: 0.06),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: BorderSide(color: cor.withValues(alpha: alerta.lido ? 0.2 : 0.5)),
      ),
      child: ListTile(
        onTap: aoTocar,
        leading: Icon(iconeDaSeveridade(alerta.severidade), color: cor),
        title: Text(
          alerta.titulo,
          style: TextStyle(fontWeight: alerta.lido ? FontWeight.normal : FontWeight.w700),
        ),
        subtitle: Text('${alerta.descricao}\n${_formatarData(alerta.data)} · via ${alerta.canal}'),
        isThreeLine: true,
        trailing: alerta.lido ? null : Icon(Icons.circle, size: 10, color: cor),
      ),
    );
  }
}

/// A pull-to-refresh list that also shows loading, error and empty states.
class _ListaComEstado extends StatelessWidget {
  final bool carregando;
  final String? erro;
  final bool vazia;
  final String mensagemVazia;
  final Future<void> Function() aoAtualizar;
  final int itemCount;
  final IndexedWidgetBuilder itemBuilder;

  const _ListaComEstado({
    required this.carregando,
    required this.erro,
    required this.vazia,
    required this.mensagemVazia,
    required this.aoAtualizar,
    required this.itemCount,
    required this.itemBuilder,
  });

  @override
  Widget build(BuildContext context) {
    if (carregando) return const Center(child: CircularProgressIndicator());
    if (erro != null && vazia) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 40, color: Colors.red),
              const SizedBox(height: 12),
              Text(erro!, textAlign: TextAlign.center),
              const SizedBox(height: 12),
              FilledButton(onPressed: aoAtualizar, child: const Text('Tentar novamente')),
            ],
          ),
        ),
      );
    }
    return RefreshIndicator(
      onRefresh: aoAtualizar,
      child: vazia
          ? ListView(children: [Padding(padding: const EdgeInsets.all(32), child: Center(child: Text(mensagemVazia)))])
          : ListView.builder(padding: const EdgeInsets.all(16), itemCount: itemCount, itemBuilder: itemBuilder),
    );
  }
}
