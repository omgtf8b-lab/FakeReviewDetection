import 'package:flutter/material.dart';
import 'screens/main_navigation_screen.dart';
import 'services/auth_state.dart';
import 'theme/app_theme.dart';

void main() {
  WidgetsFlutterBinding.ensureInitialized();
  AuthState.instance.restoreSession();
  runApp(const FakeReviewDetectionApp());
}

class FakeReviewDetectionApp extends StatelessWidget {
  const FakeReviewDetectionApp({super.key});

  @override
  Widget build(BuildContext context) {
    return MaterialApp(
      title: 'Fake Review Detection',
      debugShowCheckedModeBanner: false,
      theme: AppTheme.lightTheme,
      builder: (context, child) {
        return Container(
          color: const Color(0xFFE2E8F0),
          alignment: Alignment.center,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 430),
            child: Container(
              clipBehavior: Clip.antiAlias,
              decoration: const BoxDecoration(
                color: AppTheme.scaffoldBackground,
                boxShadow: [
                  BoxShadow(
                    color: Color(0x1A000000),
                    blurRadius: 24,
                    offset: Offset(0, 4),
                  ),
                ],
              ),
              child: child ?? const SizedBox.shrink(),
            ),
          ),
        );
      },
      home: const MainNavigationScreen(),
    );
  }
}
