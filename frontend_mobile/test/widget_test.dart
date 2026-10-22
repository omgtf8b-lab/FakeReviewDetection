import 'package:flutter/material.dart';

import 'dart:convert';

import 'package:http/http.dart' as http;
import 'package:http/testing.dart';
import 'package:frontend_mobile/services/product_api_service.dart';
import 'package:frontend_mobile/services/review_api_service.dart';
import 'package:frontend_mobile/services/workspace_api.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_mobile/data/mock_data.dart';
import 'package:frontend_mobile/main.dart';
import 'package:frontend_mobile/screens/home_screen.dart';
import 'package:frontend_mobile/screens/search_screen.dart';
import 'package:frontend_mobile/screens/product_detail_screen.dart';
import 'package:frontend_mobile/screens/product_reviews_screen.dart';
import 'package:frontend_mobile/screens/review_detail_screen.dart';

void main() {
  setUp(() {
    Future<http.Response> respond(http.Request request) async {
      final path = request.url.path;
      dynamic data;
      Map<String, dynamic> productJson(dynamic p) => {
        'id': p.id,
        'name': p.name,
        'brand': p.brand,
        'category': p.category,
        'price': p.price,
        'description': p.description,
        'shop_id': 1,
      };
      if (path == '/api/products') {
        final search = (request.url.queryParameters['search'] ?? '')
            .toLowerCase();
        final items = MockData.products
            .where((p) => p.name.toLowerCase().contains(search))
            .map(productJson)
            .toList();
        data = {
          'items': items,
          'total': items.length,
          'page': 1,
          'page_size': 100,
        };
      } else if (path.startsWith('/api/products/')) {
        data = productJson(
          MockData.products.firstWhere((p) => p.id == path.split('/').last),
        );
      } else if (path.startsWith('/api/reviews/product/')) {
        final p = MockData.products.firstWhere(
          (p) => p.id == path.split('/').last,
        );
        final items = p.reviews
            .map(
              (r) => {
                'id': r.id,
                'product_id': p.id,
                'user_id': 100 + p.reviews.indexOf(r),
                'author_name': r.author,
                'rating': r.rating,
                'content': r.content,
                'created_at': '2026-10-01T12:00:00',
                'prediction': {
                  'id': p.reviews.indexOf(r) + 1,
                  'review_id': p.reviews.indexOf(r) + 1,
                  'predicted_label': r.isFake ? 'fake' : 'real',
                  'fake_probability': r.fakeConfidence,
                  'real_probability': 1 - r.fakeConfidence,
                  'confidence_score': r.isFake
                      ? r.fakeConfidence
                      : 1 - r.fakeConfidence,
                  'model_name': 'test_fixture',
                  'model_version': 'fixture',
                },
              },
            )
            .toList();
        data = {
          'items': items,
          'total': items.length,
          'page': 1,
          'page_size': 100,
        };
      } else if (path == '/api/workspace/shops') {
        data = [];
      } else {
        return http.Response(
          jsonEncode({'detail': 'Unexpected test endpoint: $path'}),
          404,
          headers: {'content-type': 'application/json'},
        );
      }
      return http.Response(
        jsonEncode(data),
        200,
        headers: {'content-type': 'application/json'},
      );
    }

    ProductApiService.setClientForTesting(MockClient(respond));
    ReviewApiService.setClientForTesting(MockClient(respond));
    WorkspaceApi.clientFactory = () => MockClient(respond);
  });
  testWidgets('FakeReviewDetectionApp smoke test & navigation tabs', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const FakeReviewDetectionApp());

    expect(find.text('Kiểm tra sản phẩm'), findsOneWidget);
    expect(find.text('Kiểm tra'), findsOneWidget);
    expect(find.text('Lịch sử'), findsOneWidget);
    expect(find.text('Tài khoản'), findsWidgets);
    expect(find.text('Quản trị'), findsNothing);
    expect(find.text('Đặt mua'), findsNothing);
  });

  testWidgets('SearchScreen filters products correctly', (
    WidgetTester tester,
  ) async {
    await tester.pumpWidget(const MaterialApp(home: SearchScreen()));
    await tester.pumpAndSettle();

    // Verify Search Screen AppBar
    expect(find.text('Tìm kiếm sản phẩm'), findsOneWidget);

    // Enter search query
    await tester.enterText(find.byType(TextField), 'Tai nghe');
    await tester.pump(const Duration(milliseconds: 800));
    await tester.pumpAndSettle();

    // Verify result contains the earbuds product
    expect(find.text('Tai nghe không dây UltraSound ANC Pro'), findsOneWidget);
  });

  testWidgets(
    'ProductDetailScreen shows Week 7 Phân tích đánh giá and 3 review previews',
    (WidgetTester tester) async {
      final product = MockData.products.first;

      await tester.pumpWidget(
        MaterialApp(home: ProductDetailScreen(product: product)),
      );
      await tester.pumpAndSettle();

      // Verify product name, category, and formatted price
      expect(find.text(product.name), findsOneWidget);
      expect(find.text(product.formattedPrice), findsOneWidget);
      expect(
        find.text('${product.brand} • ${product.category}'),
        findsOneWidget,
      );

      // Verify Review Analysis Summary ("Phân tích đánh giá")
      expect(find.text('Phân tích đánh giá'), findsOneWidget);
      expect(find.text('Tổng đánh giá'), findsOneWidget);
      expect(find.text('Đánh giá gốc'), findsWidgets);
      expect(find.text('Đánh giá đáng ngờ'), findsWidgets);

      // Ensure NO fake Trust Score is displayed
      expect(find.text('Trust Score'), findsNothing);
      expect(find.textContaining('/ 100'), findsNothing);

      // Verify "Xem tất cả đánh giá" button exists
      expect(find.text('Xem tất cả đánh giá'), findsOneWidget);

      // Verify 3 preview reviews are rendered
      expect(find.text('Đánh giá gần đây'), findsOneWidget);
      expect(find.text('Trần Minh Quân'), findsOneWidget);
      expect(find.text('Nguyễn Văn B'), findsOneWidget);
      expect(find.text('Lê Hoàng Nam'), findsOneWidget);

      // Verify warning label and Điểm phân tích: 0.87 for suspicious review
      expect(find.text('Điểm phân tích: 0.87'), findsOneWidget);
    },
  );

  testWidgets(
    'ProductReviewsScreen supports filtering by Đáng ngờ and star ratings',
    (WidgetTester tester) async {
      final product = MockData.products.first;

      await tester.pumpWidget(
        MaterialApp(home: ProductReviewsScreen(product: product)),
      );

      // Verify required filters
      expect(find.text('Tất cả'), findsOneWidget);
      expect(find.text('5 sao'), findsOneWidget);
      expect(find.text('4 sao'), findsOneWidget);
      expect(find.text('3 sao'), findsOneWidget);
      expect(find.text('Đáng ngờ'), findsAtLeastNWidgets(1));

      // Tap "Đáng ngờ" filter
      await tester.tap(find.widgetWithText(ChoiceChip, 'Đáng ngờ'));
      await tester.pumpAndSettle();

      // Verify suspicious reviews are shown (Nguyễn Văn B)
      expect(find.text('Nguyễn Văn B'), findsOneWidget);
      // Verify genuine review (Trần Minh Quân) is filtered out
      expect(find.text('Trần Minh Quân'), findsNothing);
    },
  );

  testWidgets(
    'ReviewDetailScreen displays Kết quả phân tích, explanation, and mandatory disclaimer',
    (WidgetTester tester) async {
      final product = MockData.products.first;
      // Suspicious review
      final suspiciousReview = product.reviews[1];

      await tester.pumpWidget(
        MaterialApp(
          home: ReviewDetailScreen(review: suspiciousReview, product: product),
        ),
      );

      // Verify Review Detail screen elements
      expect(find.text('Chi tiết đánh giá'), findsOneWidget);
      expect(find.text(suspiciousReview.author), findsOneWidget);
      expect(find.text(suspiciousReview.content), findsOneWidget);

      // Verify "Kết quả phân tích" section
      expect(find.text('Kết quả phân tích'), findsOneWidget);
      expect(find.text('Đánh giá đáng ngờ'), findsWidgets);
      expect(
        find.text('Có dấu hiệu là đánh giá được sinh bởi máy tính'),
        findsOneWidget,
      );
      expect(find.text('Điểm phân tích: 0.87'), findsOneWidget);

      // Verify "Giải thích kết quả"
      expect(find.text('Giải thích kết quả'), findsOneWidget);

      // Verify mandatory disclaimer note
      expect(
        find.text(
          'Kết quả phân tích được sử dụng để hỗ trợ nhận diện đánh giá đáng ngờ và không phải là kết luận tuyệt đối về hành vi gian lận.',
        ),
        findsOneWidget,
      );
    },
  );

  testWidgets(
    'ReviewDetailScreen displays Original Review explanation for genuine reviews',
    (WidgetTester tester) async {
      final product = MockData.products.first;
      // Genuine review
      final genuineReview = product.reviews[0];

      await tester.pumpWidget(
        MaterialApp(
          home: ReviewDetailScreen(review: genuineReview, product: product),
        ),
      );

      expect(find.text('Đánh giá gốc'), findsWidgets);
      expect(
        find.text('Đánh giá có đặc điểm giống nội dung do người dùng viết'),
        findsOneWidget,
      );
      expect(find.text('Điểm phân tích: 0.05'), findsOneWidget);
    },
  );

  testWidgets(
    'Full End-to-End Navigation: Product Card -> Product Detail -> All Reviews -> Filter Đáng ngờ -> Review Detail',
    (WidgetTester tester) async {
      tester.view.physicalSize = const Size(430, 932);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      await tester.pumpWidget(
        MaterialApp(home: HomeScreen(onTabChange: (_) {})),
      );
      await tester.pumpAndSettle();

      // 1. Home Screen: Scroll and tap the first product card
      final firstProductCard = find.text(
        'Tai nghe không dây UltraSound ANC Pro',
      );
      expect(firstProductCard, findsOneWidget);
      await tester.drag(
        find.byType(SingleChildScrollView).first,
        const Offset(0, -250),
      );
      await tester.pumpAndSettle();
      await tester.tap(firstProductCard);
      await tester.pumpAndSettle();

      // 2. Product Detail Screen: Verify screen and recent reviews
      expect(find.text('Chi tiết sản phẩm'), findsOneWidget);
      expect(find.text('Phân tích đánh giá'), findsOneWidget);
      expect(find.text('1420'), findsNothing);
      expect(find.text('3'), findsWidgets);
      expect(find.text('Đánh giá gần đây'), findsOneWidget);
      expect(find.text('Nguyễn Văn B'), findsOneWidget);
      expect(find.text('Điểm phân tích: 0.87'), findsOneWidget);

      // 3. Scroll down and tap "Xem tất cả đánh giá"
      final viewAllBtn = find.text('Xem tất cả đánh giá');
      expect(viewAllBtn, findsOneWidget);
      await tester.drag(
        find.byType(SingleChildScrollView).first,
        const Offset(0, -700),
      );
      await tester.pumpAndSettle();
      await tester.ensureVisible(viewAllBtn);
      await tester.tap(viewAllBtn);
      await tester.pumpAndSettle();

      // 4. Product Reviews Screen: Verify header and filter by 'Đáng ngờ'
      expect(find.text('Đánh giá sản phẩm'), findsOneWidget);
      await tester.drag(find.text('5 sao'), const Offset(-150, 0));
      await tester.pumpAndSettle();
      await tester.tap(find.widgetWithText(ChoiceChip, 'Đáng ngờ'));
      await tester.pumpAndSettle();
      expect(find.text('Nguyễn Văn B'), findsOneWidget);

      // 5. Tap the suspicious review to open Review Detail
      await tester.tap(find.text('Nguyễn Văn B'));
      await tester.pumpAndSettle();

      // 6. Review Detail Screen: Verify classifications and explanations
      expect(find.text('Chi tiết đánh giá'), findsOneWidget);
      expect(find.text('Đánh giá đáng ngờ'), findsWidgets);
      expect(
        find.text('Có dấu hiệu là đánh giá được sinh bởi máy tính'),
        findsOneWidget,
      );
      expect(find.text('87%'), findsWidgets);

      // 7. Test back button navigation
      final backBtn = find.byTooltip('Quay lại');
      expect(backBtn, findsOneWidget);
      await tester.tap(backBtn);
      await tester.pumpAndSettle();
      expect(find.text('Đánh giá sản phẩm'), findsOneWidget);
    },
  );
}
