import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/review.dart';
import 'auth_api_service.dart';
import 'auth_state.dart';

class ReviewApiException implements Exception {
  final String message;
  final int? statusCode;
  const ReviewApiException(this.message, {this.statusCode});
  @override
  String toString() => message;
}

class ReviewApiService {
  static final http.Client _client = http.Client();

  static Future<List<Review>> getReviewsByProduct(dynamic productId) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/reviews/product/$productId');
    try {
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final Map<String, dynamic> body =
            json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        final rawItems = (body['items'] as List<dynamic>?) ?? [];
        return rawItems
            .map((e) => Review.fromJson(e as Map<String, dynamic>))
            .toList();
      } else {
        throw ReviewApiException(
            'Lỗi máy chủ: HTTP ${response.statusCode}',
            statusCode: response.statusCode);
      }
    } on ReviewApiException {
      rethrow;
    } catch (e) {
      throw const ReviewApiException('Không thể kết nối đến máy chủ.');
    }
  }

  static Future<Review> getReviewById(dynamic reviewId) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/reviews/$reviewId');
    try {
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final Map<String, dynamic> body =
            json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        return Review.fromJson(body);
      } else if (response.statusCode == 404) {
        throw const ReviewApiException('Không tìm thấy đánh giá.', statusCode: 404);
      } else {
        throw ReviewApiException(
          'Lỗi máy chủ khi kiểm tra đánh giá: HTTP ${response.statusCode}',
          statusCode: response.statusCode,
        );
      }
    } on ReviewApiException {
      rethrow;
    } catch (_) {
      throw const ReviewApiException('Không thể kết nối đến máy chủ.');
    }
  }

  static Future<void> reportReview({
    required String reviewId,
    required String reason,
    String? detail,
  }) async {
    final token = AuthState.instance.token;
    if (token == null || token.isEmpty) {
      throw const ReviewApiException('Bạn cần đăng nhập để thực hiện thao tác này.', statusCode: 401);
    }

    // Step 3 & 5: Log/debug review id and compare against GET /api/reviews/{review.id} before submission
    debugPrint('[ReportReview] Step 1: Submitting report for review.id = "$reviewId"');
    debugPrint('[ReportReview] Step 2: Comparing selected review against GET ${ApiConfig.baseUrl}/api/reviews/$reviewId');

    // If this GET succeeds (200 OK), the review ID is confirmed valid.
    // If it returns 404, it throws ReviewApiException('Không tìm thấy đánh giá.', statusCode: 404)
    await getReviewById(reviewId);
    debugPrint('[ReportReview] Review ID "$reviewId" verified successfully via GET /api/reviews/$reviewId (HTTP 200 OK).');

    // Step 6: The report service must submit that exact same review.id
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/reviews/$reviewId/report');
    final bodyMap = <String, dynamic>{
      'reason': reason,
    };
    if (detail != null && detail.trim().isNotEmpty) {
      bodyMap['description'] = detail.trim();
      bodyMap['detail'] = detail.trim();
    }
    final encodedBody = jsonEncode(bodyMap);

    debugPrint('[ReportReview] Step 3: Submitting report POST to $uri');
    debugPrint('[ReportReview] Request body: $encodedBody');

    try {
      final response = await _client
          .post(
            uri,
            headers: AuthApiService.authHeaders(token),
            body: encodedBody,
          )
          .timeout(const Duration(seconds: 15));

      debugPrint('[ReportReview] Report submission response status: ${response.statusCode}');
      debugPrint('[ReportReview] Report submission response body: ${response.body}');

      if (response.statusCode == 200 || response.statusCode == 201) {
        debugPrint('[ReportReview] Report submitted successfully.');
        return;
      }

      if (response.statusCode == 401) {
        throw const ReviewApiException('Bạn cần đăng nhập để thực hiện thao tác này.', statusCode: 401);
      }
      if (response.statusCode == 403) {
        throw const ReviewApiException('Bạn không có quyền thực hiện thao tác này.', statusCode: 403);
      }
      if (response.statusCode == 404) {
        // NOTE: The review ID was ALREADY verified via GET /api/reviews/{id} and confirmed to exist!
        // A 404 here means the backend report endpoint route was not found (HTTP 404 Not Found),
        // NOT that the review does not exist.
        String backendDetail = '';
        try {
          final Map<String, dynamic> body =
              json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
          backendDetail = (body['detail'] ?? body['message'])?.toString() ?? '';
        } catch (_) {}

        debugPrint('[ReportReview] Report endpoint returned 404 Not Found. Backend detail: "$backendDetail"');
        throw ReviewApiException(
          backendDetail.isNotEmpty
              ? 'Máy chủ phản hồi 404: $backendDetail (Đường dẫn báo cáo chưa được cấu hình trên máy chủ).'
              : 'Máy chủ phản hồi 404: Đường dẫn báo cáo không tồn tại.',
          statusCode: 404,
        );
      }
      if (response.statusCode == 409) {
        throw const ReviewApiException('Bạn đã báo cáo đánh giá này trước đó.', statusCode: 409);
      }

      // Check if duplicate report message was returned in body (e.g. 400 with duplicate message)
      try {
        final Map<String, dynamic> body =
            json.decode(utf8.decode(response.bodyBytes)) as Map<String, dynamic>;
        final msg = (body['detail'] ?? body['message'])?.toString() ?? '';
        final lower = msg.toLowerCase();
        if (lower.contains('duplicate') ||
            lower.contains('đã báo cáo') ||
            lower.contains('already reported')) {
          throw const ReviewApiException('Bạn đã báo cáo đánh giá này trước đó.', statusCode: 409);
        }
      } catch (e) {
        if (e is ReviewApiException) rethrow;
      }

      throw ReviewApiException(
        'Không thể gửi báo cáo. Vui lòng thử lại.',
        statusCode: response.statusCode,
      );
    } on ReviewApiException {
      rethrow;
    } catch (_) {
      throw const ReviewApiException('Không thể kết nối đến máy chủ.');
    }
  }
}

