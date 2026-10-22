import 'package:flutter/foundation.dart';
import 'package:firebase_core/firebase_core.dart';
import 'package:firebase_auth/firebase_auth.dart';
import 'package:firebase_messaging/firebase_messaging.dart';
import 'package:google_sign_in/google_sign_in.dart';
import 'package:flutter_facebook_auth/flutter_facebook_auth.dart';
import 'auth_state.dart';
import 'workspace_api.dart';

class FirebaseService {
  static const enabled = String.fromEnvironment('FIREBASE_API_KEY') != '';
  static bool _googleReady = false;
  static Future<void> ensureInitialized() async {
    if (!enabled) throw Exception('Chưa cấu hình Firebase.');
    if (Firebase.apps.isEmpty) {
      await Firebase.initializeApp(options: const FirebaseOptions(
        apiKey: String.fromEnvironment('FIREBASE_API_KEY'),
        appId: String.fromEnvironment('FIREBASE_APP_ID'),
        messagingSenderId: String.fromEnvironment('FIREBASE_MESSAGING_SENDER_ID'),
        projectId: String.fromEnvironment('FIREBASE_PROJECT_ID'),
        authDomain: String.fromEnvironment('FIREBASE_AUTH_DOMAIN'),
      ));
    }
  }

  static Future<void> accept(UserCredential result) async {
    final token = await result.user?.getIdToken();
    if (token == null) throw Exception('Không lấy được token xác thực.');
    final session = await WorkspaceApi.request('/api/integrations/firebase/login', method: 'POST', body: {'id_token': token});
    await AuthState.instance.acceptExternalToken(session['access_token'] as String);
  }

  static Future<void> google() async {
    await ensureInitialized();
    if (kIsWeb) { await accept(await FirebaseAuth.instance.signInWithPopup(GoogleAuthProvider())); return; }
    if (!_googleReady) {
      const clientId = String.fromEnvironment('GOOGLE_WEB_CLIENT_ID');
      await GoogleSignIn.instance.initialize(serverClientId: clientId.isEmpty ? null : clientId);
      _googleReady = true;
    }
    final account = await GoogleSignIn.instance.authenticate();
    final credential = GoogleAuthProvider.credential(idToken: account.authentication.idToken);
    await accept(await FirebaseAuth.instance.signInWithCredential(credential));
  }

  static Future<void> facebook() async {
    await ensureInitialized();
    if (kIsWeb) { await accept(await FirebaseAuth.instance.signInWithPopup(FacebookAuthProvider())); return; }
    final result = await FacebookAuth.instance.login();
    if (result.status != LoginStatus.success || result.accessToken == null) throw Exception('Đăng nhập Facebook chưa hoàn tất.');
    await accept(await FirebaseAuth.instance.signInWithCredential(FacebookAuthProvider.credential(result.accessToken!.tokenString)));
  }

  static Future<ConfirmationResult> phoneWeb(String phone) async {
    await ensureInitialized();
    return FirebaseAuth.instance.signInWithPhoneNumber(phone);
  }

  static Future<void> enablePush() async {
    await ensureInitialized();
    final permission = await FirebaseMessaging.instance.requestPermission();
    if (permission.authorizationStatus == AuthorizationStatus.denied) throw Exception('Chưa được cấp quyền thông báo.');
    const vapid = String.fromEnvironment('FIREBASE_VAPID_KEY');
    final token = await FirebaseMessaging.instance.getToken(vapidKey: kIsWeb && vapid.isNotEmpty ? vapid : null);
    if (token == null) throw Exception('Chưa lấy được token thiết bị. Kiểm tra cấu hình FCM.');
    await WorkspaceApi.request('/api/integrations/device', method: 'PUT', body: {'token': token});
    await WorkspaceApi.request('/api/integrations/preferences', method: 'PUT', body: {'push_enabled': true});
    FirebaseMessaging.instance.onTokenRefresh.listen((token) {
      if (AuthState.instance.isAuthenticated) WorkspaceApi.request('/api/integrations/device', method: 'PUT', body: {'token': token});
    });
  }
}
