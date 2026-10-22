import 'dart:convert';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/user.dart';

class AuthApiException implements Exception {
  final String message;
  final int? statusCode;

  const AuthApiException(this.message, {this.statusCode});

  @override
  String toString() => message;
}

class LoginResult {
  final String accessToken;
  final String tokenType;
  final int expiresIn;
  final User user;

  const LoginResult({
    required this.accessToken,
    required this.tokenType,
    required this.expiresIn,
    required this.user,
  });

  factory LoginResult.fromJson(Map<String, dynamic> json) {
    return LoginResult(
      accessToken: (json['access_token'] as String?) ?? '',
      tokenType: (json['token_type'] as String?) ?? 'bearer',
      expiresIn: (json['expires_in'] as num?)?.toInt() ?? 3600,
      user: User.fromJson(json['user'] as Map<String, dynamic>),
    );
  }
}

class AuthApiService {
  static final http.Client _client = http.Client();

  static Map<String, String> authHeaders(String token) {
    return {
      'Content-Type': 'application/json',
      'Accept': 'application/json',
      'Authorization': 'Bearer $token',
    };
  }

  static Future<LoginResult> login({
    required String email,
    required String password,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/auth/login');
    try {
      final response = await _client
          .post(
            uri,
            headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
            body: jsonEncode({
              'email': email.trim(),
              'password': password,
            }),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final Map<String, dynamic> body =
            json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return LoginResult.fromJson(body);
      } else {
        final errorMsg = _extractErrorMessage(response, defaultMsg: 'Đăng nhập không thành công.');
        throw AuthApiException(errorMsg, statusCode: response.statusCode);
      }
    } on AuthApiException {
      rethrow;
    } catch (e) {
      throw const AuthApiException('Không thể kết nối đến máy chủ.');
    }
  }

  static Future<User> register({
    required String email,
    required String password,
  }) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/auth/register');
    try {
      final response = await _client
          .post(
            uri,
            headers: {'Content-Type': 'application/json', 'Accept': 'application/json'},
            body: jsonEncode({
              'email': email.trim(),
              'password': password,
            }),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200 || response.statusCode == 201) {
        final Map<String, dynamic> body =
            json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return User.fromJson(body);
      } else {
        final errorMsg = _extractErrorMessage(response, defaultMsg: 'Đăng ký không thành công.');
        throw AuthApiException(errorMsg, statusCode: response.statusCode);
      }
    } on AuthApiException {
      rethrow;
    } catch (e) {
      throw const AuthApiException('Không thể kết nối đến máy chủ.');
    }
  }

  static Future<User> getCurrentUser(String token) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/auth/me');
    try {
      final response = await _client
          .get(
            uri,
            headers: authHeaders(token),
          )
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final Map<String, dynamic> body =
            json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return User.fromJson(body);
      } else if (response.statusCode == 401 || response.statusCode == 403) {
        final errorMsg = _extractErrorMessage(
          response,
          defaultMsg: response.statusCode == 403
              ? 'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.'
              : 'Phiên đăng nhập đã hết hạn hoặc không hợp lệ.',
        );
        throw AuthApiException(
          errorMsg,
          statusCode: response.statusCode,
        );
      } else {
        final errorMsg = _extractErrorMessage(response, defaultMsg: 'Không thể tải thông tin tài khoản.');
        throw AuthApiException(errorMsg, statusCode: response.statusCode);
      }
    } on AuthApiException {
      rethrow;
    } catch (e) {
      throw const AuthApiException('Không thể kết nối đến máy chủ.');
    }
  }

  static String _extractErrorMessage(http.Response response, {required String defaultMsg}) {
    try {
      final Map<String, dynamic> body =
          json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
      final detail = body['detail'];

      if (detail is String && detail.trim().isNotEmpty) {
        final lower = detail.toLowerCase();
        if (response.statusCode == 401 || response.statusCode == 403) {
          if (lower.contains('khóa') || lower.contains('inactive') || lower.contains('disabled')) {
            return 'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.';
          }
          if (response.statusCode == 403) {
            return 'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.';
          }
          return 'Email hoặc mật khẩu không đúng.';
        }
        if (response.statusCode == 400 &&
            (lower.contains('email') || lower.contains('đã được đăng ký') || lower.contains('already exists'))) {
          return 'Email này đã được sử dụng.';
        }
        return detail;
      } else if (detail is List && detail.isNotEmpty) {
        final first = detail.first;
        if (first is Map && first['msg'] != null) {
          final msg = first['msg'].toString();
          if (msg.contains('8 characters') || msg.contains('at least 8')) {
            return 'Mật khẩu phải có ít nhất 8 ký tự.';
          }
          if (msg.contains('valid email')) {
            return 'Định dạng email không hợp lệ.';
          }
          return msg;
        }
      }
    } catch (_) {}

    if (response.statusCode == 401) {
      return 'Email hoặc mật khẩu không đúng.';
    }
    if (response.statusCode == 403) {
      return 'Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.';
    }
    if (response.statusCode == 404) {
      return 'Không tìm thấy dữ liệu yêu cầu.';
    }
    return defaultMsg;
  }
}
