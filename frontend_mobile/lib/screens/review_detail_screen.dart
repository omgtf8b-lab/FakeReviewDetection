import 'package:flutter/material.dart';
import '../models/product.dart';
import '../models/review.dart';
import '../services/auth_state.dart';
import '../services/review_api_service.dart';
import '../theme/app_theme.dart';
import 'login_screen.dart';
import '../widgets/lime_explanation.dart';
import '../services/workspace_api.dart';

class ReviewDetailScreen extends StatelessWidget {
  final Review review;
  final Product product;

  const ReviewDetailScreen({
    super.key,
    required this.review,
    required this.product,
  });

  @override
  Widget build(BuildContext context) {
    final isFake = review.isFake && review.isAnalyzed;
    final isAnalyzed = review.isAnalyzed;
    final prediction = review.prediction;

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
          'Chi tiết đánh giá',
          style: TextStyle(
            fontSize: 17,
            fontWeight: FontWeight.w700,
            color: AppTheme.textPrimary,
          ),
        ),
      ),
      body: SingleChildScrollView(
        physics: const BouncingScrollPhysics(),
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            LimeExplanation(content: review.content, modelVersion: review.prediction?.modelVersion),
            // Product Reference Context Card
            Container(
              padding: const EdgeInsets.all(12),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.surfaceBorder),
              ),
              child: Row(
                children: [
                  Container(
                    padding: const EdgeInsets.all(8),
                    decoration: BoxDecoration(
                      color: AppTheme.primaryBlueSubtle,
                      borderRadius: BorderRadius.circular(8),
                    ),
                    child: Icon(product.icon,
                        size: 22, color: AppTheme.primaryBlue),
                  ),
                  const SizedBox(width: 10),
                  Expanded(
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          'Sản phẩm được đánh giá',
                          style: TextStyle(
                              fontSize: 10.5,
                              color: AppTheme.textMuted,
                              fontWeight: FontWeight.w600),
                        ),
                        Text(
                          product.name,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                  ),
                  Text(
                    product.formattedPrice,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                      color: AppTheme.primaryBlue,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Section: "Kết quả phân tích"
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: !isAnalyzed
                    ? const Color(0xFFF8FAFC)
                    : (isFake ? AppTheme.riskHighBg : AppTheme.riskLowBg),
                borderRadius: BorderRadius.circular(16),
                border: Border.all(
                  color: !isAnalyzed
                      ? const Color(0xFFCBD5E1)
                      : (isFake
                          ? const Color(0xFFFCA5A5)
                          : const Color(0xFF86EFAC)),
                  width: 1.5,
                ),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    mainAxisAlignment: MainAxisAlignment.spaceBetween,
                    children: [
                      const Text(
                        'Kết quả phân tích',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textSecondary,
                          letterSpacing: 0.3,
                        ),
                      ),
                      if (prediction != null && prediction.isFallback)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: const Color(0xFFFFFBEB),
                            borderRadius: BorderRadius.circular(12),
                            border: Border.all(
                                color: const Color(0xFFFDE68A), width: 1),
                          ),
                          child: const Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Icon(Icons.science_outlined,
                                  size: 13, color: Color(0xFFD97706)),
                              SizedBox(width: 3),
                              Text(
                                'Thử nghiệm',
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFFB45309),
                                ),
                              ),
                            ],
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  Row(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Container(
                        padding: const EdgeInsets.all(10),
                        decoration: BoxDecoration(
                          color: Colors.white,
                          shape: BoxShape.circle,
                          border: Border.all(
                            color: !isAnalyzed
                                ? const Color(0xFFCBD5E1)
                                : (isFake
                                    ? const Color(0xFFFCA5A5)
                                    : const Color(0xFF86EFAC)),
                          ),
                        ),
                        child: Icon(
                          !isAnalyzed
                              ? Icons.help_outline_rounded
                              : (isFake
                                  ? Icons.warning_amber_rounded
                                  : Icons.verified_rounded),
                          size: 26,
                          color: !isAnalyzed
                              ? AppTheme.textSecondary
                              : (isFake ? AppTheme.riskHigh : AppTheme.riskLow),
                        ),
                      ),
                      const SizedBox(width: 14),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Text(
                              review.internalStateName,
                              style: TextStyle(
                                fontSize: 16,
                                fontWeight: FontWeight.w900,
                                color: !isAnalyzed
                                    ? AppTheme.textPrimary
                                    : (isFake
                                        ? AppTheme.riskHigh
                                        : AppTheme.riskLow),
                              ),
                            ),
                            const SizedBox(height: 2),
                            Container(
                              padding: const EdgeInsets.symmetric(
                                  horizontal: 8, vertical: 2),
                              decoration: BoxDecoration(
                                color: !isAnalyzed
                                    ? const Color(0xFFF1F5F9)
                                    : (isFake
                                        ? AppTheme.riskHighBg
                                        : AppTheme.riskLowBg),
                                borderRadius: BorderRadius.circular(6),
                                border: Border.all(
                                  color: !isAnalyzed
                                      ? const Color(0xFFCBD5E1)
                                      : (isFake
                                          ? const Color(0xFFFECACA)
                                          : const Color(0xFFBBF7D0)),
                                ),
                              ),
                              child: Text(
                                review.statusLabel,
                                style: TextStyle(
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w700,
                                  color: !isAnalyzed
                                      ? AppTheme.textSecondary
                                      : (isFake
                                          ? AppTheme.riskHigh
                                          : AppTheme.riskLow),
                                ),
                              ),
                            ),
                            const SizedBox(height: 6),
                            Text(
                              review.moderationLabel == null && prediction?.explanation != null &&
                                      prediction!.explanation!.isNotEmpty
                                  ? prediction.explanation!
                                  : review.stateExplanation,
                              style: TextStyle(
                                fontSize: 12.5,
                                color: !isAnalyzed
                                    ? AppTheme.textSecondary
                                    : (isFake
                                        ? const Color(0xFF991B1B)
                                        : const Color(0xFF166534)),
                                fontWeight: FontWeight.w500,
                                height: 1.35,
                              ),
                            ),
                          ],
                        ),
                      ),
                    ],
                  ),

                  // Probability Scores Grid (Requirement 18, 19, 20)
                  if (prediction != null) ...[
                    const SizedBox(height: 14),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(12),
                        border: Border.all(
                          color: isFake
                              ? const Color(0xFFFECACA)
                              : const Color(0xFFBBF7D0),
                        ),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              // Điểm phân tích (confidence_score)
                              Expanded(
                                child: _ScoreItem(
                                  label: 'Độ tin cậy nhãn',
                                  value:
                                      '${(prediction.confidenceScore * 100).round()}%',
                                  subtitle: prediction.confidenceScore
                                      .toStringAsFixed(2),
                                  color: isFake
                                      ? AppTheme.riskHigh
                                      : AppTheme.riskLow,
                                ),
                              ),
                              Container(
                                width: 1,
                                height: 36,
                                color: const Color(0xFFE2E8F0),
                              ),
                              // Điểm gốc (real_probability)
                              Expanded(
                                child: _ScoreItem(
                                  label: 'Điểm gốc',
                                  value:
                                      '${(prediction.realProbability * 100).round()}%',
                                  subtitle: prediction.realProbability
                                      .toStringAsFixed(2),
                                  color: AppTheme.riskLow,
                                ),
                              ),
                              Container(
                                width: 1,
                                height: 36,
                                color: const Color(0xFFE2E8F0),
                              ),
                              // Điểm đáng ngờ (fake_probability)
                              Expanded(
                                child: _ScoreItem(
                                  label: 'Điểm đáng ngờ',
                                  value:
                                      '${(prediction.fakeProbability * 100).round()}%',
                                  subtitle: prediction.fakeProbability
                                      .toStringAsFixed(2),
                                  color: AppTheme.riskHigh,
                                ),
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ] else if (isAnalyzed) ...[
                    const SizedBox(height: 10),
                    Container(
                      padding: const EdgeInsets.symmetric(
                          horizontal: 10, vertical: 4),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(
                          color: isFake
                              ? const Color(0xFFFECACA)
                              : const Color(0xFFBBF7D0),
                        ),
                      ),
                      child: Text(
                        'Điểm phân tích: ${review.scoreFormatted}',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w800,
                          color: isFake ? AppTheme.riskHigh : AppTheme.riskLow,
                        ),
                      ),
                    ),
                  ],

                  // Fallback Warning Box (Requirement 10 & 22)
                  if (prediction != null && prediction.isFallback) ...[
                    const SizedBox(height: 12),
                    Container(
                      width: double.infinity,
                      padding: const EdgeInsets.all(10),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFFBEB),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFFDE68A)),
                      ),
                      child: const Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Row(
                            children: [
                              Icon(Icons.info_outline_rounded,
                                  size: 15, color: Color(0xFFD97706)),
                              SizedBox(width: 6),
                              Text(
                                'Lưu ý thử nghiệm',
                                style: TextStyle(
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFF92400E),
                                ),
                              ),
                            ],
                          ),
                          SizedBox(height: 4),
                          Text(
                            'Kết quả thử nghiệm: hệ thống hiện đang sử dụng cơ chế fallback, chưa phải mô hình AI đã huấn luyện.',
                            style: TextStyle(
                              fontSize: 11.5,
                              color: Color(0xFF78350F),
                              height: 1.35,
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],

                  // Model Metadata Info (Requirement 10)
                  if (prediction != null) ...[
                    const SizedBox(height: 10),
                    Wrap(
                      spacing: 8,
                      runSpacing: 4,
                      children: [
                        Text(
                          'Mô hình: ${prediction.modelName}',
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        const Text('•',
                            style: TextStyle(
                                fontSize: 11, color: AppTheme.textMuted)),
                        Text(
                          'Phiên bản: ${prediction.modelVersion}',
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                        if (prediction.isFallback) ...[
                          const Text('•',
                              style: TextStyle(
                                  fontSize: 11, color: AppTheme.textMuted)),
                          const Text(
                            'Trạng thái: Thử nghiệm',
                            style: TextStyle(
                              fontSize: 11,
                              color: Color(0xFFD97706),
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                        ],
                      ],
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Complete Review Content Card
            Container(
              padding: const EdgeInsets.all(16),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(16),
                border: Border.all(color: AppTheme.surfaceBorder),
              ),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  // Author, Verification & Date
                  Row(
                    children: [
                      CircleAvatar(
                        radius: 18,
                        backgroundColor: isFake
                            ? AppTheme.riskHighBg
                            : AppTheme.primaryBlueSubtle,
                        child: Text(
                          review.authorAvatar,
                          style: TextStyle(
                            fontSize: 13,
                            fontWeight: FontWeight.w700,
                            color: isFake
                                ? AppTheme.riskHigh
                                : AppTheme.primaryBlue,
                          ),
                        ),
                      ),
                      const SizedBox(width: 12),
                      Expanded(
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              children: [
                                Text(
                                  review.author,
                                  style: const TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w700,
                                    color: AppTheme.textPrimary,
                                  ),
                                ),
                                const SizedBox(width: 6),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                      horizontal: 6, vertical: 1.5),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFF1F5F9),
                                    borderRadius: BorderRadius.circular(4),
                                    border: Border.all(
                                        color: const Color(0xFFCBD5E1),
                                        width: 0.8),
                                  ),
                                  child: Text(
                                    'ID: #${review.id}',
                                    style: const TextStyle(
                                      fontSize: 10,
                                      fontWeight: FontWeight.w700,
                                      color: AppTheme.textSecondary,
                                    ),
                                  ),
                                ),
                              ],
                            ),
                            if (review.userId != null)
                              Text(
                                'Mã người dùng: #${review.userId}${review.date.isNotEmpty ? " • ${review.date}" : ""}',
                                style: const TextStyle(
                                    fontSize: 11,
                                    color: AppTheme.textSecondary),
                              )
                            else if (review.date.isNotEmpty)
                              Text(
                                review.date,
                                style: const TextStyle(
                                    fontSize: 11,
                                    color: AppTheme.textSecondary),
                              ),
                          ],
                        ),
                      ),
                      if (review.isVerifiedPurchase)
                        Container(
                          padding: const EdgeInsets.symmetric(
                              horizontal: 8, vertical: 4),
                          decoration: BoxDecoration(
                            color: AppTheme.riskLowBg,
                            borderRadius: BorderRadius.circular(8),
                          ),
                          child: const Text(
                            'Đã mua hàng',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: AppTheme.riskLow,
                            ),
                          ),
                        ),
                    ],
                  ),
                  const SizedBox(height: 12),

                  // Rating Stars
                  Row(
                    children: List.generate(
                      5,
                      (index) => Icon(
                        index < review.rating.floor()
                            ? Icons.star_rounded
                            : (index < review.rating
                                ? Icons.star_half_rounded
                                : Icons.star_outline_rounded),
                        size: 18,
                        color: const Color(0xFFF59E0B),
                      ),
                    ),
                  ),
                  if (review.title.isNotEmpty) ...[
                    const SizedBox(height: 8),
                    Text(
                      review.title,
                      style: const TextStyle(
                        fontSize: 15,
                        fontWeight: FontWeight.w800,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ],
                  const SizedBox(height: 8),

                  // Complete Review Content
                  Text(
                    review.content,
                    style: const TextStyle(
                      fontSize: 13.5,
                      color: AppTheme.textPrimary,
                      height: 1.5,
                    ),
                  ),

                  // Flagged Phrases Excerpt (if present)
                  if (review.suspiciousPhrases.isNotEmpty) ...[
                    const SizedBox(height: 14),
                    Container(
                      padding: const EdgeInsets.all(12),
                      decoration: BoxDecoration(
                        color: const Color(0xFFFFFBEB),
                        borderRadius: BorderRadius.circular(10),
                        border: Border.all(color: const Color(0xFFFDE68A)),
                      ),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          const Row(
                            children: [
                              Icon(Icons.find_in_page_outlined,
                                  size: 16, color: Color(0xFFD97706)),
                              SizedBox(width: 6),
                              Text(
                                'Cụm từ đáng ngờ phát hiện:',
                                style: TextStyle(
                                  fontSize: 11.5,
                                  fontWeight: FontWeight.w700,
                                  color: Color(0xFF92400E),
                                ),
                              ),
                            ],
                          ),
                          const SizedBox(height: 6),
                          ...review.suspiciousPhrases.map((phrase) => Padding(
                                padding: const EdgeInsets.only(bottom: 3),
                                child: Text(
                                  '• "$phrase"',
                                  style: const TextStyle(
                                    fontSize: 12,
                                    fontStyle: FontStyle.italic,
                                    color: Color(0xFFB45309),
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              )),
                        ],
                      ),
                    ),
                  ],
                ],
              ),
            ),
            const SizedBox(height: 14),

            // Section: "Giải thích kết quả" (LIME contributions if available)
            if (review.limeContributions.isNotEmpty) ...[
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(16),
                  border: Border.all(color: AppTheme.surfaceBorder),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    const Row(
                      children: [
                        Icon(Icons.insights_rounded,
                            color: AppTheme.primaryBlue, size: 20),
                        SizedBox(width: 8),
                        Text(
                          'Giải thích kết quả',
                          style: TextStyle(
                            fontSize: 15,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.textPrimary,
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 6),
                    const Text(
                      'Phân tích mức độ tác động của các từ ngữ đặc trưng đến quyết định phân loại của mô hình:',
                      style: TextStyle(
                          fontSize: 11.5,
                          color: AppTheme.textSecondary,
                          height: 1.35),
                    ),
                    const SizedBox(height: 12),
                    ...review.limeContributions.map((contrib) {
                      final isSuspicious = contrib.isSuspicious;
                      final barColor =
                          isSuspicious ? AppTheme.riskHigh : AppTheme.riskLow;

                      return Padding(
                        padding: const EdgeInsets.only(bottom: 10),
                        child: Column(
                          crossAxisAlignment: CrossAxisAlignment.start,
                          children: [
                            Row(
                              mainAxisAlignment: MainAxisAlignment.spaceBetween,
                              children: [
                                Expanded(
                                  child: Text(
                                    '"${contrib.phrase}"',
                                    style: const TextStyle(
                                      fontSize: 12,
                                      fontWeight: FontWeight.w600,
                                      color: AppTheme.textPrimary,
                                    ),
                                  ),
                                ),
                                Text(
                                  isSuspicious
                                      ? 'Đáng ngờ (+${contrib.weight.toStringAsFixed(2)})'
                                      : 'Đánh giá gốc (-${contrib.weight.toStringAsFixed(2)})',
                                  style: TextStyle(
                                    fontSize: 11,
                                    fontWeight: FontWeight.w700,
                                    color: barColor,
                                  ),
                                ),
                              ],
                            ),
                            const SizedBox(height: 4),
                            ClipRRect(
                              borderRadius: BorderRadius.circular(4),
                              child: LinearProgressIndicator(
                                value: contrib.weight.clamp(0.0, 1.0),
                                minHeight: 6,
                                backgroundColor: AppTheme.scaffoldBackground,
                                valueColor:
                                    AlwaysStoppedAnimation<Color>(barColor),
                              ),
                            ),
                          ],
                        ),
                      );
                    }),
                  ],
                ),
              ),
              const SizedBox(height: 14),
            ],

            // Mandatory Disclaimer Note
            Container(
              padding: const EdgeInsets.all(14),
              decoration: BoxDecoration(
                color: const Color(0xFFF1F5F9),
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFE2E8F0)),
              ),
              child: const Row(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Icon(
                    Icons.info_outline_rounded,
                    size: 18,
                    color: Color(0xFF64748B),
                  ),
                  SizedBox(width: 10),
                  Expanded(
                    child: Text(
                      'Kết quả phân tích được sử dụng để hỗ trợ nhận diện đánh giá đáng ngờ và không phải là kết luận tuyệt đối về hành vi gian lận.',
                      style: TextStyle(
                        fontSize: 11.5,
                        color: Color(0xFF475569),
                        height: 1.4,
                        fontStyle: FontStyle.italic,
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 14),

            // User Feedback Action Row
            Container(
              padding: const EdgeInsets.symmetric(vertical: 6, horizontal: 8),
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: AppTheme.surfaceBorder),
              ),
              child: Row(
                children: [
                  Expanded(
                    child: TextButton.icon(
                      onPressed: () async {
                        try {
                          await WorkspaceApi.request('/api/workspace/reviews/${review.id}/vote', method: 'PUT', body: {'useful': true});
                          if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Đã lưu bình chọn hữu ích')));
                        } catch (e) {
                          if (context.mounted) ScaffoldMessenger.of(context).showSnackBar(SnackBar(content: Text(e.toString())));
                        }
                      },
                      icon: const Icon(Icons.thumb_up_alt_outlined, size: 16),
                      label:
                          const Text('Hữu ích', style: TextStyle(fontSize: 12)),
                      style: TextButton.styleFrom(
                        foregroundColor: AppTheme.primaryBlue,
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                      ),
                    ),
                  ),
                  Container(
                      width: 1, height: 20, color: AppTheme.surfaceBorder),
                  Expanded(
                    child: TextButton.icon(
                      onPressed: () => _handleReportClick(context),
                      icon: const Icon(Icons.flag_outlined, size: 16),
                      label:
                          const Text('Báo cáo', style: TextStyle(fontSize: 12)),
                      style: TextButton.styleFrom(
                        foregroundColor: AppTheme.textSecondary,
                        padding: const EdgeInsets.symmetric(horizontal: 4),
                      ),
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(height: 16),
          ],
        ),
      ),
    );
  }

  void _handleReportClick(BuildContext context) {
    final auth = AuthState.instance;
    if (!auth.isAuthenticated || auth.currentUser == null) {
      ScaffoldMessenger.of(context).showSnackBar(
        SnackBar(
          content: const Text('Bạn cần đăng nhập để báo cáo đánh giá.'),
          action: SnackBarAction(
            label: 'Đăng nhập',
            textColor: Colors.white,
            onPressed: () {
              Navigator.push(
                context,
                MaterialPageRoute(builder: (_) => const LoginScreen()),
              );
            },
          ),
          duration: const Duration(seconds: 4),
        ),
      );
      return;
    }

    if (!auth.currentUser!.isActive) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Tài khoản đã bị khóa. Vui lòng liên hệ quản trị viên.'),
          backgroundColor: AppTheme.riskHigh,
          duration: Duration(seconds: 3),
        ),
      );
      return;
    }

    _showReportModal(context);
  }

  Future<void> _showReportModal(BuildContext context) async {
    final result = await showModalBottomSheet<bool>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.transparent,
      builder: (ctx) => _ReportBottomSheet(review: review),
    );

    if (result == true && context.mounted) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('Đã gửi báo cáo. Cảm ơn bạn đã phản hồi.'),
          backgroundColor: AppTheme.riskLow,
          duration: Duration(seconds: 3),
        ),
      );
    }
  }
}

