import 'package:flutter_test/flutter_test.dart';
import 'package:frontend_mobile/models/review.dart';
import 'package:frontend_mobile/models/user.dart';
import 'package:frontend_mobile/services/auth_api_service.dart';
import 'package:frontend_mobile/services/auth_state.dart';
import 'package:frontend_mobile/services/token_storage_service.dart';
import 'package:shared_preferences/shared_preferences.dart';

void main() {
  setUp(() {
    SharedPreferences.setMockInitialValues({});
  });

  group('User Model Tests', () {
    test('User fromJson parses real backend user schema correctly', () {
      final json = {
        'id': 1,
        'email': 'buyer@example.com',
        'role': 'buyer',
        'is_active': true,
        'created_at': '2026-10-03T16:07:33',
      };

      final user = User.fromJson(json);

      expect(user.id, 1);
      expect(user.email, 'buyer@example.com');
      expect(user.role, 'buyer');
      expect(user.isActive, true);
      expect(user.roleLabel, 'Người dùng');
      expect(user.statusLabel, 'Hoạt động');
      expect(user.formattedCreatedAt, '03/10/2026 16:07');
    });

    test('Role label mapping covers all backend roles', () {
      const buyer = User(id: 1, email: 'a@b.c', role: 'buyer', isActive: true);
      const seller = User(id: 2, email: 'a@b.c', role: 'seller', isActive: true);
      const admin = User(id: 3, email: 'a@b.c', role: 'admin', isActive: true);
      const engineer = User(id: 4, email: 'a@b.c', role: 'engineer', isActive: true);

      expect(buyer.roleLabel, 'Người dùng');
      expect(seller.roleLabel, 'Người bán');
      expect(admin.roleLabel, 'Quản trị viên');
      expect(engineer.roleLabel, 'Kỹ thuật viên');
    });

    test('User status label indicates active vs locked', () {
      const activeUser = User(id: 1, email: 'a@b.c', role: 'buyer', isActive: true);
      const lockedUser = User(id: 2, email: 'a@b.c', role: 'buyer', isActive: false);

      expect(activeUser.statusLabel, 'Hoạt động');
      expect(lockedUser.statusLabel, 'Đã khóa');
    });
  });

  group('LoginResult Tests', () {
    test('LoginResult parses token response format', () {
      final json = {
        'access_token': 'test_jwt_token_123',
        'token_type': 'bearer',
        'expires_in': 3600,
        'user': {
          'id': 10,
          'email': 'test@example.com',
          'role': 'buyer',
          'is_active': true,
          'created_at': '2026-10-01T12:00:00',
        },
      };

      final result = LoginResult.fromJson(json);
      expect(result.accessToken, 'test_jwt_token_123');
      expect(result.tokenType, 'bearer');
      expect(result.expiresIn, 3600);
      expect(result.user.email, 'test@example.com');
    });
  });

  group('TokenStorageService & AuthState Tests', () {
    test('TokenStorageService saves, reads, and clears token', () async {
      SharedPreferences.setMockInitialValues({});

      expect(await TokenStorageService.hasToken(), false);
      expect(await TokenStorageService.getToken(), isNull);

      await TokenStorageService.saveToken('my_jwt_token');
      expect(await TokenStorageService.hasToken(), true);
      expect(await TokenStorageService.getToken(), 'my_jwt_token');

      await TokenStorageService.clearToken();
      expect(await TokenStorageService.hasToken(), false);
      expect(await TokenStorageService.getToken(), isNull);
    });

    test('AuthState initial state and logout work correctly', () async {
      SharedPreferences.setMockInitialValues({});
      final auth = AuthState.instance;

      expect(auth.isAuthenticated, false);
      expect(auth.currentUser, isNull);
      expect(auth.token, isNull);

      await auth.logout();
      expect(auth.isAuthenticated, false);
      expect(auth.currentUser, isNull);
    });

    test('handleSessionExpired clears token and user', () async {
      SharedPreferences.setMockInitialValues({'auth_access_token': 'expired_token'});
      final auth = AuthState.instance;

      await auth.handleSessionExpired('Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.');
      expect(auth.isAuthenticated, false);
      expect(auth.currentUser, isNull);
      expect(auth.token, isNull);
      expect(await TokenStorageService.hasToken(), false);
      expect(auth.errorMessage, 'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.');
    });
  });

  group('Locked Account Handling Tests', () {
    test('User with is_active == false has correct statusLabel', () {
      const lockedUser = User(
        id: 99,
        email: 'locked@example.com',
        role: 'buyer',
        isActive: false,
      );

      expect(lockedUser.isActive, false);
      expect(lockedUser.statusLabel, 'Đã khóa');
    });
  });

  group('Review Detail Requirement 23 Tests', () {
    test('Review internalStateName returns Vietnamese headings', () {
      const genuineReview = Review(
        id: '1',
        productId: '10',
        rating: 5.0,
        content: 'Great product',
        isAnalyzed: true,
        isFake: false,
      );

      const suspiciousReview = Review(
        id: '2',
        productId: '10',
        rating: 1.0,
        content: 'Fake product review',
        isAnalyzed: true,
        isFake: true,
      );

      expect(genuineReview.internalStateName, 'Đánh giá gốc');
      expect(suspiciousReview.internalStateName, 'Đánh giá đáng ngờ');
    });
  });
}
