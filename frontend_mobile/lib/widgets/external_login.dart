import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:firebase_auth/firebase_auth.dart';
import '../services/firebase_service.dart';
import '../services/workspace_api.dart';
import '../services/auth_state.dart';

class ExternalLogin extends StatefulWidget {
  const ExternalLogin({super.key});
  @override
  State<ExternalLogin> createState() => _ExternalLoginState();
}

class _ExternalLoginState extends State<ExternalLogin> {
  final phone = TextEditingController();
  final otp = TextEditingController();
  bool busy = false;
  String? error;
  String? verificationId;
  ConfirmationResult? confirmation;
  @override
  void dispose() { phone.dispose(); otp.dispose(); super.dispose(); }
  Future<void> run(Future<void> Function() task) async {
    setState(() { busy = true; error = null; });
    try {
      await task();
      if (mounted && AuthState.instance.isAuthenticated) Navigator.maybePop(context);
    }
    catch (e) { if (mounted) setState(() { error = e.toString(); }); }
    finally { if (mounted) setState(() { busy = false; }); }
  }
  Future<void> send() async {
    await FirebaseService.ensureInitialized();
    if (kIsWeb) {
      final result = await FirebaseService.phoneWeb(phone.text.trim());
      if (mounted) setState(() { confirmation = result; });
    } else {
      await FirebaseAuth.instance.verifyPhoneNumber(phoneNumber: phone.text.trim(),
        verificationCompleted: (credential) async { await FirebaseService.accept(await FirebaseAuth.instance.signInWithCredential(credential)); },
        verificationFailed: (e) { if (mounted) setState(() { error = e.message; }); },
        codeSent: (id, _) { if (mounted) setState(() { verificationId = id; }); },
        codeAutoRetrievalTimeout: (id) { if (mounted) setState(() { verificationId = id; }); });
    }
  }
  Future<void> forgot() async {
    final controller = TextEditingController();
    final email = await showDialog<String>(context: context, builder: (ctx) => AlertDialog(title: const Text('Khôi phục mật khẩu'), content: TextField(controller: controller, decoration: const InputDecoration(labelText: 'Email')), actions: [TextButton(onPressed: () => Navigator.pop(ctx), child: const Text('Hủy')), FilledButton(onPressed: () => Navigator.pop(ctx, controller.text.trim()), child: const Text('Gửi'))]));
    if (email == null) return;
    await WorkspaceApi.request('/api/workspace/forgot-password', method: 'POST', body: {'email': email});
    if (mounted) ScaffoldMessenger.of(context).showSnackBar(const SnackBar(content: Text('Nếu email hợp lệ, hướng dẫn đã được đưa vào hàng đợi gửi.')));
  }
  @override
  Widget build(BuildContext context) => Column(children: [
    TextButton(onPressed: busy ? null : () => run(forgot), child: const Text('Quên mật khẩu?')),
    if (FirebaseService.enabled) ...[
      Wrap(spacing: 12, children: [OutlinedButton(onPressed: busy ? null : () => run(FirebaseService.google), child: const Text('Google')), OutlinedButton(onPressed: busy ? null : () => run(FirebaseService.facebook), child: const Text('Facebook'))]),
      TextField(controller: phone, keyboardType: TextInputType.phone, decoration: const InputDecoration(labelText: 'Điện thoại quốc tế (+84…)')),
      TextButton(onPressed: busy ? null : () => run(send), child: const Text('Gửi OTP')),
      if (confirmation != null || verificationId != null) ...[
        TextField(controller: otp, keyboardType: TextInputType.number, decoration: const InputDecoration(labelText: 'Mã OTP')),
        FilledButton(onPressed: busy ? null : () => run(() async { final result = confirmation != null ? await confirmation!.confirm(otp.text) : await FirebaseAuth.instance.signInWithCredential(PhoneAuthProvider.credential(verificationId: verificationId!, smsCode: otp.text)); await FirebaseService.accept(result); }), child: const Text('Xác nhận OTP')),
      ],
    ],
    if (busy) const LinearProgressIndicator(),
    if (error != null) Text(error!, style: const TextStyle(color: Colors.red)),
  ]);
}
