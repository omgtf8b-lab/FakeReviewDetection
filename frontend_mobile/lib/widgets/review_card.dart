import 'package:flutter/material.dart';
import '../models/review.dart';
import '../theme/app_theme.dart';
import 'risk_badge.dart';

class ReviewCard extends StatelessWidget {
  final Review review;
  final VoidCallback onTap;

  const ReviewCard({
    super.key,
    required this.review,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    final isFake = review.isFake && review.isAnalyzed;

    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        margin: const EdgeInsets.only(bottom: 12),
        padding: const EdgeInsets.all(14),
        decoration: BoxDecoration(
          // Subtle red/orange tint if suspicious, clean white if original
          color: isFake ? const Color(0xFFFFFBFB) : Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: isFake
                ? const Color(0xFFFCA5A5)
                : AppTheme.surfaceBorder,
            width: isFake ? 1.2 : 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.02),
              offset: const Offset(0, 2),
              blurRadius: 6,
            ),
          ],
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Top: Author avatar, name, verification, date, and status badge
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
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
                      color: isFake ? AppTheme.riskHigh : AppTheme.primaryBlue,
                    ),
                  ),
                ),
                const SizedBox(width: 10),
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      Text(
                        review.author,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          fontSize: 13.5,
                          fontWeight: FontWeight.w700,
                          color: AppTheme.textPrimary,
                        ),
                      ),
                      const SizedBox(height: 2),
                      Wrap(
                        crossAxisAlignment: WrapCrossAlignment.center,
                        children: [
                          if (review.isVerifiedPurchase) ...[
                            const Text(
                              'Đã mua hàng',
                              style: TextStyle(
                                fontSize: 10.5,
                                fontWeight: FontWeight.w600,
                                color: AppTheme.riskLow,
                              ),
                            ),
                            if (review.date.isNotEmpty)
                              const Text(' • ', style: TextStyle(fontSize: 10.5, color: AppTheme.textMuted)),
                          ],
                          if (review.date.isNotEmpty)
                            Text(
                              review.date,
                              style: const TextStyle(
                                fontSize: 10.5,
                                color: AppTheme.textMuted,
                              ),
                            ),
                        ],
                      ),
                    ],
                  ),
                ),
                const SizedBox(width: 6),
                VerdictBadge(
                  isFake: review.isFake,
                  confidencePercent: review.confidencePercent,
                  isAnalyzed: review.isAnalyzed,
                  isFallback: review.isFallback,
                  isCompact: true,
                ),
              ],
            ),
            const SizedBox(height: 10),

            // Rating Stars & Review Title (if title exists)
            Row(
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(
                    5,
                    (index) => Icon(
                      index < review.rating.floor()
                          ? Icons.star_rounded
                          : (index < review.rating
                              ? Icons.star_half_rounded
                              : Icons.star_outline_rounded),
                      size: 15,
                      color: const Color(0xFFF59E0B),
                    ),
                  ),
                ),
                if (review.title.isNotEmpty) ...[
                  const SizedBox(width: 8),
                  Expanded(
                    child: Text(
                      review.title,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: AppTheme.textPrimary,
                      ),
                    ),
                  ),
                ],
              ],
            ),
            const SizedBox(height: 6),

            // Review Content Preview
            Text(
              '"${review.content}"',
              maxLines: 3,
              overflow: TextOverflow.ellipsis,
              style: const TextStyle(
                fontSize: 12.5,
                color: AppTheme.textSecondary,
                height: 1.4,
                fontStyle: FontStyle.normal,
              ),
            ),

            const SizedBox(height: 10),

            // Bottom CTA row: Điểm phân tích (0.xx) for suspicious & "Xem chi tiết"
            Wrap(
              alignment: WrapAlignment.spaceBetween,
              crossAxisAlignment: WrapCrossAlignment.center,
              spacing: 8,
              runSpacing: 6,
              children: [
                if (isFake)
                  Container(
                    padding: const EdgeInsets.symmetric(horizontal: 8, vertical: 3),
                    decoration: BoxDecoration(
                      color: AppTheme.riskHighBg,
                      borderRadius: BorderRadius.circular(6),
                      border: Border.all(color: const Color(0xFFFECACA), width: 1),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        const Icon(
                          Icons.warning_amber_rounded,
                          size: 13,
                          color: AppTheme.riskHigh,
                        ),
                        const SizedBox(width: 4),
                        Text(
                          'Điểm phân tích: ${review.scoreFormatted}',
                          style: const TextStyle(
                            fontSize: 11,
                            fontWeight: FontWeight.w700,
                            color: AppTheme.riskHigh,
                          ),
                        ),
                      ],
                    ),
                  )
                else
                  const SizedBox.shrink(),
                const Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Text(
                      'Xem chi tiết',
                      style: TextStyle(
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                        color: AppTheme.primaryBlueLight,
                      ),
                    ),
                    SizedBox(width: 2),
                    Icon(
                      Icons.arrow_forward_ios_rounded,
                      size: 10,
                      color: AppTheme.primaryBlueLight,
                    ),
                  ],
                ),
              ],
            ),
          ],
        ),
      ),
    );
  }
}
