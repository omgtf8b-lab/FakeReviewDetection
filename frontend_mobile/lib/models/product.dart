import 'package:flutter/material.dart';
import 'review.dart';

enum RiskLevel {
  high,
  moderate,
  low;

  String get label {
    switch (this) {
      case RiskLevel.high:
        return 'Đáng ngờ';
      case RiskLevel.moderate:
        return 'Cần lưu ý';
      case RiskLevel.low:
        return 'An toàn';
    }
  }

  Color get color {
    switch (this) {
      case RiskLevel.high:
        return const Color(0xFFDC2626);
      case RiskLevel.moderate:
        return const Color(0xFFD97706);
      case RiskLevel.low:
        return const Color(0xFF16A34A);
    }
  }

  Color get backgroundColor {
    switch (this) {
      case RiskLevel.high:
        return const Color(0xFFFEF2F2);
      case RiskLevel.moderate:
        return const Color(0xFFFFFBEB);
      case RiskLevel.low:
        return const Color(0xFFF0FDF4);
    }
  }
}

class Product {
  // Core identity
  final String id;
  final String name;
  final String category;
  final String brand;
  final double price;
  final String description;
  final String? imageUrl;

  // Real API fields (nullable)
  final String? productCode;
  final String? sku;
  final String? manufacturer;
  final String? origin;
  final String? batchNumber;
  final String? productionDate;
  final String? expiryDate;
  final String? officialSourceUrl;
  final String? verificationNote;
  final bool isVerified;
  final String verificationStatus;
  final int? shopId;
  final String? createdAt;

  // Mock-only / review-derived fields (optional)
  final double rating;
  final int totalReviews;
  final int fakeReviewsCount;
  final int trustScore;
  final RiskLevel riskLevel;
  final IconData icon;
  final double verifiedBuyerPercentage;
  final List<String> auditTags;
  final List<Review> reviews;

  const Product({
    required this.id,
    required this.name,
    required this.category,
    required this.brand,
    required this.price,
    required this.description,
    this.imageUrl,
    this.productCode,
    this.sku,
    this.manufacturer,
    this.origin,
    this.batchNumber,
    this.productionDate,
    this.expiryDate,
    this.officialSourceUrl,
    this.verificationNote,
    this.isVerified = false,
    this.verificationStatus = 'pending',
    this.shopId,
    this.createdAt,
    this.rating = 0.0,
    this.totalReviews = 0,
    this.fakeReviewsCount = 0,
    this.trustScore = 0,
    this.riskLevel = RiskLevel.low,
    this.icon = Icons.inventory_2_outlined,
    this.verifiedBuyerPercentage = 0.0,
    this.auditTags = const [],
    this.reviews = const [],
  });

  factory Product.fromJson(Map<String, dynamic> json) {
    final rawCategory = (json['category'] as String?) ?? '';
    final rawBrand = (json['brand'] as String?) ?? '';

    return Product(
      id: '${json['id']}',
      productCode: json['product_code'] as String?,
      name: (json['name'] as String?) ?? '',
      brand: rawBrand,
      sku: json['sku'] as String?,
      category: rawCategory,
      price: (json['price'] as num?)?.toDouble() ?? 0.0,
      description: (json['description'] as String?) ?? '',
      imageUrl: json['image_url'] as String?,
      manufacturer: json['manufacturer'] as String?,
      origin: json['origin'] as String?,
      batchNumber: json['batch_number'] as String?,
      productionDate: json['production_date'] as String?,
      expiryDate: json['expiry_date'] as String?,
      officialSourceUrl: json['official_source_url'] as String?,
      verificationNote: json['verification_note'] as String?,
      isVerified: (json['is_verified'] as bool?) ?? false,
      verificationStatus: (json['verification_status'] as String?) ?? 'pending',
      shopId: json['shop_id'] as int?,
      createdAt: json['created_at'] as String?,
      icon: _iconForCategory(rawCategory),
    );
  }

