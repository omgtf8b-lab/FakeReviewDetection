import React, { useState } from 'react';
import { api, setAccessToken, setCurrentUser } from '../lib/api';

export default function ExternalLogin() {
  const [error, setError] = useState('');
  const [busy, setBusy] = useState(false);
  const [phone, setPhone] = useState('');
  const [otp, setOtp] = useState('');
  const [confirmation, setConfirmation] = useState(null);
  const configured = !!import.meta.env.VITE_FIREBASE_API_KEY;
  async function sdk() {
    const app = await import('firebase/app');
    const auth = await import('firebase/auth');
    const config = { apiKey: import.meta.env.VITE_FIREBASE_API_KEY, authDomain: import.meta.env.VITE_FIREBASE_AUTH_DOMAIN, projectId: import.meta.env.VITE_FIREBASE_PROJECT_ID, appId: import.meta.env.VITE_FIREBASE_APP_ID };
    return { auth: auth.getAuth(app.getApps().length ? app.getApp() : app.initializeApp(config)), sdk: auth };
  }
  async function accept(firebaseUser) {
    const result = await api.post('/api/integrations/firebase/login', { id_token: await firebaseUser.getIdToken() });
    setAccessToken(result.access_token); setCurrentUser(result.user); window.location.assign('/');
  }
  async function social(provider) {
    setBusy(true); setError('');
    try { const { auth, sdk: s } = await sdk(); const result = await s.signInWithPopup(auth, provider === 'google' ? new s.GoogleAuthProvider() : new s.FacebookAuthProvider()); await accept(result.user); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function sendOtp() {
    setBusy(true); setError('');
    try { const { auth, sdk: s } = await sdk(); const verifier = new s.RecaptchaVerifier(auth, 'phone-captcha', { size: 'normal' }); setConfirmation(await s.signInWithPhoneNumber(auth, phone, verifier)); }
    catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  async function confirmOtp() {
    setBusy(true); setError('');
    try { await accept((await confirmation.confirm(otp)).user); } catch (e) { setError(e.message); } finally { setBusy(false); }
  }
  if (!configured) return null;
  return <section style={{ marginTop: 20 }}><p>Hoặc đăng nhập với</p><div style={{ display: 'flex', gap: 10 }}><button type="button" className="btn btn-outline" disabled={busy} onClick={() => social('google')}>Google</button><button type="button" className="btn btn-outline" disabled={busy} onClick={() => social('facebook')}>Facebook</button></div><label>Số điện thoại quốc tế<input type="tel" className="form-input" placeholder="+84…" value={phone} onChange={e => setPhone(e.target.value)} /></label><div id="phone-captcha" /><button type="button" className="btn btn-outline" disabled={busy} onClick={sendOtp}>Gửi mã OTP</button>{confirmation && <><input className="form-input" aria-label="Mã OTP" value={otp} onChange={e => setOtp(e.target.value)} /><button type="button" className="btn btn-primary" disabled={busy} onClick={confirmOtp}>Xác nhận OTP</button></>}{error && <p role="alert">{error}</p>}</section>;
}
