import 'package:flutter/material.dart';
import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_mobile/models/product.dart';
import 'package:frontend_mobile/models/review.dart';
import 'package:frontend_mobile/models/user.dart';
import 'package:frontend_mobile/screens/review_detail_screen.dart';
import 'package:frontend_mobile/services/auth_state.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  const sampleProduct = Product(
    id: 'prod_1',
    name: 'Tai nghe Bluetooth Pro',
    category: 'Âm thanh',
    brand: 'TechBrand',
    price: 990000,
    description: 'Tai nghe Bluetooth không dây tiện dụng',
    rating: 4.5,
    totalReviews: 10,
    fakeReviewsCount: 2,
    trustScore: 80,
    riskLevel: RiskLevel.low,
    icon: Icons.headphones,
  );

  const sampleReview = Review(
    id: 'rev_100',
    productId: 'prod_1',
    rating: 5.0,
    content: 'Tai nghe chất lượng rất tốt, pin trâu và chống ồn ổn.',
    isAnalyzed: true,
    isFake: false,
  );

  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  tearDown(() {
    AuthState.instance.setSessionForTesting(token: null, user: null);
  });

  group('Report Review Flow Tests', () {
    testWidgets(
        'Requirement 12: Old immediate snackbar "Đã ghi nhận báo cáo" is removed',
        (WidgetTester tester) async {
      tester.view.physicalSize = const Size(800, 1200);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      AuthState.instance.setSessionForTesting(token: null, user: null);

      await tester.pumpWidget(
        const MaterialApp(
          home: ReviewDetailScreen(
            review: sampleReview,
            product: sampleProduct,
          ),
        ),
      );

      final reportBtn = find.widgetWithText(TextButton, 'Báo cáo');
      expect(reportBtn, findsOneWidget);

      await tester.ensureVisible(reportBtn);
      await tester.tap(reportBtn);
      await tester.pumpAndSettle();

      // Ensure old messages NEVER appear
      expect(find.text('Đã ghi nhận báo cáo này.'), findsNothing);
      expect(find.text('Đã ghi nhận báo cáo đánh giá này.'), findsNothing);
    });

    testWidgets(
        'Requirement 9: Logged-out user: pressing Báo cáo shows login prompt and does not open form',
        (WidgetTester tester) async {
      tester.view.physicalSize = const Size(800, 1200);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      AuthState.instance.setSessionForTesting(token: null, user: null);

      await tester.pumpWidget(
        const MaterialApp(
          home: ReviewDetailScreen(
            review: sampleReview,
            product: sampleProduct,
          ),
        ),
      );

      final reportBtn = find.widgetWithText(TextButton, 'Báo cáo');
      await tester.ensureVisible(reportBtn);
      await tester.tap(reportBtn);
      await tester.pumpAndSettle();

      // Verify login required message
      expect(
          find.text('Bạn cần đăng nhập để báo cáo đánh giá.'), findsOneWidget);
      expect(find.text('Đăng nhập'), findsOneWidget);

      // Verify report modal was NOT opened
      expect(find.text('Lý do báo cáo'), findsNothing);
      expect(find.text('Gửi báo cáo'), findsNothing);
    });

    testWidgets(
        'Requirement 9: Locked user: pressing Báo cáo shows account locked message',
        (WidgetTester tester) async {
      tester.view.physicalSize = const Size(800, 1200);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      const lockedUser = User(
        id: 99,
        email: 'locked@example.com',
        role: 'buyer',
        isActive: false,
      );
      AuthState.instance.setSessionForTesting(
        token: 'locked_token',
        user: lockedUser,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: ReviewDetailScreen(
            review: sampleReview,
            product: sampleProduct,
          ),
        ),
      );

      final reportBtn = find.widgetWithText(TextButton, 'Báo cáo');
      await tester.ensureVisible(reportBtn);
      await tester.tap(reportBtn);
      await tester.pumpAndSettle();

      // Verify locked account message
      expect(
        find.text('Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.'),
        findsOneWidget,
      );

      // Verify report modal was NOT opened
      expect(find.text('Lý do báo cáo'), findsNothing);
    });

    testWidgets(
        'Requirements 3, 4, 5, 6, 7: Active user opens form, sees preview, validates required reason, cancels',
        (WidgetTester tester) async {
      tester.view.physicalSize = const Size(800, 1200);
      tester.view.devicePixelRatio = 1.0;
      addTearDown(() {
        tester.view.resetPhysicalSize();
        tester.view.resetDevicePixelRatio();
      });

      const activeUser = User(
        id: 1,
        email: 'active@example.com',
        role: 'buyer',
        isActive: true,
      );
      AuthState.instance.setSessionForTesting(
        token: 'valid_jwt_token',
        user: activeUser,
      );

      await tester.pumpWidget(
        const MaterialApp(
          home: ReviewDetailScreen(
            review: sampleReview,
            product: sampleProduct,
          ),
        ),
      );

      // 1. Press Báo cáo
      final reportBtn = find.widgetWithText(TextButton, 'Báo cáo');
      await tester.ensureVisible(reportBtn);
      await tester.tap(reportBtn);
      await tester.pumpAndSettle();

      // 2. Report modal is open
      expect(find.text('Báo cáo đánh giá'), findsOneWidget);

      // 3. Review preview is displayed (once on screen, once in preview card)
      expect(find.text('5.0 sao'), findsOneWidget);
      expect(find.text(sampleReview.content), findsNWidgets(2));
      expect(find.text(sampleReview.statusLabel), findsWidgets);

      // 4. "Lý do báo cáo" header and options are displayed
      expect(find.text('Lý do báo cáo'), findsOneWidget);
      expect(find.text('Nghi ngờ đánh giá giả'), findsOneWidget);
      expect(find.text('Spam / nội dung lặp'), findsOneWidget);
      expect(find.text('Nội dung sai lệch'), findsOneWidget);
      expect(find.text('Nội dung không phù hợp'), findsOneWidget);
      expect(find.text('Lý do khác'), findsOneWidget);

      // 5. Optional detail text field is present
      expect(find.text('Chi tiết bổ sung (tùy chọn)'), findsOneWidget);

      // 6. Action buttons: Hủy and Gửi báo cáo
      expect(find.text('Hủy'), findsOneWidget);
      final submitBtn = find.text('Gửi báo cáo');
      expect(submitBtn, findsOneWidget);

      // 7. Validation: Press Gửi báo cáo without selecting a reason
      await tester.tap(submitBtn);
      await tester.pumpAndSettle();

      // Verify validation error
      expect(find.text('Vui lòng chọn lý do báo cáo.'), findsOneWidget);

      // 8. Select a reason
      await tester.tap(find.text('Nghi ngờ đánh giá giả'));
      await tester.pumpAndSettle();

      // Verify validation error is cleared
      expect(find.text('Vui lòng chọn lý do báo cáo.'), findsNothing);

      // 9. Press Hủy
      await tester.tap(find.text('Hủy'));
      await tester.pumpAndSettle();

      // Modal is closed
      expect(find.text('Lý do báo cáo'), findsNothing);
    });

    test('Review primary key is review.id and distinct from userId/productId', () {
      const testReview = Review(
        id: '1',
        productId: '42',
        userId: 99,
        rating: 4.5,
        content: 'Review content for testing',
      );

      // Verify that the primary key is review.id, NOT userId or productId
      expect(testReview.id, equals('1'));
      expect(testReview.productId, equals('42'));
      expect(testReview.userId, equals(99));
      expect(testReview.id, isNot(equals(testReview.userId.toString())));
      expect(testReview.id, isNot(equals(testReview.productId)));
    });
  });
}
