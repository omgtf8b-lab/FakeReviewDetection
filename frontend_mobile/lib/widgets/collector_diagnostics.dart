import 'package:flutter/material.dart';

const _diagnosticLabels = <String, String>{
  'chrome_crashpad_failed': 'Chrome dừng khi khởi tạo bộ báo lỗi.',
  'driver_version_mismatch': 'Phiên bản ChromeDriver không tương thích.',
  'profile_in_use': 'Profile Chrome đang được sử dụng.',
  'browser_permission_denied': 'Tiến trình trình duyệt thiếu quyền cần thiết.',
  'chrome_binary_missing': 'Chưa tìm thấy Chrome đã cấu hình.',
  'chrome_start_crashed': 'Chrome dừng trước khi khởi tạo xong.',
  'browser_start_unknown': 'Chưa xác định được nguyên nhân khởi động Chrome.',
  'worker_spawn_failed': 'Chưa tạo được tiến trình đọc trình duyệt.',
  'worker_exit_failed': 'Tiến trình đọc trình duyệt kết thúc bất thường.',
  'worker_invalid_output':
      'Tiến trình đọc trình duyệt chưa trả dữ liệu hợp lệ.',
  'worker_timeout': 'Tiến trình đọc trình duyệt vượt thời gian.',
  'worker_io_failed': 'Gián đoạn trao đổi với tiến trình trình duyệt.',
  'worker_execution_failed': 'Tiến trình trình duyệt chưa hoàn tất xử lý.',
  'collection_spawn_failed': 'Chưa tạo được tiến trình thu thập.',
  'collection_exit_failed': 'Tiến trình thu thập kết thúc bất thường.',
  'collection_invalid_output': 'Tiến trình thu thập chưa trả dữ liệu hợp lệ.',
  'collection_timeout': 'Tiến trình thu thập vượt thời gian.',
  'collection_io_failed': 'Gián đoạn trao đổi với tiến trình thu thập.',
};

List<Map<String, String>> collectorDiagnosticItems(Map data) {
  final rows = <Map<String, String>>[];
  final seen = <String>{};
  void add(dynamic diagnostic, dynamic fallback, dynamic collector) {
    final d = diagnostic is Map ? diagnostic : const {};
    final code = d['code'] ?? fallback;
    if (code is! String || !_diagnosticLabels.containsKey(code)) return;
    final source = collector == 'collection' ? 'collection' : 'selenium';
    if (!seen.add('$source:$code')) return;
    final row = {
      'code': code,
      'message': _diagnosticLabels[code]!,
      'source': source,
    };
    for (final field in [
      'driver_version_from_log',
      'browser_version_from_error',
    ]) {
      final version = d[field];
      if (version is String &&
          RegExp(r'^\d{1,4}\.\d{1,6}\.\d{1,8}\.\d{1,6}$').hasMatch(version)) {
        row[field] = version;
      }
    }
    rows.add(row);
  }

  final attempts = data['attempts'];
  if (attempts is List) {
    for (final item in attempts.take(8)) {
      if (item is Map &&
          ['selenium', 'collection'].contains(item['collector'])) {
        add(item['diagnostics'], item['diagnostic_code'], item['collector']);
      }
    }
  }
  final d = data['diagnostics'];
  add(
    d,
    null,
    d is Map && d['stage'] == 'collection' ? 'collection' : 'selenium',
  );
  return rows;
}

class CollectorDiagnostics extends StatelessWidget {
  final Map data;
  const CollectorDiagnostics({super.key, required this.data});
  @override
  Widget build(BuildContext context) {
    final rows = collectorDiagnosticItems(data);
    if (rows.isEmpty) return const SizedBox.shrink();
    return Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Text(
          'Thông tin lần thử thu thập',
          style: TextStyle(fontWeight: FontWeight.bold),
        ),
        for (final row in rows)
          Text(
            '${row['source'] == 'collection' ? 'Bộ thu thập' : 'Trình duyệt'}: ${row['message']} [${row['code']}]'
            '${row['driver_version_from_log'] == null ? '' : ' · Driver ${row['driver_version_from_log']}'}'
            '${row['browser_version_from_error'] == null ? '' : ' · Chrome ${row['browser_version_from_error']}'}',
          ),
        const Text(
          'Lỗi kỹ thuật này không xác nhận sàn chặn truy cập hoặc sản phẩm có đánh giá giả.',
        ),
      ],
    );
  }
}
