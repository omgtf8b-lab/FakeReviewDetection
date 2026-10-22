import 'dart:convert';
import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import '../config/api_config.dart';
import '../models/product.dart';

class ProductApiException implements Exception {
  final String message;
  const ProductApiException(this.message);
  @override
  String toString() => message;
}

class ProductListResult {
  final List<Product> items;
  final int total;
  final int page;
  final int pageSize;

  const ProductListResult({
    required this.items,
    required this.total,
    required this.page,
    required this.pageSize,
  });
}

class ProductApiService {
  static http.Client _client = http.Client();
  @visibleForTesting
  static void setClientForTesting(http.Client client) { _client = client; }

  static Future<ProductListResult> getProducts({
    String? search,
    String? category,
    int page = 1,
    int pageSize = 20,
  }) async {
    final queryParams = <String, String>{
      'page': '$page',
      'page_size': '$pageSize',
    };
    if (search != null && search.trim().isNotEmpty) {
      queryParams['search'] = search.trim();
    }
    if (category != null && category.isNotEmpty && category != 'Tất cả') {
      queryParams['category'] = category;
    }

    final uri = Uri.parse('${ApiConfig.baseUrl}/api/products')
        .replace(queryParameters: queryParams);

    try {
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final Map<String, dynamic> body = json.decode(response.body) as Map<String, dynamic>;
        final rawItems = (body['items'] as List<dynamic>?) ?? [];
        final items = rawItems
            .map((e) => Product.fromJson(e as Map<String, dynamic>))
            .toList();
        return ProductListResult(
          items: items,
          total: (body['total'] as num?)?.toInt() ?? items.length,
          page: (body['page'] as num?)?.toInt() ?? page,
          pageSize: (body['page_size'] as num?)?.toInt() ?? pageSize,
        );
      } else {
        throw ProductApiException(
            'Lỗi máy chủ: HTTP ${response.statusCode}');
      }
    } on ProductApiException {
      rethrow;
    } catch (e) {
      throw const ProductApiException('Không thể kết nối đến máy chủ.');
    }
  }

  static Future<Product> getProductById(dynamic productId) async {
    final uri = Uri.parse('${ApiConfig.baseUrl}/api/products/$productId');
    try {
      final response = await _client
          .get(uri, headers: {'Accept': 'application/json'})
          .timeout(const Duration(seconds: 15));

      if (response.statusCode == 200) {
        final Map<String, dynamic> body =
            json.decode(response.body) as Map<String, dynamic>;
        return Product.fromJson(body);
      } else if (response.statusCode == 404) {
        throw const ProductApiException('Sản phẩm không tồn tại.');
      } else {
        throw ProductApiException(
            'Lỗi máy chủ: HTTP ${response.statusCode}');
      }
    } on ProductApiException {
      rethrow;
    } catch (e) {
      throw const ProductApiException('Không thể kết nối đến máy chủ.');
    }
  }
}
