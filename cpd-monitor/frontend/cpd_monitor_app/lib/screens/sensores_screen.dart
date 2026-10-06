import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/leitura_sensor.dart';
import '../services/api_service.dart';
import '../widgets/metric_card.dart';

class SensoresScreen extends StatefulWidget {
  const SensoresScreen({super.key});

  @override
  State<SensoresScreen> createState() => _SensoresScreenState();
}

class _SensoresScreenState extends State<SensoresScreen> {
  LeituraSensor? _atual;
  List<LeituraSensor> _historico = [];
  bool _carregando = true;
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

  // A failed poll keeps the last value, and "Atualizado às" shows its age.
  Future<void> _atualizarLeitura() async {
    if (_carregando) return;
    try {
      final atual = await ApiService.leituraAtual();
      if (mounted) setState(() => _atual = atual);
    } catch (_) {}
  }

  Future<void> _carregar() async {
    setState(() => _carregando = true);
    final atual = await ApiService.leituraAtual();
    final historico = await ApiService.historicoSensores();
    setState(() {
      _atual = atual;
      _historico = historico;
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
          const Text('Sensores físicos do CPD', style: TextStyle(fontSize: 22, fontWeight: FontWeight.bold)),
          Text('Atualizado às ${_formatarHora(_atual!.atualizadoEm)}', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
          const SizedBox(height: 16),
          GridView.count(
            crossAxisCount: 2,
            shrinkWrap: true,
            physics: const NeverScrollableScrollPhysics(),
            crossAxisSpacing: 12,
            mainAxisSpacing: 12,
            childAspectRatio: 1.3,
            children: [
              MetricCard(
                titulo: 'Ar-condicionado',
                valor: '${_atual!.temperaturaC.toStringAsFixed(1)}°C',
                subtitulo: _atual!.arCondicionadoStatus ?? '-',
                icone: Icons.ac_unit,
                cor: _atual!.sensorCalorAlerta ? Colors.red : Colors.cyan,
              ),
              MetricCard(
                titulo: 'Sensor de calor',
                valor: _atual!.sensorCalorAlerta ? 'Alerta' : 'Normal',
                icone: Icons.local_fire_department,
                cor: _atual!.sensorCalorAlerta ? Colors.red : Colors.green,
              ),
              MetricCard(
                titulo: 'Sensor de presença',
                valor: _atual!.sensorPresencaAtivo ? 'Ativo' : 'Inativo',
                icone: Icons.sensors,
                cor: Colors.purple,
              ),
              MetricCard(titulo: 'Pessoas no local', valor: '${_atual!.pessoasPresentes}', icone: Icons.groups, cor: Colors.indigo),
            ],
          ),
          const SizedBox(height: 24),
          const Text('Temperatura - últimas 24h', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 12),
          SizedBox(height: 200, child: _GraficoLinha(dados: _historico.map((h) => h.temperaturaC).toList(), cor: Colors.teal)),
          const SizedBox(height: 24),
          const Text('Umidade - últimas 24h', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
          const SizedBox(height: 12),
          SizedBox(height: 200, child: _GraficoLinha(dados: _historico.map((h) => h.umidadePct).toList(), cor: Colors.blue)),
        ],
      ),
    );
  }

  String _formatarHora(DateTime d) =>
      '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}:${d.second.toString().padLeft(2, '0')}';
}

class _GraficoLinha extends StatelessWidget {
  final List<double> dados;
  final Color cor;
  const _GraficoLinha({required this.dados, required this.cor});

  @override
  Widget build(BuildContext context) {
    if (dados.isEmpty) return const Center(child: Text('Sem dados de histórico ainda'));
    final pontos = dados.asMap().entries.map((e) => FlSpot(e.key.toDouble(), e.value)).toList();
    return LineChart(
      LineChartData(
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        titlesData: const FlTitlesData(
          topTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          bottomTitles: AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(sideTitles: SideTitles(showTitles: true, reservedSize: 36)),
        ),
        borderData: FlBorderData(show: false),
        lineBarsData: [
          LineChartBarData(
            spots: pontos,
            isCurved: true,
            color: cor,
            barWidth: 2,
            dotData: const FlDotData(show: false),
            belowBarData: BarAreaData(show: true, color: cor.withValues(alpha: 0.15)),
          ),
        ],
      ),
    );
  }
}
