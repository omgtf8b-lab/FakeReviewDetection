import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';

export default function ProductExtraEditor({ products, user, busy, action }) {
  const available = products.filter(p => user?.role === 'admin' || p.shop_id === user?.id);
  const [selected, setSelected] = useState('');
  const [values, setValues] = useState(null);
  const [error, setError] = useState('');
  useEffect(() => {
    if (!selected && available.length) setSelected(String(available[0].id));
  }, [products, selected]);
  useEffect(() => {
    if (!selected) return;
    let active = true;
    setValues(null); setError('');
    api.get(`/api/workspace/products/${selected}/extra`).then(data => { if (active) setValues(data); }).catch(e => { if (active) setError(e.message); });
    return () => { active = false; };
  }, [selected]);
  if (!available.length) return <p>Chưa có sản phẩm thuộc quyền quản lý của bạn.</p>;
  return <div><h3>Ảnh, tồn kho và nhóm sản phẩm</h3><label>Sản phẩm<select className="form-input" value={selected} onChange={e => setSelected(e.target.value)}>{available.map(p => <option key={p.id} value={p.id}>#{p.id} {p.name}</option>)}</select></label>{error && <p role="alert">{error}</p>}{values && <form className="work-form" onSubmit={e => { e.preventDefault(); action(() => api.put(`/api/workspace/products/${selected}/extra`, { ...values, image_url: values.image_url || null })); }}>
    <label>Đường dẫn ảnh HTTPS<input type="url" value={values.image_url || ''} onChange={e => setValues({ ...values, image_url: e.target.value })} /></label>
    {values.image_url && <img src={values.image_url} alt="Ảnh sản phẩm" style={{ width: 120, height: 120, objectFit: 'cover', borderRadius: 10 }} />}
    <label>Tồn kho<input required type="number" min="0" value={values.stock} onChange={e => setValues({ ...values, stock: Number(e.target.value) })} /></label>
    <label>Trạng thái<select value={values.sale_status} onChange={e => setValues({ ...values, sale_status: e.target.value })}><option value="active">Đang bán</option><option value="paused">Tạm ngừng</option><option value="sold_out">Hết hàng</option></select></label>
    <label>Mã nhóm sản phẩm chung<input value={values.canonical_key || ''} onChange={e => setValues({ ...values, canonical_key: e.target.value })} /></label>
    <button className="btn btn-primary" disabled={busy}>Lưu thông tin sản phẩm</button>
  </form>}</div>;
}
