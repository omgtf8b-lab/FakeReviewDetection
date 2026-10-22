import React, { useState } from 'react';
import { Outlet, useLocation } from 'react-router-dom';
import Sidebar from '../components/Sidebar';
import Header from '../components/Header';
import '../styles/dashboard.css';

export default function DashboardLayout() {
  const location = useLocation();
  const [isSidebarCollapsed, setIsSidebarCollapsed] = useState(false);
  const [isMobileOpen, setIsMobileOpen] = useState(false);

  const getPageTitle = (pathname) => {
    switch (pathname) {
      case '/':
        return 'Tổng quan hệ thống';
      case '/users':
        return 'Quản lý người dùng';
      case '/account':
        return 'Tài khoản của tôi';
      case '/products':
        return 'Quản lý sản phẩm';
      case '/reviews':
        return 'Quản lý đánh giá';
      case '/review-check':
        return 'Kiểm tra đánh giá';
      case '/result':
        return 'Kết quả phân tích';
      case '/history':
        return 'Lịch sử kiểm tra';
      default:
        return 'Fake Review Detection';
    }
  };

  const pageTitle = getPageTitle(location.pathname);

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
