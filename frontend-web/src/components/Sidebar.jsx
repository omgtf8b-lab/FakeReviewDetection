import React from 'react';
import { useAuth } from '../contexts/AuthContext';
import { NavLink } from 'react-router-dom';
import { LayoutDashboard, Users, Package, ShieldCheck, History, FileCheck2, HelpCircle, LogOut, MessageSquare, UserCog, Bell } from 'lucide-react';

export default function Sidebar({ isCollapsed, isMobileOpen }) {
  const { logout,user } = useAuth();
  const staff=['admin','engineer'].includes(user?.role);
  const links=[['/review-check',FileCheck2,'Kiểm tra sản phẩm'],['/history',History,'Lịch sử của tôi'],['/notifications',Bell,'Thông báo'],...(staff?[['/',LayoutDashboard,'Thống kê quản trị'],['/workspace',ShieldCheck,'Quản trị & AI'],['/users',Users,'Quản lý người dùng'],['/products',Package,'Dữ liệu sản phẩm'],['/reviews',MessageSquare,'Dữ liệu đánh giá']]:[])];
  const style=({isActive})=>isActive?'sidebar-link active':'sidebar-link';
  return <aside className={`sidebar ${isCollapsed?'collapsed':''} ${isMobileOpen?'mobile-open':''}`}>
    <div className="sidebar-brand"><ShieldCheck className="brand-icon" size={28}/><span className="brand-text">Fake Review Detection</span></div>
    <nav className="sidebar-nav">{links.map(([url,Icon,label])=><NavLink key={url} to={url} end={url==='/'} className={style}><Icon size={20}/><span>{label}</span></NavLink>)}</nav>
    <div className="sidebar-bottom"><NavLink to="/account" className={style}><UserCog size={20}/><span>Tài khoản của tôi</span></NavLink><NavLink to="/help" className={style}><HelpCircle size={20}/><span>Trợ giúp</span></NavLink><NavLink to="/login" onClick={logout} className="sidebar-link" style={{color:'var(--danger)'}}><LogOut size={20}/><span>Đăng xuất</span></NavLink></div>
  </aside>;
}
