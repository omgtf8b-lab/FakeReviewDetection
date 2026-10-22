import React, { useState } from 'react';
import { Outlet, useLocation, Navigate } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import '../styles/dashboard.css';

export default function DashboardLayout() {
  const location = useLocation();
  const { loading, isAuthenticated, user } = useAuth();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/':
        return ['admin','engineer'].includes(user?.role) ? 'Thống kê quản trị' : 'Kiểm tra sản phẩm';
      case '/users':
        return 'Quản lý người dùng';
      case '/account':
        return 'Tài khoản của tôi';
      case '/products':
        return 'Quản lý sản phẩm';
      case '/reviews':
        return 'Quản lý đánh giá';
      case '/review-check':
        return 'Kiểm tra sản phẩm';
      case '/result':
        return 'Kết quả phân tích';
      case '/history':
        return 'Lịch sử kiểm tra';
      default:
        return 'Fake Review Detection';
    }
  };

  const pageTitle = getPageTitle(location.pathname);

  if (loading) return <p style={{padding:32}}>Đang khôi phục phiên đăng nhập…</p>;
  if (!isAuthenticated) return <Navigate to="/login" replace />;

  const toggleSidebar = () => {
    if (window.innerWidth <= 768) {
      setIsMobileOpen(!isMobileOpen);
    } else {
      setIsSidebarCollapsed(!isSidebarCollapsed);
    }
  };

  return (
    <div className="app-layout">
      <Sidebar isCollapsed={isSidebarCollapsed} isMobileOpen={isMobileOpen} />
      
      {/* Mobile overlay */}
      {isMobileOpen && (
        <div 
          className="modal-overlay" 
          style={{ zIndex: 30 }}
          onClick={() => setIsMobileOpen(false)}
        />
      )}
      
      <div className="main-wrapper">
        <Header title={pageTitle} toggleSidebar={toggleSidebar} />
        <main className="page-content">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
