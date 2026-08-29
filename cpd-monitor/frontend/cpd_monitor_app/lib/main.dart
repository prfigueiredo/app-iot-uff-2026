// App de Monitoramento do CPD - STI Niterói-RJ
import 'package:flutter/material.dart';
import 'package:provider/provider.dart';
import 'services/auth_provider.dart';
import 'screens/login_screen.dart';

void main() {
  runApp(const CpdMonitorApp());
}

class CpdMonitorApp extends StatelessWidget {
  const CpdMonitorApp({super.key});

  @override
  Widget build(BuildContext context) {
    return ChangeNotifierProvider(
      create: (_) => AuthProvider(),
      child: MaterialApp(
        title: 'CPD Monitor',
        debugShowCheckedModeBanner: false,
        theme: ThemeData(
          colorSchemeSeed: Colors.teal,
          useMaterial3: true,
        ),
        home: const LoginScreen(),
      ),
    );
  }
}
