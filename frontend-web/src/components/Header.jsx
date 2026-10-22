import React, { useState, useRef, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Menu, Search, Bell, User, LogOut, ChevronDown } from 'lucide-react';
import { useAuth } from '../contexts/AuthContext';

export default function Header({ title, toggleSidebar }) {
  const navigate = useNavigate();
  const { user, roleLabel, logout } = useAuth();
  const [isProfileOpen, setIsProfileOpen] = useState(false);
  const dropdownRef = useRef(null);

  // Derive display initials
  const displayName = user?.email?.split('@')[0] || 'Người dùng';
  const avatarInitials = user?.email ? user.email.substring(0, 2).toUpperCase() : 'U';

  useEffect(() => {
    const handleClickOutside = (event) => {
      if (dropdownRef.current && !dropdownRef.current.contains(event.target)) {
        setIsProfileOpen(false);
      }
    };

    const handleKeyDown = (e) => {
      if (e.key === 'Escape') {
        setIsProfileOpen(false);
      }
    };

    document.addEventListener('mousedown', handleClickOutside);
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('mousedown', handleClickOutside);
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, []);

  const handleLogout = () => {
    setIsProfileOpen(false);
    logout();
    navigate('/login');
  };

  return (
    <header className="header">
      <div className="header-left">
        <button className="toggle-sidebar-btn" onClick={toggleSidebar} aria-label="Toggle Sidebar">
          <Menu size={20} />
        </button>
        <h2 className="breadcrumb">{title}</h2>
      </div>
      
      <div className="header-right">
        <div className="search-wrapper">
          <Search className="search-icon" size={18} />
          <input 
            type="text" 
            className="search-input" 
            placeholder="Tìm kiếm nhanh..." 
          />
        </div>
        
        <div className="header-actions">
          <button className="action-btn" aria-label="Notifications">
            <Bell size={20} />
            <span style={{
              position: 'absolute',
              top: '2px',
              right: '2px',
              width: '8px',
              height: '8px',
              backgroundColor: 'var(--danger)',
              borderRadius: '50%'
            }}></span>
          </button>
          
          <div className="profile-menu-container" ref={dropdownRef}>
            <button 
              className={`user-profile-btn ${isProfileOpen ? 'active' : ''}`}
              onClick={() => setIsProfileOpen(!isProfileOpen)}
              aria-haspopup="menu"
              aria-expanded={isProfileOpen}
              aria-label="Menu tài khoản cá nhân"
            >
              <div className="user-avatar">
                {avatarInitials}
              </div>
              <div className="user-info">
                <span className="user-name">{displayName}</span>
                <span className="user-role">{roleLabel}</span>
              </div>
              <ChevronDown size={14} className="text-muted" style={{ transition: 'transform 0.2s', transform: isProfileOpen ? 'rotate(180deg)' : 'none' }} />
            </button>

            {isProfileOpen && (
              <div className="profile-dropdown" role="menu">
                <div className="profile-dropdown-header">
                  <div className="profile-dropdown-name">{displayName}</div>
                  <div className="profile-dropdown-email">{user?.email || 'Chưa đăng nhập'}</div>
                </div>
                <div className="profile-dropdown-items">
                  <button 
                    className="profile-dropdown-item"
                    role="menuitem"
                    onClick={() => {
                      setIsProfileOpen(false);
                      navigate('/account');
                    }}
                  >
                    <User size={16} />
                    <span>Tài khoản của tôi</span>
                  </button>
                  
                  <div className="dropdown-divider" />
                  
                  <button 
                    className="profile-dropdown-item danger"
                    role="menuitem"
                    onClick={handleLogout}
                  >
                    <LogOut size={16} />
                    <span>Đăng xuất</span>
                  </button>
                </div>
              </div>
            )}
          </div>
        </div>
      </div>
    </header>
  );
}

