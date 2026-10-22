import React, { useState, useEffect, useCallback } from 'react';
import { useNavigate } from 'react-router-dom';
import {
  Search, Plus, Eye, Edit, Trash2, Package, AlertCircle,
  X, CheckCircle2, ChevronLeft, ChevronRight,
  AlertTriangle, RotateCcw, ExternalLink, Loader2, QrCode,
  ShieldCheck, ShieldAlert
} from 'lucide-react';
import {
  productApi,
  formatApiError,
  getVerificationStatusLabel
} from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function Products() {
  const navigate = useNavigate();
  const { isSellerOrAdmin } = useAuth();

  // Primary data state (Real API)
  const [products, setProducts] = useState([]);
  const [totalProducts, setTotalProducts] = useState(0);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState('');

  // Search & Filter state
  const [searchTerm, setSearchTerm] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('All');

  // Pagination state (Server-side)
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(5);

  // Modals state
  const [isAddModalOpen, setIsAddModalOpen] = useState(false);
  const [isEditModalOpen, setIsEditModalOpen] = useState(false);
  const [isDeleteModalOpen, setIsDeleteModalOpen] = useState(false);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // Selected item and form state
  const [selectedProduct, setSelectedProduct] = useState(null);
  const [detailReviews, setDetailReviews] = useState([]);
  const [detailReviewsTotal, setDetailReviewsTotal] = useState(0);
  const [detailQr, setDetailQr] = useState(null);
  const [detailLoading, setDetailLoading] = useState(false);

  // Form state for Add/Edit
  const [formData, setFormData] = useState({
    name: '',
    product_code: '',
    brand: '',
    sku: '',
    category: 'Điện tử',
    price: '',
    manufacturer: '',
    origin: '',
    description: ''
  });

  const [formErrors, setFormErrors] = useState({});
  const [formServerError, setFormServerError] = useState('');
  const [isSubmitting, setIsSubmitting] = useState(false);
  const [toastMessage, setToastMessage] = useState('');

  // Debounce search term to prevent excessive backend requests
  useEffect(() => {
    const handler = setTimeout(() => {
      setDebouncedSearch(searchTerm);
      setCurrentPage(1);
    }, 400);
    return () => clearTimeout(handler);
  }, [searchTerm]);

  // Toast auto-dismiss
  useEffect(() => {
    if (toastMessage) {
      const timer = setTimeout(() => setToastMessage(''), 3000);
      return () => clearTimeout(timer);
    }
  }, [toastMessage]);

  // Prevent background page scrolling when modal is open
  useEffect(() => {
    const isAnyModalOpen = isAddModalOpen || isEditModalOpen || isDetailModalOpen || isDeleteModalOpen;
    if (isAnyModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isAddModalOpen, isEditModalOpen, isDetailModalOpen, isDeleteModalOpen]);

  // Fetch products from real FastAPI backend
  const fetchProducts = useCallback(async () => {
    setLoading(true);
    setApiError('');
    try {
      const params = {
        page: currentPage,
        page_size: pageSize
      };
      if (debouncedSearch.trim()) {
        params.search = debouncedSearch.trim();
      }
      if (categoryFilter !== 'All') {
        params.category = categoryFilter;
      }
      const data = await productApi.getProducts(params);
      setProducts(data.items || []);
      setTotalProducts(data.total || 0);
    } catch (err) {
      setApiError(formatApiError(err, 'Không thể tải danh sách sản phẩm từ máy chủ.'));
      setProducts([]);
      setTotalProducts(0);
    } finally {
      setLoading(false);
    }
  }, [currentPage, pageSize, debouncedSearch, categoryFilter]);

  // Load products on dependency change
  useEffect(() => {
    fetchProducts();
  }, [fetchProducts]);

  // Available categories
  const categories = ['All', 'Điện tử', 'Thời trang', 'Gia dụng', 'Mỹ phẩm', 'Khác'];

  // Pagination calculation
  const totalPages = Math.ceil(totalProducts / pageSize) || 1;
  const safeCurrentPage = Math.min(currentPage, totalPages);

  // Currency helper
  const formatCurrency = (amount) => {
    if (amount === undefined || amount === null || isNaN(amount)) return '0 ₫';
    return new Intl.NumberFormat('vi-VN', { style: 'currency', currency: 'VND' }).format(amount);
  };

  // Reset filters
  const handleResetFilters = () => {
    setSearchTerm('');
    setDebouncedSearch('');
    setCategoryFilter('All');
    setCurrentPage(1);
  };

  // Validation
  const validateForm = () => {
    const errors = {};

    // Validate Name
    if (!formData.name || !formData.name.trim()) {
      errors.name = 'Tên sản phẩm không được để trống';
    } else if (formData.name.trim().length < 2) {
      errors.name = 'Tên sản phẩm phải có ít nhất 2 ký tự';
    }

    // Validate Price
    if (formData.price === '' || formData.price === null || isNaN(Number(formData.price))) {
      errors.price = 'Giá sản phẩm không hợp lệ';
    } else if (Number(formData.price) <= 0) {
      errors.price = 'Giá sản phẩm phải lớn hơn 0 VNĐ';
    }

    // Validate Product Code if provided
    if (formData.product_code && formData.product_code.trim()) {
      if (formData.product_code.trim().length < 3) {
        errors.product_code = 'Mã sản phẩm phải có ít nhất 3 ký tự';
      } else if (!/^[A-Za-z0-9_-]+$/.test(formData.product_code.trim())) {
        errors.product_code = 'Mã sản phẩm chỉ gồm chữ cái, số, gạch ngang (-) hoặc dưới (_)';
      }
    }

    setFormErrors(errors);
    return Object.keys(errors).length === 0;
  };

  // Handlers for Add Modal
  const handleOpenAdd = () => {
    setFormData({
      name: '',
      product_code: '',
      brand: '',
      sku: '',
      category: 'Điện tử',
      price: '',
      manufacturer: '',
      origin: '',
      description: ''
    });
    setFormErrors({});
    setFormServerError('');
    setIsAddModalOpen(true);
  };

  // Handlers for Edit Modal
  const handleOpenEdit = (product) => {
    setSelectedProduct(product);
    setFormData({
      name: product.name || '',
      product_code: product.product_code || '',
      brand: product.brand || '',
      sku: product.sku || '',
      category: product.category || 'Điện tử',
      price: product.price !== undefined ? product.price : '',
      manufacturer: product.manufacturer || '',
      origin: product.origin || '',
      description: product.description || ''
    });
    setFormErrors({});
    setFormServerError('');
    setIsEditModalOpen(true);
  };

  const handleFormChange = (e) => {
    const { name, value } = e.target;
    setFormData(prev => ({ ...prev, [name]: value }));
    if (formErrors[name]) {
      setFormErrors(prev => ({ ...prev, [name]: '' }));
    }
    if (formServerError) {
      setFormServerError('');
    }
  };

  // Submit Add Product (POST /api/products)
  const handleAddSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm()) return;

    setIsSubmitting(true);
    setFormServerError('');

    try {
      const payload = {
        name: formData.name.trim(),
        price: Number(formData.price)
      };

      if (formData.product_code && formData.product_code.trim()) {
        payload.product_code = formData.product_code.trim();
      }
      if (formData.brand && formData.brand.trim()) {
        payload.brand = formData.brand.trim();
      }
      if (formData.sku && formData.sku.trim()) {
        payload.sku = formData.sku.trim();
      }
      if (formData.category) {
        payload.category = formData.category;
      }
      if (formData.manufacturer && formData.manufacturer.trim()) {
        payload.manufacturer = formData.manufacturer.trim();
      }
      if (formData.origin && formData.origin.trim()) {
        payload.origin = formData.origin.trim();
      }
      if (formData.description && formData.description.trim()) {
        payload.description = formData.description.trim();
      }

      const newProduct = await productApi.createProduct(payload);
      setIsAddModalOpen(false);
      setToastMessage(`Đã thêm sản phẩm "${newProduct.name}" thành công!`);
      // Refresh list
      fetchProducts();
    } catch (err) {
      setFormServerError(formatApiError(err, 'Không thể tạo sản phẩm. Vui lòng kiểm tra lại thông tin.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Submit Edit Product (PUT /api/products/{id})
  const handleEditSubmit = async (e) => {
    e.preventDefault();
    if (!validateForm() || !selectedProduct) return;

    setIsSubmitting(true);
    setFormServerError('');

    try {
      const payload = {
        name: formData.name.trim(),
        price: Number(formData.price)
      };

      if (formData.product_code && formData.product_code.trim()) {
        payload.product_code = formData.product_code.trim();
      }
      if (formData.brand !== undefined) {
        payload.brand = formData.brand.trim() || null;
      }
      if (formData.sku !== undefined) {
        payload.sku = formData.sku.trim() || null;
      }
      if (formData.category) {
        payload.category = formData.category;
      }
      if (formData.manufacturer !== undefined) {
        payload.manufacturer = formData.manufacturer.trim() || null;
      }
      if (formData.origin !== undefined) {
        payload.origin = formData.origin.trim() || null;
      }
      if (formData.description !== undefined) {
        payload.description = formData.description.trim() || null;
      }

      await productApi.updateProduct(selectedProduct.id, payload);
      setIsEditModalOpen(false);
      setToastMessage(`Đã cập nhật sản phẩm "${formData.name}" thành công!`);
      // Refresh list
      fetchProducts();
    } catch (err) {
      setFormServerError(formatApiError(err, 'Không thể cập nhật sản phẩm.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handlers for Delete Modal (DELETE /api/products/{id})
  const handleOpenDelete = (product) => {
    setSelectedProduct(product);
    setIsDeleteModalOpen(true);
  };

  const handleConfirmDelete = async () => {
    if (!selectedProduct) return;
    setIsSubmitting(true);
    try {
      await productApi.deleteProduct(selectedProduct.id);
      setIsDeleteModalOpen(false);
      setToastMessage(`Đã xóa sản phẩm "${selectedProduct.name}" khỏi hệ thống!`);
      setSelectedProduct(null);

      // Adjust page if last item on page was deleted
      if (products.length === 1 && currentPage > 1) {
        setCurrentPage(prev => prev - 1);
      } else {
        fetchProducts();
      }
    } catch (err) {
      alert(formatApiError(err, 'Không thể xóa sản phẩm.'));
    } finally {
      setIsSubmitting(false);
    }
  };

  // Handler for View Details Modal (GET /api/products/{id})
  const handleOpenDetail = async (product) => {
    setSelectedProduct(product);
    setIsDetailModalOpen(true);
    setDetailLoading(true);
    setDetailReviews([]);
    setDetailReviewsTotal(0);
    setDetailQr(null);

    try {
      // Get fresh details from backend
      const freshProduct = await productApi.getProduct(product.id);
      setSelectedProduct(freshProduct);
    } catch (e) {
      console.warn('Could not fetch fresh product details:', e);
    }

    try {
      // Load review preview for product
      const reviewData = await productApi.getProductReviews(product.id, { page: 1, page_size: 5 });
      setDetailReviews(reviewData.items || []);
      setDetailReviewsTotal(reviewData.total || 0);
    } catch (e) {
      console.warn('Could not load reviews for product:', e);
    }

    try {
      // Load QR payload
      const qrData = await productApi.getQrData(product.id);
      setDetailQr(qrData);
    } catch (e) {
      console.warn('Could not load QR data for product:', e);
    } finally {
      setDetailLoading(false);
    }
  };

  // Quick navigation to reviews of a product
  const handleViewReviewsOfProduct = (productId) => {
    setIsDetailModalOpen(false);
    navigate(`/reviews?productId=${productId}`);
  };

  // Verification status badge helper
  const renderVerificationBadge = (status) => {
    const norm = (status || '').toLowerCase();
    let badgeClass = 'badge-neutral';
    if (norm === 'verified') badgeClass = 'badge-success';
    else if (norm === 'pending') badgeClass = 'badge-warning';
    else if (norm === 'revoked') badgeClass = 'badge-danger';

    return (
      <span className={`badge ${badgeClass}`}>
        {getVerificationStatusLabel(status)}
      </span>
    );
  };

  // Summary Metrics calculated from loaded data
  const verifiedCount = products.filter(p => (p.verification_status || '').toLowerCase() === 'verified').length;
  const pendingCount = products.filter(p => (p.verification_status || '').toLowerCase() === 'pending').length;
  const revokedCount = products.filter(p => (p.verification_status || '').toLowerCase() === 'revoked').length;

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
          >
            <X size={16} />
          </button>
        </div>
      )}

      {/* Page Header */}
      <div className="page-header">
        <h1 className="page-title">Quản lý sản phẩm</h1>
        <p className="page-subtitle">Quản lý danh sách sản phẩm chính hãng, tra cứu xác thực QR và liên kết đánh giá</p>
      </div>

      {/* Summary KPI Cards */}
      <div className="grid-4">
        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Tổng sản phẩm</h3>
            <div className="kpi-icon primary"><Package size={20} /></div>
          </div>
          <p className="kpi-value">{totalProducts}</p>
          <p className="kpi-footer">Số lượng sản phẩm trong hệ thống</p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đã xác minh</h3>
            <div className="kpi-icon success"><ShieldCheck size={20} /></div>
          </div>
          <p className="kpi-value">{verifiedCount}</p>
          <p className="kpi-footer"><span className="text-success">Chính hãng</span> trên trang hiện tại</p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Chờ xác minh</h3>
            <div className="kpi-icon warning"><AlertCircle size={20} /></div>
          </div>
          <p className="kpi-value">{pendingCount}</p>
          <p className="kpi-footer">Cần kiểm tra hồ sơ sản phẩm</p>
        </div>

        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đã thu hồi</h3>
            <div className="kpi-icon danger" style={{ backgroundColor: 'rgba(220, 38, 38, 0.1)', color: 'var(--danger)' }}>
              <ShieldAlert size={20} />
            </div>
          </div>
          <p className="kpi-value">{revokedCount}</p>
          <p className="kpi-footer">Sản phẩm bị thu hồi xác thực</p>
        </div>
      </div>

      {/* Toolbar & Filters */}
      <div className="card" style={{ marginBottom: 'var(--spacing-6)', padding: 'var(--spacing-4)' }}>
        <div className="flex items-center" style={{ justifyContent: 'space-between', flexWrap: 'wrap', gap: 'var(--spacing-4)' }}>

          <div className="flex items-center" style={{ gap: 'var(--spacing-3)', flex: 1, minWidth: '320px', flexWrap: 'wrap' }}>
            {/* Search Input (Server-side) */}
            <div className="search-wrapper" style={{ flex: 1, minWidth: '240px', maxWidth: '380px' }}>
              <Search className="search-icon" size={18} />
              <input
                type="text"
                className="search-input"
                placeholder="Tìm theo tên, mã SP, thương hiệu..."
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

            {/* Category Filter */}
            <select
              className="form-input"
              value={categoryFilter}
              onChange={(e) => {
                setCategoryFilter(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: '170px' }}
              aria-label="Lọc theo danh mục"
            >
              <option value="All">Tất cả danh mục</option>
              {categories.filter(c => c !== 'All').map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            {/* Clear filters button */}
            {(searchTerm || categoryFilter !== 'All') && (
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

          {/* Add Product Button (Only for seller/admin) */}
          {isSellerOrAdmin ? (
            <button className="btn btn-primary" onClick={handleOpenAdd}>
              <Plus size={18} />
              <span>Thêm sản phẩm mới</span>
            </button>
          ) : (
            <button
              className="btn btn-outline"
              disabled
              title="Chỉ Người bán hoặc Quản trị viên mới có quyền thêm sản phẩm"
              style={{ opacity: 0.6, cursor: 'not-allowed' }}
            >
              <Plus size={18} />
              <span>Thêm sản phẩm (Giới hạn quyền)</span>
            </button>
          )}
        </div>
      </div>

      {/* Product Data Table */}
      <div className="table-wrapper">
        <div className="table-header flex items-center" style={{ justifyContent: 'space-between' }}>
          <h3 style={{ margin: 0 }}>Danh sách sản phẩm ({totalProducts})</h3>
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
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th style={{ width: '130px' }}>Mã SP</th>
                <th>Sản phẩm</th>
                <th>Danh mục</th>
                <th>Thương hiệu</th>
                <th>Đơn giá</th>
                <th>Xác thực</th>
                <th style={{ textAlign: 'right', width: '140px' }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <Loader2 size={36} className="animate-spin text-primary" />
                      <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>Đang tải dữ liệu sản phẩm...</p>
                    </div>
                  </td>
                </tr>
              ) : apiError ? (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <AlertCircle size={40} className="text-danger" />
                      <p style={{ margin: 0, fontWeight: 600, color: 'var(--danger)' }}>{apiError}</p>
                      <p className="text-muted" style={{ margin: 0, fontSize: '0.875rem' }}>
                        Kiểm tra kết nối Backend API (http://127.0.0.1:8001) và nhấn Thử lại.
                      </p>
                      <button className="btn btn-outline" onClick={fetchProducts} style={{ marginTop: 'var(--spacing-2)' }}>
                        <RotateCcw size={16} /> Thử lại
                      </button>
                    </div>
                  </td>
                </tr>
              ) : products.length > 0 ? (
                products.map((product) => (
                  <tr key={product.id}>
                    <td>
                      <span style={{ fontWeight: 600, fontFamily: 'monospace', color: 'var(--primary)', fontSize: '0.875rem' }}>
                        {product.product_code || `SP-${product.id}`}
                      </span>
                    </td>
                    <td>
                      <div className="flex items-center gap-3">
                        <div style={{
                          width: '42px',
                          height: '42px',
                          backgroundColor: 'rgba(37, 99, 235, 0.08)',
                          borderRadius: 'var(--radius-md)',
                          border: '1px solid var(--border)',
                          display: 'flex',
                          alignItems: 'center',
                          justifyContent: 'center',
                          color: 'var(--primary)',
                          flexShrink: 0
                        }}>
                          <Package size={22} />
                        </div>
                        <div>
                          <div style={{ fontWeight: 600, color: 'var(--text-main)', marginBottom: '2px' }}>
                            {product.name}
                          </div>
                          <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                            {product.created_at ? `Tạo: ${new Date(product.created_at).toLocaleDateString('vi-VN')}` : 'Chưa có thông tin'}
                          </div>
                        </div>
                      </div>
                    </td>
                    <td>
                      <span className="category-chip">{product.category || 'Chưa phân loại'}</span>
                    </td>
                    <td>
                      <span style={{ color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                        {product.brand || '—'}
                      </span>
                    </td>
                    <td>
                      <span style={{ fontWeight: 600 }}>{formatCurrency(product.price)}</span>
                    </td>
                    <td>
                      {renderVerificationBadge(product.verification_status)}
                    </td>
                    <td style={{ textAlign: 'right' }}>
                      <div className="flex items-center" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-1)' }}>
                        <button
                          className="btn-icon"
                          title="Xem chi tiết sản phẩm"
                          onClick={() => handleOpenDetail(product)}
                          aria-label={`Xem chi tiết ${product.name}`}
                        >
                          <Eye size={18} />
                        </button>

                        {isSellerOrAdmin && (
                          <>
                            <button
                              className="btn-icon"
                              title="Chỉnh sửa sản phẩm"
                              onClick={() => handleOpenEdit(product)}
                              aria-label={`Sửa ${product.name}`}
                            >
                              <Edit size={18} />
                            </button>
                            <button
                              className="btn-icon danger"
                              title="Xóa sản phẩm"
                              onClick={() => handleOpenDelete(product)}
                              aria-label={`Xóa ${product.name}`}
                            >
                              <Trash2 size={18} />
                            </button>
                          </>
                        )}
                      </div>
                    </td>
                  </tr>
                ))
              ) : (
                <tr>
                  <td colSpan="7" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <Package size={48} className="text-muted" opacity={0.4} />
                      <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>
                        {debouncedSearch || categoryFilter !== 'All' ? 'Không tìm thấy sản phẩm nào phù hợp' : 'Chưa có sản phẩm nào'}
                      </p>
                      <p className="text-muted" style={{ margin: 0, fontSize: '0.875rem' }}>
                        {debouncedSearch || categoryFilter !== 'All'
                          ? 'Thử điều chỉnh từ khóa tìm kiếm hoặc bấm "Đặt lại" để xem toàn bộ danh mục.'
                          : 'Bắt đầu bằng cách thêm sản phẩm mới vào hệ thống.'}
                      </p>
                      {(debouncedSearch || categoryFilter !== 'All') && (
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

        {/* Pagination Section (Server-side) */}
        {!loading && totalProducts > 0 && (
          <div className="pagination-container">
            <div className="pagination-info">
              Hiển thị <strong>{(safeCurrentPage - 1) * pageSize + 1}</strong> - <strong>{Math.min(safeCurrentPage * pageSize, totalProducts)}</strong> trên tổng số <strong>{totalProducts}</strong> sản phẩm
            </div>

            <div className="pagination-controls">
              <button
                className="page-btn"
                onClick={() => setCurrentPage(p => Math.max(p - 1, 1))}
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
                onClick={() => setCurrentPage(p => Math.min(p + 1, totalPages))}
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
      {/* ADD / EDIT MODAL WITH STICKY FOOTER & INTERNAL SCROLL */}
      {/* ==================================================== */}
      {(isAddModalOpen || isEditModalOpen) && (
        <div className="modal-overlay" onClick={() => { setIsAddModalOpen(false); setIsEditModalOpen(false); }}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{
              maxWidth: '580px',
              maxHeight: '90vh',
              display: 'flex',
              flexDirection: 'column',
              overflow: 'hidden'
            }}
          >
            <div className="modal-header">
              <h2 className="modal-title">
                {isAddModalOpen ? 'Thêm sản phẩm mới' : `Chỉnh sửa: ${selectedProduct?.name}`}
              </h2>
              <button
                className="modal-close"
                onClick={() => { setIsAddModalOpen(false); setIsEditModalOpen(false); }}
                aria-label="Đóng hộp thoại"
              >
                <X size={20} />
              </button>
            </div>

            <form
              onSubmit={isAddModalOpen ? handleAddSubmit : handleEditSubmit}
              noValidate
              style={{
                display: 'flex',
                flexDirection: 'column',
                flex: 1,
                minHeight: 0,
                overflow: 'hidden'
              }}
            >
              <div
                className="modal-body"
                style={{
                  flex: 1,
                  minHeight: 0,
                  overflowY: 'auto'
                }}
              >
                {/* Server Error Alert */}
                {formServerError && (
                  <div style={{
                    display: 'flex',
                    alignItems: 'center',
                    gap: 'var(--spacing-2)',
                    backgroundColor: 'rgba(220, 38, 38, 0.1)',
                    color: 'var(--danger)',
                    padding: 'var(--spacing-3)',
                    borderRadius: 'var(--radius-md)',
                    marginBottom: 'var(--spacing-4)',
                    fontSize: '0.875rem'
                  }}>
                    <AlertCircle size={16} style={{ flexShrink: 0 }} />
                    <span>{formServerError}</span>
                  </div>
                )}

                {/* Product Name */}
                <div className="form-group">
                  <label className="form-label">
                    Tên sản phẩm <span style={{ color: 'var(--danger)' }}>*</span>
                  </label>
                  <input
                    type="text"
                    name="name"
                    className={`form-input ${formErrors.name ? 'is-invalid' : ''}`}
                    value={formData.name}
                    onChange={handleFormChange}
                    placeholder="VD: Tai nghe Bluetooth Pro ANC"
                    disabled={isSubmitting}
                  />
                  {formErrors.name && (
                    <div className="form-error">
                      <AlertCircle size={14} /> {formErrors.name}
                    </div>
                  )}
                </div>

                {/* Product Code & Category */}
                <div className="grid-2" style={{ marginBottom: 0, gap: 'var(--spacing-4)' }}>
                  <div className="form-group">
                    <label className="form-label">
                      Mã sản phẩm {isAddModalOpen && <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>(bỏ trống để tự tạo)</span>}
                    </label>
                    <input
                      type="text"
                      name="product_code"
                      className={`form-input ${formErrors.product_code ? 'is-invalid' : ''}`}
                      value={formData.product_code}
                      onChange={handleFormChange}
                      placeholder="VD: SP001"
                      disabled={isSubmitting}
                    />
                    {formErrors.product_code && (
                      <div className="form-error">
                        <AlertCircle size={14} /> {formErrors.product_code}
                      </div>
                    )}
                  </div>

                  <div className="form-group">
                    <label className="form-label">
                      Danh mục <span style={{ color: 'var(--danger)' }}>*</span>
                    </label>
                    <select
                      name="category"
                      className="form-input"
                      value={formData.category}
                      onChange={handleFormChange}
                      disabled={isSubmitting}
                    >
                      <option value="Điện tử">Điện tử</option>
                      <option value="Thời trang">Thời trang</option>
                      <option value="Gia dụng">Gia dụng</option>
                      <option value="Mỹ phẩm">Mỹ phẩm</option>
                      <option value="Khác">Khác</option>
                    </select>
                  </div>
                </div>

                {/* Price & Brand */}
                <div className="grid-2" style={{ marginBottom: 0, gap: 'var(--spacing-4)' }}>
                  <div className="form-group">
                    <label className="form-label">
                      Giá niêm yết (VNĐ) <span style={{ color: 'var(--danger)' }}>*</span>
                    </label>
                    <input
                      type="number"
                      min="1000"
                      step="1000"
                      name="price"
                      className={`form-input ${formErrors.price ? 'is-invalid' : ''}`}
                      value={formData.price}
                      onChange={handleFormChange}
                      placeholder="VD: 499000"
                      disabled={isSubmitting}
                    />
                    {formErrors.price && (
                      <div className="form-error">
                        <AlertCircle size={14} /> {formErrors.price}
                      </div>
                    )}
                  </div>

                  <div className="form-group">
                    <label className="form-label">Thương hiệu</label>
                    <input
                      type="text"
                      name="brand"
                      className="form-input"
                      value={formData.brand}
                      onChange={handleFormChange}
                      placeholder="VD: SonicAura"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                {/* SKU & Origin */}
                <div className="grid-2" style={{ marginBottom: 0, gap: 'var(--spacing-4)' }}>
                  <div className="form-group">
                    <label className="form-label">Mã SKU</label>
                    <input
                      type="text"
                      name="sku"
                      className="form-input"
                      value={formData.sku}
                      onChange={handleFormChange}
                      placeholder="VD: ANC-PRO-01"
                      disabled={isSubmitting}
                    />
                  </div>

                  <div className="form-group">
                    <label className="form-label">Xuất xứ</label>
                    <input
                      type="text"
                      name="origin"
                      className="form-input"
                      value={formData.origin}
                      onChange={handleFormChange}
                      placeholder="VD: Việt Nam"
                      disabled={isSubmitting}
                    />
                  </div>
                </div>

                {/* Manufacturer */}
                <div className="form-group">
                  <label className="form-label">Nhà sản xuất</label>
                  <input
                    type="text"
                    name="manufacturer"
                    className="form-input"
                    value={formData.manufacturer}
                    onChange={handleFormChange}
                    placeholder="VD: Công ty TNHH SonicAura"
                    disabled={isSubmitting}
                  />
                </div>

                {/* Description */}
                <div className="form-group">
                  <label className="form-label">Mô tả sản phẩm</label>
                  <textarea
                    name="description"
                    className="form-input form-textarea"
                    value={formData.description}
                    onChange={handleFormChange}
                    placeholder="Nhập thông tin tính năng, chất liệu hoặc nguồn gốc chính hãng..."
                    rows={3}
                    disabled={isSubmitting}
                  />
                </div>

              </div>

              <div
                className="modal-footer"
                style={{
                  flexShrink: 0,
                  backgroundColor: 'var(--surface)'
                }}
              >
                <button
                  type="button"
                  className="btn btn-outline"
                  disabled={isSubmitting}
                  onClick={() => { setIsAddModalOpen(false); setIsEditModalOpen(false); }}
                >
                  Hủy
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={isSubmitting}
                  style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
                >
                  {isSubmitting ? (
                    <>
                      <Loader2 size={16} className="animate-spin" />
                      <span>Đang lưu...</span>
                    </>
                  ) : (
                    <span>{isAddModalOpen ? 'Thêm sản phẩm' : 'Lưu thay đổi'}</span>
                  )}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* PRODUCT DETAILS MODAL (Real Backend Data + QR) */}
      {/* ==================================================== */}
      {isDetailModalOpen && selectedProduct && (
        <div className="modal-overlay" onClick={() => setIsDetailModalOpen(false)}>
          <div
            className="modal-content"
            onClick={(e) => e.stopPropagation()}
            style={{ maxWidth: '640px', maxHeight: '90vh', display: 'flex', flexDirection: 'column' }}
          >
            <div className="modal-header">
              <div className="flex items-center gap-3">
                <div style={{
                  width: '36px',
                  height: '36px',
                  backgroundColor: 'rgba(37, 99, 235, 0.1)',
                  borderRadius: 'var(--radius-md)',
                  color: 'var(--primary)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  <Package size={20} />
                </div>
                <div>
                  <h2 className="modal-title" style={{ fontSize: '1.15rem' }}>{selectedProduct.name}</h2>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>Mã: {selectedProduct.product_code || `SP-${selectedProduct.id}`}</span>
                </div>
              </div>
              <button
                className="modal-close"
                onClick={() => setIsDetailModalOpen(false)}
                aria-label="Đóng hộp thoại"
              >
                <X size={20} />
              </button>
            </div>

            <div className="modal-body" style={{ flex: 1, overflowY: 'auto' }}>
              {/* Product Specs */}
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Danh mục</span>
                  <span className="detail-value">{selectedProduct.category || 'Chưa phân loại'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Giá niêm yết</span>
                  <span className="detail-value" style={{ color: 'var(--primary)', fontWeight: 700 }}>
                    {formatCurrency(selectedProduct.price)}
                  </span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Xác thực sản phẩm</span>
                  <div>
                    {renderVerificationBadge(selectedProduct.verification_status)}
                  </div>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Thương hiệu</span>
                  <span className="detail-value">{selectedProduct.brand || '—'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Mã SKU</span>
                  <span className="detail-value">{selectedProduct.sku || '—'}</span>
                </div>
                <div className="detail-item">
                  <span className="detail-label">Xuất xứ</span>
                  <span className="detail-value">{selectedProduct.origin || '—'}</span>
                </div>
              </div>

              {/* Description */}
              <div style={{ marginTop: 'var(--spacing-3)' }}>
                <span className="detail-label">Mô tả sản phẩm</span>
                <p style={{
                  margin: 'var(--spacing-2) 0',
                  backgroundColor: 'var(--background)',
                  padding: 'var(--spacing-3)',
                  borderRadius: 'var(--radius-md)',
                  fontSize: '0.875rem',
                  lineHeight: 1.6
                }}>
                  {selectedProduct.description || 'Chưa có mô tả chi tiết cho sản phẩm này.'}
                </p>
              </div>

              {/* QR Verification Section */}
              <div style={{
                marginTop: 'var(--spacing-4)',
                padding: 'var(--spacing-3)',
                border: '1px solid var(--border)',
                borderRadius: 'var(--radius-md)',
                backgroundColor: 'var(--surface)'
              }}>
                <div className="flex items-center gap-2" style={{ marginBottom: 'var(--spacing-2)' }}>
                  <QrCode size={18} className="text-primary" />
                  <span style={{ fontWeight: 600, fontSize: '0.9rem' }}>Mã QR Xác thực chính hãng</span>
                </div>

                <div className="flex items-center gap-4" style={{ flexWrap: 'wrap' }}>
                  <div style={{
                    width: '100px',
                    height: '100px',
                    backgroundColor: '#fff',
                    padding: '4px',
                    borderRadius: 'var(--radius-sm)',
                    border: '1px solid var(--border)',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center'
                  }}>
                    <img
                      src={productApi.getQrImageUrl(selectedProduct.id)}
                      alt={`QR Code ${selectedProduct.product_code}`}
                      style={{ width: '100%', height: '100%', objectFit: 'contain' }}
                      onError={(e) => {
                        e.target.style.display = 'none';
                        e.target.nextSibling.style.display = 'block';
                      }}
                    />
                    <div style={{ display: 'none', fontSize: '0.7rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
                      QR API
                    </div>
                  </div>

                  <div style={{ flex: 1, minWidth: '200px' }}>
                    <p style={{ margin: '0 0 6px 0', fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                      Dữ liệu QR: <code style={{ backgroundColor: 'var(--background)', padding: '2px 6px', borderRadius: '4px' }}>
                        {detailQr?.qr_payload || `FAKE-REVIEW|PRODUCT|${selectedProduct.product_code}`}
                      </code>
                    </p>
                    {detailQr?.verification_url && (
                      <p style={{ margin: 0, fontSize: '0.8rem' }}>
                        <a
                          href={detailQr.verification_url}
                          target="_blank"
                          rel="noopener noreferrer"
                          style={{ color: 'var(--primary)', textDecoration: 'none', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
                        >
                          <span>Liên kết xác thực trực tuyến</span>
                          <ExternalLink size={12} />
                        </a>
                      </p>
                    )}
                  </div>
                </div>
              </div>

              {/* Review Statistics for this product */}
              <div style={{ marginTop: 'var(--spacing-4)' }}>
                <span className="detail-label">Đánh giá của sản phẩm</span>
                {detailLoading ? (
                  <div style={{ padding: 'var(--spacing-3)', textAlign: 'center', fontSize: '0.875rem', color: 'var(--text-secondary)' }}>
                    <Loader2 size={16} className="animate-spin inline-block mr-2" /> Đang tải đánh giá...
                  </div>
                ) : detailReviews.length > 0 ? (
                  <div style={{ marginTop: 'var(--spacing-2)', display: 'flex', flexDirection: 'column', gap: 'var(--spacing-2)' }}>
                    {detailReviews.slice(0, 3).map((rev) => (
                      <div key={rev.id} style={{
                        padding: 'var(--spacing-2) var(--spacing-3)',
                        border: '1px solid var(--border)',
                        borderRadius: 'var(--radius-sm)',
                        backgroundColor: 'var(--background)',
                        fontSize: '0.825rem'
                      }}>
                        <div className="flex items-center justify-between" style={{ marginBottom: '4px' }}>
                          <span style={{ fontWeight: 600 }}>{rev.rating} ★</span>
                          {rev.prediction && (
                            <span className={`badge ${rev.prediction.predicted_label === 'fake' ? 'badge-danger' : 'badge-success'}`} style={{ fontSize: '0.7rem' }}>
                              {rev.prediction.predicted_label === 'fake' ? 'Nghi ngờ giả' : 'Đánh giá thật'}
                            </span>
                          )}
                        </div>
                        <p style={{ margin: 0, color: 'var(--text-main)', fontStyle: 'italic' }}>
                          "{rev.content}"
                        </p>
                      </div>
                    ))}
                    {detailReviewsTotal > 3 && (
                      <p style={{ margin: '4px 0 0 0', fontSize: '0.75rem', color: 'var(--text-secondary)', textAlign: 'center' }}>
                        Hiển thị 3 trong tổng số {detailReviewsTotal} đánh giá.
                      </p>
                    )}
                  </div>
                ) : (
                  <p style={{
                    margin: 'var(--spacing-2) 0 0 0',
                    padding: 'var(--spacing-3)',
                    backgroundColor: 'var(--background)',
                    borderRadius: 'var(--radius-md)',
                    fontSize: '0.825rem',
                    color: 'var(--text-secondary)'
                  }}>
                    Sản phẩm này chưa có đánh giá nào trên hệ thống.
                  </p>
                )}
              </div>
            </div>

            <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
              <button
                type="button"
                className="btn btn-primary"
                onClick={() => handleViewReviewsOfProduct(selectedProduct.id)}
              >
                <ExternalLink size={16} />
                <span>Xem tất cả đánh giá ({detailReviewsTotal})</span>
              </button>
              <button type="button" className="btn btn-outline" onClick={() => setIsDetailModalOpen(false)}>
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

      {/* ==================================================== */}
      {/* DELETE CONFIRMATION MODAL */}
      {/* ==================================================== */}
      {isDeleteModalOpen && selectedProduct && (
        <div className="modal-overlay" onClick={() => !isSubmitting && setIsDeleteModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '440px' }}>
            <div className="modal-body" style={{ textAlign: 'center', padding: 'var(--spacing-6)' }}>
              <div style={{ display: 'flex', justifyContent: 'center' }}>
                <div className="modal-confirm-icon">
                  <AlertTriangle size={28} />
                </div>
              </div>
              <h2 style={{ fontSize: '1.25rem', margin: '0 0 var(--spacing-2) 0' }}>Xác nhận xóa sản phẩm?</h2>
              <p className="text-muted" style={{ fontSize: '0.875rem', marginBottom: 'var(--spacing-4)' }}>
                Bạn có chắc chắn muốn xóa sản phẩm <strong>"{selectedProduct.name}"</strong> (Mã: <code>{selectedProduct.product_code || `SP-${selectedProduct.id}`}</code>)?
              </p>
              <div style={{
                backgroundColor: 'rgba(220, 38, 38, 0.05)',
                border: '1px solid rgba(220, 38, 38, 0.2)',
                borderRadius: 'var(--radius-md)',
                padding: 'var(--spacing-3)',
                fontSize: '0.8rem',
                color: 'var(--danger)',
                textAlign: 'left'
              }}>
                Lưu ý: Hành động này sẽ xóa sản phẩm khỏi cơ sở dữ liệu hệ thống. Dữ liệu không thể hoàn tác.
              </div>
            </div>
            <div className="modal-footer" style={{ justifyContent: 'center', gap: 'var(--spacing-3)' }}>
              <button
                type="button"
                className="btn btn-outline"
                disabled={isSubmitting}
                onClick={() => setIsDeleteModalOpen(false)}
              >
                Hủy bỏ
              </button>
              <button
                type="button"
                className="btn btn-danger"
                disabled={isSubmitting}
                onClick={handleConfirmDelete}
                style={{ display: 'flex', alignItems: 'center', gap: '6px' }}
              >
                {isSubmitting ? (
                  <>
                    <Loader2 size={16} className="animate-spin" />
                    <span>Đang xóa...</span>
                  </>
                ) : (
                  <>
                    <Trash2 size={16} />
                    <span>Xóa vĩnh viễn</span>
                  </>
                )}
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
