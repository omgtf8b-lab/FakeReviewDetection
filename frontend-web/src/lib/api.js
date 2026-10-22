// ==========================================
// REAL FASTAPI BACKEND API CLIENT
// Fake Review Detection System
// ==========================================

export const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://127.0.0.1:8001';

// Role mappings
export const ROLE_LABELS = {
  buyer: 'Người dùng',
  seller: 'Người bán',
  admin: 'Quản trị viên',
  engineer: 'Kỹ thuật viên'
};

export const getRoleLabel = (role) => {
  if (!role) return 'Người dùng';
  return ROLE_LABELS[role.toLowerCase()] || role;
};

export const isSellerOrAdmin = (role) => {
  if (!role) return false;
  const normalized = role.toLowerCase();
  return normalized === 'seller' || normalized === 'admin';
};

// Verification status mappings
export const VERIFICATION_STATUS_LABELS = {
  pending: 'Chờ xác minh',
  verified: 'Đã xác minh',
  revoked: 'Đã thu hồi'
};

export const getVerificationStatusLabel = (status) => {
  if (!status) return 'Chờ xác minh';
  return VERIFICATION_STATUS_LABELS[status.toLowerCase()] || status;
};

// Error message formatter for FastAPI
export function formatApiError(error, defaultMsg = 'Đã xảy ra lỗi khi kết nối máy chủ.') {
  if (!error) return defaultMsg;

  // Network / Connection Error
  if (error.name === 'TypeError' && error.message.includes('fetch')) {
    return 'Không thể kết nối đến máy chủ. Vui lòng kiểm tra Backend API (http://127.0.0.1:8001).';
  }

  if (typeof error === 'string') {
    return error;
  }

  // HTTP response error payload
  if (error.detail) {
    if (typeof error.detail === 'string') {
      return error.detail;
    }
    // FastAPI validation array
    if (Array.isArray(error.detail)) {
      return error.detail
        .map((item) => {
          const loc = Array.isArray(item.loc) ? item.loc.slice(1).join('.') : '';
          const msg = item.msg || 'Không hợp lệ';
          return loc ? `Trường ${loc}: ${msg}` : msg;
        })
        .join('; ');
    }
  }

  if (error.message) {
    return error.message;
  }

  return defaultMsg;
}

// Token management helpers
export function getAccessToken() {
  return localStorage.getItem('access_token');
}

export function setAccessToken(token) {
  if (token) {
    localStorage.setItem('access_token', token);
  } else {
    localStorage.removeItem('access_token');
  }
}

export function getCurrentUser() {
  const userStr = localStorage.getItem('current_user');
  if (!userStr) return null;
  try {
    return JSON.parse(userStr);
  } catch {
    return null;
  }
}

export function setCurrentUser(user) {
  if (user) {
    localStorage.setItem('current_user', JSON.stringify(user));
  } else {
    localStorage.removeItem('current_user');
  }
}

export function clearAuthSession() {
  localStorage.removeItem('access_token');
  localStorage.removeItem('current_user');
  // Dispatch custom auth event so components can update in real-time
  window.dispatchEvent(new CustomEvent('auth:logout'));
}