class _ScoreItem extends StatelessWidget {
  final String label;
  final String value;
  final String subtitle;
  final Color color;

  const _ScoreItem({
    required this.label,
    required this.value,
    required this.subtitle,
    required this.color,
  });

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        Text(
          label,
          textAlign: TextAlign.center,
          style: const TextStyle(
            fontSize: 11,
            fontWeight: FontWeight.w600,
            color: AppTheme.textSecondary,
          ),
        ),
        const SizedBox(height: 4),
        Text(
          value,
          style: TextStyle(
            fontSize: 16,
            fontWeight: FontWeight.w900,
            color: color,
          ),
        ),
        Text(
          subtitle,
          style: const TextStyle(
            fontSize: 10,
            color: AppTheme.textMuted,
          ),
        ),
      ],
    );
  }
}

class _ReportBottomSheet extends StatefulWidget {
  final Review review;

  const _ReportBottomSheet({required this.review});

  @override
  State<_ReportBottomSheet> createState() => _ReportBottomSheetState();
}

class _ReportBottomSheetState extends State<_ReportBottomSheet> {
  String? _selectedReason;
  final TextEditingController _detailController = TextEditingController();
  String? _validationError;
  String? _apiError;
  bool _isSubmitting = false;

  static const List<Map<String, String>> _reasons = [
    {'code': 'fake', 'label': 'Nghi ngờ đánh giá giả'},
    {'code': 'spam', 'label': 'Spam / nội dung lặp'},
    {'code': 'misleading', 'label': 'Nội dung sai lệch'},
    {'code': 'inappropriate', 'label': 'Nội dung không phù hợp'},
    {'code': 'other', 'label': 'Lý do khác'},
  ];

