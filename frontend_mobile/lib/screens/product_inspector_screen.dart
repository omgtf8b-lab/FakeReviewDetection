import 'dart:async';
import 'dart:convert';

import 'package:flutter/material.dart';
import 'package:file_selector/file_selector.dart';
import 'package:http/http.dart' as http;

import '../services/auth_state.dart';
import '../services/workspace_api.dart';
import 'login_screen.dart';

class ProductInspectorScreen extends StatefulWidget {
  final bool historyOnly;
  const ProductInspectorScreen({super.key, this.historyOnly = false});
  @override
  State<ProductInspectorScreen> createState() => _ProductInspectorScreenState();
}

class _ProductInspectorScreenState extends State<ProductInspectorScreen> {
  static const root = '/api/product-links';
  final _url = TextEditingController();
  List<dynamic> _history = [];
  Map<String, dynamic>? _job;
  Timer? _timer;
  int _generation = 0;
  String? _error;
  bool _busy = false;
  bool get _pending => ['queued', 'running'].contains(_job?['status']);
  @override
  void initState() {
    super.initState();
    AuthState.instance.addListener(_authChanged);
    _load();
  }

  @override
  void dispose() {
    _timer?.cancel();
    _generation++;
    _url.dispose();
    AuthState.instance.removeListener(_authChanged);
    super.dispose();
  }

  void _authChanged() {
    if (mounted) {
      _timer?.cancel();
      _generation++;
      setState(() {
        _history = [];
        _job = null;
      });
      _load();
    }
  }

