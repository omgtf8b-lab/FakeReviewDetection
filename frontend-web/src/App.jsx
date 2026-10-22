import React from 'react';
import { Routes, Route } from 'react-router-dom';

import DashboardLayout from './layouts/DashboardLayout';
import Login from './pages/Login';
import Register from './pages/Register';
import Dashboard from './pages/Dashboard';
import Products from './pages/Products';
import Reviews from './pages/Reviews';
import ReviewCheck from './pages/ReviewCheck';
import Result from './pages/Result';
import History from './pages/History';
import Users from './pages/Users';
import Account from './pages/Account';

function App() {
  return (
    <Routes>
      {/* Public routes without dashboard layout */}
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />

      {/* Protected routes wrapped in DashboardLayout */}
      <Route element={<DashboardLayout />}>
        <Route path="/" element={<Dashboard />} />
        <Route path="/users" element={<Users />} />
        <Route path="/account" element={<Account />} />
        <Route path="/products" element={<Products />} />
        <Route path="/reviews" element={<Reviews />} />
        <Route path="/review-check" element={<ReviewCheck />} />
        <Route path="/result" element={<Result />} />
        <Route path="/history" element={<History />} />
      </Route>
    </Routes>
  );
}

export default App;
