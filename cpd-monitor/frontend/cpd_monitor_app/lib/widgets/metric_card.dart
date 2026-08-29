import 'package:flutter/material.dart';

class MetricCard extends StatelessWidget {
  final String titulo;
  final String valor;
  final IconData icone;
  final Color? cor;
  final String? subtitulo;

  const MetricCard({
    super.key,
    required this.titulo,
    required this.valor,
    required this.icone,
    this.cor,
    this.subtitulo,
  });

  @override
  Widget build(BuildContext context) {
    final corBase = cor ?? Theme.of(context).colorScheme.primary;
    return Card(
      elevation: 0,
      color: corBase.withValues(alpha: 0.08),
      shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Row(
              children: [
                Icon(icone, color: corBase, size: 22),
                const SizedBox(width: 8),
                Expanded(
                  child: Text(titulo, style: TextStyle(color: corBase, fontWeight: FontWeight.w600)),
                ),
              ],
            ),
            const SizedBox(height: 10),
            Text(valor, style: const TextStyle(fontSize: 24, fontWeight: FontWeight.bold)),
            if (subtitulo != null) ...[
              const SizedBox(height: 2),
              Text(subtitulo!, style: TextStyle(color: Colors.grey[600], fontSize: 12)),
            ],
          ],
        ),
      ),
    );
  }
}