  @override
  void dispose() {
    _detailController.dispose();
    super.dispose();
  }

  Future<void> _submitReport() async {
    if (_selectedReason == null) {
      setState(() {
        _validationError = 'Vui lòng chọn lý do báo cáo.';
      });
      return;
    }

    setState(() {
      _isSubmitting = true;
      _validationError = null;
      _apiError = null;
    });

    debugPrint(
        '[ReviewDetailScreen] Submitting report for review.id: "${widget.review.id}" '
        '(userId: ${widget.review.userId}, productId: "${widget.review.productId}", '
        'reason: "$_selectedReason")');

    try {
      await ReviewApiService.reportReview(
        reviewId: widget.review.id,
        reason: _selectedReason!,
        detail: _detailController.text.trim().isNotEmpty
            ? _detailController.text.trim()
            : null,
      );

      if (!mounted) return;
      Navigator.of(context).pop(true);
    } on ReviewApiException catch (e) {
      if (!mounted) return;
      setState(() {
        _isSubmitting = false;
        _apiError = e.message;
      });
    } catch (_) {
      if (!mounted) return;
      setState(() {
        _isSubmitting = false;
        _apiError = 'Không thể gửi báo cáo. Vui lòng thử lại.';
      });
    }
  }

  @override
  Widget build(BuildContext context) {
    final bottomInset = MediaQuery.of(context).viewInsets.bottom;
    final isFake = widget.review.isFake && widget.review.isAnalyzed;
    final isAnalyzed = widget.review.isAnalyzed;

    return Container(
      constraints: BoxConstraints(
        maxHeight: MediaQuery.of(context).size.height * 0.85,
      ),
      padding: EdgeInsets.only(bottom: bottomInset),
      decoration: const BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.vertical(top: Radius.circular(20)),
      ),
      child: SafeArea(
        top: false,
        child: SingleChildScrollView(
          padding: const EdgeInsets.fromLTRB(20, 16, 20, 20),
          child: Column(
            mainAxisSize: MainAxisSize.min,
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              // Top drag handle
              Center(
                child: Container(
                  width: 40,
                  height: 4,
                  margin: const EdgeInsets.only(bottom: 14),
                  decoration: BoxDecoration(
                    color: Colors.grey.shade300,
                    borderRadius: BorderRadius.circular(2),
                  ),
                ),
              ),

              // Title and Close Button
              Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                children: [
                  const Text(
                    'Báo cáo đánh giá',
                    style: TextStyle(
                      fontSize: 18,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                    ),
                  ),
                  IconButton(
                    icon: const Icon(Icons.close, size: 20, color: AppTheme.textMuted),
                    onPressed: _isSubmitting ? null : () => Navigator.of(context).pop(false),
                    padding: EdgeInsets.zero,
                    constraints: const BoxConstraints(),
                  ),
                ],
              ),
              const SizedBox(height: 14),

              // Review Preview Card
              Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: const Color(0xFFF8FAFC),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: AppTheme.surfaceBorder),
                ),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        // Star Rating
                        Row(
                          children: [
                            ...List.generate(5, (index) {
                              return Icon(
                                index < widget.review.rating.floor()
                                    ? Icons.star_rounded
                                    : (index < widget.review.rating
                                        ? Icons.star_half_rounded
                                        : Icons.star_outline_rounded),
                                color: Colors.amber,
                                size: 16,
                              );
                            }),
                            const SizedBox(width: 6),
                            Text(
                              '${widget.review.rating.toStringAsFixed(1)} sao',
                              style: const TextStyle(
                                fontSize: 12,
                                fontWeight: FontWeight.w700,
                                color: AppTheme.textPrimary,
                              ),
                            ),
                          ],
                        ),

                        // Classification Label Badge
                        Container(
                          padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                          decoration: BoxDecoration(
                            color: !isAnalyzed
                                ? const Color(0xFFF1F5F9)
                                : (isFake ? AppTheme.riskHighBg : AppTheme.riskLowBg),
                            borderRadius: BorderRadius.circular(8),
                            border: Border.all(
                              color: !isAnalyzed
                                  ? const Color(0xFFCBD5E1)
                                  : (isFake
                                      ? const Color(0xFFFCA5A5)
                                      : const Color(0xFF86EFAC)),
                            ),
                          ),
                          child: Text(
                            widget.review.statusLabel,
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w700,
                              color: !isAnalyzed
                                  ? AppTheme.textSecondary
                                  : (isFake ? AppTheme.riskHigh : AppTheme.riskLow),
                            ),
                          ),
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    Text(
                      widget.review.content,
                      maxLines: 2,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        color: AppTheme.textSecondary,
                        height: 1.35,
                      ),
                    ),
                  ],
                ),
              ),
              const SizedBox(height: 18),

              // "Lý do báo cáo" Header
              const Text(
                'Lý do báo cáo',
                style: TextStyle(
                  fontSize: 14,
                  fontWeight: FontWeight.w700,
                  color: AppTheme.textPrimary,
                ),
              ),
              const SizedBox(height: 8),

              // Reasons list
              ..._reasons.map((r) {
                final code = r['code']!;
                final label = r['label']!;
                final isSelected = _selectedReason == code;

                return InkWell(
                  onTap: _isSubmitting
                      ? null
                      : () {
                          setState(() {
                            _selectedReason = code;
                            _validationError = null;
                          });
                        },
                  borderRadius: BorderRadius.circular(10),
                  child: Container(
                    padding: const EdgeInsets.symmetric(vertical: 8, horizontal: 10),
                    margin: const EdgeInsets.only(bottom: 6),
                    decoration: BoxDecoration(
                      color: isSelected ? AppTheme.primaryBlueSubtle : Colors.transparent,
                      borderRadius: BorderRadius.circular(10),
                      border: Border.all(
                        color: isSelected ? AppTheme.primaryBlue : AppTheme.surfaceBorder,
                        width: isSelected ? 1.5 : 1,
                      ),
                    ),
                    child: Row(
                      children: [
                        Icon(
                          isSelected
                              ? Icons.radio_button_checked
                              : Icons.radio_button_off,
                          size: 18,
                          color: isSelected ? AppTheme.primaryBlue : AppTheme.textMuted,
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            label,
                            style: TextStyle(
                              fontSize: 13.5,
                              fontWeight: isSelected ? FontWeight.w600 : FontWeight.w400,
                              color: isSelected ? AppTheme.primaryBlue : AppTheme.textPrimary,
                            ),
                          ),
                        ),
                      ],
                    ),
                  ),
                );
              }),

              // Validation Error message
              if (_validationError != null) ...[
                const SizedBox(height: 4),
                Text(
                  _validationError!,
                  style: const TextStyle(
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: AppTheme.riskHigh,
                  ),
                ),
              ],

              const SizedBox(height: 12),

              // Optional Detail Field
              const Text(
                'Chi tiết bổ sung (tùy chọn)',
                style: TextStyle(
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                  color: AppTheme.textSecondary,
                ),
              ),
              const SizedBox(height: 6),
              TextField(
                controller: _detailController,
                enabled: !_isSubmitting,
                maxLines: 2,
                decoration: InputDecoration(
                  hintText: 'Nhập thông tin chi tiết nếu có...',
                  hintStyle: const TextStyle(fontSize: 12.5, color: AppTheme.textMuted),
                  border: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppTheme.surfaceBorder),
                  ),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppTheme.surfaceBorder),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(10),
                    borderSide: const BorderSide(color: AppTheme.primaryBlue, width: 1.5),
                  ),
                  contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
                ),
              ),

              // API Error Banner
              if (_apiError != null) ...[
                const SizedBox(height: 12),
                Container(
                  padding: const EdgeInsets.all(10),
                  decoration: BoxDecoration(
                    color: AppTheme.riskHighBg,
                    borderRadius: BorderRadius.circular(8),
                    border: Border.all(color: const Color(0xFFFCA5A5)),
                  ),
                  child: Row(
                    children: [
                      const Icon(Icons.error_outline_rounded, size: 18, color: AppTheme.riskHigh),
                      const SizedBox(width: 8),
                      Expanded(
                        child: Text(
                          _apiError!,
                          style: const TextStyle(
                            fontSize: 12.5,
                            fontWeight: FontWeight.w600,
                            color: AppTheme.riskHigh,
                          ),
                        ),
                      ),
                    ],
                  ),
                ),
              ],

              const SizedBox(height: 18),

              // Action Buttons Row
              Row(
                children: [
                  Expanded(
                    child: OutlinedButton(
                      onPressed: _isSubmitting
                          ? null
                          : () => Navigator.of(context).pop(false),
                      style: OutlinedButton.styleFrom(
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        side: const BorderSide(color: AppTheme.surfaceBorder),
                      ),
                      child: const Text(
                        'Hủy',
                        style: TextStyle(
                          fontSize: 14,
                          fontWeight: FontWeight.w600,
                          color: AppTheme.textSecondary,
                        ),
                      ),
                    ),
                  ),
                  const SizedBox(width: 12),
                  Expanded(
                    flex: 2,
                    child: ElevatedButton(
                      onPressed: _isSubmitting ? null : _submitReport,
                      style: ElevatedButton.styleFrom(
                        backgroundColor: AppTheme.primaryBlue,
                        disabledBackgroundColor: AppTheme.primaryBlue.withValues(alpha: 0.6),
                        padding: const EdgeInsets.symmetric(vertical: 12),
                        shape: RoundedRectangleBorder(
                          borderRadius: BorderRadius.circular(10),
                        ),
                        elevation: 0,
                      ),
                      child: _isSubmitting
                          ? const Row(
                              mainAxisAlignment: MainAxisAlignment.center,
                              children: [
                                SizedBox(
                                  width: 16,
                                  height: 16,
                                  child: CircularProgressIndicator(
                                    strokeWidth: 2,
                                    color: Colors.white,
                                  ),
                                ),
                                SizedBox(width: 8),
                                Text(
                                  'Đang gửi báo cáo...',
                                  style: TextStyle(
                                    fontSize: 14,
                                    fontWeight: FontWeight.w600,
                                    color: Colors.white,
                                  ),
                                ),
                              ],
                            )
                          : const Text(
                              'Gửi báo cáo',
                              style: TextStyle(
                                fontSize: 14,
                                fontWeight: FontWeight.w700,
                                color: Colors.white,
                              ),
                            ),
                    ),
                  ),
                ],
              ),
            ],
          ),
        ),
      ),
    );
  }
}
