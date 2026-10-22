import 'package:flutter/material.dart';
import '../models/product.dart';
import '../models/review.dart';
import '../services/review_api_service.dart';
import '../theme/app_theme.dart';
import '../widgets/review_card.dart';
import 'review_detail_screen.dart';

class ProductReviewsScreen extends StatefulWidget {
  final Product product;

  const ProductReviewsScreen({super.key, required this.product});

  @override
  State<ProductReviewsScreen> createState() => _ProductReviewsScreenState();
}

class _ProductReviewsScreenState extends State<ProductReviewsScreen> {
  // Required filters: 'Tất cả', '5 sao', '4 sao', '3 sao', 'Đáng ngờ'
  String _selectedFilter = 'Tất cả';
  final List<String> _filters = ['Tất cả', '5 sao', '4 sao', '3 sao', 'Đáng ngờ'];
  List<Review> _reviews = [];
  bool _isLoading = false;

  @override
  void initState() {
    super.initState();
    _reviews = widget.product.reviews;
    if (_reviews.isEmpty) {
      _isLoading = true;
      _loadReviews();
    }
  }

  Future<void> _loadReviews() async {
    try {
      debugPrint('[ProductReviewsScreen] Loading reviews for product ${widget.product.id} from API');
      final items = await ReviewApiService.getReviewsByProduct(widget.product.id);
      debugPrint('[ProductReviewsScreen] Fetched ${items.length} reviews for product ${widget.product.id}');
      if (mounted) {
        setState(() {
          _reviews = items;
          _isLoading = false;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _isLoading = false;
        });
      }
    }
  }

