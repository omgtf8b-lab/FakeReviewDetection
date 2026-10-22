import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_mobile/widgets/collector_diagnostics.dart';

void main() {
  testWidgets(
    'Fallback displays safe code without raw logs, paths or invalid versions',
    (tester) async {
      final data = {
        'attempts': [
          {
            'collector': 'selenium',
            'diagnostics': {
              'code': 'chrome_crashpad_failed',
              'raw': 'synthetic-private',
              'driver_version_from_log': 'synthetic-private',
            },
          },
        ],
        'diagnostics': {
          'code': 'chrome_crashpad_failed',
          'profile': 'C:/private',
        },
      };
      await tester.pumpWidget(
        MaterialApp(
          home: Scaffold(body: CollectorDiagnostics(data: data)),
        ),
      );
      expect(find.textContaining('chrome_crashpad_failed'), findsOneWidget);
      expect(find.textContaining('synthetic-private'), findsNothing);
      expect(find.textContaining('C:/private'), findsNothing);
    },
  );
  test(
    'Malformed and unknown diagnostics are ignored; outer worker is distinct',
    () {
      expect(
        collectorDiagnosticItems({
          'diagnostics': {'code': 'synthetic-private'},
        }),
        isEmpty,
      );
      expect(
        collectorDiagnosticItems({'attempts': 'invalid', 'diagnostics': []}),
        isEmpty,
      );
      final rows = collectorDiagnosticItems({
        'diagnostics': {'stage': 'collection', 'code': 'collection_timeout'},
      });
      expect(rows.single['source'], 'collection');
    },
  );
}
