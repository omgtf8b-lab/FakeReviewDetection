import 'package:flutter/material.dart';
import '../services/auth_state.dart';
import '../services/workspace_api.dart';
import '../services/firebase_service.dart';
import 'login_screen.dart';

class WorkspaceScreen extends StatefulWidget {
  const WorkspaceScreen({super.key});
  @override
  State<WorkspaceScreen> createState() => _WorkspaceScreenState();
}

class _WorkspaceScreenState extends State<WorkspaceScreen> {
  String _section = 'shops';
  bool _busy = false;
  String? _error;
  List<dynamic> _rows = [];
  static const root = '/api/workspace';

  @override
  void initState() { super.initState(); _load(); AuthState.instance.addListener(_authChanged); }
  @override
  void dispose() { AuthState.instance.removeListener(_authChanged); super.dispose(); }
  void _authChanged() { if (mounted) _load(); }

  Future<void> _load() async {
    if (!mounted) return;
    setState(() { _busy = true; _error = null; });
    try {
      if (!AuthState.instance.isAuthenticated && _section != 'shops') {
        setState(() { _rows = []; });
        return;
      }
      dynamic result;
      if (_section == 'shops') result = await WorkspaceApi.request('$root/shops');
      if (_section == 'reports') result = await WorkspaceApi.request('$root/reports');
      if (_section == 'purchases') result = await WorkspaceApi.request('$root/purchases');
      if (_section == 'reviews') result = await WorkspaceApi.request('/api/reviews/me?page_size=100');
      if (_section == 'products') result = await WorkspaceApi.request('/api/products?page_size=100');
      if (_section == 'notifications') result = await WorkspaceApi.request('$root/notifications');
      if (_section == 'profile') result = [await WorkspaceApi.request('$root/profile')];
      if (mounted) setState(() { _rows = (result is Map ? result['items'] : result) as List<dynamic>? ?? []; });
    } catch (e) { if (mounted) setState(() { _error = e.toString(); }); }
    finally { if (mounted) setState(() { _busy = false; }); }
  }

  Future<void> _act(Future<dynamic> Function() action) async {
    setState(() { _busy = true; _error = null; });
    try {
      await action();
      if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Đã cập nhật')));
      await _load();
    } catch (e) { if (mounted) setState(() { _error = e.toString(); }); }
    finally { if (mounted) setState(() { _busy = false; }); }
  }

