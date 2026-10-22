import React, { useState, useEffect, useCallback, useMemo } from 'react';
import { useNavigate } from 'react-router-dom';
import { 
  Package, MessageSquare, AlertTriangle, CheckCircle2, 
  Loader2, AlertCircle, RotateCcw, ArrowRight, ShieldAlert, 
  ShieldCheck, Info 
} from 'lucide-react';
import { 
  BarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer,
  PieChart, Pie, Cell
} from 'recharts';
import { 
  statisticsApi, 
  reviewApi, 
  productApi, 
  formatApiError 
} from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function Dashboard() {
  const navigate = useNavigate();
  const { user } = useAuth();

  const role = (user?.role || '').toLowerCase();
  const isAdminOrEngineer = role === 'admin' || role === 'engineer';

  // Statistics state
  const [stats, setStats] = useState(null);
  const [statsLoading, setStatsLoading] = useState(true);
  const [statsError, setStatsError] = useState('');

  // Recent reviews state
  const [recentReviews, setRecentReviews] = useState([]);
  const [reviewsLoading, setReviewsLoading] = useState(true);

  // Products lookup map: id -> product name
  const [productMap, setProductMap] = useState({});

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
        console.warn('Could not load products for dashboard lookup:', err);
      }
    }
    loadProducts();
    return () => {
      isMounted = false;
    };
  }, []);

  // ==========================================
  // FETCH ROLE-BASED STATISTICS
  // Admin/Engineer: GET /api/statistics/overview
  // Buyer/Seller:   GET /api/statistics/me
  // ==========================================
  const fetchStatistics = useCallback(async () => {
    setStatsLoading(true);
    setStatsError('');
    try {
      if (isAdminOrEngineer) {
        const data = await statisticsApi.getOverview();
        setStats(data);
      } else {
        const data = await statisticsApi.getMyOverview();
        setStats(data);
      }
    } catch (err) {
      if (err.status === 403) {
        setStatsError('Bạn không có quyền xem thống kê hệ thống.');
      } else if (err.message && err.message.includes('fetch')) {
        setStatsError('Không thể kết nối đến máy chủ.');
      } else {
        setStatsError(formatApiError(err, 'Không thể tải tổng quan hệ thống.'));
      }
      setStats(null);
    } finally {
      setStatsLoading(false);
    }
  }, [isAdminOrEngineer]);

  // ==========================================
  // FETCH RECENT ANALYSIS / REVIEWS
  // Admin/Engineer: GET /api/admin/reviews
  // Buyer/Seller:   GET /api/reviews/me (or GET /api/reviews?page=1&page_size=6)
  // ==========================================
  const fetchRecentReviews = useCallback(async () => {
    setReviewsLoading(true);
    try {
      if (isAdminOrEngineer) {
        const data = await reviewApi.getAdminReviews();
        // admin reviews returns array of ReviewResponse
        const list = Array.isArray(data) ? data : (data.items || []);
        setRecentReviews(list.slice(0, 6));
      } else {
        // user reviews
        const data = await reviewApi.getMyReviews({ page: 1, page_size: 6 });
        const list = Array.isArray(data) ? data : (data.items || []);
        setRecentReviews(list.slice(0, 6));
      }
    } catch (err) {
      console.warn('Could not load recent reviews for dashboard:', err);
      // Fallback to public reviews if getMyReviews fails
      try {
        const fallbackData = await reviewApi.getReviews({ page: 1, page_size: 6 });
        setRecentReviews(fallbackData.items || []);
      } catch {
        setRecentReviews([]);
      }
    } finally {
      setReviewsLoading(false);
    }
  }, [isAdminOrEngineer]);

  useEffect(() => {
    fetchStatistics();
    fetchRecentReviews();
  }, [fetchStatistics, fetchRecentReviews]);

  // Helpers to resolve review attributes
  const getProductName = useCallback((productId) => {
    if (!productId) return 'Sản phẩm không xác định';
    return productMap[productId] || `Sản phẩm #${productId}`;
  }, [productMap]);

  const isFallbackPrediction = (pred) => {
    if (!pred) return false;
    return pred.model_name === 'fallback-heuristic' || pred.model_version === 'dev-only';
  };

  // KPI Calculations
  const totalProducts = stats?.total_products ?? 0;
  const totalReviews = isAdminOrEngineer 
    ? (stats?.total_reviews ?? 0) 
    : (stats?.my_reviews ?? 0);
  const fakeCount = isAdminOrEngineer 
    ? (stats?.fake_reviews ?? 0) 
    : (stats?.my_fake_reviews ?? 0);
  const realCount = isAdminOrEngineer 
    ? (stats?.real_reviews ?? 0) 
    : (stats?.my_real_reviews ?? 0);
  const pendingCount = isAdminOrEngineer 
    ? (stats?.pending_reviews ?? 0) 
    : (stats?.my_pending_reviews ?? 0);

  const fakePercentage = useMemo(() => {
    if (isAdminOrEngineer) {
      if (typeof stats?.fake_percentage === 'number') {
        return stats.fake_percentage.toFixed(1);
      }
      return totalReviews > 0 ? ((fakeCount / totalReviews) * 100).toFixed(1) : '0';
    } else {
      if (typeof stats?.my_fake_percentage === 'number') {
        return stats.my_fake_percentage.toFixed(1);
      }
      return totalReviews > 0 ? ((fakeCount / totalReviews) * 100).toFixed(1) : '0';
    }
  }, [stats, isAdminOrEngineer, totalReviews, fakeCount]);

  const realPercentage = useMemo(() => {
    return totalReviews > 0 ? ((realCount / totalReviews) * 100).toFixed(1) : '0';
  }, [totalReviews, realCount]);

  // Real Chart Data
  // Left: Distribution Bar Chart (Real aggregate statistics)
  const barChartData = useMemo(() => {
    return [
      { name: 'Đánh giá gốc', 'Số lượng': realCount, fill: '#16A34A' },
      { name: 'Đáng ngờ', 'Số lượng': fakeCount, fill: '#DC2626' },
      ...(pendingCount > 0 ? [{ name: 'Chưa phân tích', 'Số lượng': pendingCount, fill: '#94A3B8' }] : [])
    ];
  }, [realCount, fakeCount, pendingCount]);

  // Right: Classification Ratio Pie Chart
  const pieChartData = useMemo(() => {
    const data = [
      { name: 'Đánh giá gốc', value: realCount, color: '#16A34A' },
      { name: 'Đáng ngờ', value: fakeCount, color: '#DC2626' },
      ...(pendingCount > 0 ? [{ name: 'Chưa phân tích', value: pendingCount, color: '#94A3B8' }] : [])
    ];
    return data.filter((d) => d.value > 0);
  }, [realCount, fakeCount, pendingCount]);

  return (
    <div>
      {/* Page Header */}
      <div className="page-header flex items-center justify-between" style={{ flexWrap: 'wrap', gap: 'var(--spacing-3)' }}>
        <div>
          <h1 className="page-title">Tổng quan hệ thống</h1>
          <p className="page-subtitle">
            {isAdminOrEngineer 
              ? 'Theo dõi toàn bộ sản phẩm, đánh giá và thống kê phát hiện đánh giá giả (Quản trị viên)'
              : 'Theo dõi hoạt động đánh giá cá nhân và phát hiện đánh giá đáng ngờ'}
          </p>
        </div>
        <button 
          className="btn btn-outline"
          onClick={() => {
            fetchStatistics();
            fetchRecentReviews();
          }}
          disabled={statsLoading || reviewsLoading}
          style={{ display: 'inline-flex', alignItems: 'center', gap: '6px' }}
        >
          <RotateCcw size={16} className={statsLoading ? 'animate-spin' : ''} />
          <span>Làm mới</span>
        </button>
      </div>

      {/* Error state if stats failed to load */}
      {statsError && (
        <div style={{
          backgroundColor: 'rgba(220, 38, 38, 0.1)',
          border: '1px solid rgba(220, 38, 38, 0.3)',
          color: 'var(--danger)',
          padding: 'var(--spacing-4)',
          borderRadius: 'var(--radius-md)',
          marginBottom: 'var(--spacing-6)',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'space-between',
          gap: '12px'
        }}>
          <div className="flex items-center gap-3">
            <AlertCircle size={22} style={{ flexShrink: 0 }} />
            <div>
              <div style={{ fontWeight: 600 }}>{statsError}</div>
              <div style={{ fontSize: '0.8rem', color: 'var(--text-secondary)' }}>
                Vui lòng kiểm tra trạng thái máy chủ FastAPI (http://127.0.0.1:8001).
              </div>
            </div>
          </div>
          <button 
            className="btn btn-outline"
            onClick={fetchStatistics}
            style={{ fontSize: '0.8rem', padding: '4px 10px', backgroundColor: 'var(--surface)' }}
          >
            Thử lại
          </button>
        </div>
      )}

      {/* KPI Cards */}
      <div className="grid-4">
        {/* Card 1: Total Products */}
        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Tổng sản phẩm</h3>
            <div className="kpi-icon primary"><Package size={20} /></div>
          </div>
          <p className="kpi-value">
            {statsLoading ? '...' : totalProducts}
          </p>
          <p className="kpi-footer">
            {isAdminOrEngineer 
              ? `${stats?.total_users ?? 0} người dùng trong hệ thống`
              : 'Sản phẩm có trên hệ thống'}
          </p>
        </div>

        {/* Card 2: Total Reviews */}
        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">
              {isAdminOrEngineer ? 'Tổng đánh giá' : 'Đánh giá của tôi'}
            </h3>
            <div className="kpi-icon neutral" style={{ backgroundColor: 'var(--border)', color: 'var(--text-main)' }}>
              <MessageSquare size={20} />
            </div>
          </div>
          <p className="kpi-value">
            {statsLoading ? '...' : totalReviews}
          </p>
          <p className="kpi-footer">
            {pendingCount > 0 ? `${pendingCount} chưa phân tích` : 'Đã lưu trong hệ thống'}
          </p>
        </div>

        {/* Card 3: Suspicious Reviews */}
        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đánh giá đáng ngờ</h3>
            <div className="kpi-icon danger"><AlertTriangle size={20} /></div>
          </div>
          <p className="kpi-value">
            {statsLoading ? '...' : fakeCount}
          </p>
          <p className="kpi-footer">
            <span className="text-danger">{fakePercentage}%</span> trên tổng số đánh giá
          </p>
        </div>

        {/* Card 4: Real Reviews */}
        <div className="card kpi-card">
          <div className="kpi-header">
            <h3 className="kpi-title">Đánh giá gốc</h3>
            <div className="kpi-icon success"><CheckCircle2 size={20} /></div>
          </div>
          <p className="kpi-value">
            {statsLoading ? '...' : realCount}
          </p>
          <p className="kpi-footer">
            <span className="text-success">{realPercentage}%</span> phản ánh tự nhiên
          </p>
        </div>
      </div>

      {/* Real Aggregate Charts Row */}
      <div className="grid-2">
        {/* Left Chart: Real Distribution Bar Chart */}
        <div className="card">
          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--spacing-4)' }}>
            <h3 className="page-title" style={{ fontSize: '1.125rem', margin: 0 }}>
              Phân bố kết quả phân tích
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              Số liệu tổng hợp thực tế
            </span>
          </div>

          <div style={{ width: '100%', height: 280 }}>
            {statsLoading ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <Loader2 className="animate-spin text-primary" size={32} />
              </div>
            ) : totalReviews === 0 ? (
              <div style={{ display: 'flex', height: '100%', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                <MessageSquare size={36} opacity={0.4} />
                <p style={{ marginTop: '8px', fontSize: '0.875rem' }}>Chưa có đánh giá nào để phân bố.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={barChartData} margin={{ top: 10, right: 20, left: -20, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="3 3" vertical={false} stroke="var(--border)" />
                  <XAxis dataKey="name" axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                  <YAxis allowDecimals={false} axisLine={false} tickLine={false} tick={{ fontSize: 12, fill: 'var(--text-secondary)' }} />
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' }}
                  />
                  <Bar dataKey="Số lượng" radius={[6, 6, 0, 0]}>
                    {barChartData.map((entry, index) => (
                      <Cell key={`bar-${index}`} fill={entry.fill} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            )}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', marginTop: '8px', textAlign: 'center' }}>
            * Dữ liệu phân tích thực tế từ hệ thống. (Backend hiện chưa hỗ trợ chuỗi thời gian theo ngày/tuần).
          </div>
        </div>

        {/* Right Chart: Real Classification Ratio Pie Chart */}
        <div className="card">
          <div className="flex items-center justify-between" style={{ marginBottom: 'var(--spacing-4)' }}>
            <h3 className="page-title" style={{ fontSize: '1.125rem', margin: 0 }}>
              Tỷ lệ phân loại đánh giá
            </h3>
            <span style={{ fontSize: '0.75rem', color: 'var(--text-secondary)' }}>
              {totalReviews} đánh giá
            </span>
          </div>

          <div style={{ width: '100%', height: 280 }}>
            {statsLoading ? (
              <div style={{ display: 'flex', height: '100%', alignItems: 'center', justifyContent: 'center' }}>
                <Loader2 className="animate-spin text-primary" size={32} />
              </div>
            ) : pieChartData.length === 0 ? (
              <div style={{ display: 'flex', height: '100%', flexDirection: 'column', alignItems: 'center', justifyContent: 'center', color: 'var(--text-secondary)' }}>
                <CheckCircle2 size={36} opacity={0.4} />
                <p style={{ marginTop: '8px', fontSize: '0.875rem' }}>Chưa có dữ liệu phân loại đánh giá.</p>
              </div>
            ) : (
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={pieChartData}
                    innerRadius={70}
                    outerRadius={105}
                    paddingAngle={4}
                    dataKey="value"
                  >
                    {pieChartData.map((entry, index) => (
                      <Cell key={`pie-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip 
                    contentStyle={{ borderRadius: '8px', border: '1px solid var(--border)', boxShadow: 'var(--shadow-sm)' }}
                    itemStyle={{ color: 'var(--text-main)' }}
                    formatter={(val) => [`${val} (${((val / totalReviews) * 100).toFixed(1)}%)`, 'Số lượng']}
                  />
                  <Legend iconType="circle" layout="vertical" verticalAlign="middle" align="right" wrapperStyle={{ fontSize: 12 }} />
                </PieChart>
              </ResponsiveContainer>
            )}
          </div>
          <div style={{ fontSize: '0.725rem', color: 'var(--text-secondary)', marginTop: '8px', textAlign: 'center' }}>
            * Tỷ lệ tính toán tự động dựa trên tổng số đánh giá đã lưu.
          </div>
        </div>
      </div>

      {/* Real Recent Analysis Table */}
      <div className="table-wrapper">
        <div className="table-header flex items-center justify-between" style={{ padding: 'var(--spacing-4)' }}>
          <h3 style={{ margin: 0 }}>
            {isAdminOrEngineer ? 'Phân tích gần đây trong hệ thống' : 'Phân tích đánh giá gần đây của bạn'}
          </h3>
          <button 
            className="btn btn-outline"
            onClick={() => navigate('/reviews')}
            style={{ fontSize: '0.8rem', padding: '4px 10px', display: 'inline-flex', alignItems: 'center', gap: '4px' }}
          >
            <span>Xem tất cả</span>
            <ArrowRight size={14} />
          </button>
        </div>

        <div className="table-responsive">
          <table>
            <thead>
              <tr>
                <th>Nội dung đánh giá</th>
                <th>Sản phẩm</th>
                <th style={{ width: '160px' }}>Kết quả</th>
                <th style={{ width: '150px' }}>Điểm phân tích</th>
                <th style={{ width: '130px' }}>Thời gian</th>
              </tr>
            </thead>
            <tbody>
              {reviewsLoading ? (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: 'var(--spacing-8)' }}>
                    <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', gap: 'var(--spacing-2)' }}>
                      <Loader2 className="animate-spin text-primary" size={28} />
                      <span style={{ fontSize: '0.875rem', color: 'var(--text-secondary)' }}>Đang tải phân tích gần đây...</span>
                    </div>
                  </td>
                </tr>
              ) : recentReviews.length > 0 ? (
                recentReviews.map((item) => {
                  const pred = item.prediction;
                  const isFake = pred?.predicted_label === 'fake';
                  const isReal = pred?.predicted_label === 'real';
                  const isFallback = isFallbackPrediction(pred);
                  const productName = getProductName(item.product_id);

                  return (
                    <tr key={item.id}>
                      <td style={{ maxWidth: '320px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={item.content}>
                        "{item.content}"
                      </td>
                      <td style={{ fontWeight: 500, maxWidth: '200px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }} title={productName}>
                        {productName}
                      </td>
                      <td>
                        {!pred ? (
                          <span className="badge badge-neutral">Chưa phân tích</span>
                        ) : isFake ? (
                          <span className="badge badge-danger">Đáng ngờ</span>
                        ) : (
                          <span className="badge badge-success">Đánh giá gốc</span>
                        )}
                      </td>
                      <td>
                        {pred && pred.confidence_score !== undefined && pred.confidence_score !== null ? (
                          <div className="flex items-center gap-1">
                            <span style={{ fontWeight: 600 }}>
                              {typeof pred.confidence_score === 'number' ? pred.confidence_score.toFixed(2) : pred.confidence_score}
                            </span>
                            {isFallback && (
                              <span 
                                className="badge badge-warning" 
                                style={{ fontSize: '0.65rem', padding: '1px 5px', marginLeft: '4px' }}
                                title="Kết quả thử nghiệm từ heuristic fallback"
                              >
                                Thử nghiệm
                              </span>
                            )}
                          </div>
                        ) : (
                          <span style={{ color: 'var(--text-secondary)' }}>—</span>
                        )}
                      </td>
                      <td className="text-muted" style={{ fontSize: '0.85rem' }}>
                        {item.created_at ? new Date(item.created_at).toLocaleDateString('vi-VN') : '—'}
                      </td>
                    </tr>
                  );
                })
              ) : (
                <tr>
                  <td colSpan="5" style={{ textAlign: 'center', padding: 'var(--spacing-8)' }}>
                    <p className="text-muted" style={{ margin: 0, fontSize: '0.875rem' }}>
                      Chưa có dữ liệu phân tích gần đây.
                    </p>
                  </td>
                </tr>
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
