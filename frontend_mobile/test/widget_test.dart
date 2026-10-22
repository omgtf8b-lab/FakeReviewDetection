import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_mobile/data/mock_data.dart';
import 'package:frontend_mobile/main.dart';
import 'package:frontend_mobile/screens/product_detail_screen.dart';
import 'package:frontend_mobile/screens/product_reviews_screen.dart';
import 'package:frontend_mobile/screens/review_detail_screen.dart';

void main() {
  testWidgets('FakeReviewDetectionApp smoke test & navigation tabs',
      (WidgetTester tester) async {
    await tester.pumpWidget(const FakeReviewDetectionApp());

    // Verify header branding
    expect(find.text('FakeReview Detection'), findsOneWidget);
    expect(find.text('Bảo vệ người tiêu dùng'), findsOneWidget);

    // Verify that bottom navigation items exist
    expect(find.text('Trang chủ'), findsOneWidget);
    expect(find.text('Tìm kiếm'), findsOneWidget);
    expect(find.text('Sản phẩm'), findsOneWidget);
    expect(find.text('Tài khoản'), findsOneWidget);

    // Verify information banner
    expect(find.text('Nhận diện đánh giá giả bằng AI'), findsOneWidget);

    // Verify search shortcut field
    expect(find.text('Tìm kiếm sản phẩm...'), findsOneWidget);
  });

  testWidgets('SearchScreen filters products correctly',
      (WidgetTester tester) async {
    await tester.pumpWidget(const FakeReviewDetectionApp());

    // Switch to Search tab
    await tester.tap(find.text('Tìm kiếm'));
    await tester.pumpAndSettle();

    // Verify Search Screen AppBar
    expect(find.text('Tìm kiếm sản phẩm'), findsOneWidget);

    // Enter search query
    await tester.enterText(find.byType(TextField), 'Tai nghe');
    await tester.pumpAndSettle();

    // Verify result contains the earbuds product
    expect(find.text('Tai nghe không dây UltraSound ANC Pro'), findsOneWidget);
  });

  testWidgets(
      'ProductDetailScreen shows Week 7 Phân tích đánh giá and 3 review previews',
      (WidgetTester tester) async {
    final product = MockData.products.first;

    await tester.pumpWidget(
      MaterialApp(
        home: ProductDetailScreen(product: product),
      ),
    );

    // Verify product name, category, and formatted price
    expect(find.text(product.name), findsOneWidget);
    expect(find.text(product.formattedPrice), findsOneWidget);
    expect(find.text('${product.brand} • ${product.category}'), findsOneWidget);

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
  });

  testWidgets(
      'ProductReviewsScreen supports filtering by Đáng ngờ and star ratings',
      (WidgetTester tester) async {
    final product = MockData.products.first;

    await tester.pumpWidget(
      MaterialApp(
        home: ProductReviewsScreen(product: product),
      ),
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
  });

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
    expect(find.text('Có dấu hiệu là đánh giá được sinh bởi máy tính'), findsOneWidget);
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
  });

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
    expect(find.text('Đánh giá có đặc điểm giống nội dung do người dùng viết'), findsOneWidget);
    expect(find.text('Điểm phân tích: 0.05'), findsOneWidget);
  });

  testWidgets(
      'Full End-to-End Navigation: Product Card -> Product Detail -> All Reviews -> Filter Đáng ngờ -> Review Detail',
      (WidgetTester tester) async {
    tester.view.physicalSize = const Size(430, 932);
    tester.view.devicePixelRatio = 1.0;
    addTearDown(() {
      tester.view.resetPhysicalSize();
      tester.view.resetDevicePixelRatio();
    });

    await tester.pumpWidget(const FakeReviewDetectionApp());
    await tester.pumpAndSettle();

    // 1. Home Screen: Scroll and tap the first product card
    final firstProductCard = find.text('Tai nghe không dây UltraSound ANC Pro');
    expect(firstProductCard, findsOneWidget);
    await tester.drag(find.byType(SingleChildScrollView).first, const Offset(0, -250));
    await tester.pumpAndSettle();
    await tester.tap(firstProductCard);
    await tester.pumpAndSettle();

    // 2. Product Detail Screen: Verify screen and recent reviews
    expect(find.text('Chi tiết sản phẩm'), findsOneWidget);
    expect(find.text('Phân tích đánh giá'), findsOneWidget);
    expect(find.text('1420'), findsOneWidget);
    expect(find.text('Đánh giá gần đây'), findsOneWidget);
    expect(find.text('Nguyễn Văn B'), findsOneWidget);
    expect(find.text('Điểm phân tích: 0.87'), findsOneWidget);

    // 3. Scroll down and tap "Xem tất cả đánh giá"
    final viewAllBtn = find.text('Xem tất cả đánh giá');
    expect(viewAllBtn, findsOneWidget);
    await tester.drag(find.byType(SingleChildScrollView).first, const Offset(0, -700));
    await tester.pumpAndSettle();
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
    expect(find.text('Có dấu hiệu là đánh giá được sinh bởi máy tính'), findsOneWidget);
    expect(find.text('Điểm phân tích: 0.87'), findsOneWidget);

    // 7. Test back button navigation
    final backBtn = find.byTooltip('Quay lại');
    expect(backBtn, findsOneWidget);
    await tester.tap(backBtn);
    await tester.pumpAndSettle();
    expect(find.text('Đánh giá sản phẩm'), findsOneWidget);
  });
}
