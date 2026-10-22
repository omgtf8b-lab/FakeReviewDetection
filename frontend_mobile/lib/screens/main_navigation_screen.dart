import 'package:flutter/material.dart';

import '../services/auth_state.dart';
import '../theme/app_theme.dart';
import 'account_screen.dart';
import 'product_inspector_screen.dart';
import 'workspace_screen.dart';

class MainNavigationScreen extends StatefulWidget {
  const MainNavigationScreen({super.key});
  @override
  State<MainNavigationScreen> createState() => _MainNavigationScreenState();
}

class _MainNavigationScreenState extends State<MainNavigationScreen> {
  int _currentIndex = 0;
  @override
  void initState() {
    super.initState();
    AuthState.instance.addListener(_changed);
  }

  @override
  void dispose() {
    AuthState.instance.removeListener(_changed);
    super.dispose();
  }

  void _changed() {
    if (mounted) {
      setState(() {
        _currentIndex = 0;
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final staff = [
      'admin',
      'engineer',
    ].contains(AuthState.instance.currentUser?.role);
    return Scaffold(
      body: IndexedStack(
        index: _currentIndex,
        children: [
          const ProductInspectorScreen(),
          const ProductInspectorScreen(historyOnly: true),
          const AccountScreen(),
          if (staff) const WorkspaceScreen(),
        ],
      ),
      bottomNavigationBar: BottomNavigationBar(
        currentIndex: _currentIndex,
        onTap: (index) => setState(() {
          _currentIndex = index;
        }),
        type: BottomNavigationBarType.fixed,
        selectedItemColor: AppTheme.primaryBlue,
        items: [
          const BottomNavigationBarItem(
            icon: Icon(Icons.fact_check_outlined),
            label: 'Kiểm tra',
          ),
          const BottomNavigationBarItem(
            icon: Icon(Icons.history),
            label: 'Lịch sử',
          ),
          const BottomNavigationBarItem(
            icon: Icon(Icons.person_outline),
            label: 'Tài khoản',
          ),
          if (staff)
            const BottomNavigationBarItem(
              icon: Icon(Icons.admin_panel_settings_outlined),
              label: 'Quản trị',
            ),
        ],
      ),
    );
  }
}
