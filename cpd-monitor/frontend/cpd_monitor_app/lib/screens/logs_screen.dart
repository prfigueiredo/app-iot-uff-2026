import 'package:flutter/material.dart';
import '../models/log_entrada.dart';
import '../services/api_service.dart';

class LogsScreen extends StatefulWidget {
  const LogsScreen({super.key});

  @override
  State<LogsScreen> createState() => _LogsScreenState();
}

class _LogsScreenState extends State<LogsScreen> {
  List<LogEntrada> _logs = [];
  bool _carregando = true;
  String? _filtroNivel;

  final _niveis = ['INFO', 'WARNING', 'ERROR', 'CRITICAL'];

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    setState(() => _carregando = true);
    final logs = await ApiService.logsGraylog(nivel: _filtroNivel);
    setState(() {
      _logs = logs;
      _carregando = false;
    });
  }

  Color _corNivel(String nivel) {
    switch (nivel) {
      case 'CRITICAL':
        return Colors.red[900]!;
      case 'ERROR':
        return Colors.red;
      case 'WARNING':
        return Colors.orange;
      default:
        return Colors.blueGrey;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Padding(
          padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              const Text('Logs (GrayLog)', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              const SizedBox(height: 12),
              SizedBox(
                height: 36,
                child: ListView(
                  scrollDirection: Axis.horizontal,
                  children: [
                    _chipFiltro('Todos', null),
                    ..._niveis.map((n) => _chipFiltro(n, n)),
                  ],
                ),
              ),
            ],
          ),
        ),
        Expanded(
          child: _carregando
              ? const Center(child: CircularProgressIndicator())
              : RefreshIndicator(
                  onRefresh: _carregar,
                  child: ListView.builder(
                    padding: const EdgeInsets.symmetric(horizontal: 16),
                    itemCount: _logs.length,
                    itemBuilder: (ctx, i) {
                      final log = _logs[i];
                      return ListTile(
                        dense: true,
                        leading: Container(
                          width: 8,
                          height: 8,
                          margin: const EdgeInsets.only(top: 6),
                          decoration: BoxDecoration(color: _corNivel(log.nivel), shape: BoxShape.circle),
                        ),
                        title: Text(log.mensagem),
                        subtitle: Text('${log.origem} · ${log.nivel} · ${_formatarData(log.data)}'),
                      );
                    },
                  ),
                ),
        ),
      ],
    );
  }

  Widget _chipFiltro(String rotulo, String? valor) {
    final selecionado = _filtroNivel == valor;
    return Padding(
      padding: const EdgeInsets.only(right: 8),
      child: ChoiceChip(
        label: Text(rotulo),
        selected: selecionado,
        onSelected: (_) {
          setState(() => _filtroNivel = valor);
          _carregar();
        },
      ),
    );
  }

  String _formatarData(DateTime d) =>
      '${d.day.toString().padLeft(2, '0')}/${d.month.toString().padLeft(2, '0')} ${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}';
}
