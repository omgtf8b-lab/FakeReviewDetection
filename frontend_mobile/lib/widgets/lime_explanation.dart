import 'package:flutter/material.dart';
import '../services/workspace_api.dart';

class LimeExplanation extends StatefulWidget {
  final String content;
  final String? modelVersion;
  const LimeExplanation({super.key, required this.content, this.modelVersion});
  @override
  State<LimeExplanation> createState() => _LimeExplanationState();
}

class _LimeExplanationState extends State<LimeExplanation> {
  bool busy = false;
  String? error;
  Map<String, dynamic>? result;
  Future<void> explain() async {
    setState(() { busy = true; error = null; });
    try {
      final response = await WorkspaceApi.request('/api/workspace/explain', method: 'POST', body: {'content': widget.content, if (widget.modelVersion != null) 'model_version': widget.modelVersion});
      if (mounted) setState(() { result = response as Map<String, dynamic>; });
    } catch (e) { if (mounted) setState(() { error = e.toString(); }); }
    finally { if (mounted) setState(() { busy = false; }); }
  }
  @override
  Widget build(BuildContext context) {
    final features = (result?['features'] as List<dynamic>?) ?? [];
    final weights = {for (final f in features) (f['token'] as String).toLowerCase(): (f['weight'] as num).toDouble()};
    final tokens = RegExp(r'\w+|\W+').allMatches(widget.content).map((m) => m.group(0)!);
    return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      const Text('Giải thích bằng LIME', style: TextStyle(fontWeight: FontWeight.bold)),
      const Text('Đỏ tăng dự đoán fake; xanh giảm dự đoán fake. Không phải bằng chứng chắc chắn về gian lận.'),
      FilledButton(onPressed: busy ? null : explain, child: Text(busy ? 'Đang phân tích…' : 'Xem từ khóa ảnh hưởng')),
      if (error != null) Text(error!, style: const TextStyle(color: Colors.red)),
      if (result != null) ...[
        Text.rich(TextSpan(style: const TextStyle(color: Colors.black87, height: 1.7), children: tokens.map((word) {
          final weight = weights[word.toLowerCase()];
          return TextSpan(text: word, style: weight == null ? null : TextStyle(backgroundColor: weight > 0 ? Colors.red.shade100 : Colors.green.shade100));
        }).toList())),
        Wrap(spacing: 6, children: features.map((f) => Chip(label: Text('${f['token']}: ${(f['weight'] as num).toStringAsFixed(3)}'))).toList()),
      ],
    ])));
  }
}