  Future<void> _load() async {
    if (!AuthState.instance.isAuthenticated) return;
    final token = AuthState.instance.token;
    try {
      final rows = await WorkspaceApi.request(root);
      if (mounted && token == AuthState.instance.token) {
        setState(() {
          _history = rows as List<dynamic>;
        });
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
        });
      }
    }
  }

  void _follow(Map<String, dynamic> job) {
    _timer?.cancel();
    final generation = ++_generation;
    setState(() {
      _job = job;
    });
    void poll() {
      _timer = Timer(const Duration(seconds: 2), () async {
        try {
          final next = await WorkspaceApi.request(
            '$root/${job['id']}',
          ) as Map<String, dynamic>;
          if (!mounted || generation != _generation) return;
          setState(() {
            _job = next;
          });
          if (['queued', 'running'].contains(next['status'])) {
            poll();
          } else {
            await _load();
          }
        } catch (e) {
          if (mounted && generation == _generation) {
            setState(() {
              _error = '$e Mở lại từ lịch sử để tải kết quả.';
              _job = null;
            });
          }
        }
      });
    }

    if (_pending) poll();
  }

  Future<void> _execute(Future<dynamic> Function() action) async {
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      final job = await action();
      if (mounted) {
        _follow(job as Map<String, dynamic>);
        await _load();
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
        });
      }
    } finally {
      if (mounted) {
        setState(() {
          _busy = false;
        });
      }
    }
  }

  Future<void> _files(bool video) async {
    try {
      final files = await openFiles(
        acceptedTypeGroups: [
          XTypeGroup(
            label: video ? 'Video' : 'Ảnh',
            extensions: video
                ? ['mp4', 'webm', 'mov', 'avi']
                : ['jpg', 'jpeg', 'png', 'webp', 'gif'],
          ),
        ],
      );
      if (files.isEmpty || !mounted) return;
      if (files.length > 6) throw Exception('Tối đa 6 tệp mỗi lần.');
      final upload = <http.MultipartFile>[];
      int total = 0;
      for (final file in files) {
        final size = await file.length();
        total += size;
        if (size > 40000000 || total > 60000000) {
          throw Exception('Mỗi tệp tối đa 40 MB, tổng tối đa 60 MB.');
        }
        upload.add(
          http.MultipartFile.fromBytes(
            'files',
            await file.readAsBytes(),
            filename: file.name,
          ),
        );
      }
      if (mounted) {
        await _execute(() => WorkspaceApi.upload('$root/media', upload));
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
        });
      }
    }
  }

  Future<void> _importReviews() async {
    try {
      if (_url.text.trim().isEmpty) {
        throw Exception('Nhập link sản phẩm tương ứng trước.');
      }
      final file = await openFile(
        acceptedTypeGroups: [
          const XTypeGroup(label: 'Review JSON', extensions: ['json']),
        ],
      );
      if (file == null) return;
      if (await file.length() > 2000000) {
        throw Exception('File JSON tối đa 2 MB.');
      }
      final data = jsonDecode(await file.readAsString());
      if (data is! Map || data['reviews'] is! List) {
        throw Exception('File cần có danh sách reviews.');
      }
      if (mounted) {
        await _execute(
          () => WorkspaceApi.request(
            '$root/import',
            method: 'POST',
            body: {
              'url': _url.text.trim(),
              'reviews': data['reviews'],
              'product_name': data['product_name'] ?? '',
            },
          ),
        );
      }
    } catch (e) {
      if (mounted) {
        setState(() {
          _error = e.toString();
        });
      }
    }
  }

  static const _verdict = {
    'insufficient_data': 'Chưa đủ cơ sở kết luận',
    'signals_detected': 'Có dấu hiệu cần kiểm tra',
    'no_obvious_signals': 'Chưa thấy dấu hiệu rõ trong mẫu',
    'technical_signals': 'Có dấu hiệu kỹ thuật cần xem',
  };
  Future<void> _manualReview() async {
    if (_url.text.trim().isEmpty) {
      setState(() {
        _error = 'Nhập link sản phẩm tương ứng trước khi viết review dự phòng.';
      });
      return;
    }
    final text = TextEditingController();
    final name = TextEditingController();
    final form = GlobalKey<FormState>();
    final values = await showDialog<Map<String, String>>(
      context: context,
      builder: (ctx) => AlertDialog(
        title: const Text('Review kiểm thử / dự phòng'),
        content: SingleChildScrollView(
          child: Form(
            key: form,
            child: Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                const Text(
                  'Dữ liệu bạn nhập không phải review vừa lấy từ sàn hoặc nhãn thật/giả đã xác minh.',
                ),
                TextFormField(
                  controller: name,
                  maxLength: 300,
                  decoration: const InputDecoration(
                    labelText: 'Tên sản phẩm (tùy chọn)',
                  ),
                ),
                TextFormField(
                  controller: text,
                  maxLength: 5000,
                  maxLines: 4,
                  decoration: const InputDecoration(
                    labelText: 'Review dự phòng',
                  ),
                  validator: (v) => v == null || v.trim().isEmpty
                      ? 'Nhập nội dung review'
                      : null,
                ),
              ],
            ),
          ),
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx),
            child: const Text('Hủy'),
          ),
          FilledButton(
            onPressed: () {
              if (form.currentState!.validate()) {
                Navigator.pop(ctx, {'name': name.text, 'text': text.text});
              }
            },
            child: const Text('Lưu và phân tích'),
          ),
        ],
      ),
    );
    Future<void>.delayed(const Duration(seconds: 1), () {
      text.dispose();
      name.dispose();
    });
    if (values == null || !mounted) return;
    await _execute(
      () => WorkspaceApi.request(
        '$root/import',
        method: 'POST',
        body: {
          'url': _url.text.trim(),
          'input_method': 'form',
          'product_name': values['name'],
          'reviews': [
            {
              'id': 'entry-${DateTime.now().microsecondsSinceEpoch}',
              'text': values['text'],
              'language': 'unknown',
            },
          ],
        },
      ),
    );
  }

  Widget _result() {
    final data = _job?['result'];
    if (data is! Map) return const SizedBox.shrink();
    if (_job?['status'] == 'failed') {
      return Column(
        children: [
          Text(data['message'] ?? 'Chưa hoàn tất phân tích.'),
          if (data['snapshot_id'] != null)
            OutlinedButton(
              onPressed: _pending || _busy
                  ? null
                  : () => _execute(
                      () => WorkspaceApi.request(
                        '$root/snapshots/${data['snapshot_id']}/analyze',
                        method: 'POST',
                      ),
                    ),
              child: const Text('Phân tích lại dữ liệu đã lưu'),
            ),
        ],
      );
    }
    final summary = data['summary'] as Map? ?? {};
    final upload = data['source'] == 'user_upload';
    return Card(
      child: Padding(
        padding: const EdgeInsets.all(16),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Text(
              'Kết quả #${_job!['id']}',
              style: Theme.of(context).textTheme.titleLarge,
            ),
            Text(
              data['product']?['name']?.toString().isNotEmpty == true
                  ? data['product']['name']
                  : 'Dữ liệu đã gửi',
            ),
            const SizedBox(height: 12),
            Text(
              _verdict[summary['verdict']] ?? 'Chưa có kết luận',
              style: const TextStyle(
                fontWeight: FontWeight.bold,
                color: Color(0xFF92631A),
              ),
            ),
            if (data['collection_message'] != null)
              Text(data['collection_message']),
            if (data['provenance']?['mode'] == 'snapshot')
              Text(
                'Kết quả phân tích bản lưu được lưu lúc ${data['provenance']['captured_at']}. Lần này không lấy dữ liệu mới từ sàn.',
                style: const TextStyle(color: Colors.orange),
              ),
            if (data['provenance']?['snapshot_id'] != null &&
                (data['reviews'] as List? ?? []).isNotEmpty)
              TextButton(
                onPressed: _busy || _pending
                    ? null
                    : () => _execute(
                        () => WorkspaceApi.request(
                          '$root/snapshots/${data['provenance']['snapshot_id']}/analyze',
                          method: 'POST',
                        ),
                      ),
                child: const Text('Phân tích lại bản lưu'),
              ),
            const Divider(),
            Text(
              upload
                  ? '${summary['observed_files']} tệp đã đọc · ${summary['files_with_signals']} tệp có dấu hiệu kỹ thuật'
                  : '${summary['observed_reviews']} review đã đọc · ${summary['reviews_with_signals']} review có dấu hiệu',
            ),
            Text(
              '${upload ? 'Tỷ lệ tệp có dấu hiệu' : 'Tỷ lệ review có dấu hiệu'}: ${summary['signal_percentage'] == null ? 'chưa có số liệu' : '${summary['signal_percentage']}%'}',
              style: const TextStyle(fontSize: 18, fontWeight: FontWeight.bold),
            ),
            const Text(
              'Không phải xác suất sản phẩm hoặc nội dung là giả.',
              style: TextStyle(fontSize: 12),
            ),
            if ([
              'user_supplied_review_import',
              'user_written_review',
            ].contains(data['source']))
              const Text('Review do bạn nhập; chưa xác minh nguồn với sàn.'),
            for (final aspect
                in (data['observations']?['aspects'] as List? ?? []))
              ExpansionTile(
                tilePadding: EdgeInsets.zero,
                title: Text(aspect['aspect']),
                subtitle: Text(
                  '${aspect['mentions']} nội dung không trùng · ${aspect['positive_mentions']} nhắc tích cực · ${aspect['negative_mentions']} nhắc tiêu cực',
                ),
                children: [
                  const Text(
                    'Tổng hợp theo từ khóa, chưa xác minh trải nghiệm thật.',
                  ),
                  for (final evidence in aspect['evidence'])
                    Text(
                      'Review #${evidence['review_id']}: ${evidence['quote']}',
                    ),
                ],
              ),
            for (final review in (data['reviews'] as List? ?? []))
              ExpansionTile(
                tilePadding: EdgeInsets.zero,
                title: Text('Review #${review['id']}'),
                subtitle: Text(
                  review['text'] ?? '',
                  maxLines: 2,
                  overflow: TextOverflow.ellipsis,
                ),
                children: [
                  SelectableText(review['text'] ?? ''),
                  for (final signal in review['signals'])
                    ListTile(dense: true, title: Text(signal['message'])),
                  if (review['nlp'] == null)
                    const Text(
                      'Chưa có điểm NLP cho review này; chỉ kiểm tra theo quy tắc.',
                    ),
                ],
              ),
            for (final file in (data['files'] as List? ?? []))
              ExpansionTile(
                tilePadding: EdgeInsets.zero,
                title: Text(file['name']),
                subtitle: Text(
                  file['kind'] == 'video'
                      ? '${file['duration_seconds']}s · ${file['frames_sampled']} khung hình mẫu'
                      : '${file['width']} × ${file['height']} px',
                ),
                children: [
                  for (final signal in file['signals'])
                    Text('• ${signal['message']}'),
                  if ((file['signals'] as List).isEmpty)
                    const Text(
                      'Chưa thấy dấu hiệu kỹ thuật trong phạm vi kiểm tra.',
                    ),
                ],
              ),
            ExpansionTile(
              tilePadding: EdgeInsets.zero,
              title: const Text('Phạm vi và giới hạn'),
              children: [
                for (final item in (data['limitations'] as List? ?? []))
                  Padding(
                    padding: const EdgeInsets.only(bottom: 8),
                    child: Text('• $item'),
                  ),
              ],
            ),
          ],
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    final signedIn = AuthState.instance.isAuthenticated;
    return Scaffold(
      appBar: AppBar(
        title: Text(
          widget.historyOnly ? 'Lịch sử của tôi' : 'Kiểm tra sản phẩm',
        ),
      ),
      body: RefreshIndicator(
        onRefresh: _load,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            if (!widget.historyOnly) ...[
              Text(
                'Hiểu sản phẩm hơn.\nXem điều đáng lưu ý.',
                style: Theme.of(context).textTheme.headlineSmall
                    ?.copyWith(fontWeight: FontWeight.bold),
              ),
              const SizedBox(height: 12),
              const Text(
                'Dán link Shopee, TikTok Shop, Lazada hoặc gửi ảnh/video để xem dấu hiệu và bằng chứng.',
              ),
              const SizedBox(height: 20),
            ],
            if (!signedIn)
              Card(
                child: Padding(
                  padding: const EdgeInsets.all(18),
                  child: Column(
                    children: [
                      const Text(
                        'Đăng nhập để kiểm tra và lưu kết quả riêng của bạn.',
                      ),
                      FilledButton(
                        onPressed: () => Navigator.push(
                          context,
                          MaterialPageRoute(
                            builder: (_) => const LoginScreen(),
                          ),
                        ),
                        child: const Text('Đăng nhập'),
                      ),
                    ],
                  ),
                ),
              ),
            if (signedIn && !widget.historyOnly) ...[
              TextField(
                controller: _url,
                keyboardType: TextInputType.url,
                decoration: const InputDecoration(
                  labelText: 'Link sản phẩm',
                  hintText: 'https://shopee.vn/…',
                  border: OutlineInputBorder(),
                ),
              ),
              const SizedBox(height: 12),
              FilledButton.icon(
                onPressed: _busy || _pending
                    ? null
                    : () => _execute(
                        () => WorkspaceApi.request(
                          root,
                          method: 'POST',
                          body: {'url': _url.text.trim(), 'limit': 50},
                        ),
                      ),
                icon: const Icon(Icons.link),
                label: const Text('Kiểm tra link'),
              ),
              Wrap(
                spacing: 8,
                children: [
                  OutlinedButton.icon(
                    onPressed: _busy || _pending ? null : () => _files(false),
                    icon: const Icon(Icons.image_outlined),
                    label: const Text('Tải ảnh'),
                  ),
                  OutlinedButton.icon(
                    onPressed: _busy || _pending ? null : () => _files(true),
                    icon: const Icon(Icons.video_file_outlined),
                    label: const Text('Tải video'),
                  ),
                ],
              ),
              const Text(
                'Tối đa 6 tệp · 40 MB/tệp · 60 MB/lần · video tối đa 5 phút.',
                style: TextStyle(fontSize: 12),
              ),
              TextButton(
                onPressed: _busy || _pending ? null : _importReviews,
                child: const Text('Dự phòng: nhập file review JSON'),
              ),
              TextButton(
                onPressed: _busy || _pending ? null : _manualReview,
                child: const Text('Dự phòng: viết review trực tiếp'),
              ),
            ],
            if (_error != null)
              Padding(
                padding: const EdgeInsets.symmetric(vertical: 12),
                child: Text(_error!, style: const TextStyle(color: Colors.red)),
              ),
            if (_busy || _pending)
              const Padding(
                padding: EdgeInsets.all(20),
                child: Column(
                  children: [
                    LinearProgressIndicator(),
                    SizedBox(height: 10),
                    Text('Đang kiểm tra dữ liệu…'),
                  ],
                ),
              ),
            _result(),
            const SizedBox(height: 20),
            if (signedIn)
              Text(
                'Lịch sử kiểm tra riêng của bạn',
                style: Theme.of(context).textTheme.titleMedium,
              ),
            if (signedIn && _history.isEmpty)
              const Padding(
                padding: EdgeInsets.all(16),
                child: Text('Chưa có lần kiểm tra nào.'),
              ),
            for (final row in _history)
              Card(
                child: ListTile(
                  leading: Icon(
                    row['platform'] == 'upload'
                        ? Icons.perm_media_outlined
                        : Icons.link,
                  ),
                  title: Text(
                    row['result']?['product']?['name']?.toString().isNotEmpty ==
                            true
                        ? row['result']['product']['name']
                        : row['platform'] == 'upload'
                        ? 'Ảnh / video đã gửi'
                        : row['url'],
                    maxLines: 2,
                    overflow: TextOverflow.ellipsis,
                  ),
                  subtitle: Text('${row['created_at']} · ${row['status']}'),
                  onTap: () => _follow(row as Map<String, dynamic>),
                ),
              ),
          ],
        ),
      ),
    );
  }
}
