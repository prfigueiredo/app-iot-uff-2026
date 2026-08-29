import 'package:flutter/material.dart';

class StatusDot extends StatelessWidget {
  final String status; // up | warning | down

  const StatusDot({super.key, required this.status});

  Color get _cor {
    switch (status) {
      case 'up':
        return Colors.green;
      case 'warning':
        return Colors.orange;
      case 'down':
        return Colors.red;
      default:
        return Colors.grey;
    }
  }

  String get _rotulo {
    switch (status) {
      case 'up':
        return 'Operacional';
      case 'warning':
        return 'Instável';
      case 'down':
        return 'Fora do ar';
      default:
        return status;
    }
  }

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Container(width: 10, height: 10, decoration: BoxDecoration(color: _cor, shape: BoxShape.circle)),
        const SizedBox(width: 6),
        Text(_rotulo, style: TextStyle(color: _cor, fontWeight: FontWeight.w600, fontSize: 13)),
      ],
    );
  }
}
