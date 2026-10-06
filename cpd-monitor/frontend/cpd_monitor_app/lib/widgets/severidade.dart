import 'package:flutter/material.dart';

Color corDaSeveridade(String severidade) {
  switch (severidade) {
    case 'alta':
      return Colors.red;
    case 'media':
      return Colors.orange;
    default:
      return Colors.blueGrey;
  }
}

IconData iconeDaSeveridade(String severidade) {
  switch (severidade) {
    case 'alta':
      return Icons.error;
    case 'media':
      return Icons.warning_amber_rounded;
    default:
      return Icons.check_circle_outline;
  }
}

/// Card color for an alert level (normal | atencao | critico).
Color corDoNivel(String nivel, Color corNormal) {
  switch (nivel) {
    case 'critico':
      return Colors.red;
    case 'atencao':
      return Colors.orange;
    default:
      return corNormal;
  }
}

String rotuloDoNivel(String nivel) {
  switch (nivel) {
    case 'critico':
      return 'Crítico';
    case 'atencao':
      return 'Atenção';
    default:
      return 'Normal';
  }
}