  Product copyWith({
    String? id,
    String? name,
    String? category,
    String? brand,
    double? price,
    String? description,
    String? imageUrl,
    String? productCode,
    String? sku,
    String? manufacturer,
    String? origin,
    String? batchNumber,
    String? productionDate,
    String? expiryDate,
    String? officialSourceUrl,
    String? verificationNote,
    bool? isVerified,
    String? verificationStatus,
    int? shopId,
    String? createdAt,
    double? rating,
    int? totalReviews,
    int? fakeReviewsCount,
    int? trustScore,
    RiskLevel? riskLevel,
    IconData? icon,
    double? verifiedBuyerPercentage,
    List<String>? auditTags,
    List<Review>? reviews,
  }) {
    return Product(
      id: id ?? this.id,
      name: name ?? this.name,
      category: category ?? this.category,
      brand: brand ?? this.brand,
      price: price ?? this.price,
      description: description ?? this.description,
      imageUrl: imageUrl ?? this.imageUrl,
      productCode: productCode ?? this.productCode,
      sku: sku ?? this.sku,
      manufacturer: manufacturer ?? this.manufacturer,
      origin: origin ?? this.origin,
      batchNumber: batchNumber ?? this.batchNumber,
      productionDate: productionDate ?? this.productionDate,
      expiryDate: expiryDate ?? this.expiryDate,
      officialSourceUrl: officialSourceUrl ?? this.officialSourceUrl,
      verificationNote: verificationNote ?? this.verificationNote,
      isVerified: isVerified ?? this.isVerified,
      verificationStatus: verificationStatus ?? this.verificationStatus,
      shopId: shopId ?? this.shopId,
      createdAt: createdAt ?? this.createdAt,
      rating: rating ?? this.rating,
      totalReviews: totalReviews ?? this.totalReviews,
      fakeReviewsCount: fakeReviewsCount ?? this.fakeReviewsCount,
      trustScore: trustScore ?? this.trustScore,
      riskLevel: riskLevel ?? this.riskLevel,
      icon: icon ?? this.icon,
      verifiedBuyerPercentage: verifiedBuyerPercentage ?? this.verifiedBuyerPercentage,
      auditTags: auditTags ?? this.auditTags,
      reviews: reviews ?? this.reviews,
    );
  }

  int get fakePercentage => totalReviews == 0 ? 0 : ((fakeReviewsCount / totalReviews) * 100).round();
  int get genuineReviewsCount => totalReviews - fakeReviewsCount;
  int get genuinePercentage => 100 - fakePercentage;

  String get verificationStatusLabel {
    switch (verificationStatus) {
      case 'verified':
        return 'Đã xác minh';
      case 'revoked':
        return 'Đã thu hồi';
      default:
        return 'Chờ xác minh';
    }
  }

  Color get verificationStatusColor {
    switch (verificationStatus) {
      case 'verified':
        return const Color(0xFF16A34A);
      case 'revoked':
        return const Color(0xFFDC2626);
      default:
        return const Color(0xFFD97706);
    }
  }

  Color get verificationStatusBgColor {
    switch (verificationStatus) {
      case 'verified':
        return const Color(0xFFF0FDF4);
      case 'revoked':
        return const Color(0xFFFEF2F2);
      default:
        return const Color(0xFFFFFBEB);
    }
  }

  String get formattedPrice {
    final int amount = price.round();
    final digits = amount.toString();
    final buffer = StringBuffer();
    for (int i = 0; i < digits.length; i++) {
      if (i > 0 && (digits.length - i) % 3 == 0) {
        buffer.write('.');
      }
      buffer.write(digits[i]);
    }
    return '${buffer.toString()} ₫';
  }

  static IconData _iconForCategory(String category) {
    final lower = category.toLowerCase();
    if (lower.contains('am thanh') || lower.contains('tai nghe') || lower.contains('loa') || lower.contains('\u00e2m thanh')) {
      return Icons.headphones;
    }
    if (lower.contains('dien thoai') || lower.contains('mobile') || lower.contains('\u0111i\u1ec7n tho\u1ea1i')) {
      return Icons.smartphone;
    }
    if (lower.contains('may tinh') || lower.contains('gaming') || lower.contains('laptop') || lower.contains('m\u00e1y t\u00ednh')) {
      return Icons.computer;
    }
    if (lower.contains('dong ho') || lower.contains('suc khoe') || lower.contains('deo') || lower.contains('\u0111\u1ed3ng h\u1ed3')) {
      return Icons.watch;
    }
    if (lower.contains('nha') || lower.contains('bep') || lower.contains('doi song') || lower.contains('nh\u00e0')) {
      return Icons.home_outlined;
    }
    if (lower.contains('noi that') || lower.contains('van phong') || lower.contains('n\u1ed9i th\u1ea5t')) {
      return Icons.chair_outlined;
    }
    return Icons.inventory_2_outlined;
  }
}
