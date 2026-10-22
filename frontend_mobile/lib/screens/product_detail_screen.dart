import 'package:flutter/material.dart';
import '../models/product.dart';
import '../models/review.dart';
import '../services/product_api_service.dart';
import '../services/review_api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/review_card.dart';
import 'product_reviews_screen.dart';
import 'review_detail_screen.dart';

class ProductDetailScreen extends StatefulWidget {
  final Product product;

  const ProductDetailScreen({super.key, required this.product});

  @override
  State<ProductDetailScreen> createState() => _ProductDetailScreenState();
}

class _ProductDetailScreenState extends State<ProductDetailScreen> {
  late Product _product;
  bool _isLoadingReviews = true;
  String? _productError;
  String? _reviewError;
  List<Review> _reviews = const [];

  @override
  void initState() {
    super.initState();
    _product = widget.product;
    _reviews = const [];
    _isLoadingReviews = true;
    _loadData();
  }

  Future<void> _loadData({bool isRefresh = false}) async {
    if (!mounted) return;
    setState(() {
      _isLoadingReviews = true;
      _reviewError = null;
      _productError = null;
    });

    // 1. Refresh Product Details from GET /api/products/{id}
    try {
      final freshProduct = await ProductApiService.getProductById(_product.id);
      if (mounted) {
        setState(() {
          _product = _product.copyWith(
            name: freshProduct.name,
            brand: freshProduct.brand,
            category: freshProduct.category,
            price: freshProduct.price,
            description: freshProduct.description,
            imageUrl: freshProduct.imageUrl,
            productCode: freshProduct.productCode,
            sku: freshProduct.sku,
            manufacturer: freshProduct.manufacturer,
            origin: freshProduct.origin,
            batchNumber: freshProduct.batchNumber,
            productionDate: freshProduct.productionDate,
            expiryDate: freshProduct.expiryDate,
            officialSourceUrl: freshProduct.officialSourceUrl,
            verificationNote: freshProduct.verificationNote,
            isVerified: freshProduct.isVerified,
            verificationStatus: freshProduct.verificationStatus,
            shopId: freshProduct.shopId,
            createdAt: freshProduct.createdAt,
          );
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _productError = 'Không thể tải thông tin sản phẩm.';
        });
      }
    }

    // 2. Refresh Reviews from GET /api/reviews/product/{id}
    try {
      debugPrint('[ProductDetailScreen] Loading reviews from API: GET /api/reviews/product/${_product.id}');
      final reviews = await ReviewApiService.getReviewsByProduct(_product.id);
      debugPrint('[ProductDetailScreen] Received ${reviews.length} reviews for product ${_product.id}: '
          '${reviews.map((r) => "{id: ${r.id}, userId: ${r.userId}, content: ${r.content}}").toList()}');
      if (mounted) {
        final totalReviews = reviews.length;
        final suspiciousReviews =
            reviews.where((r) => r.prediction?.predictedLabel == 'fake').length;
        final double? avgRating = reviews.isEmpty
            ? null
            : reviews.map((r) => r.rating).reduce((a, b) => a + b) /
                reviews.length;

        setState(() {
          _reviews = reviews;
          _isLoadingReviews = false;
          _product = _product.copyWith(
            reviews: reviews,
            totalReviews: totalReviews,
            fakeReviewsCount: suspiciousReviews,
            rating: avgRating ?? 0.0,
          );
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoadingReviews = false;
          _reviewError = 'Không thể tải đánh giá.';
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    // Take up to 3 recent reviews
    final recentReviews = _reviews.take(3).toList();

    // Calculate real stats
    final totalReviews = _reviews.length;
    final realReviews =
        _reviews.where((r) => r.prediction?.predictedLabel == 'real').length;
    final suspiciousReviews =
        _reviews.where((r) => r.prediction?.predictedLabel == 'fake').length;
    final double? averageRating = _reviews.isEmpty
        ? null
        : _reviews.map((r) => r.rating).reduce((a, b) => a + b) /
            _reviews.length;

    return Scaffold(
      backgroundColor: AppTheme.scaffoldBackground,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded,
              color: AppTheme.textPrimary, size: 20),
          tooltip: 'Quay lại',
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Chi tiết sản phẩm',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w700,
            color: AppTheme.textPrimary,
          ),
        ),
        actions: [
          IconButton(
            icon: const Icon(Icons.share_outlined, color: AppTheme.primaryBlue),
            tooltip: 'Chia sẻ sản phẩm',
            onPressed: () {
              ScaffoldMessenger.of(context).showSnackBar(
                SnackBar(
                  content:
                      Text('Đã sao chép liên kết sản phẩm "${_product.name}".'),
                  duration: const Duration(seconds: 2),
                ),
              );
            },
          ),
        ],
      ),
      body: RefreshIndicator(
        onRefresh: () => _loadData(isRefresh: true),
        color: AppTheme.primaryBlue,
        child: SingleChildScrollView(
          physics: const AlwaysScrollableScrollPhysics(
            parent: BouncingScrollPhysics(),
          ),
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Product Error Banner if any
              if (_productError != null) ...[
                Container(
                  margin: const EdgeInsets.only(bottom: 14),
                  padding:
                      const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
                  decoration: BoxDecoration(
                    color: const Color(0xFFFEF2F2),
                    borderRadius: BorderRadius.circular(12),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded,
                          color: AppTheme.riskHigh, size: 20),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _productError!,
                          style: const TextStyle(
                            fontSize: 12.5,
                            color: AppTheme.riskHigh,
                            fontWeight: FontWeight.w600,
                          ),
                        ),
                      ),
                      TextButton(
                        onPressed: () => _loadData(),
                        style: TextButton.styleFrom(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 10, vertical: 4),
                          minimumSize: Size.zero,
                          tapTargetSize: MaterialTapTargetSize.shrinkWrap,
                        ),
                        child: const Text('Thử lại',
                            style: TextStyle(
                                fontSize: 12, fontWeight: FontWeight.w700)),
                      ),
                    ],
                  ),
                ),
              ],

              // Warning Banner if suspicious reviews detected
              if (!_isLoadingReviews && suspiciousReviews > 0) ...[
                Container(
                  margin: const EdgeInsets.only(bottom: 14),
                  padding: const EdgeInsets.all(14),
                  decoration: BoxDecoration(
                    color: AppTheme.riskHighBg,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: const Color(0xFFFECACA)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.warning_amber_rounded,
                          color: AppTheme.riskHigh, size: 22),
                      const SizedBox(width: 10),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            const Text(
                              'Phát hiện đánh giá đáng ngờ',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.riskHigh,
                              ),
                            ),
                            const SizedBox(height: 2),
                            Text(
                              'Sản phẩm này có $suspiciousReviews đánh giá cần lưu ý.',
                              style: const TextStyle(
                                fontSize: 11.5,
                                color: Color(0xFF991B1B),
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              // 1. Product Image & Core Information Card
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.surfaceBorder),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.02),
                      offset: const Offset(0, 2),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    // Product Image Placeholder Box
                    Container(
                      height: 170,
                      width: double.infinity,
                      decoration: BoxDecoration(
                        color: AppTheme.primaryBlueSubtle,
                        borderRadius: BorderRadius.circular(14),
                        border: Border.all(color: const Color(0xFFDBEAFE)),
                      ),
                      child: Stack(
                        alignment: Alignment.center,
                        children: [
                          Icon(
                            _product.icon,
                            size: 76,
                            color: AppTheme.primaryBlue,
                          ),
                          Positioned(
                            top: 10,
                            right: 10,
                            child: Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 4),
                              decoration: BoxDecoration(
                                color: _product.verificationStatusBgColor,
                                borderRadius: BorderRadius.circular(8),
                              ),
                              child: Row(
                                mainAxisSize: MainAxisSize.min,
                                children: [
                                  Icon(
                                    _product.verificationStatus == 'verified'
                                        ? Icons.verified_rounded
                                        : _product.verificationStatus ==
                                                'revoked'
                                            ? Icons.cancel_rounded
                                            : Icons.pending_rounded,
                                    size: 13,
                                    color: _product.verificationStatusColor,
                                  ),
                                  const SizedBox(width: 4),
                                  Text(
                                    _product.verificationStatusLabel,
                                    style: TextStyle(
                                      fontSize: 11,
                                      fontWeight: FontWeight.w700,
                                      color: _product.verificationStatusColor,
                                    ),
                                  ),
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 14),

                    // Brand & Category
                    Text(
                      '${_product.brand} • ${_product.category}',
                      style: const TextStyle(
                        fontSize: 12.5,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.primaryBlue,
                      ),
                    ),
                    const SizedBox(height: 4),

                    // Product Name
                    Text(
                      _product.name,
                      style: const TextStyle(
                        fontSize: 18,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textPrimary,
                        height: 1.3,
                      ),
                    ),
                    const SizedBox(height: 10),

                    // Wrap price and rating on narrow screens.
                    Wrap(
                      spacing: 12,
                      runSpacing: 6,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Text(
                          _product.formattedPrice,
                          style: const TextStyle(
                            fontSize: 22,
                            fontWeight: FontWeight.w900,
                            color: AppTheme.primaryBlue,
                          ),
                        ),
                        const SizedBox(width: 12),
                        if (averageRating != null) ...[
                          Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              const Icon(Icons.star_rounded,
                                  size: 17, color: Color(0xFFF59E0B)),
                              const SizedBox(width: 3),
                              Text(
                                averageRating.toStringAsFixed(1),
                                style: const TextStyle(
                                  fontSize: 13.5,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                              Text(
                                ' ($totalReviews)',
                                style: const TextStyle(
                                  fontSize: 12,
                                  color: AppTheme.textSecondary,
                                ),
                              ),
                            ],
                          ),
                        ] else if (!_isLoadingReviews) ...[
                          const Text(
                            'Chưa có đánh giá',
                            style: TextStyle(
                              fontSize: 12,
                              color: AppTheme.textMuted,
                              fontStyle: FontStyle.italic,
                            ),
                          ),
                        ],
                      ],
                    ),
                    const SizedBox(height: 10),

                    // Real Product Information Chips
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: [
                        if (_product.productCode != null &&
                            _product.productCode!.isNotEmpty)
                          _InfoChip(
                            icon: Icons.qr_code_2_rounded,
                            label: _product.productCode!,
                          ),
                        if (_product.brand.isNotEmpty)
                          _InfoChip(
                            icon: Icons.storefront_outlined,
                            label: _product.brand,
                          ),
                        if (_product.origin != null &&
                            _product.origin!.isNotEmpty)
                          _InfoChip(
                            icon: Icons.place_outlined,
                            label: _product.origin!,
                          ),
                        if (_product.sku != null && _product.sku!.isNotEmpty)
                          _InfoChip(
                            icon: Icons.tag_rounded,
                            label: 'SKU: ${_product.sku!}',
                          ),
                        if (_product.manufacturer != null &&
                            _product.manufacturer!.isNotEmpty)
                          _InfoChip(
                            icon: Icons.business_outlined,
                            label: _product.manufacturer!,
                          ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // Product Description Card
              Container(
                width: double.infinity,
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.surfaceBorder),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Text(
                      'Mô tả sản phẩm',
                      style: TextStyle(
                        fontSize: 14,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Text(
                      _product.description.isNotEmpty
                          ? _product.description
                          : 'Chưa có thông tin mô tả chi tiết cho sản phẩm này.',
                      style: TextStyle(
                        fontSize: 13,
                        color: _product.description.isNotEmpty
                            ? AppTheme.textSecondary
                            : AppTheme.textMuted,
                        height: 1.5,
                        fontStyle: _product.description.isNotEmpty
                            ? FontStyle.normal
                            : FontStyle.italic,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 14),

              // 3. Review Analysis Summary Card ("Phân tích đánh giá")
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.surfaceBorder),
                  boxShadow: [
                    BoxShadow(
                      color: Colors.black.withValues(alpha: 0.02),
                      offset: const Offset(0, 2),
                      blurRadius: 8,
                    ),
                  ],
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.analytics_outlined,
                            color: AppTheme.primaryBlue, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Phân tích đánh giá',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 14),

                    // 3 Real Calculated Statistics Cards:
                    // Tổng đánh giá | Đánh giá gốc | Đáng ngờ
                    Row(
                      children: [
                        // Statistic 1: Tổng đánh giá
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                vertical: 12, horizontal: 8),
                            decoration: BoxDecoration(
                              color: const Color(0xFFF8FAFC),
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFFE2E8F0)),
                            ),
                            child: Column(
                              children: [
                                Text(
                                  '$totalReviews',
                                  style: const TextStyle(
                                    fontSize: 17,
                                    fontWeight: FontWeight.w800,
                                    color: AppTheme.textPrimary,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Tổng đánh giá',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.textSecondary,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),

                        // Statistic 2: Đánh giá gốc
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                vertical: 12, horizontal: 8),
                            decoration: BoxDecoration(
                              color: AppTheme.riskLowBg,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFFBBF7D0)),
                            ),
                            child: Column(
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    const Icon(
                                        Icons.check_circle_outline_rounded,
                                        size: 15,
                                        color: AppTheme.riskLow),
                                    const SizedBox(width: 4),
                                    Text(
                                      '$realReviews',
                                      style: const TextStyle(
                                        fontSize: 17,
                                        fontWeight: FontWeight.w800,
                                        color: AppTheme.riskLow,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Đánh giá gốc',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.riskLow,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),

                        // Statistic 3: Đánh giá đáng ngờ
                        Expanded(
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                                vertical: 12, horizontal: 8),
                            decoration: BoxDecoration(
                              color: AppTheme.riskHighBg,
                              borderRadius: BorderRadius.circular(12),
                              border: Border.all(color: const Color(0xFFFECACA)),
                            ),
                            child: Column(
                              children: [
                                Row(
                                  mainAxisAlignment: MainAxisAlignment.center,
                                  children: [
                                    const Icon(Icons.warning_amber_rounded,
                                        size: 15, color: AppTheme.riskHigh),
                                    const SizedBox(width: 4),
                                    Text(
                                      '$suspiciousReviews',
                                      style: const TextStyle(
                                        fontSize: 17,
                                        fontWeight: FontWeight.w800,
                                        color: AppTheme.riskHigh,
                                      ),
                                    ),
                                  ],
                                ),
                                const SizedBox(height: 4),
                                const Text(
                                  'Đánh giá đáng ngờ',
                                  textAlign: TextAlign.center,
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w600,
                                    color: AppTheme.riskHigh,
                                  ),
                                ),
                              ],
                            ),
                          ),
                        ),
                      ],
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // 4. Section: "Đánh giá gần đây"
              const Row(
                children: [
                  Icon(Icons.comment_outlined,
                      color: AppTheme.primaryBlue, size: 18),
                  SizedBox(width: 8),
                  Text(
                    'Đánh giá gần đây',
                    style: TextStyle(
                      fontSize: 15,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 10),

              // Loading State / Error State / Review List
              if (_isLoadingReviews && _reviews.isEmpty)
                Container(
                  padding: const EdgeInsets.all(28),
                  alignment: Alignment.center,
                  child: const Column(
                    children: [
                      SizedBox(
                        width: 26,
                        height: 26,
                        child: CircularProgressIndicator(
                          strokeWidth: 2.2,
                          color: AppTheme.primaryBlue,
                        ),
                      ),
                      SizedBox(height: 10),
                      Text(
                        'Đang tải đánh giá...',
                        style: TextStyle(
                          fontSize: 13,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ],
                  ),
                )
              else if (_reviewError != null && _reviews.isEmpty)
                Container(
                  padding: const EdgeInsets.all(18),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    borderRadius: BorderRadius.circular(14),
                    border: Border.all(color: AppTheme.surfaceBorder),
                  ),
                  child: Column(
                    children: [
                      const Icon(Icons.error_outline_rounded,
                          color: AppTheme.riskHigh, size: 30),
                      const SizedBox(height: 8),
                      Text(
                        _reviewError!,
                        style: const TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 10),
                      OutlinedButton.icon(
                        onPressed: () => _loadData(),
                        icon: const Icon(Icons.refresh_rounded, size: 16),
                        label: const Text('Thử lại'),
                      ),
                    ],
                  ),
                )
              else if (_reviews.isEmpty)
                const Center(
                  child: Padding(
                    padding: EdgeInsets.all(24),
                    child: Text(
                      'Chưa có đánh giá cho sản phẩm này.',
                      style: TextStyle(color: AppTheme.textSecondary),
                    ),
                  ),
                )
              else ...[
                ListView.builder(
                  shrinkWrap: true,
                  physics: const NeverScrollableScrollPhysics(),
                  itemCount: recentReviews.length,
                  itemBuilder: (context, index) {
                    final review = recentReviews[index];
                    return ReviewCard(
                      review: review,
                      onTap: () {
                        debugPrint('[ProductDetailScreen] Tapped review card: review.id = ${review.id}, userId = ${review.userId}, content = ${review.content}');
                        Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (context) => ReviewDetailScreen(
                              review: review,
                              product: _product,
                            ),
                          ),
                        );
                      },
                    );
                  },
                ),
                const SizedBox(height: 6),
                SizedBox(
                  width: double.infinity,
                  child: ElevatedButton.icon(
                    onPressed: () {
                      Navigator.push(
                        context,
                        MaterialPageRoute(
                          builder: (context) =>
                              ProductReviewsScreen(product: _product),
                        ),
                      );
                    },
                    icon: const Icon(Icons.rate_review_outlined, size: 18),
                    label: const Text(
                      'Xem tất cả đánh giá',
                      style: TextStyle(
                          fontSize: 14, fontWeight: FontWeight.w700),
                    ),
                    style: ElevatedButton.styleFrom(
                      padding: const EdgeInsets.symmetric(vertical: 14),
                      backgroundColor: AppTheme.primaryBlue,
                      foregroundColor: Colors.white,
                      elevation: 0,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(12),
                      ),
                    ),
                  ),
                ),
              ],
              const SizedBox(height: 16),
            ],
          ),
        ),
      ),
    );
  }
}

class _InfoChip extends StatelessWidget {
  final IconData icon;
  final String label;

  const _InfoChip({required this.icon, required this.label});

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
      decoration: BoxDecoration(
        color: AppTheme.primaryBlueSubtle,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: const Color(0xFFDBEAFE)),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 12, color: AppTheme.primaryBlueLight),
          const SizedBox(width: 4),
          Text(
            label,
            style: const TextStyle(
              fontSize: 11,
              fontWeight: FontWeight.w600,
              color: AppTheme.primaryBlue,
            ),
          ),
        ],
      ),
    );
  }
}
