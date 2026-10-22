import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:frontend_mobile/models/user.dart';
import 'package:frontend_mobile/screens/product_inspector_screen.dart';
import 'package:frontend_mobile/services/auth_state.dart';
import 'package:frontend_mobile/services/workspace_api.dart';

void main() {
  setUp(() {
    AuthState.instance.setSessionForTesting(
      token: 'fixture-token',
      user: const User(
        id: 1,
        email: 'fixture@example.com',
        role: 'buyer',
        isActive: true,
      ),
    );
  });
  tearDown(() {
    AuthState.instance.setSessionForTesting(token: null, user: null);
  });
  testWidgets(
    'Link submits, polls and reports unavailable reviews without a fake percentage',
    (tester) async {
      bool posted = false;
      WorkspaceApi.clientFactory = () => MockClient((request) async {
        dynamic result = [];
        if (request.method == 'POST') {
          posted = true;
          expect(
            jsonDecode(request.body)['url'],
            'https://shopee.vn/product/123/456',
          );
          result = {'id': 7, 'status': 'queued', 'platform': 'shopee'};
        } else if (request.url.path.endsWith('/7')) {
          result = {
            'id': 7,
            'status': 'completed',
            'platform': 'shopee',
            'result': {
              'source': 'public_page_structured_data',
              'collection_message': 'Sàn chưa cung cấp review.',
              'summary': {
                'observed_reviews': 0,
                'reviews_with_signals': 0,
                'signal_percentage': null,
                'verdict': 'insufficient_data',
              },
              'reviews': [],
              'limitations': [],
            },
          };
        }
        return http.Response(
          jsonEncode(result),
          200,
          headers: {'content-type': 'application/json'},
        );
      });
      await tester.pumpWidget(
        const MaterialApp(home: ProductInspectorScreen()),
      );
      await tester.pumpAndSettle();
      await tester.enterText(
        find.byType(TextField),
        'https://shopee.vn/product/123/456',
      );
      await tester.tap(find.text('Kiểm tra link'));
      await tester.pump();
      await tester.pump(const Duration(seconds: 2));
      await tester.pumpAndSettle();
      expect(posted, isTrue);
      expect(find.text('Chưa đủ cơ sở kết luận'), findsOneWidget);
      expect(find.textContaining('chưa có số liệu'), findsOneWidget);
      expect(find.text('Tải ảnh'), findsOneWidget);
      expect(find.text('Tải video'), findsOneWidget);
      expect(find.textContaining('0%'), findsNothing);
      await tester.pumpWidget(const SizedBox());
    },
  );
  testWidgets('History screen does not show purchase controls', (tester) async {
    WorkspaceApi.clientFactory = () =>
        MockClient((request) async => http.Response('[]', 200));
    await tester.pumpWidget(
      const MaterialApp(home: ProductInspectorScreen(historyOnly: true)),
    );
    await tester.pumpAndSettle();
    expect(find.text('Lịch sử của tôi'), findsOneWidget);
    expect(find.text('Đặt mua'), findsNothing);
    expect(find.text('Kiểm tra link'), findsNothing);
    await tester.pumpWidget(const SizedBox());
  });
}
