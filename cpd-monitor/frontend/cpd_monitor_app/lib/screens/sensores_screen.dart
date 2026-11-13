import 'dart:async';
import 'package:flutter/material.dart';
import 'package:fl_chart/fl_chart.dart';
import '../models/leitura_sensor.dart';
import '../models/media_historico.dart';
import '../services/api_service.dart';
import '../widgets/metric_card.dart';
import '../widgets/severidade.dart';

class SensoresScreen extends StatefulWidget {
  const SensoresScreen({super.key});

  @override
  State<SensoresScreen> createState() => _SensoresScreenState();
}

class _SensoresScreenState extends State<SensoresScreen> {
  static const _periodos = {24: '24 h', 24 * 7: '7 dias', 24 * 30: '30 dias'};

  LeituraSensor? _atual;
  HistoricoMedias? _historico;
  int _horas = 24;
  bool _carregando = true;
  String? _erro;
  String? _erroHistorico;
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
    if (_carregando || _atual == null) return;
    try {
      final atual = await ApiService.leituraAtual();
      if (mounted) setState(() => _atual = atual);
    } catch (_) {}
  }

  Future<void> _carregar() async {
    setState(() {
      _carregando = true;
      _erro = null;
    });
    try {
      final atual = await ApiService.leituraAtual();
      if (!mounted) return;
      setState(() => _atual = atual);
    } catch (e) {
      if (!mounted) return;
      setState(() => _erro = e.toString().replaceFirst('Exception: ', ''));
    }
    await _carregarHistorico();
    if (mounted) setState(() => _carregando = false);
  }

  Future<void> _carregarHistorico() async {
    try {
      final historico = await ApiService.historicoMedias(horas: _horas);
      if (!mounted) return;
      setState(() {
        _historico = historico;
        _erroHistorico = null;
      });
    } catch (e) {
      if (!mounted) return;
      setState(() => _erroHistorico = e.toString().replaceFirst('Exception: ', ''));
    }
  }

  @override
  Widget build(BuildContext context) {
    if (_carregando && _atual == null) return const Center(child: CircularProgressIndicator());
    if (_atual == null) {
      return Center(
        child: Padding(
          padding: const EdgeInsets.all(24),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Icon(Icons.error_outline, size: 40, color: Colors.red),
              const SizedBox(height: 12),
              Text(_erro ?? 'Não foi possível carregar os sensores', textAlign: TextAlign.center),
              const SizedBox(height: 12),
              FilledButton(onPressed: _carregar, child: const Text('Tentar novamente')),
            ],
          ),
        ),
      );
    }

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
                valor: _atual!.temperaturaC == null ? '-' : '${_atual!.temperaturaC!.toStringAsFixed(1)}°C',
                subtitulo: _atual!.temperaturaAtualizadaEm == null
                    ? 'Aguardando sensor'
                    : '${_atual!.arCondicionadoStatus ?? '-'} · ${_formatarHora(_atual!.temperaturaAtualizadaEm!)}',
                icone: Icons.ac_unit,
                cor: corDoNivel(_atual!.nivel('temperatura'), Colors.cyan),
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
          const Text('Histórico', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 18)),
          const SizedBox(height: 8),
          Wrap(
            spacing: 8,
            children: [
              for (final entrada in _periodos.entries)
                ChoiceChip(
                  label: Text(entrada.value),
                  selected: _horas == entrada.key,
                  onSelected: (_) {
                    setState(() => _horas = entrada.key);
                    _carregarHistorico();
                  },
                ),
            ],
          ),
          const SizedBox(height: 12),
          ..._secaoHistorico(),
        ],
      ),
    );
  }

  List<Widget> _secaoHistorico() {
    if (_erroHistorico != null) {
      return [Text('Não foi possível carregar o histórico: $_erroHistorico', style: const TextStyle(color: Colors.red))];
    }
    final historico = _historico;
    if (historico == null) return [const Center(child: CircularProgressIndicator())];
    if (historico.medias.isEmpty) {
      return [
        Padding(
          padding: const EdgeInsets.symmetric(vertical: 24),
          child: Text(
            'Ainda não há médias neste período. Cada média é gravada quando o seu período de '
            '${_descreverIntervalo(historico.intervaloMin)} termina.',
            textAlign: TextAlign.center,
            style: TextStyle(color: Colors.grey[700]),
          ),
        ),
      ];
    }
    final medias = historico.medias;
    final comUmidade = medias.where((m) => m.umidadeMedia != null).toList();
    return [
      Text('Temperatura (média a cada ${_descreverIntervalo(historico.intervaloMin)})',
          style: const TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
      const SizedBox(height: 4),
      Text('Linha cheia: média · tracejadas: mínimo e máximo', style: TextStyle(color: Colors.grey[600], fontSize: 12)),
      const SizedBox(height: 12),
      SizedBox(
        height: 220,
        child: _GraficoMedias(
          medias: medias,
          media: (m) => m.temperaturaMedia,
          minimo: (m) => m.temperaturaMin,
          maximo: (m) => m.temperaturaMax,
          cor: Colors.teal,
        ),
      ),
      const SizedBox(height: 24),
      const Text('Umidade (média)', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
      const SizedBox(height: 12),
      SizedBox(
        height: 180,
        child: comUmidade.isEmpty
            ? const Center(child: Text('O sensor não enviou umidade neste período'))
            : _GraficoMedias(medias: comUmidade, media: (m) => m.umidadeMedia!, cor: Colors.blue),
      ),
      const SizedBox(height: 24),
      const Text('Registros', style: TextStyle(fontWeight: FontWeight.bold, fontSize: 16)),
      const SizedBox(height: 8),
      for (final m in medias.reversed) _LinhaMedia(media: m),
    ];
  }

  String _descreverIntervalo(int minutos) => minutos % 60 == 0 ? '${minutos ~/ 60} h' : '$minutos min';

  String _formatarHora(DateTime d) =>
      '${d.hour.toString().padLeft(2, '0')}:${d.minute.toString().padLeft(2, '0')}:${d.second.toString().padLeft(2, '0')}';
}

String _numero(double v, [int casas = 1]) => v.toStringAsFixed(casas).replaceAll('.', ',');

String _dataHora(DateTime d) {
  String dois(int n) => n.toString().padLeft(2, '0');
  return '${dois(d.day)}/${dois(d.month)} ${dois(d.hour)}:${dois(d.minute)}';
}

class _LinhaMedia extends StatelessWidget {
  final MediaHistorico media;
  const _LinhaMedia({required this.media});

  @override
  Widget build(BuildContext context) {
    final umidade = media.umidadeMedia == null ? '' : ' · umidade ${_numero(media.umidadeMedia!, 0)}%';
    return Padding(
      padding: const EdgeInsets.symmetric(vertical: 6),
      child: Row(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          SizedBox(width: 92, child: Text(_dataHora(media.inicio), style: const TextStyle(fontWeight: FontWeight.w600))),
          Expanded(
            child: Text(
              '${_numero(media.temperaturaMedia)}°C (mín ${_numero(media.temperaturaMin)}, máx ${_numero(media.temperaturaMax)})'
              '$umidade · ${media.amostras} leituras',
            ),
          ),
        ],
      ),
    );
  }
}

