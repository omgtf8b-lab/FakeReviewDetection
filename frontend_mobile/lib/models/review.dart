class LimeContribution {
  final String phrase;
  final double weight;
  final bool isSuspicious;

  const LimeContribution({
    required this.phrase,
    required this.weight,
    required this.isSuspicious,
  });
}

class ReviewPrediction {
  final int id;
  final int reviewId;
  final String predictedLabel; // "real", "fake", etc.
  final double fakeProbability;
  final double realProbability;
  final double confidenceScore;
  final String? explanation;
  final String modelName;
  final String modelVersion;
  final DateTime? createdAt;

  const ReviewPrediction({
    required this.id,
    required this.reviewId,
    required this.predictedLabel,
    required this.fakeProbability,
    required this.realProbability,
    required this.confidenceScore,
    this.explanation,
    required this.modelName,
    required this.modelVersion,
    this.createdAt,
  });

  factory ReviewPrediction.fromJson(Map<String, dynamic> json) {
    return ReviewPrediction(
      id: (json['id'] as num?)?.toInt() ?? 0,
      reviewId: (json['review_id'] as num?)?.toInt() ?? 0,
      predictedLabel: (json['predicted_label'] as String?) ?? '',
      fakeProbability: (json['fake_probability'] as num?)?.toDouble() ?? 0.0,
      realProbability: (json['real_probability'] as num?)?.toDouble() ?? 0.0,
      confidenceScore: (json['confidence_score'] as num?)?.toDouble() ?? 0.0,
      explanation: json['explanation'] as String?,
      modelName: (json['model_name'] as String?) ?? '',
      modelVersion: (json['model_version'] as String?) ?? '',
      createdAt: json['created_at'] != null
          ? DateTime.tryParse(json['created_at'].toString())
          : null,
    );
  }

  bool get isFallback =>
      modelName == 'fallback-heuristic' || modelVersion == 'dev-only';

  String get labelText {
    if (predictedLabel == 'real') return 'Đánh giá gốc';
    if (predictedLabel == 'fake') return 'Đáng ngờ';
    return 'Chưa phân tích';
  }
}

class Review {
  final String id;
  final String productId;
  final int? userId;
  final double rating;
  final String content;
  final DateTime? createdAt;
  final ReviewPrediction? prediction;

  // Optional / compatibility fields
  final String? _inputAuthor;
  final String? _inputAuthorAvatar;
  final String? _inputDate;
  final String? _inputTitle;
  final bool? _customIsFake;
  final double? _customFakeConfidence;
  final bool? _customIsAnalyzed;
  final bool isVerifiedPurchase;
  final List<String> flaggedReasons;
  final double stylometricScore;
  final double accountTrustScore;
  final double velocityAnomalyScore;
  final List<String> suspiciousPhrases;
  final List<LimeContribution> limeContributions;

  const Review({
    required this.id,
    required this.productId,
    this.userId,
    required this.rating,
    required this.content,
    this.createdAt,
    this.prediction,
    String? author,
    String? authorAvatar,
    String? date,
    String? title,
    bool? isFake,
    double? fakeConfidence,
    bool? isAnalyzed,
    this.isVerifiedPurchase = false,
    this.flaggedReasons = const [],
    this.stylometricScore = 0.0,
    this.accountTrustScore = 0.0,
    this.velocityAnomalyScore = 0.0,
    this.suspiciousPhrases = const [],
    this.limeContributions = const [],
  })  : _inputAuthor = author,
        _inputAuthorAvatar = authorAvatar,
        _inputDate = date,
        _inputTitle = title,
        _customIsFake = isFake,
        _customFakeConfidence = fakeConfidence,
        _customIsAnalyzed = isAnalyzed ?? (prediction != null || fakeConfidence != null || isFake != null);

  factory Review.fromJson(Map<String, dynamic> json) {
    final rawUserId = (json['user_id'] as num?)?.toInt();
    final rawCreatedAt = json['created_at'] != null
        ? DateTime.tryParse(json['created_at'].toString())
        : null;

    ReviewPrediction? prediction;
    if (json['prediction'] != null && json['prediction'] is Map<String, dynamic>) {
      prediction = ReviewPrediction.fromJson(json['prediction'] as Map<String, dynamic>);
    }

    return Review(
      id: '${json['id'] ?? ''}',
      productId: '${json['product_id'] ?? ''}',
      userId: rawUserId,
      rating: (json['rating'] as num?)?.toDouble() ?? 5.0,
      content: (json['content'] as String?) ?? '',
      createdAt: rawCreatedAt,
      prediction: prediction,
      isAnalyzed: prediction != null,
    );
  }

  String get author {
    final a = _inputAuthor;
    if (a != null && a.isNotEmpty) return a;
    if (userId != null) return 'Người dùng #$userId';
    return 'Người dùng';
  }

  String get authorAvatar {
    final av = _inputAuthorAvatar;
    if (av != null && av.isNotEmpty) return av;
    if (userId != null) return '#$userId';
    return 'ND';
  }

  String get date {
    final dStr = _inputDate;
    if (dStr != null && dStr.isNotEmpty) return dStr;
    if (createdAt != null) {
      final d = createdAt!;
      final day = d.day.toString().padLeft(2, '0');
      final month = d.month.toString().padLeft(2, '0');
      final year = d.year.toString();
      final hour = d.hour.toString().padLeft(2, '0');
      final minute = d.minute.toString().padLeft(2, '0');
      return '$day/$month/$year $hour:$minute';
    }
    return '';
  }

  String get title => _inputTitle ?? '';

  bool get isAnalyzed {
    if (prediction != null) return true;
    final custom = _customIsAnalyzed;
    if (custom != null) return custom;
    return false;
  }

  bool get isFake {
    if (prediction != null) {
      return prediction!.predictedLabel == 'fake';
    }
    return _customIsFake ?? false;
  }

  double get fakeConfidence {
    if (prediction != null) {
      return prediction!.confidenceScore;
    }
    return _customFakeConfidence ?? 0.0;
  }

  String get statusLabel {
    if (!isAnalyzed) return 'Chưa phân tích';
    return isFake ? 'Đáng ngờ' : 'Đánh giá gốc';
  }

  String get internalStateName {
    if (!isAnalyzed) return 'Chưa phân tích';
    return isFake ? 'Đánh giá đáng ngờ' : 'Đánh giá gốc';
  }

  String get internalCode {
    if (!isAnalyzed) return 'UA';
    return isFake ? 'CG' : 'OR';
  }

  String get stateExplanation {
    if (!isAnalyzed) return 'Đánh giá chưa qua mô hình phân tích';
    return isFake
        ? 'Có dấu hiệu là đánh giá được sinh bởi máy tính'
        : 'Đánh giá có đặc điểm giống nội dung do người dùng viết';
  }

  String get verdictText => statusLabel;
  int get confidencePercent => (fakeConfidence * 100).round();
  String get scoreFormatted => fakeConfidence.toStringAsFixed(2);
  String get analysisScoreText => 'Điểm phân tích: $scoreFormatted';

  bool get isFallback => prediction?.isFallback ?? false;
}