  @override
  Widget build(BuildContext context) {
    final allReviews = _reviews;

    // Filter reviews according to the selected filter
    final List<Review> filteredReviews = allReviews.where((r) {
      switch (_selectedFilter) {
        case '5 sao':
          return r.rating >= 5.0;
        case '4 sao':
          return r.rating >= 4.0 && r.rating < 5.0;
        case '3 sao':
          return r.rating >= 3.0 && r.rating < 4.0;
        case 'Đáng ngờ':
          return r.isFake;
        case 'Tất cả':
        default:
          return true;
      }
    }).toList();

    return Scaffold(
      backgroundColor: AppTheme.scaffoldBackground,
      appBar: AppBar(
        backgroundColor: Colors.white,
        elevation: 0,
        leading: IconButton(
          icon: const Icon(Icons.arrow_back_ios_new_rounded, color: AppTheme.textPrimary, size: 20),
          tooltip: 'Quay lại',
          onPressed: () => Navigator.pop(context),
        ),
        title: const Text(
          'Đánh giá sản phẩm',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w700,
            color: AppTheme.textPrimary,
          ),
        ),
      ),
      body: Column(
        children: [
          // Selected Product Summary Header
          Container(
            padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
            decoration: const BoxDecoration(
              color: Colors.white,
              border: Border(bottom: BorderSide(color: AppTheme.surfaceBorder)),
            ),
            child: Row(
              children: [
                Container(
                  padding: const EdgeInsets.all(8),
                  decoration: BoxDecoration(
                    color: AppTheme.primaryBlueSubtle,
                    borderRadius: BorderRadius.circular(10),
                  ),
                  child: Icon(widget.product.icon, size: 24, color: AppTheme.primaryBlue),
                ),
                const SizedBox(width: 12),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        widget.product.name,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Wrap(
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          if (widget.product.totalReviews > 0) ...[
                            const Icon(Icons.star_rounded, size: 15, color: Color(0xFFF59E0B)),
                            const SizedBox(width: 2),
                            Text(
                              '${widget.product.rating.toStringAsFixed(1)} • ${widget.product.totalReviews} đánh giá',
                              style: const TextStyle(fontSize: 11.5, color: AppTheme.textSecondary),
                            ),
                          ] else ...[
                            const Text(
                              'Chưa có đánh giá',
                              style: TextStyle(fontSize: 11.5, color: AppTheme.textSecondary, fontStyle: FontStyle.italic),
                            ),
                          ],
                        ],
                      ),
                    ],
                  ),
                ),
                Container(
                  padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 4),
                  decoration: BoxDecoration(
                    color: AppTheme.riskHighBg,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: AppTheme.riskHigh.withValues(alpha: 0.2)),
                  ),
                  child: Text(
                    '${widget.product.fakeReviewsCount} Đáng ngờ',
                    style: const TextStyle(
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.riskHigh,
                    ),
                  ),
                ),
              ],
            ),
          ),

          // Filters Bar: Tất cả, 5 sao, 4 sao, 3 sao, Đáng ngờ
          Container(
            color: Colors.white,
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 10),
            child: SingleChildScrollView(
              scrollDirection: Axis.horizontal,
              child: Row(
                children: _filters.map((filter) {
                  final isSelected = filter == _selectedFilter;
                  final isSuspiciousFilter = filter == 'Đáng ngờ';
                  final Color activeColor = isSuspiciousFilter ? AppTheme.riskHigh : AppTheme.primaryBlue;

                  return Padding(
                    padding: const EdgeInsets.only(right: 8),
                    child: ChoiceChip(
                      selected: isSelected,
                      label: Text(filter),
                      labelStyle: TextStyle(
                        fontSize: 11.5,
                        fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
                        color: isSelected
                            ? Colors.white
                            : (isSuspiciousFilter ? AppTheme.riskHigh : AppTheme.textSecondary),
                      ),
                      backgroundColor: isSuspiciousFilter
                          ? AppTheme.riskHighBg
                          : AppTheme.scaffoldBackground,
                      selectedColor: activeColor,
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(16),
                        side: BorderSide(
                          color: isSelected
                              ? activeColor
                              : (isSuspiciousFilter
                                  ? AppTheme.riskHigh.withValues(alpha: 0.3)
                                  : AppTheme.surfaceBorder),
                        ),
                      ),
                      onSelected: (val) {
                        setState(() {
                          _selectedFilter = filter;
                        });
                      },
                    ),
                  );
                }).toList(),
              ),
            ),
          ),

          const Divider(height: 1),

          // Review Count indicator
          Padding(
            padding: const EdgeInsets.fromLTRB(16, 10, 16, 6),
            child: Row(
              mainAxisAlignment: MainAxisAlignment.spaceBetween,
              children: [
                Text(
                  'Hiển thị ${filteredReviews.length} đánh giá',
                  style: const TextStyle(
                    fontSize: 12.5,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.textSecondary,
                  ),
                ),
              ],
            ),
          ),

          // Reviews List
          Expanded(
            child: _isLoading
                ? const Center(child: CircularProgressIndicator())
                : filteredReviews.isEmpty
                    ? Center(
                        child: Padding(
                          padding: const EdgeInsets.all(32),
                          child: Column(
                            mainAxisAlignment: MainAxisAlignment.center,
                            children: [
                              const Icon(Icons.rate_review_outlined, size: 44, color: AppTheme.textMuted),
                              const SizedBox(height: 12),
                              const Text(
                                'Không có đánh giá phù hợp',
                                style: TextStyle(
                                  fontSize: 15,
                                  fontWeight: FontWeight.w700,
                                  color: AppTheme.textPrimary,
                                ),
                              ),
                              const SizedBox(height: 4),
                              const Text(
                                'Hãy thử chọn bộ lọc khác để xem thêm đánh giá.',
                                style: TextStyle(fontSize: 12.5, color: AppTheme.textSecondary),
                              ),
                            ],
                          ),
                        ),
                      )
                    : ListView.builder(
                        padding: const EdgeInsets.fromLTRB(16, 6, 16, 16),
                        itemCount: filteredReviews.length,
                        itemBuilder: (context, index) {
                          final review = filteredReviews[index];
                          return ReviewCard(
                            review: review,
                            onTap: () {
                              debugPrint('[ProductReviewsScreen] Tapped review card: review.id = ${review.id}, userId = ${review.userId}, content = ${review.content}');
                              Navigator.push(
                                context,
                                MaterialPageRoute(
                                  builder: (context) => ReviewDetailScreen(
                                    review: review,
                                    product: widget.product,
                                  ),
                                ),
                              );
                            },
                          );
                        },
                      ),
          ),
        ],
      ),
    );
  }
}
