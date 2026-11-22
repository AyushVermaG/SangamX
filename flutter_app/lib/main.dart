import 'package:flutter/material.dart';
import 'core/service_locator.dart';
import 'screens/home_screen.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  ServiceLocator.instance.init();
  runApp(const SangamXApp());
}

class SangamXApp extends StatelessWidget {
  const SangamXApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'SangamX',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      darkTheme: AppTheme.darkTheme,
      themeMode: ThemeMode.light,
      home: const HomeScreen(),
    );
  }
}
