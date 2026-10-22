import React, { useState, useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import { Search, Loader2, AlertCircle, Info, Sparkles } from 'lucide-react';
import { predictionApi, productApi, formatApiError } from '../lib/api';

export default function ReviewCheck() {
  const navigate = useNavigate();
  const [reviewText, setReviewText] = useState('');
  const [isAnalyzing, setIsAnalyzing] = useState(false);
  const [errorMessage, setErrorMessage] = useState('');

  // Optional context fields
  const [products, setProducts] = useState([]);
  const [selectedProductId, setSelectedProductId] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('Điện tử');
  const [selectedRating, setSelectedRating] = useState(5);

  // Load real products for product selector (optional context)
  useEffect(() => {
    let isMounted = true;
    async function loadProducts() {
      try {
        const data = await productApi.getProducts({ page: 1, page_size: 100 });
        if (isMounted) {
          setProducts(data.items || []);
        }
      } catch (err) {
        console.warn('Could not load products in ReviewCheck:', err);
      }
    }
    loadProducts();
    return () => {
      isMounted = false;
    };
  }, []);

  const handleAnalyze = async (e) => {
    if (e && e.preventDefault) e.preventDefault();
    if (isAnalyzing) return;

    setErrorMessage('');
    const trimmedContent = reviewText.trim();

    // Frontend validation
    if (!trimmedContent) {
      setErrorMessage('Vui lòng nhập nội dung đánh giá cần kiểm tra.');
      return;
    }

    if (trimmedContent.length < 5) {
      setErrorMessage('Nội dung đánh giá phải có ít nhất 5 ký tự.');
      return;
    }

    if (trimmedContent.length > 5000) {
      setErrorMessage('Nội dung đánh giá không được vượt quá 5000 ký tự.');
      return;
    }

    setIsAnalyzing(true);

    try {
      // Call REAL FastAPI backend endpoint: POST /api/predictions/analyze
      const response = await predictionApi.analyze(trimmedContent);

      const selectedProduct = products.find((p) => String(p.id) === String(selectedProductId));

      // Navigate to Result page with REAL API response
      navigate('/result', {
        state: {
          analysis: response,
          content: trimmedContent,
          productName: selectedProduct ? selectedProduct.name : null,
          productId: selectedProduct ? selectedProduct.id : null,
          category: selectedCategory,
          rating: Number(selectedRating)
        }
      });
    } catch (err) {
      if (err.status === 400 || err.status === 422) {
        setErrorMessage(formatApiError(err, 'Nội dung đánh giá không hợp lệ (tối thiểu 5 ký tự, tối đa 5000 ký tự).'));
      } else if (err.message && err.message.includes('fetch')) {
        setErrorMessage('Không thể kết nối đến máy chủ.');
      } else {
        setErrorMessage(formatApiError(err, 'Không thể phân tích đánh giá. Vui lòng thử lại.'));
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  return (
    <div>
      <div className="page-header">
        <h1 className="page-title">Kiểm tra đánh giá</h1>
        <p className="page-subtitle">Phân tích trực tiếp nội dung đánh giá và phát hiện dấu hiệu bất thường từ mô hình AI</p>
      </div>

      <div className="grid-2" style={{ gridTemplateColumns: '1fr 320px', alignItems: 'start' }}>
        <div className="card">
          <form onSubmit={handleAnalyze} noValidate>
            {/* Error banner */}
            {errorMessage && (
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
                <span>{errorMessage}</span>
              </div>
            )}

            {/* Optional Product Selection */}
            <div className="form-group">
              <label className="form-label" htmlFor="check-product">
                Sản phẩm liên kết <span style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>(Tùy chọn)</span>
              </label>
              <select 
                id="check-product"
                className="form-input"
                value={selectedProductId}
                onChange={(e) => setSelectedProductId(e.target.value)}
                disabled={isAnalyzing}
              >
                <option value="">-- Không chọn sản phẩm cụ thể --</option>
                {products.map((p) => (
                  <option key={p.id} value={p.id}>
                    #{p.id} - {p.name}
                  </option>
                ))}
              </select>
            </div>

            <div className="grid-2" style={{ marginBottom: 0, gap: 'var(--spacing-4)' }}>
              <div className="form-group">
                <label className="form-label" htmlFor="check-category">Danh mục</label>
                <select 
                  id="check-category"
                  className="form-input"
                  value={selectedCategory}
                  onChange={(e) => setSelectedCategory(e.target.value)}
                  disabled={isAnalyzing}
                >
                  <option value="Điện tử">Điện tử</option>
                  <option value="Thời trang">Thời trang</option>
                  <option value="Gia dụng">Gia dụng</option>
                  <option value="Mỹ phẩm">Mỹ phẩm</option>
                  <option value="Khác">Khác</option>
                </select>
              </div>

              <div className="form-group">
                <label className="form-label" htmlFor="check-rating">Mức đánh giá (Sao)</label>
                <select 
                  id="check-rating"
                  className="form-input"
                  value={selectedRating}
                  onChange={(e) => setSelectedRating(Number(e.target.value))}
                  disabled={isAnalyzing}
                >
                  <option value="5">5 Sao ⭐⭐⭐⭐⭐</option>
                  <option value="4">4 Sao ⭐⭐⭐⭐</option>
                  <option value="3">3 Sao ⭐⭐⭐</option>
                  <option value="2">2 Sao ⭐⭐</option>
                  <option value="1">1 Sao ⭐</option>
                </select>
              </div>
            </div>

            <div className="form-group">
              <label className="form-label" htmlFor="check-content">
                Nội dung đánh giá <span style={{ color: 'var(--danger)' }}>*</span>
              </label>
              <textarea 
                id="check-content"
                className="form-input form-textarea" 
                placeholder="Nhập nội dung đánh giá cần kiểm tra (tối thiểu 5 ký tự)..."
                value={reviewText}
                onChange={(e) => {
                  setReviewText(e.target.value);
                  if (errorMessage) setErrorMessage('');
                }}
                style={{ minHeight: '180px', resize: 'vertical' }}
                disabled={isAnalyzing}
              />
              <div className="flex items-center justify-between" style={{ marginTop: 'var(--spacing-2)' }}>
                <span style={{ fontSize: '0.75rem', color: reviewText.trim().length < 5 && reviewText.length > 0 ? 'var(--danger)' : 'var(--text-secondary)' }}>
                  {reviewText.trim().length < 5 && reviewText.length > 0 ? 'Cần tối thiểu 5 ký tự' : 'Tối thiểu 5 ký tự, tối đa 5000 ký tự'}
                </span>
                <span className="text-muted" style={{ fontSize: '0.875rem' }}>
                  {reviewText.length} / 5000 ký tự
                </span>
              </div>
            </div>

            <div style={{ marginTop: 'var(--spacing-4)' }}>
              <button 
                type="submit"
                className="btn btn-primary" 
                style={{ width: '100%', padding: 'var(--spacing-3)', fontSize: '1rem', justifyContent: 'center' }}
                disabled={isAnalyzing || !reviewText.trim()}
              >
                {isAnalyzing ? (
                  <>
                    <Loader2 className="animate-spin" size={20} />
                    <span>Đang phân tích...</span>
                  </>
                ) : (
                  <>
                    <Search size={20} />
                    <span>Phân tích đánh giá</span>
                  </>
                )}
              </button>
            </div>
          </form>
        </div>

        <div>
          <div className="card" style={{ backgroundColor: 'var(--background)', border: '1px dashed var(--border)' }}>
            <div className="flex items-center gap-2" style={{ marginBottom: 'var(--spacing-3)' }}>
              <Sparkles size={18} className="text-primary" />
              <h3 style={{ fontSize: '1rem', margin: 0 }}>Cơ chế phân tích</h3>
            </div>
            <p className="text-muted" style={{ fontSize: '0.875rem', marginBottom: 'var(--spacing-4)', lineHeight: 1.5 }}>
              Hệ thống kết nối trực tiếp với API phân tích (<code>POST /api/predictions/analyze</code>) để nhận diện các đặc trưng ngôn ngữ tự nhiên và phát hiện các mẫu đánh giá bất thường.
            </p>
            <ul className="text-muted" style={{ fontSize: '0.875rem', paddingLeft: 'var(--spacing-4)', margin: 0 }}>
              <li style={{ marginBottom: 'var(--spacing-2)' }}>Phân loại: Đánh giá gốc vs. Đáng ngờ</li>
              <li style={{ marginBottom: 'var(--spacing-2)' }}>Trích xuất điểm phân tích & xác suất</li>
              <li style={{ marginBottom: 'var(--spacing-2)' }}>Phát hiện cơ chế fallback tự động</li>
              <li>Hiển thị giải thích chi tiết từ mô hình</li>
            </ul>
          </div>
        </div>
      </div>
    </div>
  );
}
