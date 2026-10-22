import React, { createContext, useContext, useState, useEffect, useCallback } from 'react';
import { 
  authApi, 
  getCurrentUser, 
  getAccessToken, 
  setCurrentUser, 
  clearAuthSession,
  isSellerOrAdmin,
  getRoleLabel 
} from '../lib/api';

const AuthContext = createContext(null);

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => getCurrentUser());
  const [token, setToken] = useState(() => getAccessToken());
  const [loading, setLoading] = useState(true);

  // Restore session on application load
  const restoreSession = useCallback(async () => {
    const currentToken = getAccessToken();
    if (!currentToken) {
      setUser(null);
      setLoading(false);
      return;
    }

    try {
      const userData = await authApi.getMe();
      setUser(userData);
      setCurrentUser(userData);
      setToken(currentToken);
    } catch (err) {
      console.warn('Session verification failed, logging out:', err.message);
      clearAuthSession();
      setUser(null);
      setToken(null);
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    restoreSession();

    // Listen for logout events dispatched from API client (e.g., on 401)
    const handleLogoutEvent = () => {
      setUser(null);
      setToken(null);
    };

    window.addEventListener('auth:logout', handleLogoutEvent);
    return () => {
      window.removeEventListener('auth:logout', handleLogoutEvent);
    };
  }, [restoreSession]);

  const login = async (email, password) => {
    const data = await authApi.login(email, password);
    setToken(data.access_token);
    setUser(data.user);
    return data;
  };

  const register = async (email, password) => {
    return authApi.register(email, password);
  };

  const logout = () => {
    authApi.logout();
    setUser(null);
    setToken(null);
  };

  const value = {
    user,
    token,
    loading,
    isAuthenticated: !!token && !!user,
    isSellerOrAdmin: isSellerOrAdmin(user?.role),
    roleLabel: getRoleLabel(user?.role),
    login,
    register,
    logout,
    restoreSession
  };

  return (
    <AuthContext.Provider value={value}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}
