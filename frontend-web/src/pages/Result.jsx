import React from 'react';
import Explanation from '../components/Explanation';
import ReviewDiscussion from '../components/ReviewDiscussion';
import { useNavigate, useLocation } from 'react-router-dom';
import { 
  AlertTriangle, RotateCcw, ShieldAlert, ShieldCheck, 
  ArrowLeft, Package, User, Cpu, AlertCircle, MessageSquare
} from 'lucide-react';

export default function Result() {
  const navigate = useNavigate();
  const location = useLocation();

  // Retrieve state passed from ReviewCheck or Reviews page
  const state = location.state || {};
  const passedReview = state.review;
  const analysis = state.analysis || passedReview?.prediction;
  const analyzedContent = state.content || passedReview?.content;
  const productName = state.productName || passedReview?.productName;
  const rating = state.rating || passedReview?.rating;

  // Empty / No-Data State: If user navigates directly without analysis data
  if (!analysis || !analyzedContent) {
    return (
      <div>
        <div className="page-header flex items-center justify-between">
          <div>
            <h1 className="page-title">Kết quả phân tích</h1>
            <p className="page-subtitle">Chi tiết kết quả phân tích nội dung đánh giá từ mô hình AI</p>
          </div>
          <button 
            className="btn btn-outline"
            onClick={() => navigate('/review-check')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--spacing-2)' }}
          >
            <ArrowLeft size={16} />
            <span>Đi đến Kiểm tra đánh giá</span>
          </button>
        </div>

        <div className="card" style={{ textAlign: 'center', padding: 'var(--spacing-12)' }}>
          <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-3)' }}>
            <AlertCircle size={52} className="text-muted" opacity={0.5} />
            <h2 style={{ fontSize: '1.25rem', margin: 0, color: 'var(--text-main)' }}>
              Chưa có kết quả phân tích
            </h2>
            <p className="text-muted" style={{ margin: 0, maxWidth: '480px', fontSize: '0.9rem', lineHeight: 1.5 }}>
              Hiện chưa có dữ liệu phân tích nào. Vui lòng nhập nội dung đánh giá tại trang 
              <strong> Kiểm tra đánh giá</strong> để thực hiện phân tích bằng API thực tế.
            </p>
            <button 
              className="btn btn-primary" 
              onClick={() => navigate('/review-check')}
              style={{ marginTop: 'var(--spacing-3)' }}
            >
              <RotateCcw size={16} />
              <span>Bắt đầu kiểm tra đánh giá</span>
            </button>
          </div>
        </div>
      </div>
    );
  }

  // Label mapping per requirements:
  // real -> Đánh giá gốc
  // fake -> Đáng ngờ (Do NOT display "Đánh giá giả chắc chắn")
  const isFake = analysis.predicted_label === 'fake';
  const labelText = isFake ? 'Đáng ngờ' : 'Đánh giá gốc';

  // Fallback heuristic detection:
  // If model_name === "fallback-heuristic" or model_version === "dev-only"
  const isFallback = Boolean(
    analysis.model_name === 'fallback-heuristic' || 
    analysis.model_version === 'dev-only'
  );

  const confidenceScore = analysis.confidence_score;
  const fakeProb = analysis.fake_probability;
  const realProb = analysis.real_probability;

  return (
    <div>
      <div className="page-header flex items-center justify-between" style={{ flexWrap: 'wrap', gap: 'var(--spacing-3)' }}>
        <div>
          <h1 className="page-title">Kết quả phân tích</h1>
          <p className="page-subtitle">Chi tiết kết quả phân loại và giải thích từ mô hình AI</p>
        </div>

        <div className="flex items-center gap-2">
          {passedReview && (
            <button 
              className="btn btn-outline"
              onClick={() => navigate('/reviews')}
              style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--spacing-2)' }}
            >
              <ArrowLeft size={16} />
              <span>Quay lại Quản lý đánh giá</span>
            </button>
          )}
          <button 
            className="btn btn-primary"
            onClick={() => navigate('/review-check')}
            style={{ display: 'inline-flex', alignItems: 'center', gap: 'var(--spacing-2)' }}
          >
            <RotateCcw size={16} />
            <span>Kiểm tra đánh giá khác</span>
          </button>
        </div>
      </div>

      <Explanation content={analyzedContent} modelVersion={analysis.model_version} />
      {passedReview?.id && <ReviewDiscussion reviewId={passedReview.id} productId={passedReview.productId} />}
      {/* Fallback Heuristic Warning (Requirement 6) */}
      {isFallback && (
        <div style={{
          backgroundColor: 'rgba(217, 119, 6, 0.1)',
          border: '1px solid rgba(217, 119, 6, 0.35)',
          borderRadius: 'var(--radius-md)',
          padding: 'var(--spacing-4)',
          marginBottom: 'var(--spacing-6)',
          display: 'flex',
          alignItems: 'flex-start',
          gap: '12px',
          color: '#B45309'
        }}>
          <AlertTriangle size={22} style={{ flexShrink: 0, marginTop: '2px' }} />
          <div>
            <div style={{ fontWeight: 600, fontSize: '0.95rem', marginBottom: '4px' }}>
              Kết quả thử nghiệm: backend hiện đang sử dụng cơ chế fallback, chưa phải mô hình AI đã huấn luyện.
            </div>
            <div style={{ fontSize: '0.85rem', color: '#92400E' }}>
              Mô hình hiện tại: <strong>Model: fallback-heuristic (dev-only)</strong>. Khi mô hình AI chính thức được nạp, kết quả phân loại sẽ tự động cập nhật.
            </div>
          </div>
        </div>
      )}

      <div className="grid-2" style={{ gridTemplateColumns: '1fr 340px', alignItems: 'start' }}>
        {/* Main Workspace */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-6)' }}>
          
          {/* Result Card */}
          <div className="card" style={{ borderTop: `4px solid ${isFake ? 'var(--danger)' : 'var(--success)'}` }}>
            <div className="flex items-center gap-4" style={{ marginBottom: 'var(--spacing-4)' }}>
              {isFake ? (
                <ShieldAlert size={48} className="text-danger" />
              ) : (
                <ShieldCheck size={48} className="text-success" />
              )}
              <div>
                <h2 style={{ fontSize: '1.5rem', margin: '0 0 var(--spacing-1) 0', color: isFake ? 'var(--danger)' : 'var(--success)' }}>
                  {labelText}
                </h2>
                <p className="text-muted" style={{ margin: 0, fontSize: '0.95rem' }}>
                  {isFake 
                    ? 'Đánh giá có dấu hiệu bất thường, có thể được tạo tự động bởi công cụ AI hoặc spam bot.' 
                    : 'Đánh giá mang đặc trưng ngôn ngữ tự nhiên, phản ánh trải nghiệm thực tế của người dùng.'}
                </p>
              </div>
            </div>

            {/* Scores Section */}
            <div style={{ backgroundColor: 'var(--background)', padding: 'var(--spacing-4)', borderRadius: 'var(--radius-md)' }}>
              {/* Confidence Score Display (Requirement 5) */}
              <div className="flex items-center" style={{ justifyContent: 'space-between', marginBottom: 'var(--spacing-2)' }}>
                <span style={{ fontWeight: 600, fontSize: '0.95rem' }}>Điểm phân tích:</span>
                <span style={{ fontSize: '1.25rem', fontWeight: 700, color: isFake ? 'var(--danger)' : 'var(--success)' }}>
                  {typeof confidenceScore === 'number' ? confidenceScore.toFixed(2) : (confidenceScore || '—')}
                </span>
              </div>
              {typeof confidenceScore === 'number' && (
                <div style={{ width: '100%', height: '8px', backgroundColor: 'var(--border)', borderRadius: '4px', marginBottom: 'var(--spacing-4)', overflow: 'hidden' }}>
                  <div style={{ 
                    width: `${Math.min(100, Math.max(0, confidenceScore * 100))}%`, 
                    height: '100%', 
                    backgroundColor: isFake ? 'var(--danger)' : 'var(--success)' 
                  }}></div>
                </div>
              )}

              {/* Sub-scores: Điểm giả & Điểm gốc */}
              <div className="grid-2" style={{ gap: 'var(--spacing-3)', marginTop: 'var(--spacing-3)', paddingTop: 'var(--spacing-3)', borderTop: '1px solid var(--border)' }}>
                <div style={{ backgroundColor: 'rgba(220, 38, 38, 0.05)', padding: 'var(--spacing-3)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(220, 38, 38, 0.15)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Điểm giả</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--danger)' }}>
                    {typeof fakeProb === 'number' ? `${(fakeProb * 100).toFixed(1)}%` : '—'}
                  </div>
                </div>

                <div style={{ backgroundColor: 'rgba(22, 163, 74, 0.05)', padding: 'var(--spacing-3)', borderRadius: 'var(--radius-sm)', border: '1px solid rgba(22, 163, 74, 0.15)' }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)', marginBottom: '2px' }}>Điểm gốc</div>
                  <div style={{ fontSize: '1.1rem', fontWeight: 700, color: 'var(--success)' }}>
                    {typeof realProb === 'number' ? `${(realProb * 100).toFixed(1)}%` : '—'}
                  </div>
                </div>
              </div>
            </div>
          </div>

          {/* Explanation Section (Requirement 8) */}
          <div className="card">
            <h3 style={{ fontSize: '1.125rem', marginBottom: 'var(--spacing-2)' }}>Giải thích kết quả</h3>
            <p className="text-muted" style={{ fontSize: '0.875rem', marginBottom: 'var(--spacing-4)' }}>
              Thông tin chi tiết từ hệ thống phân tích đối với nội dung đánh giá này:
            </p>

            <div style={{ 
              backgroundColor: 'var(--background)', 
              padding: 'var(--spacing-4)', 
              borderRadius: 'var(--radius-md)',
              border: '1px solid var(--border)',
              lineHeight: 1.6
            }}>
              {analysis.explanation ? (
                <p style={{ margin: 0, color: 'var(--text-main)', fontSize: '0.925rem' }}>
                  {analysis.explanation}
                </p>
              ) : (
                <p style={{ margin: 0, fontStyle: 'italic', color: 'var(--text-secondary)', fontSize: '0.875rem' }}>
                  Chưa có thông tin giải thích.
                </p>
              )}
            </div>
          </div>

        </div>

        {/* Sidebar Context */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-6)' }}>
          
          {/* Metadata Card if available */}
          {(productName || rating) && (
            <div className="card">
              <h3 style={{ fontSize: '1rem', marginBottom: 'var(--spacing-3)' }}>Thông tin liên quan</h3>
              <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-3)' }}>
                {productName && (
                  <div className="flex items-center gap-2">
                    <Package size={16} className="text-primary" />
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Sản phẩm</div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{productName}</div>
                    </div>
                  </div>
                )}
                {rating && (
                  <div className="flex items-center gap-2">
                    <User size={16} className="text-secondary" />
                    <div>
                      <div style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>Đánh giá</div>
                      <div style={{ fontWeight: 600, fontSize: '0.875rem' }}>{rating} ⭐</div>
                    </div>
                  </div>
                )}
              </div>
            </div>
          )}

          {/* Analyzed Content Card */}
          <div className="card">
            <div className="flex items-center gap-2" style={{ marginBottom: 'var(--spacing-2)' }}>
              <MessageSquare size={16} className="text-primary" />
              <h3 style={{ fontSize: '1rem', margin: 0 }}>Nội dung đã phân tích</h3>
            </div>
            <div style={{ 
              backgroundColor: 'var(--background)', 
              padding: 'var(--spacing-3)', 
              borderRadius: 'var(--radius-md)', 
              fontSize: '0.875rem', 
              lineHeight: 1.6, 
              fontStyle: 'italic', 
              borderLeft: '3px solid var(--primary)',
              wordBreak: 'break-word'
            }}>
              "{analyzedContent}"
            </div>
            <div style={{ marginTop: 'var(--spacing-2)', textAlign: 'right', fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              {analyzedContent.length} ký tự
            </div>
          </div>

          {/* Model Information Card (Requirement 4 & 6) */}
          <div className="card">
            <div className="flex items-center gap-2" style={{ marginBottom: 'var(--spacing-3)' }}>
              <Cpu size={16} className="text-primary" />
              <h3 style={{ fontSize: '1rem', margin: 0 }}>Thông tin mô hình</h3>
            </div>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-2)', fontSize: '0.85rem' }}>
              <div className="flex items-center justify-between">
                <span className="text-muted">Mô hình:</span>
                <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                  {analysis.model_name || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted">Phiên bản:</span>
                <span style={{ fontWeight: 600, fontFamily: 'monospace' }}>
                  {analysis.model_version || '—'}
                </span>
              </div>
              <div className="flex items-center justify-between">
                <span className="text-muted">Chế độ:</span>
                <span className={`badge ${isFallback ? 'badge-warning' : 'badge-success'}`} style={{ fontSize: '0.75rem' }}>
                  {isFallback ? 'Fallback dev-only' : 'Mô hình chính thức'}
                </span>
              </div>
            </div>
          </div>

          {/* Action Buttons */}
          <div className="card">
            <h3 style={{ fontSize: '1rem', marginBottom: 'var(--spacing-3)' }}>Thao tác</h3>
            <div style={{ display: 'flex', flexDirection: 'column', gap: 'var(--spacing-3)' }}>
              <button 
                className="btn btn-outline" 
                style={{ width: '100%', justifyContent: 'center' }} 
                onClick={() => navigate('/review-check')}
              >
                <RotateCcw size={16} />
                <span>Kiểm tra đánh giá khác</span>
              </button>
              <button 
                className="btn btn-outline" 
                style={{ width: '100%', justifyContent: 'center' }} 
                onClick={() => navigate('/reviews')}
              >
                <MessageSquare size={16} />
                <span>Đến danh sách đánh giá</span>
              </button>
            </div>
          </div>

        </div>
      </div>
    </div>
  );
}
