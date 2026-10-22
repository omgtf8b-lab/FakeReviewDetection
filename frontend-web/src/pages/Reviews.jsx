import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate, useSearchParams } from 'react-router-dom';
import { 
  Search, Eye, ShieldCheck, ShieldAlert, Star, MessageSquare, 
  ChevronLeft, ChevronRight, X, RotateCcw, ExternalLink, 
  Package, AlertTriangle, User, Plus, Edit, Trash2, Loader2,
  AlertCircle, CheckCircle2, Info
} from 'lucide-react';
import { 
  reviewApi, 
  productApi, 
  formatApiError 
} from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function Reviews() {
  const navigate = useNavigate();
  const [searchParams, setSearchParams] = useSearchParams();
  const { user } = useAuth();

  // Primary review data from API
  const [reviews, setReviews] = useState([]);
  const [totalReviews, setTotalReviews] = useState(0);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState('');

  // Products lookup map for resolving product_id to product name
  const [products, setProducts] = useState([]);
  const [productsLoading, setProductsLoading] = useState(false);

  // Summary Metrics from API
  const [metrics, setMetrics] = useState({
    total: 0,
    real: 0,
    fake: 0,
    suspiciousRatio: 0
  });

  // Filters state
  const [searchTerm, setSearchTerm] = useState('');
  const [classificationFilter, setClassificationFilter] = useState('All'); // 'All' | 'real' | 'fake'
  const [ratingFilter, setRatingFilter] = useState('All'); // 'All' | '1'..'5'

  // Product filter derived from URL search parameter or local state
  const urlProductId = searchParams.get('productId');
  const [localProductFilter, setLocalProductFilter] = useState('All');
  const productFilter = urlProductId || localProductFilter;

  // Pagination state (Server-side)
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(6);

  // Detail Modal state
  const [selectedReview, setSelectedReview] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);
  const [detailLoading, setDetailLoading] = useState(false);

  // Create Review Modal state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [addFormData, setAddFormData] = useState({
    product_id: '',
    rating: 5,
    content: ''
  });
  const [addFormErrors, setAddFormErrors] = useState({});

  // Edit Review Modal state
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [editingReview, setEditingReview] = useState(null);
  const [editFormData, setEditFormData] = useState({
    rating: 5,
    content: ''
  });
  const [editFormErrors, setEditFormErrors] = useState({});

  // Delete Review Modal state
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [deletingReview, setDeletingReview] = useState(null);

  // Shared form action states
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [formServerError, setFormServerError] = useState('');
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
    const isAnyModalOpen = isDetailModalOpen || isAddModalOpen || isEditModalOpen || isDeleteModalOpen;
    if (isAnyModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isDetailModalOpen, isAddModalOpen, isEditModalOpen, isDeleteModalOpen]);

  // ==========================================
  // PERMISSIONS HELPER
  // Admin: can edit/delete any review
  // Normal users: can edit/delete only reviews they own (review.user_id === user.id)
  // ==========================================
  const canEditOrDelete = useCallback((review) => {
    if (!user) return false;
    const role = (user.role || '').toLowerCase();
    if (role === 'admin') return true;
    return review && Number(review.user_id) === Number(user.id);
  }, [user]);

  // ==========================================
  // LOAD PRODUCTS ONCE FOR ID -> NAME LOOKUP
  // ==========================================
  const fetchProducts = useCallback(async () => {
    setProductsLoading(true);
    try {
      const data = await productApi.getProducts({ page: 1, page_size: 100 });
      setProducts(data.items || []);
    } catch (err) {
      console.warn('Could not load products for review name lookup:', err);
    } finally {
      setProductsLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // Memoized product lookup map: id -> product name
  const productMap = useMemo(() => {
    const map = {};
    products.forEach((p) => {
      map[p.id] = p.name;
    });
    return map;
  }, [products]);

  // Resolve product name with fallback
  const getProductName = useCallback((productId) => {
    if (!productId) return 'Sản phẩm không xác định';
    return productMap[productId] || `Sản phẩm #${productId}`;
  }, [productMap]);

  // ==========================================
  // LOAD REVIEW METRICS FOR SUMMARY CARDS
  // Using lightweight API requests
  // ==========================================
  const fetchMetrics = useCallback(async () => {
    try {
      const [allRes, realRes, fakeRes] = await Promise.all([
        reviewApi.getReviews({ page: 1, page_size: 1 }),
        reviewApi.getReviews({ label: 'real', page: 1, page_size: 1 }),
        reviewApi.getReviews({ label: 'fake', page: 1, page_size: 1 })
      ]);
      const total = allRes.total || 0;
      const real = realRes.total || 0;
      const fake = fakeRes.total || 0;
      const suspiciousRatio = total > 0 ? Math.round((fake / total) * 100) : 0;

      setMetrics({
        total,
        real,
        fake,
        suspiciousRatio
      });
    } catch (err) {
      console.warn('Could not fetch review metrics:', err);
    }
  }, []);

  useEffect(() => {
    fetchMetrics();
  }, [fetchMetrics]);

  // ==========================================
  // FETCH REVIEWS FROM REAL API
  // Supported params: product_id, label, rating, page, page_size
  // ==========================================
  const fetchReviews = useCallback(async () => {
    setLoading(true);
    setApiError('');
    try {
      const params = {
        page: currentPage,
        page_size: pageSize
      };

      if (classificationFilter !== 'All') {
        params.label = classificationFilter;
      }
      if (ratingFilter !== 'All') {
        params.rating = Number(ratingFilter);
      }
      if (productFilter !== 'All') {
        params.product_id = Number(productFilter);
      }

      const data = await reviewApi.getReviews(params);
      setReviews(data.items || []);
      setTotalReviews(data.total || 0);
    } catch (err) {
      setReviews([]);
      setTotalReviews(0);
      setApiError(formatApiError(err, 'Không thể kết nối đến máy chủ.'));
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, classificationFilter, ratingFilter, productFilter]);

  useEffect(() => {
    fetchReviews();
  }, [fetchReviews]);

  // Update product filter
  const handleProductFilterChange = (newProductId) => {
    setCurrentPage(1);
    if (newProductId === 'All') {
      setLocalProductFilter('All');
      searchParams.delete('productId');
      setSearchParams(searchParams);
    } else {
      setLocalProductFilter(newProductId);
      setSearchParams({ productId: newProductId });
    }
  };

  // Reset all filters
  const handleResetFilters = () => {
    setSearchTerm('');
    setClassificationFilter('All');
    setLocalProductFilter('All');
    setRatingFilter('All');
    setCurrentPage(1);
    searchParams.delete('productId');
    setSearchParams(searchParams);
  };

  // Client-side search filtering on current loaded page items
  const displayedReviews = useMemo(() => {
    if (!searchTerm.trim()) return reviews;
    const term = searchTerm.toLowerCase().trim();
    return reviews.filter((r) => {
      const pName = getProductName(r.product_id).toLowerCase();
      const content = (r.content || '').toLowerCase();
      const idMatch = String(r.id).includes(term);
      const userMatch = `người dùng #${r.user_id}`.toLowerCase().includes(term) || String(r.user_id).includes(term);
      const prodIdMatch = String(r.product_id).includes(term);

      return (
        content.includes(term) ||
        pName.includes(term) ||
        idMatch ||
        userMatch ||
        prodIdMatch
      );
    });
  }, [reviews, searchTerm, getProductName]);

  // Server-side pagination calculation
  const totalPages = Math.ceil(totalReviews / pageSize) || 1;
  const safeCurrentPage = Math.min(currentPage, totalPages);

  // Active product display
  const activeFilteredProduct = useMemo(() => {
    if (productFilter === 'All') return null;
    const prodIdNum = Number(productFilter);
    return products.find((p) => p.id === prodIdNum) || { id: productFilter, name: getProductName(productFilter) };
  }, [productFilter, products, getProductName]);

  // ==========================================
  // REVIEW DETAIL MODAL (GET /api/reviews/{id})
  // ==========================================
  const handleOpenDetail = async (review) => {
    setSelectedReview(review);
    setIsDetailModalOpen(true);
    setDetailLoading(true);

    try {
      const freshReview = await reviewApi.getReview(review.id);
      setSelectedReview(freshReview);
    } catch (err) {
      console.warn('Could not fetch fresh review detail, using item data:', err);
    } finally {
      setDetailLoading(false);
    }
  };

  // Navigate to Result page with review context
  const handleNavigateToResult = (review) => {
    const isFake = review.prediction?.predicted_label === 'fake';
    navigate('/result', {
      state: {
        review: {
          id: review.id,
          productId: review.product_id,
          productName: getProductName(review.product_id),
          reviewerName: `Người dùng #${review.user_id}`,
          rating: review.rating,
          content: review.content,
          date: review.created_at ? new Date(review.created_at).toLocaleString('vi-VN') : '',
          classification: isFake ? 'Computer Generated' : 'Original Review',
          confidence: review.prediction?.confidence_score ?? 0.5,
          prediction: review.prediction
        }
      }
    });
  };

  // ==========================================
  // CREATE REVIEW (POST /api/reviews)
  // ==========================================
  const handleOpenAdd = () => {
    // Default to first product if available
    const defaultProductId = productFilter !== 'All' ? productFilter : (products[0]?.id || '');
    setAddFormData({
      product_id: defaultProductId,
      rating: 5,
      content: ''
    });
    setAddFormErrors({});
    setFormServerError('');
    setIsAddModalOpen(true);
  };

  const validateAddForm = () => {
    const errors = {};
    if (!addFormData.product_id || Number(addFormData.product_id) <= 0) {
      errors.product_id = 'Vui lòng chọn sản phẩm đánh giá';
    }
    if (!addFormData.rating || Number(addFormData.rating) < 1 || Number(addFormData.rating) > 5) {
      errors.rating = 'Số sao đánh giá phải từ 1 đến 5';
    }
    const contentTrimmed = (addFormData.content || '').trim();
    if (!contentTrimmed) {
      errors.content = 'Nội dung đánh giá không được để trống';
    } else if (contentTrimmed.length < 5) {
      errors.content = 'Nội dung đánh giá phải có ít nhất 5 ký tự';
    } else if (contentTrimmed.length > 5000) {
      errors.content = 'Nội dung đánh giá không được vượt quá 5000 ký tự';
    }

    setAddFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!validateAddForm()) return;

    setIsSubmitting(true);
    setFormServerError('');

    try {
      await reviewApi.createReview({
        product_id: Number(addFormData.product_id),
        rating: Number(addFormData.rating),
        content: addFormData.content.trim()
      });

      setIsAddModalOpen(false);
      setToastMessage('Đã thêm đánh giá thành công! Hệ thống đã tự động phân tích.');
      fetchReviews();
      fetchMetrics();
    } catch (err) {
      setFormServerError(formatApiError(err, 'Không thể tạo đánh giá. Vui lòng kiểm tra lại.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // ==========================================
  // EDIT REVIEW (PUT /api/reviews/{id})
  // ==========================================
  const handleOpenEdit = (review) => {
    setEditingReview(review);
    setEditFormData({
      rating: review.rating || 5,
      content: review.content || ''
    });
    setEditFormErrors({});
    setFormServerError('');
    setIsEditModalOpen(true);
  };

  const validateEditForm = () => {
    const errors = {};
    if (!editFormData.rating || Number(editFormData.rating) < 1 || Number(editFormData.rating) > 5) {
      errors.rating = 'Số sao đánh giá phải từ 1 đến 5';
    }
    const contentTrimmed = (editFormData.content || '').trim();
    if (!contentTrimmed) {
      errors.content = 'Nội dung đánh giá không được để trống';
    } else if (contentTrimmed.length < 5) {
      errors.content = 'Nội dung đánh giá phải có ít nhất 5 ký tự';
    } else if (contentTrimmed.length > 5000) {
      errors.content = 'Nội dung đánh giá không được vượt quá 5000 ký tự';
    }

    setEditFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!validateEditForm() || !editingReview) return;

    setIsSubmitting(true);
    setFormServerError('');

    try {
      await reviewApi.updateReview(editingReview.id, {
        rating: Number(editFormData.rating),
        content: editFormData.content.trim()
      });

      setIsEditModalOpen(false);
      setToastMessage('Đã cập nhật đánh giá thành công! Đánh giá đã được phân tích lại.');
      fetchReviews();
      fetchMetrics();
    } catch (err) {
      if (err.status === 403) {
        setFormServerError('Bạn không có quyền sửa đánh giá này.');
      } else if (err.status === 404) {
        setFormServerError('Đánh giá không tồn tại.');
      } else {
        setFormServerError(formatApiError(err, 'Không thể cập nhật đánh giá.'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // ==========================================
  // DELETE REVIEW (DELETE /api/reviews/{id})
  // ==========================================
  const handleOpenDelete = (review) => {
    setDeletingReview(review);
    setIsDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!deletingReview) return;

    setIsSubmitting(true);
    try {
      await reviewApi.deleteReview(deletingReview.id);
      setIsDeleteModalOpen(false);
      setToastMessage(`Đã xóa đánh giá #${deletingReview.id} thành công!`);
      setDeletingReview(null);

      // Adjust pagination if deleting last item on current page
      if (reviews.length === 1 && currentPage > 1) {
        setCurrentPage((p) => p - 1);
      } else {
        fetchReviews();
      }
      fetchMetrics();
    } catch (err) {
      if (err.status === 403) {
        alert('Bạn không có quyền xóa đánh giá này.');
      } else if (err.status === 404) {
        alert('Đánh giá không tồn tại.');
      } else {
        alert(formatApiError(err, 'Không thể xóa đánh giá.'));
      }
    } finally {
      setIsSubmitting(false);
    }
  };

  // Helper for model fallback indicator
  const isFallbackModel = (pred) => {
    if (!pred) return false;
    return pred.model_name === 'fallback-heuristic' || pred.model_version === 'dev-only';
  };

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
            title="Đóng thông báo"
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Quản lý đánh giá</h1>
        <p className="page-subtitle">Theo dõi, phân loại và kiểm tra tính xác thực của các đánh giá sản phẩm</p>
      </div>

      {/* KPI Summary Cards */}
      <div className="grid-4">
        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Tổng đánh giá</h3>
            <div className="kpi-icon primary"><MessageSquare size={20} /></div>
          </div>
          <p className="kpi-value">{metrics.total}</p>
          <p className="kpi-footer">Từ tất cả các sản phẩm</p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đánh giá gốc (OR)</h3>
            <div className="kpi-icon success"><ShieldCheck size={20} /></div>
          </div>
          <p className="kpi-value">{metrics.real}</p>
          <p className="kpi-footer">
            <span className="text-success">
              {metrics.total > 0 ? Math.round((metrics.real / metrics.total) * 100) : 0}%
            </span> tự nhiên do người dùng viết
          </p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đáng ngờ (CG)</h3>
            <div className="kpi-icon danger"><ShieldAlert size={20} /></div>
          </div>
          <p className="kpi-value">{metrics.fake}</p>
          <p className="kpi-footer">
            <span className="text-danger">{metrics.suspiciousRatio}%</span> có dấu hiệu AI/Spam bot
          </p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Tỷ lệ đáng ngờ</h3>
            <div className="kpi-icon warning"><AlertTriangle size={20} /></div>
          </div>
          <p className="kpi-value">{metrics.suspiciousRatio}%</p>
          <p className="kpi-footer">Mô hình phân loại độ tin cậy cao</p>
        </div>
      </div>

      {/* Active Product Filter Alert Banner */}
      {activeFilteredProduct && (
        <div style={{
          backgroundColor: 'rgba(37, 99, 235, 0.08)',
          border: '1px solid rgba(37, 99, 235, 0.2)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--spacing-3) var(--spacing-4)',
          marginBottom: 'var(--spacing-4)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          <div className="flex items-center gap-3">
            <Package size={18} className="text-primary" />
            <span style={{ fontSize: '0.875rem' }}>
              Đang lọc đánh giá cho sản phẩm: <strong>{activeFilteredProduct.name}</strong> (#{activeFilteredProduct.id})
            </span>
          </div>
          <button 
            className="btn btn-outline" 
            style={{ padding: '2px 8px', fontSize: '0.75rem', backgroundColor: 'var(--surface)' }}
            onClick={() => handleProductFilterChange('All')}
          >
            Bỏ lọc sản phẩm
          </button>
        </div>
      )}

      {/* Toolbar & Filters */}
      <div className="card" style={{ marginBottom: 'var(--spacing-6)', padding: 'var(--spacing-4)' }}>
        <div className="flex items-center" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-4)' }}>
          
          <div className="flex items-center" style={{ gap: 'var(--spacing-3)', flex: 1, minWidth: '320px', flexWrap: 'wrap' }}>
            {/* Search Input */}
            <div className="search-wrapper" style={{ flex: 1, minWidth: '240px', maxWidth: '340px' }}>
              <Search className="search-icon" size={18} />
              <input 
                type="text" 
                className="search-input" 
                placeholder="Tìm nội dung, mã SP, ID..." 
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ width: '100%' }}
              />
              {searchTerm && (
                <button 
                  onClick={() => setSearchTerm('')} 
                  style={{ position: 'absolute', right: '10px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                  title="Xóa tìm kiếm"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Classification / Label Filter (real, fake) */}
            <select 
              className="form-input"
              value={classificationFilter}
              onChange={(e) => {
                setClassificationFilter(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: '220px' }}
              aria-label="Lọc theo kết quả phân loại"
            >
              <option value="All">Tất cả kết quả</option>
              <option value="real">🟢 Đánh giá gốc</option>
              <option value="fake">🔴 Đáng ngờ</option>
            </select>

            {/* Product Filter (Real Products) */}
            <select 
              className="form-input"
              value={productFilter}
              onChange={(e) => handleProductFilterChange(e.target.value)}
              style={{ width: '220px' }}
              aria-label="Lọc theo sản phẩm"
            >
              <option value="All">Tất cả sản phẩm</option>
              {products.map((p) => (
                <option key={p.id} value={String(p.id)}>
                  #{p.id} - {p.name.length > 25 ? `${p.name.substring(0, 25)}...` : p.name}
                </option>
              ))}
            </select>

            {/* Rating Filter (1 to 5) */}
            <select 
              className="form-input"
              value={ratingFilter}
              onChange={(e) => {
                setRatingFilter(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: '130px' }}
              aria-label="Lọc theo số sao"
            >
              <option value="All">Tất cả sao</option>
              <option value="5">5 Sao ⭐</option>
              <option value="4">4 Sao ⭐</option>
              <option value="3">3 Sao ⭐</option>
              <option value="2">2 Sao ⭐</option>
              <option value="1">1 Sao ⭐</option>
            </select>

            {/* Reset button */}
            {(searchTerm || classificationFilter !== 'All' || productFilter !== 'All' || ratingFilter !== 'All') && (
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

          {/* Add Review Action */}
          <div>
            {user ? (
              <button className="btn btn-primary" onClick={handleOpenAdd}>
                <Plus size={18} />
                <span>Thêm đánh giá mới</span>
              </button>
            ) : (
              <button 
                className="btn btn-outline" 
                onClick={() => navigate('/login')}
                title="Đăng nhập để viết đánh giá"
              >
                <Plus size={18} />
                <span>Đăng nhập để đánh giá</span>
              </button>
            )}
          </div>

        </div>
      </div>

      {/* Review Data Table */}
      <div className="table-wrapper">
        <div className="table-header flex items-center" style={{ justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0 }}>
            Danh sách đánh giá ({totalReviews})
          </h3>
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
            >
              <option value={6}>6</option>
              <option value={10}>10</option>
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th style={{ width: '85px' }}>Mã</th>
                <th>Sản phẩm liên kết</th>
                <th>Người đánh giá</th>
                <th style={{ width: '90px' }}>Đánh giá</th>
                <th>Nội dung đánh giá</th>
                <th style={{ width: '170px' }}>Kết quả phân loại</th>
                <th style={{ width: '160px' }}>Điểm phân tích</th>
                <th style={{ textAlign: 'right', width: '130px' }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <Loader2 size={36} className="animate-spin text-primary" />
                      <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>Đang tải đánh giá...</p>
                    </div>
                  </td>
                </tr>
              ) : apiError ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <AlertCircle size={40} className="text-danger" />
                      <p style={{ margin: 0, fontWeight: 600, color: 'var(--danger)' }}>{apiError}</p>
                      <p className="text-muted" style={{ margin: 0, fontSize: '0.875rem' }}>
                        Kiểm tra kết nối Backend API (http://127.0.0.1:8001) và nhấn Thử lại.
                      </p>
                      <button className="btn btn-outline" onClick={fetchReviews} style={{ marginTop: 'var(--spacing-2)' }}>
                        <RotateCcw size={16} /> Thử lại
                      </button>
                    </div>
                  </td>
                </tr>
              ) : displayedReviews.length > 0 ? (
                displayedReviews.map((review) => {
                  const pred = review.prediction;
                  const isFake = pred?.predicted_label === 'fake';
                  const isReal = pred?.predicted_label === 'real';
                  const isPending = !pred;
                  const isFallback = isFallbackModel(pred);
                  const productName = getProductName(review.product_id);
                  const isOwnerOrAdmin = canEditOrDelete(review);

                  return (
                    <tr key={review.id}>
                      <td>
                        <span style={{ fontWeight: 600, fontFamily: 'monospace', color: 'var(--text-secondary)', fontSize: '0.8rem' }}>
                          #{review.id}
                        </span>
                        <div style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                          {review.created_at ? new Date(review.created_at).toLocaleDateString('vi-VN') : '—'}
                        </div>
                      </td>
                      <td>
                        <div style={{ maxWidth: '190px' }}>
                          <span 
                            style={{ 
                              fontWeight: 600, 
                              color: 'var(--primary)', 
                              cursor: 'pointer',
                              display: 'block',
                              whiteSpace: 'nowrap',
                              overflow: 'hidden',
                              textOverflow: 'ellipsis'
                            }}
                            title={`Lọc theo sản phẩm: ${productName}`}
                            onClick={() => handleProductFilterChange(String(review.product_id))}
                          >
                            {productName}
                          </span>
                          <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            Mã SP: #{review.product_id}
                          </span>
                        </div>
                      </td>
                      <td>
                        <div className="flex items-center gap-2">
                          <div style={{
                            width: '28px',
                            height: '28px',
                            borderRadius: '50%',
                            backgroundColor: isFake ? 'rgba(220, 38, 38, 0.1)' : 'rgba(37, 99, 235, 0.1)',
                            color: isFake ? 'var(--danger)' : 'var(--primary)',
                            display: 'flex',
                            alignItems: 'center',
                            justifyContent: 'center',
                            fontSize: '0.75rem',
                            fontWeight: 600,
                            flexShrink: 0
                          }}>
                            {review.user_id ? String(review.user_id).charAt(0) : 'U'}
                          </div>
                          <div>
                            <span style={{ fontWeight: 500, fontSize: '0.85rem' }}>
                              Người dùng #{review.user_id}
                            </span>
                            {user && Number(user.id) === Number(review.user_id) && (
                              <span style={{ fontSize: '0.65rem', marginLeft: '4px', color: 'var(--primary)', fontWeight: 600 }}>
                                (Tôi)
                              </span>
                            )}
                          </div>
                        </div>
                      </td>
                      <td>
                        <div className="star-rating">
                          {Array.from({ length: 5 }, (_, i) => (
                            <Star 
                              key={i} 
                              size={13} 
                              fill={i < review.rating ? '#F59E0B' : 'none'} 
                              color={i < review.rating ? '#F59E0B' : 'var(--border)'} 
                            />
                          ))}
                        </div>
                      </td>
                      <td style={{ maxWidth: '280px' }}>
                        <div style={{ 
                          whiteSpace: 'nowrap', 
                          overflow: 'hidden', 
                          textOverflow: 'ellipsis',
                          color: 'var(--text-main)',
                          fontSize: '0.85rem'
                        }} title={review.content}>
                          "{review.content}"
                        </div>
                      </td>
                      <td>
                        {isPending ? (
                          <span className="badge badge-neutral">Chưa phân tích</span>
                        ) : isFake ? (
                          <span className="badge badge-danger">Đáng ngờ</span>
                        ) : (
                          <span className="badge badge-success">Đánh giá gốc</span>
                        )}
                      </td>
                      <td>
                        {pred && pred.confidence_score !== undefined && pred.confidence_score !== null ? (
                          <div>
                            <div className="flex items-center justify-between" style={{ fontSize: '0.8rem', fontWeight: 600, marginBottom: '2px' }}>
                              <span>Điểm: {typeof pred.confidence_score === 'number' ? pred.confidence_score.toFixed(2) : pred.confidence_score}</span>
                              <span style={{ fontSize: '0.7rem', color: 'var(--text-secondary)' }}>
                                {pred.confidence_score >= 0.8 ? 'Rất cao' : pred.confidence_score >= 0.5 ? 'Ổn định' : 'Thấp'}
                              </span>
                            </div>
                            <div style={{ 
                              width: '100%', 
                              height: '5px', 
                              backgroundColor: 'var(--border)', 
                              borderRadius: '3px', 
                              overflow: 'hidden' 
                            }}>
                              <div style={{ 
                                width: `${Math.min(100, Math.max(0, pred.confidence_score * 100))}%`, 
                                height: '100%', 
                                backgroundColor: isFake ? 'var(--danger)' : 'var(--success)' 
                              }}></div>
                            </div>
                            {isFallback && (
                              <div 
                                style={{ 
                                  fontSize: '0.68rem', 
                                  color: '#D97706', 
                                  marginTop: '2px', 
                                  fontWeight: 500 
                                }} 
                                title="Kết quả thử nghiệm (fallback) - chưa dùng mô hình AI chính thức"
                              >
                                ⚠️ Thử nghiệm (fallback)
                              </div>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)', fontSize: '0.8rem' }}>—</span>
                        )}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div className="flex items-center" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-1)' }}>
                          <button 
                            className="btn-icon" 
                            title="Xem chi tiết đánh giá" 
                            onClick={() => handleOpenDetail(review)}
                            aria-label={`Xem chi tiết đánh giá ${review.id}`}
                          >
                            <Eye size={17} />
                          </button>
                          <button 
                            className="btn-icon" 
                            title="Xem kết quả phân tích giải thích AI (LIME)" 
                            onClick={() => handleNavigateToResult(review)}
                            aria-label={`Xem phân tích mô hình cho đánh giá ${review.id}`}
                            style={{ color: 'var(--primary)' }}
                          >
                            <ExternalLink size={17} />
                          </button>

                          {isOwnerOrAdmin && (
                            <>
                              <button 
                                className="btn-icon" 
                                title="Chỉnh sửa đánh giá" 
                                onClick={() => handleOpenEdit(review)}
                                aria-label={`Sửa đánh giá ${review.id}`}
                              >
                                <Edit size={17} />
                              </button>
                              <button 
                                className="btn-icon danger" 
                                title="Xóa đánh giá" 
                                onClick={() => handleOpenDelete(review)}
                                aria-label={`Xóa đánh giá ${review.id}`}
                              >
                                <Trash2 size={17} />
                              </button>
                            </>
                          )}
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <MessageSquare size={48} className="text-muted" opacity={0.4} />
                      <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>
                        {searchTerm || classificationFilter !== 'All' || ratingFilter !== 'All' || productFilter !== 'All' 
                          ? 'Không tìm thấy đánh giá nào phù hợp' 
                          : 'Chưa có đánh giá nào'}
                      </p>
                      <p className="text-muted" style={{ margin: 0, fontSize: '0.875rem' }}>
                        {searchTerm || classificationFilter !== 'All' || ratingFilter !== 'All' || productFilter !== 'All'
                          ? 'Hãy thử điều chỉnh bộ lọc hoặc bấm "Đặt lại" để xem toàn bộ đánh giá.'
                          : 'Hãy là người đầu tiên tạo đánh giá sản phẩm trong hệ thống.'}
                      </p>
                      {(searchTerm || classificationFilter !== 'All' || ratingFilter !== 'All' || productFilter !== 'All') && (
                        <button className="btn btn-outline" onClick={handleResetFilters} style={{ marginTop: 'var(--spacing-2)' }}>
                          <RotateCcw size={16} /> Đặt lại bộ lọc
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Server-side Pagination Section */}
        {!loading && totalReviews > 0 && (
          <div className="pagination-container">
            <div className="pagination-info">
              Hiển thị <strong>{(safeCurrentPage - 1) * pageSize + 1}</strong> - <strong>{Math.min(safeCurrentPage * pageSize, totalReviews)}</strong> trên tổng số <strong>{totalReviews}</strong> đánh giá
            </div>

            <div className="pagination-controls">
              <button 
                className="page-btn" 
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={safeCurrentPage === 1}
                title="Trang trước"
              >
                <ChevronLeft size={16} />
              </button>

              {Array.from({ length: totalPages }, (_, i) => i + 1).map((pageNum) => (
                <button
                  key={pageNum}
                  className={`page-btn ${pageNum === safeCurrentPage ? 'active' : ''}`}
                  onClick={() => setCurrentPage(pageNum)}
                >
                  {pageNum}
                </button>
              ))}

              <button 
                className="page-btn" 
                onClick={() => setCurrentPage((p) => Math.min(p + 1, totalPages))}
                disabled={safeCurrentPage === totalPages}
                title="Trang tiếp"
              >
                <ChevronRight size={16} />
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ==================================================== */}
      {/* REVIEW DETAILS MODAL (GET /api/reviews/{id})         */}
      {/* ==================================================== */}
      {isDetailModalOpen && selectedReview && (
        <div className="modal-overlay" onClick={() => setIsDetailModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '620px' }}>
            <div className="modal-header">
              <div className="flex items-center gap-3">
                <div style={{
                  width: '36px',
                  height: '36px',
                  backgroundColor: selectedReview.prediction?.predicted_label === 'fake' 
                    ? 'rgba(220, 38, 38, 0.1)' 
                    : 'rgba(22, 163, 74, 0.1)',
                  borderRadius: 'var(--radius-md)',
                  color: selectedReview.prediction?.predicted_label === 'fake' ? 'var(--danger)' : 'var(--success)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {selectedReview.prediction?.predicted_label === 'fake' ? <ShieldAlert size={20} /> : <ShieldCheck size={20} />}
                </div>
                <div>
                  <h2 className="modal-title" style={{ fontSize: '1.15rem' }}>
                    Chi tiết đánh giá #{selectedReview.id}
                  </h2>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Thời gian: {selectedReview.created_at ? new Date(selectedReview.created_at).toLocaleString('vi-VN') : '—'}
                  </span>
                </div>
              </div>
              <button className="modal-close" onClick={() => setIsDetailModalOpen(false)} aria-label="Đóng">✕</button>
            </div>

            <div className="modal-body">
              {detailLoading ? (
                <div style={{ textAlign: 'center', padding: 'var(--spacing-8)' }}>
                  <Loader2 size={32} className="animate-spin text-primary" style={{ margin: '0 auto var(--spacing-2)' }} />
                  <p style={{ margin: 0, fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Đang cập nhật chi tiết từ máy chủ...</p>
                </div>
              ) : (
                <>
                  {/* Product and Reviewer Info */}
                  <div className="detail-grid">
                    <div className="detail-item">
                      <span className="detail-label">Sản phẩm liên kết</span>
                      <span className="detail-value" style={{ color: 'var(--primary)' }}>
                        {getProductName(selectedReview.product_id)}
                      </span>
                      <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                        Mã SP: #{selectedReview.product_id}
                      </span>
                    </div>

                    <div className="detail-item">
                      <span className="detail-label">Người đánh giá</span>
                      <div className="flex items-center gap-2">
                        <User size={16} className="text-muted" />
                        <span className="detail-value">Người dùng #{selectedReview.user_id}</span>
                      </div>
                      <div className="star-rating" style={{ marginTop: '2px' }}>
                        {Array.from({ length: 5 }, (_, i) => (
                          <Star 
                            key={i} 
                            size={13} 
                            fill={i < selectedReview.rating ? '#F59E0B' : 'none'} 
                            color={i < selectedReview.rating ? '#F59E0B' : 'var(--border)'} 
                          />
                        ))}
                        <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginLeft: '4px' }}>
                          ({selectedReview.rating} sao)
                        </span>
                      </div>
                    </div>
                  </div>

                  {/* Review Content */}
                  <div style={{ marginTop: 'var(--spacing-3)' }}>
                    <span className="detail-label">Nội dung đánh giá</span>
                    <div className={`quote-box ${selectedReview.prediction?.predicted_label === 'fake' ? 'danger' : 'success'}`}>
                      "{selectedReview.content}"
                    </div>
                  </div>

                  {/* AI Detection Result Section */}
                  <div style={{ 
                    marginTop: 'var(--spacing-4)', 
                    backgroundColor: 'var(--background)', 
                    padding: 'var(--spacing-4)', 
                    borderRadius: 'var(--radius-md)',
                    border: '1px solid var(--border)'
                  }}>
                    <div className="flex items-center justify-between" style={{ marginBottom: 'var(--spacing-3)' }}>
                      <span className="detail-label" style={{ margin: 0 }}>Kết quả phân loại</span>
                      {selectedReview.prediction ? (
                        <span className={`badge ${selectedReview.prediction.predicted_label === 'fake' ? 'badge-danger' : 'badge-success'}`}>
                          {selectedReview.prediction.predicted_label === 'fake' ? 'Đáng ngờ' : 'Đánh giá gốc'}
                        </span>
                      ) : (
                        <span className="badge badge-neutral">Chưa phân tích</span>
                      )}
                    </div>

                    {selectedReview.prediction ? (
                      <div>
                        {/* Fallback Heuristic Warning */}
                        {isFallbackModel(selectedReview.prediction) && (
                          <div style={{
                            backgroundColor: 'rgba(217, 119, 6, 0.1)',
                            border: '1px solid rgba(217, 119, 6, 0.3)',
                            borderRadius: 'var(--radius-sm)',
                            padding: '8px 12px',
                            marginBottom: 'var(--spacing-3)',
                            display: 'flex',
                            alignItems: 'center',
                            gap: '8px',
                            fontSize: '0.8rem',
                            color: '#B45309'
                          }}>
                            <Info size={16} style={{ flexShrink: 0 }} />
                            <span>
                              <strong>Kết quả thử nghiệm (fallback)</strong>: Mô hình AI chính thức chưa nạp, sử dụng thuật toán heuristic phát hiện tạm thời.
                            </span>
                          </div>
                        )}

                        <div style={{ marginBottom: 'var(--spacing-3)' }}>
                          <div className="flex items-center justify-between" style={{ fontSize: '0.875rem', marginBottom: 'var(--spacing-1)' }}>
                            <span>Điểm phân tích:</span>
                            <strong style={{ fontSize: '1rem' }}>
                              {selectedReview.prediction.confidence_score !== undefined && selectedReview.prediction.confidence_score !== null
                                ? (typeof selectedReview.prediction.confidence_score === 'number' 
                                    ? selectedReview.prediction.confidence_score.toFixed(2) 
                                    : selectedReview.prediction.confidence_score)
                                : '—'}
                            </strong>
                          </div>
                          {selectedReview.prediction.confidence_score !== undefined && selectedReview.prediction.confidence_score !== null && (
                            <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                              <div style={{ 
                                width: `${Math.min(100, Math.max(0, selectedReview.prediction.confidence_score * 100))}%`, 
                                height: '100%', 
                                backgroundColor: selectedReview.prediction.predicted_label === 'fake' ? 'var(--danger)' : 'var(--success)' 
                              }}></div>
                            </div>
                          )}
                        </div>

                        {/* Model details & Explanation */}
                        <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px', borderTop: '1px solid var(--border)', paddingTop: '8px' }}>
                          <div className="flex items-center justify-between">
                            <span>Mô hình phân tích:</span>
                            <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                              {selectedReview.prediction.model_name || '—'} (v{selectedReview.prediction.model_version || '—'})
                            </span>
                          </div>
                          {selectedReview.prediction.fake_probability !== undefined && (
                            <div className="flex items-center justify-between">
                              <span>Xác suất đáng ngờ:</span>
                              <span style={{ fontWeight: 600, color: 'var(--danger)' }}>
                                {(selectedReview.prediction.fake_probability * 100).toFixed(1)}%
                              </span>
                            </div>
                          )}
                          {selectedReview.prediction.real_probability !== undefined && (
                            <div className="flex items-center justify-between">
                              <span>Xác suất đánh giá gốc:</span>
                              <span style={{ fontWeight: 600, color: 'var(--success)' }}>
                                {(selectedReview.prediction.real_probability * 100).toFixed(1)}%
                              </span>
                            </div>
                          )}
                          {selectedReview.prediction.explanation && (
                            <div style={{ marginTop: '6px' }}>
                              <span style={{ fontWeight: 600, display: 'block', marginBottom: '2px' }}>Giải thích:</span>
                              <p style={{ margin: 0, fontStyle: 'italic', color: 'var(--text-main)' }}>
                                {selectedReview.prediction.explanation}
                              </p>
                            </div>
                          )}
                        </div>
                      </div>
                    ) : (
                      <p style={{ margin: 0, fontSize: '0.85rem', color: 'var(--text-secondary)' }}>
                        Đánh giá này chưa có kết quả phân tích AI.
                      </p>
                    )}
                  </div>
                </>
              )}
            </div>

            <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
              <button 
                type="button" 
                className="btn btn-primary"
                onClick={() => {
                  setIsDetailModalOpen(false);
                  handleNavigateToResult(selectedReview);
                }}
              >
                <ExternalLink size={16} />
                <span>Xem chi tiết tại trang Kết quả phân tích</span>
              </button>
              <button type="button" className="btn btn-outline" onClick={() => setIsDetailModalOpen(false)}>
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* CREATE REVIEW MODAL (POST /api/reviews)              */}
      {/* ==================================================== */}
      {isAddModalOpen && (
        <div className="modal-overlay" onClick={() => !isSubmitting && setIsAddModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <div className="modal-header">
              <h2 className="modal-title">Thêm đánh giá mới</h2>
              <button 
                className="modal-close" 
                onClick={() => !isSubmitting && setIsAddModalOpen(false)}
                aria-label="Đóng"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleAddSubmit} noValidate>
              <div className="modal-body">
                {formServerError && (
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
                    <span>{formServerError}</span>
                  </div>
                )}

                {/* Product Selection */}
                <div className="form-group" style={{ marginBottom: 'var(--spacing-4)' }}>
                  <label className="form-label" htmlFor="add-product-id">
                    Sản phẩm <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <select
                    id="add-product-id"
                    className="form-input"
                    value={addFormData.product_id}
                    onChange={(e) => {
                      setAddFormData((prev) => ({ ...prev, product_id: e.target.value }));
                      if (addFormErrors.product_id) setAddFormErrors((prev) => ({ ...prev, product_id: '' }));
                    }}
                    style={{ width: '100%' }}
                    disabled={isSubmitting}
                  >
                    <option value="">-- Chọn sản phẩm --</option>
                    {products.map((p) => (
                      <option key={p.id} value={p.id}>
                        #{p.id} - {p.name}
                      </option>
                    ))}
                  </select>
                  {addFormErrors.product_id && (
                    <span className="form-error" style={{ color: 'var(--danger)', fontSize: '0.75rem', marginTop: '4px', display: 'block' }}>
                      {addFormErrors.product_id}
                    </span>
                  )}
                </div>

                {/* Rating (1 - 5) */}
                <div className="form-group" style={{ marginBottom: 'var(--spacing-4)' }}>
                  <label className="form-label">
                    Số sao đánh giá <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <div className="flex items-center gap-2" style={{ marginTop: '4px' }}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setAddFormData((prev) => ({ ...prev, rating: star }))}
                        disabled={isSubmitting}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: '4px',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                        title={`${star} sao`}
                      >
                        <Star 
                          size={24} 
                          fill={star <= addFormData.rating ? '#F59E0B' : 'none'} 
                          color={star <= addFormData.rating ? '#F59E0B' : 'var(--border)'} 
                        />
                      </button>
                    ))}
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)', marginLeft: '8px' }}>
                      {addFormData.rating} / 5 sao
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="form-group">
                  <label className="form-label" htmlFor="add-content">
                    Nội dung đánh giá <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <textarea
                    id="add-content"
                    className="form-input"
                    rows={4}
                    placeholder="Nhập trải nghiệm thực tế về sản phẩm (tối thiểu 5 ký tự)..."
                    value={addFormData.content}
                    onChange={(e) => {
                      setAddFormData((prev) => ({ ...prev, content: e.target.value }));
                      if (addFormErrors.content) setAddFormErrors((prev) => ({ ...prev, content: '' }));
                    }}
                    style={{ width: '100%', resize: 'vertical' }}
                    disabled={isSubmitting}
                  />
                  <div className="flex items-center justify-between" style={{ marginTop: '4px' }}>
                    <span style={{ color: 'var(--danger)', fontSize: '0.75rem' }}>
                      {addFormErrors.content || ''}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {addFormData.content.length} / 5000 ký tự
                    </span>
                  </div>
                </div>
              </div>

              <div className="modal-footer" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-2)' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  onClick={() => setIsAddModalOpen(false)}
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
                      <span>Đang gửi và phân tích...</span>
                    </>
                  ) : (
                    <span>Gửi đánh giá</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* EDIT REVIEW MODAL (PUT /api/reviews/{id})            */}
      {/* ==================================================== */}
      {isEditModalOpen && editingReview && (
        <div className="modal-overlay" onClick={() => !isSubmitting && setIsEditModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '560px' }}>
            <div className="modal-header">
              <h2 className="modal-title">Chỉnh sửa đánh giá #{editingReview.id}</h2>
              <button 
                className="modal-close" 
                onClick={() => !isSubmitting && setIsEditModalOpen(false)}
                aria-label="Đóng"
              >
                ✕
              </button>
            </div>

            <form onSubmit={handleEditSubmit} noValidate>
              <div className="modal-body">
                {formServerError && (
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
                    <span>{formServerError}</span>
                  </div>
                )}

                {/* Read-only Product Name */}
                <div className="form-group" style={{ marginBottom: 'var(--spacing-4)' }}>
                  <label className="form-label">Sản phẩm</label>
                  <input
                    type="text"
                    className="form-input"
                    value={getProductName(editingReview.product_id)}
                    readOnly
                    disabled
                    style={{ width: '100%', backgroundColor: 'var(--background)' }}
                  />
                </div>

                {/* Rating (1 - 5) */}
                <div className="form-group" style={{ marginBottom: 'var(--spacing-4)' }}>
                  <label className="form-label">
                    Số sao đánh giá <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <div className="flex items-center gap-2" style={{ marginTop: '4px' }}>
                    {[1, 2, 3, 4, 5].map((star) => (
                      <button
                        key={star}
                        type="button"
                        onClick={() => setEditFormData((prev) => ({ ...prev, rating: star }))}
                        disabled={isSubmitting}
                        style={{
                          background: 'none',
                          border: 'none',
                          cursor: 'pointer',
                          padding: '4px',
                          display: 'flex',
                          alignItems: 'center'
                        }}
                        title={`${star} sao`}
                      >
                        <Star 
                          size={24} 
                          fill={star <= editFormData.rating ? '#F59E0B' : 'none'} 
                          color={star <= editFormData.rating ? '#F59E0B' : 'var(--border)'} 
                        />
                      </button>
                    ))}
                    <span style={{ fontSize: '0.875rem', fontWeight: 600, color: 'var(--text-main)', marginLeft: '8px' }}>
                      {editFormData.rating} / 5 sao
                    </span>
                  </div>
                </div>

                {/* Content */}
                <div className="form-group">
                  <label className="form-label" htmlFor="edit-content">
                    Nội dung đánh giá <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <textarea
                    id="edit-content"
                    className="form-input"
                    rows={4}
                    value={editFormData.content}
                    onChange={(e) => {
                      setEditFormData((prev) => ({ ...prev, content: e.target.value }));
                      if (editFormErrors.content) setEditFormErrors((prev) => ({ ...prev, content: '' }));
                    }}
                    style={{ width: '100%', resize: 'vertical' }}
                    disabled={isSubmitting}
                  />
                  <div className="flex items-center justify-between" style={{ marginTop: '4px' }}>
                    <span style={{ color: 'var(--danger)', fontSize: '0.75rem' }}>
                      {editFormErrors.content || ''}
                    </span>
                    <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                      {editFormData.content.length} / 5000 ký tự
                    </span>
                  </div>
                </div>
              </div>

              <div className="modal-footer" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-2)' }}>
                <button 
                  type="button" 
                  className="btn btn-outline" 
                  onClick={() => setIsEditModalOpen(false)}
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
                      <span>Đang lưu và phân tích lại...</span>
                    </>
                  ) : (
                    <span>Lưu thay đổi</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* DELETE CONFIRMATION DIALOG (DELETE /api/reviews/{id})*/}
      {/* ==================================================== */}
      {isDeleteModalOpen && deletingReview && (
        <div className="modal-overlay" onClick={() => !isSubmitting && setIsDeleteModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '480px' }}>
            <div className="modal-header">
              <div className="flex items-center gap-3">
                <div style={{
                  width: '36px',
                  height: '36px',
                  backgroundColor: 'rgba(220, 38, 38, 0.1)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--danger)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Trash2 size={20} />
                </div>
                <h2 className="modal-title" style={{ fontSize: '1.15rem' }}>Xác nhận xóa đánh giá</h2>
              </div>
              <button 
                className="modal-close" 
                onClick={() => !isSubmitting && setIsDeleteModalOpen(false)}
                aria-label="Đóng"
              >
                ✕
              </button>
            </div>

            <div className="modal-body">
              <p style={{ margin: '0 0 var(--spacing-3) 0', color: 'var(--text-main)', lineHeight: 1.5 }}>
                Bạn có chắc chắn muốn xóa vĩnh viễn đánh giá <strong>#{deletingReview.id}</strong> của sản phẩm <strong>"{getProductName(deletingReview.product_id)}"</strong> không?
              </p>
              <div style={{ 
                backgroundColor: 'var(--background)', 
                padding: 'var(--spacing-3)', 
                borderRadius: 'var(--radius-sm)',
                border: '1px solid var(--border)',
                fontStyle: 'italic',
                fontSize: '0.85rem',
                color: 'var(--text-secondary)'
              }}>
                "{deletingReview.content}"
              </div>
              <p style={{ margin: 'var(--spacing-3) 0 0 0', color: 'var(--danger)', fontSize: '0.8rem' }}>
                * Thao tác này không thể hoàn tác. Dữ liệu phân tích đi kèm cũng sẽ bị xóa.
              </p>
            </div>

            <div className="modal-footer" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-2)' }}>
              <button 
                type="button" 
                className="btn btn-outline" 
                onClick={() => setIsDeleteModalOpen(false)}
                disabled={isSubmitting}
              >
                Hủy
              </button>
              <button 
                type="button" 
                className="btn btn-danger"
                onClick={handleConfirmDelete}
                disabled={isSubmitting}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Đang xóa...</span>
                  </>
                ) : (
                  <span>Xác nhận xóa</span>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
