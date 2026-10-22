class User {
  final int id;
  final String email;
  final String role;
  final bool isActive;
  final DateTime? createdAt;

  const User({
    required this.id,
    required this.email,
    required this.role,
    required this.isActive,
    this.createdAt,
  });

  factory User.fromJson(Map<String, dynamic> json) {
    return User(
      id: (json['id'] as num?)?.toInt() ?? 0,
      email: (json['email'] as String?) ?? '',
      role: (json['role'] as String?) ?? 'buyer',
      isActive: (json['is_active'] as bool?) ?? true,
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
    );
  }

  Map<String, dynamic> toJson() {
    return {
      'id': id,
      'email': email,
      'role': role,
      'is_active': isActive,
      'created_at': createdAt?.toIso8601String(),
    };
  }

  String get roleLabel {
    switch (role.toLowerCase()) {
      case 'buyer':
        return 'Người dùng';
      case 'seller':
        return 'Người bán';
      case 'admin':
        return 'Quản trị viên';
      case 'engineer':
        return 'Kỹ thuật viên';
      default:
        return role;
    }
  }

  String get statusLabel => isActive ? 'Hoạt động' : 'Đã khóa';

  String get formattedCreatedAt {
    if (createdAt == null) return '';
    final d = createdAt!;
    final day = d.day.toString().padLeft(2, '0');
    final month = d.month.toString().padLeft(2, '0');
    final year = d.year.toString();
    final hour = d.hour.toString().padLeft(2, '0');
    final minute = d.minute.toString().padLeft(2, '0');
    return '$day/$month/$year $hour:$minute';
  }
}
