import React, { useState } from 'react';
import { useNavigate, Link, useLocation } from 'react-router-dom';
import { ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { formatApiError } from '../lib/api';
import '../styles/dashboard.css';
import ExternalLogin from '../components/ExternalLogin';

export default function Login() {
  const navigate = useNavigate();
  const location = useLocation();
  const { login } = useAuth();

  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [error, setError] = useState(location.state?.error || '');
  const [successMsg, setSuccessMsg] = useState(location.state?.message || '');
  const [loading, setLoading] = useState(false);

  const handleLogin = async (e) => {
    e.preventDefault();
    setError('');
    setSuccessMsg('');
    setLoading(true);

    try {
      await login(email.trim(), password);
      const redirectPath = location.state?.from?.pathname || '/';
      navigate(redirectPath, { replace: true });
    } catch (err) {
      setError(formatApiError(err, 'Đăng nhập không thành công. Vui lòng kiểm tra lại email hoặc mật khẩu.'));
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="auth-layout">
      <div className="auth-card">
        <div className="auth-header">
          <div className="auth-brand">
            <ShieldCheck size={32} strokeWidth={2.5} />
            <span>Fake Review Detection</span>
          </div>
          <h1 className="auth-title">Đăng nhập</h1>
          <p className="auth-subtitle">Đăng nhập để tiếp tục quản lý và phân tích đánh giá</p>
        </div>

        {error && (
          <div style={{
            display: 'flex',
            alignItems: 'center',
            gap: 'var(--spacing-2)',
            backgroundColor: 'rgba(220, 38, 38, 0.1)',
            color: 'var(--danger)',
            padding: 'var(--spacing-3)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--spacing-4)',
            fontSize: '0.875rem',
            fontWeight: 500
          }}>
            <AlertCircle size={18} style={{ flexShrink: 0 }} />
            <span>{error}</span>
          </div>
        )}

        {successMsg && (
          <div style={{
            backgroundColor: 'rgba(22, 163, 74, 0.1)',
            color: 'var(--success)',
            padding: 'var(--spacing-3)',
            borderRadius: 'var(--radius-md)',
            marginBottom: 'var(--spacing-4)',
            fontSize: '0.875rem',
            fontWeight: 500
          }}>
            {successMsg}
          </div>
        )}

        <form onSubmit={handleLogin}>
          <div className="form-group">
            <label className="form-label">Email</label>
            <input 
              required 
              type="email" 
              className="form-input" 
              placeholder="admin@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
              style={{ padding: 'var(--spacing-3)' }}
            />
          </div>
          
          <div className="form-group">
            <div className="flex items-center" style={{ justifyContent: 'space-between' }}>
              <label className="form-label" style={{ marginBottom: 0 }}>Mật khẩu</label>
              <Link to="/forgot-password" className="text-muted" style={{ fontSize: '0.875rem', textDecoration: 'none' }}>Quên mật khẩu?</Link>
            </div>
            <input 
              required 
              type="password" 
              className="form-input" 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
              style={{ padding: 'var(--spacing-3)', marginTop: 'var(--spacing-2)' }}
            />
          </div>

          <div className="form-group flex items-center gap-2">
            <input type="checkbox" id="remember" style={{ accentColor: 'var(--primary)' }} />
            <label htmlFor="remember" style={{ fontSize: '0.875rem', cursor: 'pointer' }}>Ghi nhớ đăng nhập</label>
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading}
            style={{ width: '100%', padding: 'var(--spacing-3)', fontSize: '1rem', marginTop: 'var(--spacing-4)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Đang xử lý...</span>
              </>
            ) : (
              <span>Đăng nhập</span>
            )}
          </button>
        </form>
        <ExternalLogin />

        <div style={{ marginTop: 'var(--spacing-6)', textAlign: 'center' }}>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>
            Chưa có tài khoản? <Link to="/register" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }}>Đăng ký</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
