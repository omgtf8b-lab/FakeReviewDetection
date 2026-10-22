import 'dart:convert';

import 'package:http/http.dart' as http;

import '../config/api_config.dart';
import 'auth_state.dart';

class WorkspaceApi {
  static http.Client Function() clientFactory = http.Client.new;
  static Future<dynamic> upload(
    String path,
    List<http.MultipartFile> files,
  ) async {
    final request = http.MultipartRequest(
      'POST',
      Uri.parse('${ApiConfig.baseUrl}$path'),
    );
    final token = AuthState.instance.token;
    if (token != null) request.headers['Authorization'] = 'Bearer $token';
    request.files.addAll(files);
    final client = clientFactory();
    try {
      final response = await http.Response.fromStream(
        await client.send(request).timeout(const Duration(seconds: 120)),
      );
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      if (response.statusCode == 401) {
        await AuthState.instance.handleSessionExpired();
      }
      if (response.statusCode >= 400) {
        throw Exception(
          data is Map && data['detail'] is String
              ? data['detail']
              : 'Không tải được tệp.',
        );
      }
      return data;
    } finally {
      client.close();
    }
  }

  static Future<dynamic> request(
    String path, {
    String method = 'GET',
    Map<String, dynamic>? body,
  }) async {
    final token = AuthState.instance.token;
    final request = http.Request(
      method,
      Uri.parse('${ApiConfig.baseUrl}$path'),
    );
    request.headers['Accept'] = 'application/json';
    if (token != null) request.headers['Authorization'] = 'Bearer $token';
    if (body != null) {
      request.headers['Content-Type'] = 'application/json';
      request.body = jsonEncode(body);
    }
    final client = clientFactory();
    try {
      final streamed = await client
          .send(request)
          .timeout(const Duration(seconds: 60));
      final response = await http.Response.fromStream(streamed);
      final data = jsonDecode(utf8.decode(response.bodyBytes));
      if (response.statusCode == 401) {
        await AuthState.instance.handleSessionExpired();
      }
      if (response.statusCode >= 400) {
        final detail = data is Map ? data['detail'] : null;
        throw Exception(
          detail is String
              ? detail
              : 'Yêu cầu không hợp lệ (${response.statusCode}).',
        );
      }
      return data;
    } finally {
      client.close();
    }
  }
}
