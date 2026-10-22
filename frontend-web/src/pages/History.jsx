import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Search, Calendar, ArrowRight, ExternalLink, Eye, RotateCcw, 
  Loader2, AlertCircle, AlertTriangle, ShieldCheck, ShieldAlert,
  Package, Star, Clock, Cpu, X, Info
} from 'lucide-react';
import { 
  predictionApi, 
  reviewApi, 
  productApi, 
  formatApiError 
} from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function History() {
  const navigate = useNavigate();
  const { user, isAuthenticated } = useAuth();

  // Primary history state from API
  const [historyList, setHistoryList] = useState([]);
  const [loading, setLoading] = useState(true);
  const [apiError, setApiError] = useState('');

  // Associated review and product caches
  const [reviewCache, setReviewCache] = useState({});
  const [productMap, setProductMap] = useState({});

  // Local filter states
  const [searchTerm, setSearchTerm] = useState('');
  const [dateFilter, setDateFilter] = useState('');
  const [resultFilter, setResultFilter] = useState('All'); // 'All' | 'real' | 'fake'

  // Pagination state (Client-side over loaded records)
  const [currentPage, setCurrentPage] = useState(1);
  const [pageSize, setPageSize] = useState(10);

  // Detail Modal state
  const [selectedItem, setSelectedItem] = useState(null);
  const [isDetailModalOpen, setIsDetailModalOpen] = useState(false);

  // Prevent background scrolling when modal is open
  useEffect(() => {
    if (isDetailModalOpen) {
      document.body.style.overflow = 'hidden';
    } else {
      document.body.style.overflow = '';
    }
    return () => {
      document.body.style.overflow = '';
    };
  }, [isDetailModalOpen]);

  // ==========================================
  // LOAD PRODUCTS ONCE FOR ID -> NAME LOOKUP
  // ==========================================
  useEffect(() => {
    let isMounted = true;
    async function loadProducts() {
      try {
        const data = await productApi.getProducts({ page: 1, page_size: 100 });
        if (isMounted) {
          const map = {};
          (data.items || []).forEach((p) => {
            map[p.id] = p.name;
          });
          setProductMap(map);
        }
      } catch (err) {
        console.warn('Could not load products for history resolution:', err);
      }
    }
    loadProducts();
    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // FETCH USER PREDICTION HISTORY (GET /api/predictions/history/me?limit=50)
  // ==========================================
  const fetchHistory = useCallback(async () => {
    setLoading(true);
    setApiError('');
    try {
      // Limit to 50 records per requirements
      const data = await predictionApi.getMyHistory(50);
      setHistoryList(Array.isArray(data) ? data : []);
    } catch (err) {
      setHistoryList([]);
      if (err.status === 401) {
        setApiError('Phiên đăng nhập đã hết hạn. Vui lòng đăng nhập lại.');
      } else if (err.message && err.message.includes('fetch')) {
        setApiError('Không thể kết nối đến máy chủ.');
      } else {
        setApiError(formatApiError(err, 'Không thể tải lịch sử kiểm tra.'));
      }
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    fetchHistory();
  }, [fetchHistory]);

  // ==========================================
  // RESOLVE REVIEWS FOR UNIQUE review_id
  // Caches review details during page load
  // ==========================================
  useEffect(() => {
    if (!historyList.length) return;

    const uniqueReviewIds = [...new Set(historyList.map((h) => h.review_id).filter(Boolean))];
    const uncachedIds = uniqueReviewIds.filter((id) => !reviewCache[id]);

    if (!uncachedIds.length) return;

    let isMounted = true;
    Promise.allSettled(uncachedIds.map((id) => reviewApi.getReview(id)))
      .then((results) => {
        if (!isMounted) return;
        setReviewCache((prev) => {
          const next = { ...prev };
          results.forEach((res, index) => {
            if (res.status === 'fulfilled' && res.value) {
              next[uncachedIds[index]] = res.value;
            }
          });
          return next;
        });
      });

    return () => {
      isMounted = false;
    };
  }, [historyList, reviewCache]);

  // Helper to resolve review content
  const getReviewContent = useCallback((item) => {
    const rev = reviewCache[item.review_id];
    if (rev && rev.content) return rev.content;
    return `Đánh giá #${item.review_id}`;
  }, [reviewCache]);

  // Helper to resolve product name
  const getProductName = useCallback((item) => {
    const rev = reviewCache[item.review_id];
    if (rev && rev.product_id) {
      return productMap[rev.product_id] || `Sản phẩm #${rev.product_id}`;
    }
    return `Review #${item.review_id}`;
  }, [reviewCache, productMap]);

  // Helper to resolve review rating
  const getReviewRating = useCallback((item) => {
    const rev = reviewCache[item.review_id];
    return rev ? rev.rating : null;
  }, [reviewCache]);

  // Helper to format date
  const formatDate = (dateString) => {
    if (!dateString) return '—';
    try {
      const d = new Date(dateString);
      return d.toLocaleDateString('vi-VN') + ' ' + d.toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
    } catch {
      return dateString;
    }
  };

  // Check fallback heuristic
  const isFallbackModel = (item) => {
    if (!item) return false;
    return item.model_name === 'fallback-heuristic' || item.model_version === 'dev-only';
  };

  // ==========================================
  // LOCAL FILTERS
  // ==========================================
  const filteredHistory = useMemo(() => {
    return historyList.filter((item) => {
      const content = getReviewContent(item).toLowerCase();
      const product = getProductName(item).toLowerCase();
      const idStr = String(item.id);
      const revIdStr = String(item.review_id);
      const term = searchTerm.toLowerCase().trim();

      const matchesSearch = !term || 
        content.includes(term) || 
        product.includes(term) || 
        idStr.includes(term) || 
        revIdStr.includes(term);

      const matchesResult = 
        resultFilter === 'All' || 
        item.predicted_label === resultFilter;

      let matchesDate = true;
      if (dateFilter && item.created_at) {
        matchesDate = item.created_at.startsWith(dateFilter);
      }

      return matchesSearch && matchesResult && matchesDate;
    });
  }, [historyList, searchTerm, resultFilter, dateFilter, getReviewContent, getProductName]);

  // Reset filters
  const handleResetFilters = () => {
    setSearchTerm('');
    setDateFilter('');
    setResultFilter('All');
    setCurrentPage(1);
  };

  // Pagination calculation
  const totalPages = Math.ceil(filteredHistory.length / pageSize) || 1;
  const safeCurrentPage = Math.min(currentPage, totalPages);
  const paginatedHistory = useMemo(() => {
    const startIndex = (safeCurrentPage - 1) * pageSize;
    return filteredHistory.slice(startIndex, startIndex + pageSize);
  }, [filteredHistory, safeCurrentPage, pageSize]);

  // Open detail modal
  const handleOpenDetail = (item) => {
    setSelectedItem(item);
    setIsDetailModalOpen(true);
  };

  // Navigate to Result page with full context
  const handleNavigateToResult = (item) => {
    const rev = reviewCache[item.review_id];
    navigate('/result', {
      state: {
        analysis: item,
        content: rev ? rev.content : `Đánh giá #${item.review_id}`,
        productName: rev ? (productMap[rev.product_id] || `Sản phẩm #${rev.product_id}`) : null,
        rating: rev ? rev.rating : null,
        review: rev ? {
          id: rev.id,
          productName: productMap[rev.product_id] || `Sản phẩm #${rev.product_id}`,
          reviewerName: `Người dùng #${rev.user_id}`,
          rating: rev.rating,
          content: rev.content,
          date: rev.created_at ? formatDate(rev.created_at) : '',
          prediction: item
        } : null
      }
    });
  };

  return (
    <div>
      {/* Page Header */}
      <div className="page-header flex items-center justify-between" style={{ flexWrap: 'wrap', gap: 'var(--spacing-3)' }}>
        <div>
          <h1 className="page-title">Lịch sử kiểm tra</h1>
          <p className="page-subtitle">Xem lại các đánh giá đã được phân tích bởi hệ thống</p>
        </div>
        <button 
          className="btn btn-primary"
          onClick={() => navigate('/reviews')}
          style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--spacing-2)' }}
        >
          <span>Đến Quản lý đánh giá</span>
          <ArrowRight size={16} />
        </button>
      </div>

      {/* Toolbar & Filters */}
      <div className="toolbar" style={{ marginBottom: 'var(--spacing-6)' }}>
        <div className="card" style={{ padding: 'var(--spacing-4)' }}>
          <div className="flex gap-4" style={{ flexWrap: 'wrap', alignItems: 'center' }}>
            {/* Search Input */}
            <div className="search-wrapper" style={{ flex: 1, minWidth: '240px', maxWidth: '380px' }}>
              <Search className="search-icon" size={18} />
              <input 
                type="text" 
                className="search-input" 
                placeholder="Tìm nội dung, sản phẩm, mã..." 
                value={searchTerm}
                onChange={(e) => {
                  setSearchTerm(e.target.value);
                  setCurrentPage(1);
                }}
                style={{ width: '100%' }}
              />
              {searchTerm && (
                <button 
                  onClick={() => {
                    setSearchTerm('');
                    setCurrentPage(1);
                  }}
                  style={{ position: 'absolute', right: '10px', background: 'none', border: 'none', color: 'var(--text-secondary)', cursor: 'pointer' }}
                  title="Xóa tìm kiếm"
                >
                  <X size={16} />
                </button>
              )}
            </div>

            {/* Date Filter */}
            <div className="search-wrapper" style={{ width: '190px' }}>
              <Calendar className="search-icon" size={18} />
              <input 
                type="date" 
                className="form-input" 
                value={dateFilter}
                onChange={(e) => {
                  setDateFilter(e.target.value);
                  setCurrentPage(1);
                }}
                style={{ paddingLeft: 'calc(var(--spacing-8) + var(--spacing-2))', width: '100%' }}
                aria-label="Lọc theo ngày"
              />
            </div>

            {/* Classification Filter (real, fake) */}
            <select 
              className="form-input"
              value={resultFilter}
              onChange={(e) => {
                setResultFilter(e.target.value);
                setCurrentPage(1);
              }}
              style={{ width: '200px' }}
              aria-label="Lọc theo kết quả"
            >
              <option value="All">Tất cả kết quả</option>
              <option value="real">🟢 Đánh giá gốc</option>
              <option value="fake">🔴 Đáng ngờ</option>
            </select>

            {/* Reset Filters button */}
            {(searchTerm || dateFilter || resultFilter !== 'All') && (
              <button 
                className="btn btn-outline"
                onClick={handleResetFilters}
                style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
                title="Đặt lại bộ lọc"
              >
                <RotateCcw size={15} />
                <span>Đặt lại</span>
              </button>
            )}
          </div>
        </div>
      </div>

      {/* History Data Table */}
      <div className="table-wrapper">
        <div className="table-header flex items-center" style={{ justifyContent: 'space-between', padding: 'var(--spacing-4)' }}>
          <h3 style={{ margin: 0 }}>
            Danh sách lịch sử phân tích ({filteredHistory.length})
          </h3>
          <div className="flex items-center gap-2">
            <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Mỗi trang:</span>
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
              <option value={15}>15</option>
              <option value={20}>20</option>
            </select>
          </div>
        </div>

        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th style={{ width: '90px' }}>Mã</th>
                <th>Nội dung đánh giá</th>
                <th>Sản phẩm</th>
                <th style={{ width: '150px' }}>Kết quả</th>
                <th style={{ width: '130px' }}>Điểm phân tích</th>
                <th style={{ width: '160px' }}>Mô hình</th>
                <th style={{ width: '160px' }}>Thời gian</th>
                <th style={{ textAlign: 'right', width: '110px' }}>Thao tác</th>
              </tr>
            </thead>
            <tbody>
              {loading ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <Loader2 size={36} className="animate-spin text-primary" />
                      <p style={{ margin: 0, fontWeight: 500, color: 'var(--text-main)' }}>Đang tải lịch sử kiểm tra...</p>
                    </div>
                  </td>
                </tr>
              ) : apiError ? (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
                      <AlertCircle size={40} className="text-danger" />
                      <p style={{ margin: 0, fontWeight: 600, color: 'var(--danger)' }}>{apiError}</p>
                      <button className="btn btn-outline" onClick={fetchHistory} style={{ marginTop: 'var(--spacing-2)' }}>
                        <RotateCcw size={16} /> Thử lại
                      </button>
                    </div>
                  </td>
                </tr>
              ) : paginatedHistory.length > 0 ? (
                paginatedHistory.map((item) => {
                  const isFake = item.predicted_label === 'fake';
                  const isFallback = isFallbackModel(item);
                  const content = getReviewContent(item);
                  const product = getProductName(item);

                  return (
                    <tr key={item.id}>
                      <td className="text-muted" style={{ fontFamily: 'monospace', fontWeight: 600, fontSize: '0.85rem' }}>
                        #{item.id}
                      </td>
                      <td style={{ maxWidth: '280px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={content}>
                        "{content}"
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: '180px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={product}>
                        {product}
                      </td>
                      <td>
                        <span className={`badge ${isFake ? 'badge-danger' : 'badge-success'}`}>
                          {isFake ? 'Đáng ngờ' : 'Đánh giá gốc'}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600 }}>
                        {item.confidence_score !== undefined && item.confidence_score !== null 
                          ? (typeof item.confidence_score === 'number' ? item.confidence_score.toFixed(2) : item.confidence_score)
                          : '—'}
                      </td>
                      <td>
                        <div style={{ fontSize: '0.8rem' }}>
                          <span style={{ fontFamily: 'monospace' }}>{item.model_name || '—'}</span>
                          {isFallback && (
                            <span 
                              className="badge badge-warning" 
                              style={{ display: 'inline-block', marginLeft: '6px', fontSize: '0.65rem', padding: '2px 6px' }}
                              title="Kết quả thử nghiệm từ heuristic fallback"
                            >
                              Thử nghiệm
                            </span>
                          )}
                        </div>
                      </td>
                      <td className="text-muted" style={{ fontSize: '0.85rem' }}>
                        {formatDate(item.created_at)}
                      </td>
                      <td style={{ textAlign: 'right' }}>
                        <div className="flex items-center" style={{ justifyContent: 'flex-end', gap: 'var(--spacing-1)' }}>
                          <button 
                            className="btn-icon" 
                            title="Xem chi tiết phân tích" 
                            onClick={() => handleOpenDetail(item)}
                            aria-label={`Xem chi tiết bản ghi ${item.id}`}
                          >
                            <Eye size={17} />
                          </button>
                          <button 
                            className="btn-icon" 
                            title="Xem tại trang Kết quả phân tích" 
                            onClick={() => handleNavigateToResult(item)}
                            aria-label={`Mở trang kết quả cho ${item.id}`}
                            style={{ color: 'var(--primary)' }}
                          >
                            <ExternalLink size={17} />
                          </button>
                        </div>
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="8" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-2)' }}>
                      <Clock size={44} className="text-muted" opacity={0.4} />
                      <p style={{ margin: 0, fontWeight: 600, color: 'var(--text-main)', fontSize: '1rem' }}>
                        {searchTerm || dateFilter || resultFilter !== 'All' 
                          ? 'Không tìm thấy lịch sử nào phù hợp với bộ lọc' 
                          : 'Chưa có lịch sử phân tích'}
                      </p>
                      <p className="text-muted" style={{ margin: 0, fontSize: '0.875rem', maxWidth: '420px', lineHeight: 1.5 }}>
                        {searchTerm || dateFilter || resultFilter !== 'All'
                          ? 'Hãy thử điều chỉnh bộ lọc hoặc bấm "Đặt lại" để xem toàn bộ lịch sử.'
                          : 'Lịch sử hiện chỉ bao gồm các kết quả phân tích của đánh giá đã được lưu.'}
                      </p>
                      {(searchTerm || dateFilter || resultFilter !== 'All') && (
                        <button className="btn btn-outline" onClick={handleResetFilters} style={{ marginTop: 'var(--spacing-2)' }}>
                          <RotateCcw size={15} /> Đặt lại bộ lọc
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>

        {/* Client-side Pagination */}
        {!loading && filteredHistory.length > 0 && (
          <div className="pagination-container" style={{ padding: 'var(--spacing-4)' }}>
            <div className="pagination-info">
              Hiển thị <strong>{(safeCurrentPage - 1) * pageSize + 1}</strong> - <strong>{Math.min(safeCurrentPage * pageSize, filteredHistory.length)}</strong> trên tổng số <strong>{filteredHistory.length}</strong> bản ghi
            </div>

            <div className="pagination-controls">
              <button 
                className="page-btn" 
                onClick={() => setCurrentPage((p) => Math.max(p - 1, 1))}
                disabled={safeCurrentPage === 1}
                title="Trang trước"
              >
                Trước
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
                Sau
              </button>
            </div>
          </div>
        )}
      </div>

      {/* ==================================================== */}
      {/* DETAIL MODAL FOR HISTORY RECORD                      */}
      {/* ==================================================== */}
      {isDetailModalOpen && selectedItem && (
        <div className="modal-overlay" onClick={() => setIsDetailModalOpen(false)}>
          <div className="modal-content" onClick={(e) => e.stopPropagation()} style={{ maxWidth: '600px' }}>
            <div className="modal-header">
              <div className="flex items-center gap-3">
                <div style={{
                  width: '36px',
                  height: '36px',
                  backgroundColor: selectedItem.predicted_label === 'fake' 
                    ? 'rgba(220, 38, 38, 0.1)' 
                    : 'rgba(22, 163, 74, 0.1)',
                  borderRadius: 'var(--radius-md)',
                  color: selectedItem.predicted_label === 'fake' ? 'var(--danger)' : 'var(--success)',
                  display: 'flex',
                  alignItems: 'center',
                  justifyContent: 'center'
                }}>
                  {selectedItem.predicted_label === 'fake' ? <ShieldAlert size={20} /> : <ShieldCheck size={20} />}
                </div>
                <div>
                  <h2 className="modal-title" style={{ fontSize: '1.15rem' }}>
                    Chi tiết bản ghi phân tích #{selectedItem.id}
                  </h2>
                  <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                    Thời gian: {formatDate(selectedItem.created_at)}
                  </span>
                </div>
              </div>
              <button className="modal-close" onClick={() => setIsDetailModalOpen(false)} aria-label="Đóng">✕</button>
            </div>

            <div className="modal-body">
              {/* Product and Rating Info */}
              <div className="detail-grid">
                <div className="detail-item">
                  <span className="detail-label">Sản phẩm liên kết</span>
                  <span className="detail-value" style={{ color: 'var(--primary)' }}>
                    {getProductName(selectedItem)}
                  </span>
                  <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
                    Mã đánh giá: #{selectedItem.review_id}
                  </span>
                </div>

                <div className="detail-item">
                  <span className="detail-label">Mức đánh giá gốc</span>
                  <div className="flex items-center gap-2">
                    {getReviewRating(selectedItem) ? (
                      <div className="star-rating" style={{ marginTop: '2px' }}>
                        {Array.from({ length: 5 }, (_, i) => (
                          <Star 
                            key={i} 
                            size={14} 
                            fill={i < getReviewRating(selectedItem) ? '#F59E0B' : 'none'} 
                            color={i < getReviewRating(selectedItem) ? '#F59E0B' : 'var(--border)'} 
                          />
                        ))}
                        <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', marginLeft: '4px' }}>
                          ({getReviewRating(selectedItem)} sao)
                        </span>
                      </div>
                    ) : (
                      <span className="detail-value text-muted">—</span>
                    )}
                  </div>
                </div>
              </div>

              {/* Review Content */}
              <div style={{ marginTop: 'var(--spacing-3)' }}>
                <span className="detail-label">Nội dung đánh giá</span>
                <div className={`quote-box ${selectedItem.predicted_label === 'fake' ? 'danger' : 'success'}`}>
                  "{getReviewContent(selectedItem)}"
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
                  <span className={`badge ${selectedItem.predicted_label === 'fake' ? 'badge-danger' : 'badge-success'}`}>
                    {selectedItem.predicted_label === 'fake' ? 'Đáng ngờ' : 'Đánh giá gốc'}
                  </span>
                </div>

                {/* Fallback Warning */}
                {isFallbackModel(selectedItem) && (
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
                      <strong>Kết quả thử nghiệm (fallback)</strong>: Backend hiện đang dùng cơ chế fallback dev-only.
                    </span>
                  </div>
                )}

                <div style={{ marginBottom: 'var(--spacing-3)' }}>
                  <div className="flex items-center justify-between" style={{ fontSize: '0.875rem', marginBottom: 'var(--spacing-1)' }}>
                    <span>Điểm phân tích:</span>
                    <strong style={{ fontSize: '1.05rem', color: selectedItem.predicted_label === 'fake' ? 'var(--danger)' : 'var(--success)' }}>
                      {selectedItem.confidence_score !== undefined && selectedItem.confidence_score !== null 
                        ? (typeof selectedItem.confidence_score === 'number' ? selectedItem.confidence_score.toFixed(2) : selectedItem.confidence_score)
                        : '—'}
                    </strong>
                  </div>
                  {selectedItem.confidence_score !== undefined && selectedItem.confidence_score !== null && (
                    <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border)', borderRadius: '4px', overflow: 'hidden' }}>
                      <div style={{ 
                        width: `${Math.min(100, Math.max(0, selectedItem.confidence_score * 100))}%`, 
                        height: '100%', 
                        backgroundColor: selectedItem.predicted_label === 'fake' ? 'var(--danger)' : 'var(--success)' 
                      }}></div>
                    </div>
                  )}
                </div>

                {/* Scores & Model Info */}
                <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)', display: 'flex', flexDirection: 'column', gap: '4px', borderTop: '1px solid var(--border)', paddingTop: '8px' }}>
                  <div className="flex items-center justify-between">
                    <span>Mô hình:</span>
                    <span style={{ fontFamily: 'monospace', fontWeight: 600 }}>
                      {selectedItem.model_name || '—'} (v{selectedItem.model_version || '—'})
                    </span>
                  </div>
                  {selectedItem.fake_probability !== undefined && (
                    <div className="flex items-center justify-between">
                      <span>Điểm giả:</span>
                      <span style={{ fontWeight: 600, color: 'var(--danger)' }}>
                        {(selectedItem.fake_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                  {selectedItem.real_probability !== undefined && (
                    <div className="flex items-center justify-between">
                      <span>Điểm gốc:</span>
                      <span style={{ fontWeight: 600, color: 'var(--success)' }}>
                        {(selectedItem.real_probability * 100).toFixed(1)}%
                      </span>
                    </div>
                  )}
                  {selectedItem.explanation && (
                    <div style={{ marginTop: '6px' }}>
                      <span style={{ fontWeight: 600, display: 'block', marginBottom: '2px' }}>Giải thích:</span>
                      <p style={{ margin: 0, fontStyle: 'italic', color: 'var(--text-main)' }}>
                        {selectedItem.explanation}
                      </p>
                    </div>
                  )}
                </div>
              </div>
            </div>

            <div className="modal-footer" style={{ justifyContent: 'space-between' }}>
              <button 
                type="button" 
                className="btn btn-primary"
                onClick={() => {
                  setIsDetailModalOpen(false);
                  handleNavigateToResult(selectedItem);
                }}
              >
                <ExternalLink size={16} />
                <span>Xem tại trang Kết quả phân tích</span>
              </button>
              <button type="button" className="btn btn-outline" onClick={() => setIsDetailModalOpen(false)}>
                Đóng
              </button>
            </div>
          </div>
        </div>
      )}

    </div>
  );
}