  Future<Map<String, String>?> _form(String title, Map<String, String> fields, {Set<String> optional = const {}, Set<String> passwords = const {}}) async {
    final controllers = {for (final entry in fields.entries) entry.key: TextEditingController(text: entry.value)};
    final key = GlobalKey<FormState>();
    final result = await showDialog<Map<String, String>>(context: context, builder: (ctx) => AlertDialog(
      title: Text(title),
      content: SingleChildScrollView(child: Form(key: key, child: Column(mainAxisSize: MainAxisSize.min, children: controllers.entries.map((e) => Padding(
        padding: const EdgeInsets.symmetric(vertical: 7), child: TextFormField(controller: e.value,
        obscureText: passwords.contains(e.key), maxLines: passwords.contains(e.key) ? 1 : null,
        decoration: InputDecoration(labelText: e.key),
        validator: (v) => !optional.contains(e.key) && (v == null || v.trim().isEmpty) ? 'Vui lòng nhập thông tin' : null),
      )).toList()))),
      actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Hủy')),
        FilledButton(onPressed: () { if (key.currentState!.validate()) Navigator.pop(ctx, {for (final e in controllers.entries) e.key: e.value.text.trim()}); }, child: const Text('Lưu'))],
    ));
    // Controllers stay alive until the route transition has finished.
    Future<void>.delayed(const Duration(seconds: 1), () { for (final c in controllers.values) { c.dispose(); } });
    return result;
  }

  Future<void> _writeReview(dynamic order) async {
    final values = await _form('Viết đánh giá sản phẩm #${order['product_id']}', {'Nội dung': '', 'Số sao (1–5)': '5'});
    if (values == null || !mounted) return;
    final rating = double.tryParse(values['Số sao (1–5)']!);
    if (rating == null || rating < 1 || rating > 5) { setState(() { _error = 'Số sao phải từ 1 đến 5'; }); return; }
    await _act(() => WorkspaceApi.request('/api/reviews', method: 'POST', body: {'product_id': order['product_id'], 'content': values['Nội dung'], 'rating': rating}));
  }

  Future<void> _editProduct([dynamic product]) async {
    final values = await _form(product == null ? 'Thêm sản phẩm' : 'Sửa sản phẩm', {
      'Tên sản phẩm': product?['name']?.toString() ?? '', 'Giá': product?['price']?.toString() ?? '',
      'Danh mục': product?['category']?.toString() ?? '', 'Mô tả': product?['description']?.toString() ?? '',
    }, optional: {'Mô tả', 'Danh mục'});
    if (values == null || !mounted) return;
    final price = double.tryParse(values['Giá']!);
    if (price == null || price <= 0) { setState(() { _error = 'Giá phải lớn hơn 0'; }); return; }
    await _act(() => WorkspaceApi.request(product == null ? '/api/products' : '/api/products/${product['id']}', method: product == null ? 'POST' : 'PUT',
      body: {'name': values['Tên sản phẩm'], 'price': price, 'category': values['Danh mục'], 'description': values['Mô tả']}));
  }

  Future<void> _editExtra(dynamic product) async {
    try {
      final current = await WorkspaceApi.request('$root/products/${product['id']}/extra');
      if (!mounted) return;
      final values = await _form('Ảnh và tồn kho', {'Ảnh HTTPS': current['image_url'] ?? '', 'Tồn kho': '${current['stock']}', 'Trạng thái (active/paused/sold_out)': current['sale_status'], 'Mã nhóm sản phẩm': current['canonical_key'] ?? ''}, optional: {'Ảnh HTTPS', 'Mã nhóm sản phẩm'});
      if (values == null || !mounted) return;
      await _act(() => WorkspaceApi.request('$root/products/${product['id']}/extra', method: 'PUT', body: {'image_url': values['Ảnh HTTPS']!.isEmpty ? null : values['Ảnh HTTPS'], 'stock': int.tryParse(values['Tồn kho']!) ?? -1, 'sale_status': values['Trạng thái (active/paused/sold_out)'], 'canonical_key': values['Mã nhóm sản phẩm']}));
    } catch (e) { if (mounted) setState(() { _error = e.toString(); }); }
  }

  Future<void> _editProfile(dynamic profile) async {
    final seller = ['seller', 'admin'].contains(AuthState.instance.currentUser?.role);
    final values = await _form('Thông tin cá nhân', {'Tên hiển thị': profile['display_name'] ?? '', 'Điện thoại': profile['phone'] ?? '', if (seller) 'Tên shop': profile['shop_name'] ?? '', if (seller) 'Giới thiệu shop': profile['shop_description'] ?? ''}, optional: {'Điện thoại', 'Giới thiệu shop'});
    if (values == null || !mounted) return;
    await _act(() => WorkspaceApi.request('$root/profile', method: 'PUT', body: {'display_name': values['Tên hiển thị'], 'phone': values['Điện thoại'], if (seller) 'shop_name': values['Tên shop'], if (seller) 'shop_description': values['Giới thiệu shop']}));
  }

  Widget _shop(dynamic shop) => Card(child: Padding(padding: const EdgeInsets.all(16), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
    Text(shop['shop_name'], style: Theme.of(context).textTheme.titleMedium),
    Text('Độ uy tín: ${shop['trust_score'] ?? 'chưa đủ dữ liệu'} · Đáng ngờ: ${shop['fake_percentage'] ?? '—'}%'),
    Text('${shop['analyzed_reviews']} review đã phân loại / ${shop['total_reviews']} tổng review'),
    Text('Số sao sau lọc: ${shop['filtered_average_rating'] ?? '—'}'),
    if ((shop['timeline'] as List).isNotEmpty) SizedBox(height: 160, child: CustomPaint(size: const Size(double.infinity, 160), painter: _TrustPainter(shop['timeline']))),
    const Text('Biểu đồ tỷ lệ đáng ngờ theo ngày (0–100%).', style: TextStyle(fontSize: 12)),
    Text(shop['note'], style: const TextStyle(fontSize: 12)),
  ])));

  Widget _row(dynamic row) {
    final user = AuthState.instance.currentUser;
    final seller = ['seller', 'admin'].contains(user?.role);
    if (_section == 'shops') return _shop(row);
    if (_section == 'reports') return Card(child: ListTile(title: Text('Báo cáo #${row['id']} · review #${row['review_id']}'), subtitle: Text('${row['reason']} · ${row['status']}\n${row['resolution']?['note'] ?? 'Đang chờ xử lý'}')));
    if (_section == 'notifications') return Card(child: ListTile(title: Text(row['message']), subtitle: Text(row['created_at']), trailing: row['read'] == true ? const Icon(Icons.done_all) : IconButton(icon: const Icon(Icons.mark_email_read_outlined), onPressed: () => _act(() => WorkspaceApi.request('$root/notifications/${row['id']}/read', method: 'PATCH')))));
    if (_section == 'purchases') {
      return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Đơn #${row['id']} · sản phẩm #${row['product_id']}'), Text('Số lượng: ${row['quantity']} · ${row['status']}'),
      if (row['status'] == 'completed' && row['user_id'] == user?.id) TextButton(onPressed: () => _writeReview(row), child: const Text('Viết đánh giá')),
      if (seller && row['status'] == 'pending') Wrap(children: ['completed', 'cancelled'].map((status) => TextButton(onPressed: () => _act(() => WorkspaceApi.request('$root/purchases/${row['id']}', method: 'PATCH', body: {'status': status})), child: Text(status == 'completed' ? 'Xác nhận hoàn tất' : 'Hủy'))).toList()),
    ])));
    }
    if (_section == 'reviews') {
      return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('Review #${row['id']} · sản phẩm #${row['product_id']} · ${row['rating']} sao'), Text(row['content']),
      Text(row['prediction'] == null ? 'Chưa phân tích' : 'P(fake): ${((row['prediction']['fake_probability'] as num) * 100).toStringAsFixed(2)}%'),
      Wrap(children: [TextButton(onPressed: () async { final v = await _form('Sửa review', {'Nội dung': row['content']}); if (v != null && mounted) await _act(() => WorkspaceApi.request('/api/reviews/${row['id']}', method: 'PUT', body: {'content': v['Nội dung']})); }, child: const Text('Sửa')),
        TextButton(onPressed: () async { final ok = await _confirm('Xóa review #${row['id']}?'); if (ok && mounted) await _act(() => WorkspaceApi.request('/api/reviews/${row['id']}', method: 'DELETE')); }, child: const Text('Xóa'))]),
    ])));
    }
    if (_section == 'products') {
      return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(crossAxisAlignment: CrossAxisAlignment.start, children: [
      Text('#${row['id']} ${row['name']}', style: Theme.of(context).textTheme.titleMedium), Text('${row['price']} ₫ · ${row['category'] ?? ''}'),
      Wrap(children: [
        if (row['shop_id'] != user?.id) TextButton(onPressed: () => _act(() => WorkspaceApi.request('$root/purchases', method: 'POST', body: {'product_id': row['id'], 'quantity': 1})), child: const Text('Tạo đơn nội bộ')),
        TextButton(onPressed: () => _act(() => WorkspaceApi.request('$root/products/${row['id']}/watch', method: 'PUT', body: {'useful': true})), child: const Text('Theo dõi cảnh báo')),
        if (seller && (row['shop_id'] == user?.id || user?.role == 'admin')) ...[
          TextButton(onPressed: () => _editProduct(row), child: const Text('Sửa')),
          TextButton(onPressed: () => _editExtra(row), child: const Text('Ảnh / tồn kho')),
          TextButton(onPressed: () async { final ok = await _confirm('Xóa sản phẩm và các review liên quan?'); if (ok && mounted) await _act(() => WorkspaceApi.request('/api/products/${row['id']}', method: 'DELETE')); }, child: const Text('Xóa')),
        ],
      ]),
    ])));
    }
    return Card(child: Padding(padding: const EdgeInsets.all(14), child: Column(children: [Text(user?.email ?? ''), Text(row['display_name'] ?? ''), TextButton(onPressed: () => _editProfile(row), child: const Text('Sửa hồ sơ')),
      TextButton(onPressed: () async { final v = await _form('Đổi mật khẩu', {'Mật khẩu hiện tại': '', 'Mật khẩu mới': ''}, passwords: {'Mật khẩu hiện tại', 'Mật khẩu mới'}); if (v != null && mounted) await _act(() async { await WorkspaceApi.request('$root/password', method: 'POST', body: {'current_password': v['Mật khẩu hiện tại'], 'new_password': v['Mật khẩu mới']}); await AuthState.instance.logout(); }); }, child: const Text('Đổi mật khẩu')),
    ])));
  }

  Future<bool> _confirm(String message) async => await showDialog<bool>(context: context, builder: (ctx) => AlertDialog(title: Text(message), actions: [TextButton(onPressed: () => Navigator.pop(ctx, false), child: const Text('Hủy')), TextButton(onPressed: () => Navigator.pop(ctx, true), child: const Text('Xác nhận'))])) ?? false;

  @override
  Widget build(BuildContext context) {
    final auth = AuthState.instance;
    return Scaffold(appBar: AppBar(title: const Text('Hoạt động & độ uy tín'), actions: [IconButton(onPressed: _busy ? null : _load, icon: const Icon(Icons.refresh))]), body: Column(children: [
      SizedBox(height: 58, child: ListView(scrollDirection: Axis.horizontal, padding: const EdgeInsets.all(8), children: {'shops':'Shop','products':'Sản phẩm','purchases':'Đơn hàng','reviews':'Review của tôi','reports':'Báo cáo','notifications':'Thông báo','profile':'Hồ sơ'}.entries.map((e) => Padding(padding: const EdgeInsets.only(right: 8), child: ChoiceChip(label: Text(e.value), selected: _section == e.key, onSelected: (_) { setState(() { _section = e.key; }); _load(); }))).toList())),
      if (_busy) const LinearProgressIndicator(),
      if (_error != null) Padding(padding: const EdgeInsets.all(12), child: Text(_error!, style: const TextStyle(color: Colors.red))),
      if (!auth.isAuthenticated && _section != 'shops') Padding(padding: const EdgeInsets.all(20), child: FilledButton(onPressed: () => Navigator.push(context, MaterialPageRoute(builder: (_) => const LoginScreen())), child: const Text('Đăng nhập để sử dụng')))
      else Expanded(child: RefreshIndicator(onRefresh: _load, child: ListView(padding: const EdgeInsets.all(12), children: [
        if (_section == 'notifications' && FirebaseService.enabled) OutlinedButton(onPressed: () => _act(FirebaseService.enablePush), child: const Text('Bật thông báo đẩy trên thiết bị này')),
        if (_section == 'products' && ['seller','admin'].contains(auth.currentUser?.role)) FilledButton.icon(onPressed: () => _editProduct(), icon: const Icon(Icons.add), label: const Text('Thêm sản phẩm')),
        if (_rows.isEmpty && !_busy) const Padding(padding: EdgeInsets.all(30), child: Text('Chưa có dữ liệu.')),
        ..._rows.map(_row),
      ]))),
    ]));
  }
}

class _TrustPainter extends CustomPainter {
  final List<dynamic> data;
  _TrustPainter(this.data);
  @override
  void paint(Canvas canvas, Size size) {
    final axis = Paint()..color = Colors.grey.shade300..strokeWidth = 1;
    for (final y in [0.0, .5, 1.0]) { canvas.drawLine(Offset(0, 10 + y * (size.height - 20)), Offset(size.width, 10 + y * (size.height - 20)), axis); }
    final pen = Paint()..color = Colors.red.shade600..strokeWidth = 2;
    Offset? previous;
    for (int i=0; i<data.length; i++) {
      final value = data[i]['fake_percentage'];
      if (value == null) { previous = null; continue; }
      final point = Offset(data.length == 1 ? size.width / 2 : i * size.width / (data.length - 1), size.height - 10 - (value as num).toDouble() / 100 * (size.height - 20));
      if (previous != null) canvas.drawLine(previous, point, pen);
      canvas.drawCircle(point, 4, pen); previous = point;
    }
  }
  @override
  bool shouldRepaint(covariant _TrustPainter oldDelegate) => true;
}