/// Line chart of periodic averages over time, optionally with min and max lines.
/// A missing period breaks the line instead of joining distant points.
class _GraficoMedias extends StatelessWidget {
  final List<MediaHistorico> medias; // oldest first
  final double Function(MediaHistorico) media;
  final double Function(MediaHistorico)? minimo;
  final double Function(MediaHistorico)? maximo;
  final Color cor;

  const _GraficoMedias({required this.medias, required this.media, this.minimo, this.maximo, required this.cor});

  // X axis: hours since the first period.
  double _x(MediaHistorico m) => m.inicio.difference(medias.first.inicio).inMinutes / 60;

  List<FlSpot> _pontos(double Function(MediaHistorico) valor) {
    final pontos = <FlSpot>[];
    for (var i = 0; i < medias.length; i++) {
      if (i > 0 && medias[i].inicio != medias[i - 1].fim) pontos.add(FlSpot.nullSpot);
      pontos.add(FlSpot(_x(medias[i]), valor(medias[i])));
    }
    return pontos;
  }

  LineChartBarData _linha(double Function(MediaHistorico) valor, {bool tracejada = false}) => LineChartBarData(
        spots: _pontos(valor),
        color: tracejada ? cor.withValues(alpha: 0.5) : cor,
        barWidth: tracejada ? 1 : 2.5,
        dashArray: tracejada ? [4, 4] : null,
        dotData: FlDotData(show: medias.length <= 3),
      );

  @override
  Widget build(BuildContext context) {
    // The axis spans exactly the data, so short periods (a demo with 1-minute
    // averages) are not squeezed into a fixed hour. About four labels, each on
    // a whole number of periods, so they fall on round times.
    final duracaoHoras = _x(medias.last) + medias.last.minutos / 60;
    final periodoHoras = medias.first.minutos / 60;
    final intervaloRotulo = (duracaoHoras / 4 / periodoHoras).ceil() * periodoHoras;
    return LineChart(
      LineChartData(
        minX: 0,
        maxX: duracaoHoras,
        gridData: const FlGridData(show: true, drawVerticalLine: false),
        borderData: FlBorderData(show: false),
        titlesData: FlTitlesData(
          topTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          rightTitles: const AxisTitles(sideTitles: SideTitles(showTitles: false)),
          leftTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 44,
              // Only the regular steps: the extremes would overlap their neighbors.
              minIncluded: false,
              maxIncluded: false,
              getTitlesWidget: (valor, meta) => SideTitleWidget(
                axisSide: meta.axisSide,
                child: Text(_numero(valor), style: const TextStyle(fontSize: 11)),
              ),
            ),
          ),
          bottomTitles: AxisTitles(
            sideTitles: SideTitles(
              showTitles: true,
              reservedSize: 28,
              interval: intervaloRotulo,
              getTitlesWidget: (valor, meta) {
                final momento = medias.first.inicio.add(Duration(minutes: (valor * 60).round()));
                final texto = duracaoHoras <= 48
                    ? '${momento.hour.toString().padLeft(2, '0')}:${momento.minute.toString().padLeft(2, '0')}'
                    : '${momento.day.toString().padLeft(2, '0')}/${momento.month.toString().padLeft(2, '0')}';
                return SideTitleWidget(axisSide: meta.axisSide, child: Text(texto, style: const TextStyle(fontSize: 11)));
              },
            ),
          ),
        ),
        lineBarsData: [
          if (minimo != null) _linha(minimo!, tracejada: true),
          if (maximo != null) _linha(maximo!, tracejada: true),
          _linha(media),
        ],
      ),
    );
  }
}
