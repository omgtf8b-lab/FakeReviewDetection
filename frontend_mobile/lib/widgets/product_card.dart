import 'package:flutter/material.dart';
import '../models/product.dart';
import '../theme/app_theme.dart';

class ProductCard extends StatelessWidget {
  final Product product;
  final VoidCallback onTap;

  const ProductCard({
    super.key,
    required this.product,
    required this.onTap,
  });

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(14),
      child: Container(
        margin: const EdgeInsets.only(bottom: 10),
        padding: const EdgeInsets.all(12),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(14),
          border: Border.all(
            color: AppTheme.surfaceBorder,
            width: 1,
          ),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.025),
              offset: const Offset(0, 2),
              blurRadius: 8,
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            // Product Icon
            Container(
              width: 72,
              height: 72,
              decoration: BoxDecoration(
                color: AppTheme.primaryBlueSubtle,
                borderRadius: BorderRadius.circular(12),
                border: Border.all(color: const Color(0xFFDBEAFE), width: 1),
              ),
              clipBehavior: Clip.antiAlias,
              child: product.imageUrl != null && product.imageUrl!.isNotEmpty ? Image.network(product.imageUrl!, fit: BoxFit.cover, errorBuilder: (_, _, _) => Icon(product.icon, color: AppTheme.primaryBlue)) : Icon(
                product.icon,
                size: 34,
                color: AppTheme.primaryBlue,
              ),
            ),
            const SizedBox(width: 12),

            // Product Information
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                mainAxisAlignment: MainAxisAlignment.center,
                children: [
                  // Brand • Category row
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          _brandCategory,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 11,
                            color: AppTheme.textSecondary,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                      ),
                      const SizedBox(width: 4),
                      // Verification status badge
                      _VerificationBadge(status: product.verificationStatus),
                    ],
                  ),
                  const SizedBox(height: 3),

                  // Product Name
                  Text(
                    product.name,
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 13.5,
                      fontWeight: FontWeight.w700,
                      color: AppTheme.textPrimary,
                      height: 1.25,
                    ),
                  ),
                  const SizedBox(height: 6),

                  // Price row
                  Row(
                    children: [
                      Expanded(
                        child: Text(
                          product.formattedPrice,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            fontSize: 14.5,
                            fontWeight: FontWeight.w800,
                            color: AppTheme.primaryBlue,
                          ),
                        ),
                      ),
                      // Product code (small)
                      if (product.productCode != null)
                        Text(
                          product.productCode!,
                          style: const TextStyle(
                            fontSize: 10.5,
                            color: AppTheme.textMuted,
                            fontWeight: FontWeight.w500,
                          ),
                        ),
                    ],
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  String get _brandCategory {
    final parts = <String>[];
    if (product.brand.isNotEmpty) parts.add(product.brand);
    if (product.category.isNotEmpty) parts.add(product.category);
    return parts.join(' • ');
  }
}

class _VerificationBadge extends StatelessWidget {
  final String status;
  const _VerificationBadge({required this.status});

  @override
  Widget build(BuildContext context) {
    final Color color;
    final Color bg;
    final String label;
    final IconData icon;

    switch (status) {
      case 'verified':
        color = const Color(0xFF16A34A);
        bg = const Color(0xFFF0FDF4);
        label = 'Đã xác minh';
        icon = Icons.verified_rounded;
        break;
      case 'revoked':
        color = const Color(0xFFDC2626);
        bg = const Color(0xFFFEF2F2);
        label = 'Đã thu hồi';
        icon = Icons.cancel_rounded;
        break;
      default:
        color = const Color(0xFFD97706);
        bg = const Color(0xFFFFFBEB);
        label = 'Chờ xác minh';
        icon = Icons.pending_rounded;
    }

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 6, vertical: 2),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(6),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Icon(icon, size: 10, color: color),
          const SizedBox(width: 3),
          Text(
            label,
            style: TextStyle(
              fontSize: 9.5,
              fontWeight: FontWeight.w700,
              color: color,
            ),
          ),
        ],
      ),
    );
  }
}
