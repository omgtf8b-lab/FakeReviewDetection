import React, { useState, useMemo, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, Eye, Edit, Lock, Unlock, Users as UsersIcon, 
  UserCheck, UserX, Shield, ShieldAlert, X, CheckCircle2, 
  ChevronLeft, ChevronRight, RotateCcw, Mail, Calendar, 
  AlertCircle, Loader2, Plus, Info, ShieldCheck
} from 'lucide-react';
import { 
  userApi, 
  formatApiError, 
  getRoleLabel 
} from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function Users() {
  const navigate = useNavigate();
  const { user: currentUser } = useAuth();

  const isAdmin = (currentUser?.role || '').toLowerCase() === 'admin';

  // Primary data state (Real API)
  const [users, setUsers] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState('');

  // Filters state
  const [searchTerm, setSearchTerm] = useState('');
  const [roleFilter, setRoleFilter] = useState('All');
  const [statusFilter, setStatusFilter] = useState('All');
  const [sortBy, setSortBy] = useState('id-desc');

  // Pagination state (Client-side)
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Modals state
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [isRoleModalOpen, setIsRoleModalOpen] = useState(false);
  const [isLockModalOpen, setIsLockModalOpen] = useState(false);

  // Selected user and action data
  const [selectedUser, setSelectedUser] = useState(null);
  const [newRole, setNewRole] = useState('buyer');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [modalError, setModalError] = useState('');
  const [toastMessage, setToastMessage] = useState('');

  // Toast auto-dismiss
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(''), 3500);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // Prevent background scrolling when any modal is open
  useEffect(() => {
    const isAnyModalOpen = isDetailModalOpen || isRoleModalOpen || isLockModalOpen;
    if (isAnyModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isDetailModalOpen, isRoleModalOpen, isLockModalOpen]);

  // ==========================================
  // FETCH USERS (ADMIN ONLY: GET /api/users)
  // ==========================================
  const fetchUsers = useCallback(async () => {
    if (!isAdmin) {
      setLoading(false);
      return;
    }

    setLoading(true);
    setApiError('');
    try {
      const data = await userApi.getUsers();
      setUsers(Array.isArray(data) ? data : []);
    } catch (err) {
      setUsers([]);
      if (err.status === 401) {
        setApiError('Phiên đăng nhập đã hết hạn.');
      } else if (err.status === 403) {
        setApiError('Bạn không có quyền quản lý người dùng.');
      } else if (err.message && err.message.includes('fetch')) {
        setApiError('Không thể kết nối đến máy chủ.');
      } else {
        setApiError(formatApiError(err, 'Không thể tải danh sách người dùng.'));
      }
    } finally {
      setLoading(false);
    }
  }, [isAdmin]);

  useEffect(() => {
    fetchUsers();
  }, [fetchUsers]);

  // Dynamic statistics calculated directly from real users
  const totalUsers = users.length;
  const activeUsers = users.filter((u) => u.is_active === true).length;
  const lockedUsers = users.filter((u) => u.is_active === false).length;
  const adminCount = users.filter((u) => (u.role || '').toLowerCase() === 'admin').length;

  // Filter and sort users locally
  const filteredUsers = useMemo(() => {
    return users
      .filter((u) => {
        const query = searchTerm.toLowerCase().trim();
        const emailMatch = (u.email || '').toLowerCase().includes(query);
        const idMatch = String(u.id).includes(query);
        const roleLabelMatch = getRoleLabel(u.role).toLowerCase().includes(query);
        const roleValMatch = (u.role || '').toLowerCase().includes(query);

        const matchesSearch = !query || emailMatch || idMatch || roleLabelMatch || roleValMatch;

        const matchesRole = 
          roleFilter === 'All' || 
          (u.role || '').toLowerCase() === roleFilter.toLowerCase();

        let matchesStatus = true;
        if (statusFilter === 'active') matchesStatus = u.is_active === true;
        if (statusFilter === 'locked') matchesStatus = u.is_active === false;

        return matchesSearch && matchesRole && matchesStatus;
      })
      .sort((a, b) => {
        if (sortBy === 'email-asc') {
          return (a.email || '').localeCompare(b.email || '');
        }
        if (sortBy === 'email-desc') {
          return (b.email || '').localeCompare(a.email || '');
        }
        if (sortBy === 'id-asc') {
          return a.id - b.id;
        }
        // default newest (id-desc)
        return b.id - a.id;
      });
  }, [users, searchTerm, roleFilter, statusFilter, sortBy]);

  // Pagination calculation
  const totalPages = Math.ceil(filteredUsers.length / pageSize) || 1;
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const paginatedUsers = useMemo(() => {
    const startIndex = (safeCurrentPage - 1) * pageSize;
    return filteredUsers.slice(startIndex, startIndex + pageSize);
  }, [filteredUsers, safeCurrentPage, pageSize]);

  // Role Badge Styling Helper
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

  const handleResetFilters = () => {
    setSearchTerm('');
    setRoleFilter('All');
    setStatusFilter('All');
    setSortBy('id-desc');
    setCurrentPage(1);
  };

  // ==========================================
  // MODAL HANDLERS
  // ==========================================
  const handleOpenDetail = (targetUser) => {
    setSelectedUser(targetUser);
    setIsDetailModalOpen(true);
  };

  const handleOpenRole = (targetUser) => {
    if (targetUser.id === currentUser?.id) {
      alert('Không thể thay đổi vai trò của tài khoản đang đăng nhập từ giao diện này.');
      return;
    }
    setSelectedUser(targetUser);
    setNewRole((targetUser.role || 'buyer').toLowerCase());
    setModalError('');
    setIsRoleModalOpen(true);
  };

  const handleOpenLock = (targetUser) => {
    if (targetUser.id === currentUser?.id) {
      alert('Không thể tự khóa tài khoản đang đăng nhập.');
      return;
    }
    setSelectedUser(targetUser);
    setModalError('');
    setIsLockModalOpen(true);
  };

  // ==========================================
  // CHANGE ROLE (PATCH /api/admin/users/{id}/role)
  // ==========================================
  const handleRoleSubmit = async (e) => {
    e.preventDefault();
    if (!selectedUser) return;
    if (selectedUser.id === currentUser?.id) {
      setModalError('Không thể thay đổi vai trò của tài khoản đang đăng nhập từ giao diện này.');
      return;
    }

    setIsSubmitting(true);
    setModalError('');

    try {
      await userApi.changeRole(selectedUser.id, newRole);
      setIsRoleModalOpen(false);
      setToastMessage(`Đã cập nhật vai trò người dùng thành "${getRoleLabel(newRole)}".`);
      fetchUsers();
    } catch (err) {
      setModalError(formatApiError(err, 'Không thể thay đổi vai trò người dùng.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // ==========================================
  // LOCK / UNLOCK (PATCH /api/users/{id}/status?is_active=bool)
  // ==========================================
  const handleConfirmLockToggle = async () => {
    if (!selectedUser) return;
    if (selectedUser.id === currentUser?.id) {
      setModalError('Không thể tự khóa tài khoản đang đăng nhập.');
      return;
    }

    const nextStatus = !selectedUser.is_active;
    setIsSubmitting(true);
    setModalError('');

    try {
      await userApi.changeStatus(selectedUser.id, nextStatus);
      setIsLockModalOpen(false);
      setToastMessage(nextStatus ? 'Đã mở khóa tài khoản.' : 'Đã khóa tài khoản.');
      fetchUsers();
    } catch (err) {
      if (err.status === 400) {
        setModalError(formatApiError(err, 'Không thể thực hiện thao tác trên tài khoản này.'));
      } else {
        setModalError(formatApiError(err, 'Không thể cập nhật trạng thái tài khoản.'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ==========================================
  // ACCESS DENIED VIEW FOR NON-ADMIN
  // ==========================================
  if (!isAdmin) {
    return (
      <div>
        <div className="page-header">
          <h1 className="page-title">Quản lý người dùng</h1>
          <p className="page-subtitle">Khu vực dành riêng cho Quản trị viên</p>
        </div>

        <div className="card" style={{ textAlign: 'center', padding: 'var(--spacing-12)', marginTop: 'var(--spacing-6)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
            <ShieldAlert size={56} className="text-danger" opacity={0.8} />
            <h2 style={{ fontSize: '1.35rem', margin: 0, color: 'var(--text-main)' }}>
              Truy cập bị từ chối
            </h2>
            <p className="text-muted" style={{ margin: 0, fontSize: '1rem', maxWidth: '440px', lineHeight: 1.5 }}>
              Bạn không có quyền quản lý người dùng.
            </p>
            <button 
              className="btn btn-primary" 
              onClick={() => navigate('/')} 
              style={{ marginTop: 'var(--spacing-2)' }}
            >
              Quay lại trang chủ
            </button>
          </div>
        </div>
      </div>
    );
  }

  return (
    <div>
      {/* Toast Notification */}
      {toastMessage && (
        <div className="alert-toast">
          <CheckCircle2 size={18} className="text-success" />
          <span>{toastMessage}</span>
          <button 
            onClick={() => setToastMessage('')} 
            style={{ background: 'none', border: 'none', color: '#94A3B8', cursor: 'pointer', padding: 0 }}
            aria-label="Đóng thông báo"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Quản lý người dùng</h1>
        <p className="page-subtitle">Quản lý tài khoản, phân quyền vai trò và trạng thái hoạt động trong hệ thống</p>
      </div>

      {/* 4 Summary Cards */}
      <div className="grid-4">
        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Tổng người dùng</h3>
            <div className="kpi-icon primary"><UsersIcon size={20} /></div>
          </div>
          <p className="kpi-value">{loading ? '...' : totalUsers}</p>
          <p className="kpi-footer">Tất cả tài khoản trong hệ thống</p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đang hoạt động</h3>
            <div className="kpi-icon success"><UserCheck size={20} /></div>
          </div>
          <p className="kpi-value">{loading ? '...' : activeUsers}</p>
          <p className="kpi-footer">
            <span className="text-success">{Math.round((activeUsers / (totalUsers || 1)) * 100)}%</span> tỷ lệ đang hoạt động
          </p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đã khóa</h3>
            <div className="kpi-icon danger"><UserX size={20} /></div>
          </div>
          <p className="kpi-value">{loading ? '...' : lockedUsers}</p>
          <p className="kpi-footer">Tài khoản tạm dừng truy cập</p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Quản trị viên</h3>
            <div className="kpi-icon neutral" style={{ backgroundColor: 'rgba(37, 99, 235, 0.1)', color: 'var(--primary)' }}>
              <Shield size={20} />
            </div>
          </div>
          <p className="kpi-value">{loading ? '...' : adminCount}</p>
          <p className="kpi-footer">Có toàn quyền quản trị</p>
        </div>
      </div>

      {/* Search & Filter Toolbar */}
      <div className="card" style={{ marginBottom: 'var(--spacing-6)', padding: 'var(--spacing-4)' }}>
        <div className="flex items-center" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-4)' }}>
          
          <div className="flex items-center" style={{ gap: 'var(--spacing-3)', flex: 1, minWidth: '320px', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div className="search-wrapper" style={{ flex: 1, minWidth: '240px', maxWidth: '380px' }}>
              <Search className="search-icon" size={18} />
              <input 
                type="text" 
                className="search-input" 
                placeholder="Tìm email, mã ID, vai trò..." 
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                style={{ width: '100%' }}
                aria-label="Tìm kiếm người dùng"
              />
              {searchTerm && (
                <button 
                  onClick={() => {
                    setSearchTerm('');
                    setCurrentPage(1);
                  }} 
                  style={{ position: 'absolute', right: '10px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                  title="Xóa tìm kiếm"
                  aria-label="Xóa tìm kiếm"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Role Filter */}
            <select 
              className="form-input"
              value={roleFilter}
              onChange={(e) => {
                setRoleFilter(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: '190px' }}
              aria-label="Lọc theo vai trò"
            >
              <option value="All">Tất cả vai trò</option>
              <option value="buyer">Người dùng (buyer)</option>
              <option value="seller">Người bán (seller)</option>
              <option value="admin">Quản trị viên (admin)</option>
              <option value="engineer">Kỹ thuật viên (engineer)</option>
            </select>

            {/* Status Filter */}
            <select 
              className="form-input"
              value={statusFilter}
              onChange={(e) => {
                setStatusFilter(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: '170px' }}
              aria-label="Lọc theo trạng thái"
            >
              <option value="All">Tất cả trạng thái</option>
              <option value="active">Đang hoạt động</option>
              <option value="locked">Đã khóa</option>
            </select>

            {/* Sort */}
            <select 
              className="form-input"
              value={sortBy}
              onChange={(e) => setSortBy(e.target.value)}
              style={{ width: '170px' }}
              aria-label="Sắp xếp danh sách"
            >
              <option value="id-desc">Mới nhất (ID giảm)</option>
              <option value="id-asc">Cũ nhất (ID tăng)</option>
              <option value="email-asc">Email (A-Z)</option>
              <option value="email-desc">Email (Z-A)</option>
            </select>

            {/* Reset Filters */}
            {(searchTerm || roleFilter !== 'All' || statusFilter !== 'All' || sortBy !== 'id-desc') && (
              <button 
                className="btn btn-outline" 
                onClick={handleResetFilters} 
                style={{ padding: 'var(--spacing-2) var(--spacing-3)' }}
                title="Khôi phục bộ lọc mặc định"
              >
                <RotateCcw size={15} />
                <span>Đặt lại</span>
              </button>
            )}
          </div>

          {/* Add User Button (Disabled per Requirement 16) */}
          <div title="Backend hiện chưa hỗ trợ quản trị viên tạo người dùng.">
            <button 
              className="btn btn-outline" 
              disabled
              style={{ opacity: 0.65, cursor: 'not-allowed' }}
              aria-disabled="true"
            >
              <Plus size={18} />
              <span>Thêm người dùng</span>
            </button>
          </div>
        </div>
      </div>

      {/* User Data Table */}
      <div className="table-wrapper">
        <div className="table-header flex items-center" style={{ justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0 }}>Danh sách người dùng ({filteredUsers.length})</h3>
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Hiển thị mỗi trang:</span>
            <select 
              className="form-input" 
              value={pageSize} 
              onChange={(e) => {
                setPageSize(Number(e.target.value));
                setCurrentPage(1);
              }}
              style={{ width: '70px', padding: '4px 8px' }}
              aria-label="Số dòng mỗi trang"
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th style={{ width: '90px' }}>Mã ID</th>
                <th>Email tài khoản</th>
                <th style={{ width: '170px' }}>Vai trò</th>
                <th style={{ width: '150px' }}>Trạng thái</th>
                <th style={{ width: '150px' }}>Ngày tạo</th>
                <th style={{ textAlign: 'right', width: '140px' }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <Loader2 size={36} className="animate-spin text-primary" />
                      <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>Đang tải danh sách người dùng...</p>
                    </div>
                  </td>
                </tr>
              ) : apiError ? (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <AlertCircle size={40} className="text-danger" />
                      <p style={{ margin: 0, fontWeight: 600, color: 'var(--danger)' }}>{apiError}</p>
                      <button className="btn btn-outline" onClick={fetchUsers} style={{ marginTop: 'var(--spacing-2)' }}>
                        <RotateCcw size={16} /> Thử lại
                      </button>
                    </div>
                  </td>
                </tr>
              ) : paginatedUsers.length > 0 ? (
                paginatedUsers.map((item) => {
                  const isSelf = item.id === currentUser?.id;
                  const initialChar = item.email ? item.email.charAt(0).toUpperCase() : 'U';

                  return (
                    <tr key={item.id}>
                      <td>
                        <span style={{ fontWeight: 600, fontFamily: 'monospace', color: 'var(--primary)' }}>
                          #{item.id}
                        </span>
                      </td>
                      <td>
                        <div className="flex items-center gap-3">
                          <div style={{
                            width: '34px',
                            height: '34px',
                            borderRadius: '50%',
                            backgroundColor: (item.role || '').toLowerCase() === 'admin' 
                              ? 'rgba(37, 99, 235, 0.12)' 
                              : (item.role || '').toLowerCase() === 'seller'
                                ? 'rgba(147, 51, 234, 0.12)'
                                : 'rgba(100, 116, 139, 0.12)',
                            color: (item.role || '').toLowerCase() === 'admin' 
                              ? 'var(--primary)' 
                              : (item.role || '').toLowerCase() === 'seller'
                                ? '#7E22CE'
                                : 'var(--text-main)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontWeight: 600,
                            fontSize: '0.85rem',
                            flexShrink: 0
                          }}>
                            {initialChar}
                          </div>
                          <div>
                            <div style={{ fontWeight: 500, color: 'var(--text-main)' }}>
                              {item.email}
                            </div>
                            {isSelf && (
                              <span style={{ fontSize: '0.7rem', color: 'var(--primary)', fontWeight: 600 }}>
                                (Tài khoản đang đăng nhập)
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td>
                        <span className="badge" style={getRoleBadgeStyle(item.role)}>
                          {getRoleLabel(item.role)}
                        </span>
                      </td>
                      <td>
                        <span className={`badge ${item.is_active ? 'badge-success' : 'badge-danger'}`}>
                          {item.is_active ? 'Đang hoạt động' : 'Đã khóa'}
                        </span>
                      </td>
                      <td>
                        <span style={{ color: 'var(--text-secondary)', fontSize: '0.85rem' }}>
                          {item.created_at ? new Date(item.created_at).toLocaleDateString('vi-VN') : '—'}
                        </span>
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div className="flex items-center" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-1)' }}>
                          {/* View detail */}
                          <button 
                            className="btn-icon" 
                            title="Xem chi tiết" 
                            onClick={() => handleOpenDetail(item)}
                            aria-label={`Xem chi tiết ${item.email}`}
                          >
                            <Eye size={17} />
                          </button>

                          {/* Change role */}
                          {isSelf ? (
                            <button 
                              className="btn-icon" 
                              disabled
                              style={{ opacity: 0.35, cursor: 'not-allowed' }}
                              title="Không thể thay đổi vai trò của tài khoản đang đăng nhập từ giao diện này."
                              aria-disabled="true"
                            >
                              <Edit size={17} />
                            </button>
                          ) : (
                            <button 
                              className="btn-icon" 
                              title="Đổi vai trò người dùng" 
                              onClick={() => handleOpenRole(item)}
                              aria-label={`Đổi vai trò ${item.email}`}
                            >
                              <Edit size={17} />
                            </button>
                          )}

                          {/* Lock / Unlock */}
                          {isSelf ? (
                            <button 
                              className="btn-icon" 
                              disabled
                              style={{ opacity: 0.35, cursor: 'not-allowed' }}
                              title="Không thể tự khóa tài khoản đang đăng nhập."
                              aria-disabled="true"
                            >
                              <Lock size={17} />
                            </button>
                          ) : (
                            <button 
                              className={`btn-icon ${item.is_active ? 'danger' : ''}`}
                              title={item.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'} 
                              onClick={() => handleOpenLock(item)}
                              aria-label={item.is_active ? `Khóa ${item.email}` : `Mở khóa ${item.email}`}
                            >
                              {item.is_active ? (
                                <Lock size={17} />
                              ) : (
                                <Unlock size={17} style={{ color: 'var(--success)' }} />
                              )}
                            </button>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="6" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <UsersIcon size={48} className="text-muted" opacity={0.35} />
                      <p style={{ margin: 0, fontWeight: 600, fontSize: '1rem', color: 'var(--text-main)' }}>
                        Không tìm thấy người dùng
                      </p>
                      <p className="text-muted" style={{ margin: 0, fontSize: '0.875rem' }}>
                        Thử thay đổi từ khóa hoặc bộ lọc.
                      </p>
                      <button className="btn btn-outline" onClick={handleResetFilters} style={{ marginTop: 'var(--spacing-2)' }}>
                        <RotateCcw size={15} /> Đặt lại bộ lọc
                      </button>
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Pagination Section */}
        {!loading && filteredUsers.length > 0 && (
          <div className="pagination-container">
            <div className="pagination-info">
              Hiển thị <strong>{(safeCurrentPage - 1) * pageSize + 1}</strong> - <strong>{Math.min(safeCurrentPage * pageSize, filteredUsers.length)}</strong> trên tổng số <strong>{filteredUsers.length}</strong> người dùng
            </div>

            <div className="pagination-controls">
              <button 
                className="page-btn" 
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={safeCurrentPage === 1}
                title="Trang trước"
                aria-label="Trang trước"
              >
                <ChevronLeft size={16} />
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNumber) => (
                <button
                  key={pageNumber}
                  className={`page-btn ${pageNumber === safeCurrentPage ? 'active' : ''}`}
                  onClick={() => setCurrentPage(pageNumber)}
                  aria-label={`Trang ${pageNumber}`}
                  aria-current={pageNumber === safeCurrentPage ? 'page' : undefined}
                >
                  {pageNumber}
                </button>
              ))}

              <button 
                className="page-btn" 
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                disabled={safeCurrentPage === totalPages}
                title="Trang tiếp"
                aria-label="Trang tiếp"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ==========================================
          MODAL: USER DETAIL (REAL FIELDS ONLY)
          ========================================== */}
      {isDetailModalOpen && selectedUser && (
        <div className="modal-overlay" onClick={() => setIsDetailModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Chi tiết người dùng #{selectedUser.id}</h3>
              <button className="modal-close" onClick={() => setIsDetailModalOpen(false)} aria-label="Đóng">
                <X size={20} />
              </button>
            </div>

            <div className="modal-body">
              {/* Profile Card Summary */}
              <div style={{
                display: 'flex',
                alignItems: 'center',
                gap: 'var(--spacing-4)',
                padding: 'var(--spacing-4)',
                backgroundColor: 'var(--background)',
                borderRadius: 'var(--radius-lg)',
                marginBottom: 'var(--spacing-4)'
              }}>
                <div style={{
                  width: '52px',
                  height: '52px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(37, 99, 235, 0.12)',
                  color: 'var(--primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontSize: '1.25rem',
                  fontWeight: 700
                }}>
                  {selectedUser.email ? selectedUser.email.charAt(0).toUpperCase() : 'U'}
                </div>
                <div style={{ flex: 1, minWidth: 0 }}>
                  <div style={{ fontWeight: 600, fontSize: '1rem', color: 'var(--text-main)', marginBottom: '4px', wordBreak: 'break-all' }}>
                    {selectedUser.email}
                  </div>
                  <div className="flex items-center gap-2">
                    <span className="badge" style={getRoleBadgeStyle(selectedUser.role)}>
                      {getRoleLabel(selectedUser.role)}
                    </span>
                    <span className={`badge ${selectedUser.is_active ? 'badge-success' : 'badge-danger'}`}>
                      {selectedUser.is_active ? 'Đang hoạt động' : 'Đã khóa'}
                    </span>
                  </div>
                </div>
              </div>

              {/* Supported Information Grid */}
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Mã tài khoản</span>
                  <span className="detail-value" style={{ fontFamily: 'monospace', fontWeight: 600, color: 'var(--primary)' }}>
                    #{selectedUser.id}
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Ngày tạo tài khoản</span>
                  <span className="detail-value flex items-center gap-1">
                    <Calendar size={14} className="text-muted" />
                    {selectedUser.created_at ? new Date(selectedUser.created_at).toLocaleDateString('vi-VN') : '—'}
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Vai trò trong hệ thống</span>
                  <span className="detail-value">
                    {getRoleLabel(selectedUser.role)} (<code>{selectedUser.role}</code>)
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Trạng thái đăng nhập</span>
                  <span className="detail-value">
                    {selectedUser.is_active ? 'Được phép đăng nhập' : 'Bị tạm dừng đăng nhập'}
                  </span>
                </div>
              </div>

              <div style={{ 
                marginTop: 'var(--spacing-3)', 
                padding: 'var(--spacing-3)', 
                backgroundColor: 'var(--background)', 
                borderRadius: 'var(--radius-sm)',
                fontSize: '0.75rem',
                color: 'var(--text-secondary)',
                display: 'flex',
                alignItems: 'center',
                gap: '8px'
              }}>
                <Info size={16} style={{ flexShrink: 0 }} />
                <span>Backend hiện quản lý thông tin bảo mật tối giản: chỉ gồm Email, Vai trò và Trạng thái hoạt động.</span>
              </div>
            </div>

            <div className="modal-footer" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-2)' }}>
              {selectedUser.id !== currentUser?.id && (
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  onClick={() => {
                    setIsDetailModalOpen(false);
                    handleOpenRole(selectedUser);
                  }}
                >
                  <Edit size={16} />
                  <span>Đổi vai trò</span>
                </button>
              )}
              <button type="button" className="btn btn-primary" onClick={() => setIsDetailModalOpen(false)}>
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL: CHANGE ROLE (PATCH /api/admin/users/{id}/role)
          ========================================== */}
      {isRoleModalOpen && selectedUser && (
        <div className="modal-overlay" onClick={() => !isSubmitting && setIsRoleModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '460px' }}>
            <div className="modal-header">
              <h3 className="modal-title">Cập nhật quyền người dùng</h3>
              <button 
                className="modal-close" 
                onClick={() => !isSubmitting && setIsRoleModalOpen(false)} 
                aria-label="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleRoleSubmit}>
              <div className="modal-body">
                {modalError && (
                  <div style={{
                    backgroundColor: 'rgba(220, 38, 38, 0.1)',
                    border: '1px solid rgba(220, 38, 38, 0.3)',
                    color: 'var(--danger)',
                    padding: 'var(--spacing-3)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.875rem',
                    marginBottom: 'var(--spacing-4)',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '8px'
                  }}>
                    <AlertCircle size={18} style={{ flexShrink: 0 }} />
                    <span>{modalError}</span>
                  </div>
                )}

                <div className="form-group" style={{ marginBottom: 'var(--spacing-4)' }}>
                  <label className="form-label">Email tài khoản</label>
                  <input 
                    type="text" 
                    className="form-input"
                    value={selectedUser.email}
                    readOnly
                    disabled
                    style={{ width: '100%', backgroundColor: 'var(--background)' }}
                  />
                </div>

                <div className="form-group" style={{ marginBottom: 'var(--spacing-4)' }}>
                  <label className="form-label">Vai trò mới <span className="text-danger">*</span></label>
                  <select 
                    className="form-input"
                    value={newRole}
                    onChange={(e) => setNewRole(e.target.value)}
                    style={{ width: '100%' }}
                    disabled={isSubmitting}
                  >
                    <option value="buyer">Người dùng (buyer)</option>
                    <option value="seller">Người bán (seller)</option>
                    <option value="admin">Quản trị viên (admin)</option>
                    <option value="engineer">Kỹ thuật viên (engineer)</option>
                  </select>
                </div>

                <div style={{
                  padding: 'var(--spacing-3)',
                  backgroundColor: 'rgba(37, 99, 235, 0.05)',
                  border: '1px solid rgba(37, 99, 235, 0.2)',
                  borderRadius: 'var(--radius-sm)',
                  fontSize: '0.8rem',
                  color: 'var(--text-secondary)',
                  lineHeight: 1.5
                }}>
                  * Vai trò sẽ được cập nhật trực tiếp tại <code>PATCH /api/admin/users/{selectedUser.id}/role</code>.
                </div>
              </div>

              <div className="modal-footer" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-2)' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  onClick={() => setIsRoleModalOpen(false)}
                  disabled={isSubmitting}
                >
                  Hủy
                </button>
                <button 
                  type="submit" 
                  className="btn btn-primary"
                  disabled={isSubmitting}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Đang lưu...</span>
                    </>
                  ) : (
                    <span>Lưu vai trò</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==========================================
          MODAL: LOCK / UNLOCK CONFIRMATION
          ========================================== */}
      {isLockModalOpen && selectedUser && (
        <div className="modal-overlay" onClick={() => !isSubmitting && setIsLockModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '440px' }}>
            <div className="modal-header">
              <h3 className="modal-title">
                {selectedUser.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}
              </h3>
              <button 
                className="modal-close" 
                onClick={() => !isSubmitting && setIsLockModalOpen(false)} 
                aria-label="Đóng"
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-body" style={{ textAlign: 'center', padding: 'var(--spacing-6) var(--spacing-5)' }}>
              {modalError && (
                <div style={{
                  backgroundColor: 'rgba(220, 38, 38, 0.1)',
                  border: '1px solid rgba(220, 38, 38, 0.3)',
                  color: 'var(--danger)',
                  padding: 'var(--spacing-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.875rem',
                  marginBottom: 'var(--spacing-4)',
                  display: 'flex',
                  alignItems: 'center',
                  gap: '8px',
                  textAlign: 'left'
                }}>
                  <AlertCircle size={18} style={{ flexShrink: 0 }} />
                  <span>{modalError}</span>
                </div>
              )}

              <div 
                style={{ 
                  width: '52px',
                  height: '52px',
                  borderRadius: '50%',
                  margin: '0 auto var(--spacing-4)',
                  backgroundColor: selectedUser.is_active ? 'rgba(220, 38, 38, 0.1)' : 'rgba(22, 163, 74, 0.1)',
                  color: selectedUser.is_active ? 'var(--danger)' : 'var(--success)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}
              >
                {selectedUser.is_active ? <Lock size={26} /> : <Unlock size={26} />}
              </div>

              <h4 style={{ margin: '0 0 var(--spacing-2) 0', fontSize: '1.1rem' }}>
                {selectedUser.is_active 
                  ? 'Bạn có chắc muốn khóa tài khoản này?'
                  : 'Bạn có chắc muốn mở khóa tài khoản này?'}
              </h4>

              <p style={{ color: 'var(--text-secondary)', fontSize: '0.875rem', marginBottom: 'var(--spacing-4)', lineHeight: 1.5 }}>
                {selectedUser.is_active
                  ? 'Người dùng sẽ không thể đăng nhập hoặc thực hiện các thao tác xác thực cho đến khi tài khoản được mở khóa.'
                  : 'Người dùng sẽ có thể đăng nhập lại vào hệ thống bình thường.'}
              </p>

              <div style={{
                backgroundColor: 'var(--background)',
                padding: 'var(--spacing-3)',
                borderRadius: 'var(--radius-md)',
                display: 'inline-flex',
                alignItems: 'center',
                gap: 'var(--spacing-3)',
                maxWidth: '100%'
              }}>
                <div style={{
                  width: '32px',
                  height: '32px',
                  borderRadius: '50%',
                  backgroundColor: 'rgba(37, 99, 235, 0.12)',
                  color: 'var(--primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center',
                  fontWeight: 600,
                  fontSize: '0.85rem'
                }}>
                  {selectedUser.email ? selectedUser.email.charAt(0).toUpperCase() : 'U'}
                </div>
                <div style={{ textAlign: 'left', overflow: 'hidden' }}>
                  <div style={{ fontWeight: 600, fontSize: '0.875rem', color: 'var(--text-main)', wordBreak: 'break-all' }}>
                    {selectedUser.email}
                  </div>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    Mã #{selectedUser.id} • {getRoleLabel(selectedUser.role)}
                  </div>
                </div>
              </div>
            </div>

            <div className="modal-footer" style={{ justifyContent: 'center', gap: 'var(--spacing-3)' }}>
              <button 
                type="button" 
                className="btn btn-outline" 
                onClick={() => setIsLockModalOpen(false)}
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button 
                type="button" 
                className={`btn ${selectedUser.is_active ? 'btn-danger' : 'btn-primary'}`}
                onClick={handleConfirmLockToggle}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Đang xử lý...</span>
                  </>
                ) : (
                  <span>{selectedUser.is_active ? 'Khóa tài khoản' : 'Mở khóa tài khoản'}</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
