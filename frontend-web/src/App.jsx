import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import ProductInspector from './pages/ProductInspector';
import ConsumerSupport from './pages/ConsumerSupport';
import ConsumerAccount from './pages/ConsumerAccount';
import InspectionAdmin from './pages/InspectionAdmin';

import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Reviews from './pages/Reviews';
import Result from './pages/Result';
import History from './pages/History';
import Users from './pages/Users';
import Workspace from './pages/Workspace';
import PasswordRecovery from './pages/PasswordRecovery';

function StaffOnly({children}) {
  const {user}=useAuth();
  return ['admin','engineer'].includes(user?.role)?children:<Navigate to="/review-check" replace />;
}

function Home() {
  const {user}=useAuth();
  return ['admin','engineer'].includes(user?.role)?<InspectionAdmin />:<ProductInspector />;
}

function App() {
  return (
    <Routes>
      {/* Public routes without dashboard layout */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/forgot-password" element={<PasswordRecovery />} />
      <Route path="/reset-password" element={<PasswordRecovery />} />

      {/* Protected routes wrapped in DashboardLayout */}
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<Home />} />
        <Route path="/users" element={<StaffOnly><Users /></StaffOnly>} />
        <Route path="/account" element={<ConsumerAccount />} />
        <Route path="/workspace" element={<StaffOnly><Workspace /></StaffOnly>} />
        <Route path="/products" element={<StaffOnly><Products /></StaffOnly>} />
        <Route path="/reviews" element={<StaffOnly><Reviews /></StaffOnly>} />
        <Route path="/review-check" element={<ProductInspector />} />
        <Route path="/help" element={<ConsumerSupport />} />
        <Route path="/notifications" element={<ConsumerSupport notifications />} />
        <Route path="/result" element={<Result />} />
        <Route path="/history" element={<ProductInspector historyOnly />} />
        <Route path="/text-history" element={<History />} />
      </Route>
    </Routes>
  );
}

export default App;
