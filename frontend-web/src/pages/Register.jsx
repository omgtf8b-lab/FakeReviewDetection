import React, { useState } from 'react';
import { useNavigate, Link } from 'react-router-dom';
import { ShieldCheck, AlertCircle, Loader2 } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { formatApiError } from '../lib/api';

export default function Register() {
  const navigate = useNavigate();
  const { register } = useAuth();

  const [fullName, setFullName] = useState('');
  const [email, setEmail] = useState('');
  const [password, setPassword] = useState('');
  const [confirmPassword, setConfirmPassword] = useState('');
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleRegister = async (e) => {
    e.preventDefault();
    setError('');

    if (password.length < 8) {
      setError('Mật khẩu phải có tối thiểu 8 ký tự theo yêu cầu bảo mật.');
      return;
    }

    if (password !== confirmPassword) {
      setError('Mật khẩu xác nhận không khớp.');
      return;
    }

    setLoading(true);
    try {
      // Backend /api/auth/register accepts email and password
      await register(email.trim(), password);
      navigate('/login', { 
        state: { message: 'Tạo tài khoản thành công! Vui lòng đăng nhập với thông tin vừa tạo.' } 
      });
    } catch (err) {
      setError(formatApiError(err, 'Đăng ký không thành công. Vui lòng thử lại.'));
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
          <h1 className="auth-title">Đăng ký</h1>
          <p className="auth-subtitle">Tạo tài khoản để sử dụng hệ thống</p>
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

        <form onSubmit={handleRegister}>
          <div className="form-group">
            <label className="form-label">Họ và tên</label>
            <input 
              type="text" 
              className="form-input" 
              placeholder="Nguyễn Văn A"
              value={fullName}
              onChange={(e) => setFullName(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Email</label>
            <input 
              required 
              type="email" 
              className="form-input" 
              placeholder="user@example.com"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              disabled={loading}
            />
          </div>
          
          <div className="form-group">
            <label className="form-label">Mật khẩu (tối thiểu 8 ký tự)</label>
            <input 
              required 
              type="password" 
              className="form-input" 
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              disabled={loading}
            />
          </div>

          <div className="form-group">
            <label className="form-label">Xác nhận mật khẩu</label>
            <input 
              required 
              type="password" 
              className="form-input" 
              placeholder="••••••••"
              value={confirmPassword}
              onChange={(e) => {
                setConfirmPassword(e.target.value);
                if (error) setError('');
              }}
              disabled={loading}
            />
          </div>

          <button 
            type="submit" 
            className="btn btn-primary" 
            disabled={loading}
            style={{ width: '100%', padding: 'var(--spacing-3)', fontSize: '1rem', marginTop: 'var(--spacing-6)', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '8px' }}
          >
            {loading ? (
              <>
                <Loader2 size={18} className="animate-spin" />
                <span>Đang tạo tài khoản...</span>
              </>
            ) : (
              <span>Tạo tài khoản</span>
            )}
          </button>
        </form>

        <div style={{ marginTop: 'var(--spacing-6)', textAlign: 'center' }}>
          <p className="text-muted" style={{ fontSize: '0.875rem' }}>
            Đã có tài khoản? <Link to="/login" style={{ color: 'var(--primary)', fontWeight: 600, textDecoration: 'none' }}>Đăng nhập</Link>
          </p>
        </div>
      </div>
    </div>
  );
}
