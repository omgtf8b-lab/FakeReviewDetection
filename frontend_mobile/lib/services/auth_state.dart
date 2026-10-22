import 'package:flutter/foundation.dart';
import '../models/user.dart';
import 'auth_api_service.dart';
import 'token_storage_service.dart';

class AuthState extends ChangeNotifier {
  static final AuthState instance = AuthState._internal();

  AuthState._internal();

  bool _isLoading = false;
  bool _isSubmitting = false;
  String? _token;
  User? _currentUser;
  String? _errorMessage;

  bool get isLoading => _isLoading;
  bool get isSubmitting => _isSubmitting;
  bool get isAuthenticated => _token != null && _currentUser != null;
  String? get token => _token;
  User? get currentUser => _currentUser;
  String? get errorMessage => _errorMessage;

  /// Restores user session on app start.
  /// Calls GET /api/auth/me to verify validity if token exists.
  /// If the account is locked (is_active == false), clears session.
  Future<void> restoreSession() async {
    try {
      final savedToken = await TokenStorageService.getToken();
      if (savedToken != null && savedToken.isNotEmpty) {
        _isLoading = true;
        _errorMessage = null;
        notifyListeners();

        try {
          final user = await AuthApiService.getCurrentUser(savedToken);
          if (!user.isActive) {
            // Locked account: clear token and remain unauthenticated
            await TokenStorageService.clearToken();
            _token = null;
            _currentUser = null;
          } else {
            _token = savedToken;
            _currentUser = user;
          }
        } on AuthApiException catch (e) {
          // Token is invalid/expired or user is locked (401/403)
          await TokenStorageService.clearToken();
          _token = null;
          _currentUser = null;
          if (e.statusCode == 401 || e.statusCode == 403) {
            _errorMessage = e.message;
          }
        } catch (_) {
          await TokenStorageService.clearToken();
          _token = null;
          _currentUser = null;
        }
      } else {
        _token = null;
        _currentUser = null;
      }
    } finally {
      _isLoading = false;
      notifyListeners();
    }
  }

  /// Logs in the user with backend credentials.
  /// Verifies active status via current-user endpoint before marking authenticated.
  Future<void> login(String email, String password) async {
    _isSubmitting = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final result = await AuthApiService.login(email: email, password: password);

      // Fast check if backend user object in login payload already indicates inactive
      if (!result.user.isActive) {
        await TokenStorageService.clearToken();
        _token = null;
        _currentUser = null;
        throw const AuthApiException(
          'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.',
          statusCode: 403,
        );
      }

      // DO NOT immediately mark as authenticated.
      // First call the real current-user endpoint to verify actual active status.
      final currentUser = await AuthApiService.getCurrentUser(result.accessToken);
      if (!currentUser.isActive) {
        await TokenStorageService.clearToken();
        _token = null;
        _currentUser = null;
        throw const AuthApiException(
          'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.',
          statusCode: 403,
        );
      }

      // User is active: persist token and mark as authenticated
      await TokenStorageService.saveToken(result.accessToken);
      _token = result.accessToken;
      _currentUser = currentUser;
    } on AuthApiException {
      await TokenStorageService.clearToken();
      _token = null;
      _currentUser = null;
      rethrow;
    } catch (e) {
      await TokenStorageService.clearToken();
      _token = null;
      _currentUser = null;
      rethrow;
    } finally {
      _isSubmitting = false;
      notifyListeners();
    }
  }

  /// Clears session when a protected API reports 401 or 403.
  Future<void> acceptExternalToken(String token) async {
    final user = await AuthApiService.getCurrentUser(token);
    if (!user.isActive) {
      throw const AuthApiException('Tài khoản đã bị khóa.', statusCode: 403);
    }
    await TokenStorageService.saveToken(token);
    _token = token;
    _currentUser = user;
    _errorMessage = null;
    notifyListeners();
  }

  /// Clears session when a protected API reports 401 or 403.
  Future<void> handleSessionExpired([String? reason]) async {
    await TokenStorageService.clearToken();
    _token = null;
    _currentUser = null;
    _errorMessage = reason ?? 'Tài khoản đã bị khóa hoặc phiên đăng nhập đã hết hạn.';
    notifyListeners();
  }

  /// Registers a new user.
  Future<User> register(String email, String password) async {
    _isSubmitting = true;
    _errorMessage = null;
    notifyListeners();

    try {
      final user = await AuthApiService.register(email: email, password: password);
      return user;
    } catch (e) {
      rethrow;
    } finally {
      _isSubmitting = false;
      notifyListeners();
    }
  }

  /// Logs out the user and clears stored token.
  Future<void> logout() async {
    await TokenStorageService.clearToken();
    _token = null;
    _currentUser = null;
    _errorMessage = null;
    notifyListeners();
  }

  /// Sets session for testing purposes.
  @visibleForTesting
  void setSessionForTesting({String? token, User? user}) {
    _token = token;
    _currentUser = user;
    notifyListeners();
  }
}

