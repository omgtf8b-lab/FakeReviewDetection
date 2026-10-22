import 'package:flutter/material.dart';
import '../models/product.dart';
import '../theme/app_theme.dart';

class RiskBadge extends StatelessWidget {
  final RiskLevel riskLevel;
  final bool isSmall;

  const RiskBadge({
    super.key,
    required this.riskLevel,
    this.isSmall = false,
  });

  @override
  Widget build(BuildContext context) {
    IconData icon;
    switch (riskLevel) {
      case RiskLevel.high:
        icon = Icons.warning_amber_rounded;
        break;
      case RiskLevel.moderate:
        icon = Icons.info_outline_rounded;
        break;
      case RiskLevel.low:
        icon = Icons.verified_user_outlined;
        break;
    }

    return Container(
      padding: EdgeInsets.symmetric(
        horizontal: isSmall ? 8 : 10,
        vertical: isSmall ? 3 : 5,
      ),
      decoration: BoxDecoration(
        color: riskLevel.backgroundColor,
        borderRadius: BorderRadius.circular(20),
        border: Border.all(
          color: riskLevel.color.withValues(alpha: 0.35),
          width: 1,
        ),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(
            icon,
            size: isSmall ? 12 : 14,
            color: riskLevel.color,
          ),
          const SizedBox(width: 4),
          Text(
            riskLevel.label,
            style: TextStyle(
              color: riskLevel.color,
              fontSize: isSmall ? 11 : 12,
              fontWeight: FontWeight.w700,
              letterSpacing: -0.1,
            ),
          ),
        ],
      ),
    );
  }
}

class VerdictBadge extends StatelessWidget {
  final bool isFake;
  final int confidencePercent;
  final bool isCompact;
  final bool isAnalyzed;
  final bool isFallback;

  const VerdictBadge({
    super.key,
    required this.isFake,
    required this.confidencePercent,
    this.isCompact = false,
    this.isAnalyzed = true,
    this.isFallback = false,
  });

  @override
  Widget build(BuildContext context) {
    Widget badgeWidget;

    if (!isAnalyzed) {
      badgeWidget = Container(
        padding: EdgeInsets.symmetric(
          horizontal: isCompact ? 8 : 10,
          vertical: isCompact ? 3 : 5,
        ),
        decoration: BoxDecoration(
          color: const Color(0xFFF1F5F9),
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFCBD5E1), width: 1),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.help_outline_rounded, size: isCompact ? 12 : 13, color: const Color(0xFF64748B)),
            const SizedBox(width: 4),
            Text(
              'Chưa phân tích',
              style: TextStyle(
                color: const Color(0xFF64748B),
                fontSize: isCompact ? 11 : 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      );
    } else if (isFake) {
      badgeWidget = Container(
        padding: EdgeInsets.symmetric(
          horizontal: isCompact ? 8 : 10,
          vertical: isCompact ? 3 : 5,
        ),
        decoration: BoxDecoration(
          color: AppTheme.riskHighBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFFCA5A5), width: 1),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.warning_amber_rounded, size: isCompact ? 13 : 15, color: AppTheme.riskHigh),
            const SizedBox(width: 4),
            Text(
              'Đáng ngờ',
              style: TextStyle(
                color: AppTheme.riskHigh,
                fontSize: isCompact ? 11 : 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      );
    } else {
      // Original review
      badgeWidget = Container(
        padding: EdgeInsets.symmetric(
          horizontal: isCompact ? 8 : 10,
          vertical: isCompact ? 3 : 5,
        ),
        decoration: BoxDecoration(
          color: AppTheme.riskLowBg,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFF86EFAC), width: 1),
        ),
        child: Row(
          mainAxisSize: MainAxisSize.min,
          children: [
            Icon(Icons.check_circle_outline_rounded, size: isCompact ? 13 : 15, color: AppTheme.riskLow),
            const SizedBox(width: 4),
            Text(
              'Đánh giá gốc',
              style: TextStyle(
                color: AppTheme.riskLow,
                fontSize: isCompact ? 11 : 12,
                fontWeight: FontWeight.w700,
              ),
            ),
          ],
        ),
      );
    }

    if (!isFallback) {
      return badgeWidget;
    }

    return Wrap(
      spacing: 4,
      runSpacing: 4,
      crossAxisAlignment: WrapCrossAlignment.center,
      children: [
        badgeWidget,
        Container(
          padding: EdgeInsets.symmetric(
            horizontal: isCompact ? 6 : 8,
            vertical: isCompact ? 2 : 4,
          ),
          decoration: BoxDecoration(
            color: const Color(0xFFFFFBEB),
            borderRadius: BorderRadius.circular(16),
            border: Border.all(color: const Color(0xFFFDE68A), width: 1),
          ),
          child: Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Icon(
                Icons.science_outlined,
                size: isCompact ? 11 : 12,
                color: const Color(0xFFD97706),
              ),
              const SizedBox(width: 3),
              Text(
                'Thử nghiệm',
                style: TextStyle(
                  color: const Color(0xFFB45309),
                  fontSize: isCompact ? 10.5 : 11,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ],
          ),
        ),
      ],
    );
  }
}
