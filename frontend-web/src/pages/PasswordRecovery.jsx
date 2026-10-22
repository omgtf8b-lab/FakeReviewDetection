import React, { useState } from 'react';
import { Link, useSearchParams } from 'react-router-dom';
import { api } from '../lib/api';

export default function PasswordRecovery() {
  const [params] = useSearchParams();
  const token = params.get('token');
  const [value, setValue] = useState('');
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState('');
  async function submit(e) {
    e.preventDefault(); setBusy(true); setMessage('');
    try { const result = await api.post('/api/workspace/' + (token ? 'reset-password' : 'forgot-password'), token ? { token, new_password: value } : { email: value }); setMessage(result.message); }
    catch (err) { setMessage(err.message); } finally { setBusy(false); }
  }
  return <main style={{ maxWidth: 480, margin: '10vh auto', padding: 28 }} className="card"><h1>{token ? 'Đặt lại mật khẩu' : 'Khôi phục tài khoản'}</h1><form onSubmit={submit}><label className="form-label">{token ? 'Mật khẩu mới (ít nhất 8 ký tự)' : 'Email đăng ký'}<input className="form-input" required minLength={token ? 8 : undefined} type={token ? 'password' : 'email'} value={value} onChange={e => setValue(e.target.value)} /></label><button className="btn btn-primary" disabled={busy}>{busy ? 'Đang xử lý…' : 'Gửi yêu cầu'}</button></form><p role="status">{message}</p><Link to="/login">Quay lại đăng nhập</Link></main>;
}
