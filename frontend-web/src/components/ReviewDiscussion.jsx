import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';
import { useAuth } from '../contexts/AuthContext';

export default function ReviewDiscussion({ reviewId, productId }) {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [product, setProduct] = useState(null);
  const [reply, setReply] = useState('');
  const [reason, setReason] = useState('spam');
  const [description, setDescription] = useState('');
  const [message, setMessage] = useState('');
  const [busy, setBusy] = useState(false);
  const path = `/api/workspace/reviews/${reviewId}`;
  useEffect(() => {
    let active = true;
    api.get(path + '/discussion').then(value => { if (active) setData(value); }).catch(e => { if (active) setMessage(e.message); });
    if (productId) api.get(`/api/products/${productId}`).then(value => { if (active) setProduct(value); }).catch(e => { if (active) setMessage(e.message); });
    return () => { active = false; };
  }, [reviewId, productId]);
  async function act(fn) {
    setBusy(true); setMessage('');
    try { await fn(); setData(await api.get(path + '/discussion')); setMessage('Đã lưu'); }
    catch (e) { setMessage(e.message); } finally { setBusy(false); }
  }
  const canReply = user?.role === 'admin' || (user?.role === 'seller' && product?.shop_id === user.id);
  return <section className="card" style={{ marginTop: 20 }}><h3>Phản hồi và kiểm duyệt review #{reviewId}</h3>{data?.moderation && <p><strong>Nhãn kiểm duyệt: {data.moderation.label === 'fake' ? 'Đáng ngờ' : 'Đánh giá gốc'}</strong> · {data.moderation.reason}. Kết quả AI gốc được giữ để đối chiếu.</p>}<div className="work-toolbar"><button className="btn btn-outline" disabled={busy} onClick={() => act(() => api.put(path + '/vote', { useful: true }))}>Hữu ích ({data?.useful || 0})</button><button className="btn btn-outline" disabled={busy} onClick={() => act(() => api.put(path + '/vote', { useful: false }))}>Không hữu ích ({data?.not_useful || 0})</button></div>{data?.replies.map(r => <blockquote key={r.id}>Shop / tài khoản #{r.user_id}: {r.content}</blockquote>)}{canReply && <form onSubmit={e => { e.preventDefault(); act(() => api.post(path + '/reply', { content: reply })); }}><label className="form-label">Phản hồi của shop<textarea className="form-input" required maxLength={5000} value={reply} onChange={e => setReply(e.target.value)} /></label><button className="btn btn-primary" disabled={busy}>Gửi phản hồi</button></form>}<details style={{ marginTop: 16 }}><summary>Báo cáo review nghi vấn</summary><form onSubmit={e => { e.preventDefault(); act(() => api.post(`/api/reviews/${reviewId}/report`, { reason, description })); }}><select aria-label="Lý do báo cáo" className="form-input" value={reason} onChange={e => setReason(e.target.value)}>{[['fake','Nghi giả'],['spam','Spam'],['misleading','Gây hiểu nhầm'],['inappropriate','Không phù hợp'],['other','Lý do khác']].map(([v,l]) => <option key={v} value={v}>{l}</option>)}</select><textarea aria-label="Mô tả báo cáo" className="form-input" maxLength={1000} value={description} onChange={e => setDescription(e.target.value)} /><button className="btn btn-outline" disabled={busy}>Gửi báo cáo</button></form></details><p role="status">{message}</p></section>;
}
