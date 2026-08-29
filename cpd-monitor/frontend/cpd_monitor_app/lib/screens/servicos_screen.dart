import 'package:flutter/material.dart';
import '../models/servico_zabbix.dart';
import '../services/api_service.dart';
import '../widgets/status_dot.dart';

class ServicosScreen extends StatefulWidget {
  const ServicosScreen({super.key});

  @override
  State<ServicosScreen> createState() => _ServicosScreenState();
}

class _ServicosScreenState extends State<ServicosScreen> {
  List<ServicoZabbix> _servicos = [];
  bool _carregando = true;

  @override
  void initState() {
    super.initState();
    _carregar();
  }

  Future<void> _carregar() async {
    setState(() => _carregando = true);
    final servicos = await ApiService.statusZabbix();
    setState(() {
      _servicos = servicos;
      _carregando = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) return const Center(child: CircularProgressIndicator());

    return RefreshIndicator(
      onRefresh: _carregar,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          const Text('Serviços monitorados', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          Text('Via integração com Zabbix', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
          const SizedBox(height: 16),
          ..._servicos.map((s) => Card(
                elevation: 0,
                margin: const EdgeInsets.only(bottom: 10),
                shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[300]!)),
                child: ListTile(
                  contentPadding: const EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  title: Text(s.nome, style: const TextStyle(fontWeight: FontWeight.w600)),
                  subtitle: Text('${s.tipo} · uptime ${s.uptimePct.toStringAsFixed(2)}%'),
                  trailing: StatusDot(status: s.status),
                ),
              )),
        ],
      ),
    );
  }
}
