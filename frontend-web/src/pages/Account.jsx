import React, { useState, useEffect } from 'react';
import { 
  User, Shield, Lock, Calendar, Info, Loader2, AlertCircle 
} from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';
import { authApi, api, getRoleLabel } from '../lib/api';

export default function Account() {
  const { user: authUser, loading: authLoading } = useAuth();
  const [currentUser, setCurrentUser] = useState(authUser || null);
  const [loading, setLoading] = useState(!authUser && authLoading);

  // Sync with AuthContext and fetch fresh user info from backend
  useEffect(() => {
    let isMounted = true;

    if (authUser) {
      setCurrentUser(authUser);
    }

    const fetchAccountData = async () => {
      try {
        let userData;
        try {
          userData = await authApi.getMe();
        } catch {
          userData = await api.get('/api/users/me');
        }

        if (isMounted && userData) {
          setCurrentUser(userData);
        }
      } catch {
        // Fall back gracefully to authUser if backend request errors
      } finally {
        if (isMounted) {
          setLoading(false);
        }
      }
    };

    fetchAccountData();

    return () => {
      isMounted = false;
    };
  }, [authUser]);

  // Format date helper
  const formatDate = (dateStr) => {
    if (!dateStr) return '—';
    try {
      const d = new Date(dateStr);
      if (isNaN(d.getTime())) return String(dateStr);
      return d.toLocaleDateString('vi-VN');
    } catch {
      return String(dateStr);
    }
  };

  // Derive role badge styles
  const getRoleBadgeStyle = (r) => {
    const normalized = (r || '').toLowerCase();
    switch (normalized) {
      case 'admin':
        return { backgroundColor: 'rgba(37, 99, 235, 0.12)', color: 'var(--primary)', border: '1px solid rgba(37, 99, 235, 0.25)' };
      case 'seller':
        return { backgroundColor: 'rgba(147, 51, 234, 0.12)', color: '#7E22CE', border: '1px solid rgba(147, 51, 234, 0.25)' };
      case 'engineer':
        return { backgroundColor: 'rgba(13, 148, 136, 0.12)', color: '#0D9488', border: '1px solid rgba(13, 148, 136, 0.25)' };
      default:
        return { backgroundColor: 'var(--border)', color: 'var(--text-main)', border: '1px solid var(--border)' };
    }
  };

  if (loading && !currentUser) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Tài khoản của tôi</h1>
          <p className="page-subtitle">Quản lý thông tin tài khoản và cài đặt bảo mật</p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
            <Loader2 size={36} className="animate-spin text-primary" />
            <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>Đang tải thông tin tài khoản...</p>
          </div>
        </div>
      </div>
    );
  }

  if (!currentUser) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Tài khoản của tôi</h1>
          <p className="page-subtitle">Quản lý thông tin tài khoản và cài đặt bảo mật</p>
        </div>
        <div className="card" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
            <AlertCircle size={36} className="text-danger" />
            <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>Vui lòng đăng nhập để xem thông tin tài khoản.</p>
          </div>
        </div>
      </div>
    );
  }

  const email = currentUser.email || '—';
  const avatarInitials = currentUser.email ? currentUser.email.substring(0, 2).toUpperCase() : 'U';
  const roleText = getRoleLabel(currentUser.role);
  const isActive = currentUser.is_active !== false;
  const statusText = isActive ? 'Đang hoạt động' : 'Đã khóa';
  const createdDateText = formatDate(currentUser.created_at);

  return (
    <div>
      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Tài khoản của tôi</h1>
        <p className="page-subtitle">Quản lý thông tin tài khoản và cài đặt bảo mật</p>
      </div>

      <div className="account-layout">
        {/* Left Column: Profile Summary Card */}
        <div className="card account-profile-card">
          <div className="account-avatar-large">
            {avatarInitials}
          </div>

          <h2 style={{ fontSize: '1.25rem', marginBottom: '6px', wordBreak: 'break-all' }}>
            {email}
          </h2>

          <div style={{ display: 'flex', justifyContent: 'center', gap: 'var(--spacing-2)', marginBottom: 'var(--spacing-4)', flexWrap: 'wrap' }}>
            <span className="badge" style={getRoleBadgeStyle(currentUser.role)}>
              {roleText}
            </span>
            <span className={`badge ${isActive ? 'badge-success' : 'badge-danger'}`}>
              {statusText}
            </span>
          </div>

          <div className="account-info-list">
            <div className="account-info-row">
              <span className="label">Mã tài khoản:</span>
              <span className="value" style={{ fontFamily: 'monospace', color: 'var(--primary)', fontWeight: 600 }}>
                {currentUser.id != null ? `#${currentUser.id}` : '—'}
              </span>
            </div>

            <div className="account-info-row">
              <span className="label">Email:</span>
              <span className="value" style={{ wordBreak: 'break-all' }}>
                {email}
              </span>
            </div>

            <div className="account-info-row">
              <span className="label">Vai trò:</span>
              <span className="value">
                {roleText}
              </span>
            </div>

            <div className="account-info-row">
              <span className="label">Trạng thái:</span>
              <span className="value">
                {statusText}
              </span>
            </div>

            <div className="account-info-row">
              <span className="label">Ngày tạo:</span>
              <span className="value">
                {createdDateText}
              </span>
            </div>
          </div>
        </div>

        {/* Right Column: Account Details & Security */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-6)' }}>
          {/* Section 1: Account Information (Read-only real backend fields) */}
          <div className="card">
            <div className="table-header" style={{ padding: '0 0 var(--spacing-4) 0', borderBottom: '1px solid var(--border)', marginBottom: 'var(--spacing-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}>
                <User size={20} className="text-primary" />
                <h3 style={{ margin: 0, fontSize: '1.125rem' }}>Thông tin tài khoản</h3>
              </div>
            </div>

            <div>
              <div className="grid-2" style={{ marginBottom: 'var(--spacing-4)', gap: 'var(--spacing-4)' }}>
                <div className="form-group">
                  <label className="form-label">
                    Mã tài khoản (ID)
                  </label>
                  <input 
                    type="text" 
                    className="form-input"
                    value={currentUser.id != null ? String(currentUser.id) : ''}
                    readOnly
                    disabled
                    style={{ 
                      backgroundColor: 'var(--background)', 
                      cursor: 'default',
                      color: 'var(--primary)',
                      fontFamily: 'monospace',
                      fontWeight: 600
                    }}
                  />
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Địa chỉ email
                  </label>
                  <input 
                    type="email" 
                    className="form-input"
                    value={email}
                    readOnly
                    disabled
                    style={{ 
                      backgroundColor: 'var(--background)', 
                      cursor: 'default',
                      color: 'var(--text-main)',
                      fontWeight: 500
                    }}
                  />
                </div>
              </div>

              <div className="grid-2" style={{ marginBottom: 'var(--spacing-4)', gap: 'var(--spacing-4)' }}>
                <div className="form-group">
                  <label className="form-label">
                    Vai trò trong hệ thống
                  </label>
                  <div style={{ position: 'relative' }}>
                    <input 
                      type="text" 
                      className="form-input"
                      value={roleText}
                      readOnly
                      disabled
                      style={{ 
                        backgroundColor: 'var(--background)', 
                        cursor: 'default',
                        color: 'var(--text-main)',
                        fontWeight: 500
                      }}
                    />
                    <Lock size={16} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                  </div>
                </div>

                <div className="form-group">
                  <label className="form-label">
                    Trạng thái hoạt động
                  </label>
                  <input 
                    type="text" 
                    className="form-input"
                    value={statusText}
                    readOnly
                    disabled
                    style={{ 
                      backgroundColor: 'var(--background)', 
                      cursor: 'default',
                      color: isActive ? 'var(--success)' : 'var(--danger)',
                      fontWeight: 600
                    }}
                  />
                </div>
              </div>

              <div className="form-group" style={{ marginBottom: 0 }}>
                <label className="form-label">
                  Ngày tạo tài khoản
                </label>
                <div style={{ position: 'relative' }}>
                  <input 
                    type="text" 
                    className="form-input"
                    value={createdDateText}
                    readOnly
                    disabled
                    style={{ 
                      backgroundColor: 'var(--background)', 
                      cursor: 'default',
                      color: 'var(--text-main)'
                    }}
                  />
                  <Calendar size={16} style={{ position: 'absolute', right: '12px', top: '50%', transform: 'translateY(-50%)', color: 'var(--text-secondary)' }} />
                </div>
              </div>

              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-2)',
                padding: 'var(--spacing-3) var(--spacing-4)',
                backgroundColor: 'var(--background)',
                borderRadius: 'var(--radius-md)',
                border: '1px solid var(--border)',
                color: 'var(--text-secondary)',
                fontSize: '0.85rem',
                marginTop: 'var(--spacing-4)'
              }}>
                <Info size={16} style={{ flexShrink: 0, color: 'var(--primary)' }} />
                <span>Thông tin tài khoản được quản lý đồng bộ từ hệ thống. Máy chủ hiện chưa hỗ trợ chỉnh sửa thông tin hồ sơ.</span>
              </div>
            </div>
          </div>

          {/* Section 2: Account Security - Change Password */}
          <div className="card">
            <div className="table-header" style={{ padding: '0 0 var(--spacing-4) 0', borderBottom: '1px solid var(--border)', marginBottom: 'var(--spacing-4)' }}>
              <div style={{ display: 'flex', alignItems: 'center', gap: 'var(--spacing-2)' }}>
                <Shield size={20} className="text-primary" />
                <h3 style={{ margin: 0, fontSize: '1.125rem' }}>Đổi mật khẩu</h3>
              </div>
            </div>

            <div style={{
              display: 'flex',
              alignItems: 'flex-start',
              gap: 'var(--spacing-3)',
              padding: 'var(--spacing-4)',
              backgroundColor: 'var(--background)',
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)'
            }}>
              <Lock size={20} style={{ color: 'var(--text-secondary)', marginTop: '2px', flexShrink: 0 }} />
              <div>
                <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '4px' }}>
                  Backend hiện chưa hỗ trợ đổi mật khẩu.
                </div>
                <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)', lineHeight: 1.5 }}>
                  Hệ thống xác thực chưa cung cấp endpoint API phục vụ tính năng cập nhật mật khẩu trực tiếp.
                </p>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