// Core HTTP request function
async function request(endpoint, options = {}) {
  const url = endpoint.startsWith('http') ? endpoint : `${API_BASE_URL}${endpoint}`;
  const token = getAccessToken();

  const headers = {
    Accept: 'application/json',
    ...options.headers
  };

  // Only set Content-Type if there is a body and it is not FormData
  if (options.body && !(options.body instanceof FormData) && !headers['Content-Type']) {
    headers['Content-Type'] = 'application/json';
  }

  if (token && !headers['Authorization']) {
    headers['Authorization'] = `Bearer ${token}`;
  }

  let response;
  try {
    response = await fetch(url, {
      ...options,
      headers
    });
  } catch (err) {
    throw new Error('Không thể kết nối đến máy chủ. Vui lòng kiểm tra Backend API.');
  }

  // Handle 401 Unauthorized cleanly
  if (response.status === 401) {
    clearAuthSession();
    // Only redirect if not already on /login or /register
    if (!window.location.pathname.includes('/login') && !window.location.pathname.includes('/register')) {
      window.location.href = '/login';
    }
    throw new Error('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
  }

  // Parse JSON response
  let data;
  const contentType = response.headers.get('content-type');
  if (contentType && contentType.includes('application/json')) {
    data = await response.json();
  } else {
    data = await response.text();
  }

  if (!response.ok) {
    const error = new Error(formatApiError(data, `Lỗi máy chủ (${response.status})`));
    error.status = response.status;
    error.data = data;
    throw error;
  }

  return data;
}

// REST Client methods
export const api = {
  get: (endpoint, params = null) => {
    let url = endpoint;
    if (params) {
      const searchParams = new URLSearchParams();
      Object.entries(params).forEach(([key, value]) => {
        if (value !== undefined && value !== null && value !== '') {
          searchParams.append(key, value);
        }
      });
      const queryString = searchParams.toString();
      if (queryString) {
        url += (url.includes('?') ? '&' : '?') + queryString;
      }
    }
    return request(url, { method: 'GET' });
  },

  post: (endpoint, body = null) => {
    return request(endpoint, {
      method: 'POST',
      body: body ? JSON.stringify(body) : undefined
    });
  },

  put: (endpoint, body = null) => {
    return request(endpoint, {
      method: 'PUT',
      body: body ? JSON.stringify(body) : undefined
    });
  },

  patch: (endpoint, body = null) => {
    return request(endpoint, {
      method: 'PATCH',
      body: body ? JSON.stringify(body) : undefined
    });
  },

  delete: (endpoint) => {
    return request(endpoint, { method: 'DELETE' });
  }
};

// Authentication Services
export const authApi = {
  login: async (email, password) => {
    const data = await api.post('/api/auth/login', { email, password });
    if (data.access_token) {
      setAccessToken(data.access_token);
    }
    if (data.user) {
      setCurrentUser(data.user);
    }
    return data;
  },

  register: async (email, password) => {
    return api.post('/api/auth/register', { email, password });
  },

  getMe: async () => {
    const user = await api.get('/api/auth/me');
    if (user) {
      setCurrentUser(user);
    }
    return user;
  },

  logout: () => {
    clearAuthSession();
  }
};

// Product Services
export const productApi = {
  getProducts: (params = {}) => {
    return api.get('/api/products', params);
  },

  getProduct: (id) => {
    return api.get(`/api/products/${id}`);
  },

  createProduct: (productData) => {
    return api.post('/api/products', productData);
  },

  updateProduct: (id, productData) => {
    return api.put(`/api/products/${id}`, productData);
  },

  deleteProduct: (id) => {
    return api.delete(`/api/products/${id}`);
  },

  getProductReviews: (productId, params = { page: 1, page_size: 10 }) => {
    return api.get(`/api/reviews/product/${productId}`, params);
  },

  getQrData: (productId) => {
    return api.get(`/api/products/${productId}/qr`);
  },

  getQrImageUrl: (productId) => {
    return `${API_BASE_URL}/api/products/${productId}/qr/image`;
  }
};

// Review Services
export const reviewApi = {
  getReviews: (params = {}) => {
    return api.get('/api/reviews', params);
  },

  getReview: (id) => {
    return api.get(`/api/reviews/${id}`);
  },

  createReview: (reviewData) => {
    return api.post('/api/reviews', reviewData);
  },

  updateReview: (id, reviewData) => {
    return api.put(`/api/reviews/${id}`, reviewData);
  },

  deleteReview: (id) => {
    return api.delete(`/api/reviews/${id}`);
  },

  getProductReviews: (productId, params = { page: 1, page_size: 10 }) => {
    return api.get(`/api/reviews/product/${productId}`, params);
  },

  getAdminReviews: () => {
    return api.get('/api/admin/reviews');
  },

  getMyReviews: (params = { page: 1, page_size: 10 }) => {
    return api.get('/api/reviews/me', params);
  }
};

// Prediction Services
export const predictionApi = {
  analyze: (content) => {
    return api.post('/api/predictions/analyze', { content });
  },

  getMyHistory: (limit = 50) => {
    return api.get('/api/predictions/history/me', { limit });
  },

  getPrediction: (id) => {
    return api.get(`/api/predictions/${id}`);
  },

  getModelInfo: () => {
    return api.get('/api/predictions/model-info');
  }
};

// Statistics Services
export const statisticsApi = {
  getOverview: () => {
    return api.get('/api/statistics/overview');
  },

  getMyOverview: () => {
    return api.get('/api/statistics/me');
  }
};

// User Management Services (Admin Only)
export const userApi = {
  getUsers: () => {
    return api.get('/api/users');
  },

  changeStatus: (userId, isActive) => {
    return api.patch(`/api/users/${userId}/status?is_active=${Boolean(isActive)}`);
  },

  changeRole: (userId, role) => {
    return api.patch(`/api/admin/users/${userId}/role`, { role });
  }
};

export default api;





