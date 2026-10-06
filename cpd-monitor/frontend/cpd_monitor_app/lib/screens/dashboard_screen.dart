import 'dart:async';
import 'package:flutter/material.dart';
import '../models/leitura_sensor.dart';
import '../models/servico_zabbix.dart';
import '../models/alerta.dart';
import '../services/api_service.dart';
import '../widgets/metric_card.dart';
import '../widgets/status_dot.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  LeituraSensor? _leitura;
  List<ServicoZabbix> _servicos = [];
  List<Alerta> _alertas = [];
  Map<String, dynamic>? _preferencias;
  bool _carregando = true;
  String? _erro;
  Timer? _timerSensores;

  @override
  void initState() {
    super.initState();
    _carregar();
    _timerSensores = Timer.periodic(ApiService.intervaloAtualizacaoSensores, (_) => _atualizarLeitura());
  }

  @override
  void dispose() {
    _timerSensores?.cancel();
    super.dispose();
  }

  // Refreshes only the sensor reading, without the full-screen spinner.
  // A failed poll keeps the last value and the next tick tries again.
  Future<void> _atualizarLeitura() async {
    if (_carregando || _erro != null) return;
    try {
      final leitura = await ApiService.leituraAtual();
      if (mounted) setState(() => _leitura = leitura);
    } catch (_) {}
  }

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final resultados = await Future.wait([
        ApiService.leituraAtual(),
        ApiService.statusZabbix(),
        ApiService.listarAlertas(),
        ApiService.obterPreferenciasDashboard(),
      ]);
      setState(() {
        _leitura = resultados[0] as LeituraSensor;
        _servicos = resultados[1] as List<ServicoZabbix>;
        _alertas = resultados[2] as List<Alerta>;
        _preferencias = resultados[3] as Map<String, dynamic>;
        _carregando = false;
      });
    } catch (e) {
      setState(() {
        _erro = e.toString().replaceFirst('Exception: ', '');
        _carregando = false;
      });
    }
  }

  Future<void> _abrirPersonalizacao() async {
    if (_preferencias == null) return;
    final metricasDisponiveis = ['temperatura', 'umidade', 'combustivel', 'presenca'];
    final selecionadas = Set<String>.from(_preferencias!['metricas']);

    await showModalBottomSheet(
      context: context,
      builder: (ctx) {
        return StatefulBuilder(
          builder: (ctx, setModalState) => Padding(
            padding: const EdgeInsets.all(20),
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                const Text('Métricas do painel', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
                const SizedBox(height: 12),
                Wrap(
                  spacing: 8,
                  children: metricasDisponiveis.map((m) {
                    final ativo = selecionadas.contains(m);
                    return FilterChip(
                      label: Text(m),
                      selected: ativo,
                      onSelected: (v) => setModalState(() => v ? selecionadas.add(m) : selecionadas.remove(m)),
                    );
                  }).toList(),
                ),
                const SizedBox(height: 20),
                FilledButton(
                  onPressed: () async {
                    await ApiService.salvarPreferenciasDashboard({
                      'metricas': selecionadas.toList(),
                      'servicos': _preferencias!['servicos'],
                      'tipos_alerta': _preferencias!['tipos_alerta'],
                    });
                    if (ctx.mounted) Navigator.pop(ctx);
                    _carregar();
                  },
                  child: const Text('Salvar'),
                ),
              ],
            ),
          ),
        );
      },
    );
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando) return const Center(child: CircularProgressIndicator());
    if (_erro != null) return _ErroCarregamento(mensagem: _erro!, aoTentarNovamente: _carregar);

    final metricas = Set<String>.from(_preferencias?['metricas'] ?? []);
    final servicosFora = _servicos.where((s) => s.status != 'up').length;
    final alertasNaoLidos = _alertas.where((a) => !a.lido).length;

    return RefreshIndicator(
      onRefresh: _carregar,
      child: ListView(
        padding: const EdgeInsets.all(16),
        children: [
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              const Text('Painel', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
              IconButton(icon: const Icon(Icons.tune), onPressed: _abrirPersonalizacao, tooltip: 'Personalizar métricas'),
            ],
          ),
          const SizedBox(height: 12),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.3,
            children: [
              if (metricas.contains('temperatura'))
                MetricCard(
                  titulo: 'Temperatura',
                  valor: _leitura!.temperaturaC == null ? '-' : '${_leitura!.temperaturaC!.toStringAsFixed(1)}°C',
                  icone: Icons.thermostat,
                  cor: _leitura!.sensorCalorAlerta ? Colors.red : Colors.teal,
                  subtitulo: _leitura!.temperaturaAtualizadaEm == null
                      ? 'Aguardando sensor'
                      : '${_leitura!.sensorCalorAlerta ? 'Acima do limite' : 'Normal'} · ${_formatarHora(_leitura!.temperaturaAtualizadaEm!)}',
                ),
              if (metricas.contains('umidade'))
                MetricCard(titulo: 'Umidade', valor: '${_leitura!.umidadePct.toStringAsFixed(0)}%', icone: Icons.water_drop, cor: Colors.blue),
              if (metricas.contains('combustivel'))
                MetricCard(
                  titulo: 'Gerador (combustível)',
                  valor: '${_leitura!.combustivelGeradorPct.toStringAsFixed(0)}%',
                  icone: Icons.local_gas_station,
                  cor: Colors.orange,
                ),
              if (metricas.contains('presenca'))
                MetricCard(
                  titulo: 'Presença',
                  valor: '${_leitura!.pessoasPresentes} pessoa(s)',
                  icone: Icons.person_pin_circle,
                  cor: Colors.purple,
                ),
              MetricCard(
                titulo: 'Serviços fora do ar',
                valor: '$servicosFora',
                icone: Icons.dns,
                cor: servicosFora > 0 ? Colors.red : Colors.green,
              ),
              MetricCard(
                titulo: 'Alertas não lidos',
                valor: '$alertasNaoLidos',
                icone: Icons.notifications_active,
                cor: alertasNaoLidos > 0 ? Colors.red : Colors.green,
              ),
            ],
          ),
          const SizedBox(height: 20),
          const Text('Status dos serviços', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 8),
          Card(
            elevation: 0,
            shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(12), side: BorderSide(color: Colors.grey[300]!)),
            child: Column(
              children: _servicos
                  .map((s) => ListTile(
                        title: Text(s.nome),
                        subtitle: Text(s.tipo),
                        trailing: StatusDot(status: s.status),
                      ))
                  .toList(),
            ),
          ),
        ],
      ),
    );
  }

  String _formatarHora(DateTime d) =>
      '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}:${d.second.toString().padLeft(2, '0')}';
}

class _ErroCarregamento extends StatelessWidget {
  final String mensagem;
  final VoidCallback aoTentarNovamente;
  const _ErroCarregamento({required this.mensagem, required this.aoTentarNovamente});

  @override
  Widget build(BuildContext context) {
    return Center(
      child: Padding(
        padding: const EdgeInsets.all(24),
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const Icon(Icons.error_outline, size: 40, color: Colors.red),
            const SizedBox(height: 12),
            Text(mensagem, textAlign: TextAlign.center),
            const SizedBox(height: 12),
            FilledButton(onPressed: aoTentarNovamente, child: const Text('Tentar novamente')),
          ],
        ),
      ),
    );
  }
}
