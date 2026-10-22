import React from 'react';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Package, ShieldCheck, History, FileCheck2, HelpCircle, LogOut, MessageSquare, UserCog } from 'lucide-react';

export default function Sidebar({ isCollapsed, isMobileOpen }) {
  return (
    <aside className={`sidebar ${isCollapsed ? 'collapsed' : ''} ${isMobileOpen ? 'mobile-open' : ''}`}>
      <div className="sidebar-brand">
        <ShieldCheck className="brand-icon" size={28} strokeWidth={2.5} />
        <span className="brand-text">Fake Review Detection</span>
      </div>
      
      <nav className="sidebar-nav">
        <NavLink 
          to="/" 
          end
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <LayoutDashboard size={20} />
          <span>Tổng quan</span>
        </NavLink>

        <NavLink 
          to="/users" 
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <Users size={20} />
          <span>Quản lý người dùng</span>
        </NavLink>
        
        <NavLink 
          to="/products" 
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <Package size={20} />
          <span>Quản lý sản phẩm</span>
        </NavLink>

        <NavLink 
          to="/reviews" 
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <MessageSquare size={20} />
          <span>Quản lý đánh giá</span>
        </NavLink>
        
        <NavLink 
          to="/review-check" 
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <FileCheck2 size={20} />
          <span>Kiểm tra đánh giá</span>
        </NavLink>

        <NavLink 
          to="/result" 
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <ShieldCheck size={20} />
          <span>Kết quả phân tích</span>
        </NavLink>
        
        <NavLink 
          to="/history" 
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <History size={20} />
          <span>Lịch sử kiểm tra</span>
        </NavLink>
      </nav>

      <div className="sidebar-bottom">
        <NavLink 
          to="/account" 
          className={({ isActive }) => isActive ? "sidebar-link active" : "sidebar-link"}
        >
          <UserCog size={20} />
          <span>Tài khoản của tôi</span>
        </NavLink>
        <a href="#" className="sidebar-link">
          <HelpCircle size={20} />
          <span>Trợ giúp</span>
        </a>
        <NavLink 
          to="/login" 
          className="sidebar-link"
          style={{ color: 'var(--danger)' }}
        >
          <LogOut size={20} />
          <span>Đăng xuất</span>
        </NavLink>
      </div>
    </aside>
  );
}

