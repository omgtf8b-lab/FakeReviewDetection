import React, { useEffect, useState } from 'react';
import { api } from '../lib/api';

export default function ConsumerSupport({ notifications = false }) {
  const [rows,setRows]=useState([]);const [error,setError]=useState('');
  const endpoint=notifications?'/api/workspace/notifications':'/api/workspace/content';
  useEffect(()=>{let active=true;api.get(endpoint).then(v=>{if(active)setRows(v);}).catch(e=>{if(active)setError(e.message);});return()=>{active=false;};},[endpoint]);
  return <div className="card"><h1>{notifications?'Thông báo của bạn':'Hướng dẫn kiểm tra sản phẩm'}</h1>{error&&<p role="alert">{error}</p>}{!notifications&&<p>Dán link sản phẩm hoặc tải ảnh/video trong mục Kiểm tra sản phẩm. Đọc dấu hiệu và bằng chứng; tỷ lệ có dấu hiệu không xác nhận hàng giả hay người thật. Nếu sàn không cung cấp dữ liệu, kết quả sẽ báo chưa đủ cơ sở.</p>}{rows.map(r=><article key={r.id}><h3>{r.title||r.message}</h3><p style={{whiteSpace:'pre-wrap'}}>{r.body||r.created_at}</p>{notifications&&!r.read&&<button onClick={async()=>{try{await api.patch(`/api/workspace/notifications/${r.id}/read`);setRows(await api.get(endpoint));}catch(e){setError(e.message);}}}>Đánh dấu đã đọc</button>}</article>)}{!rows.length&&<p>{notifications?'Bạn chưa có thông báo.':'Chọn Link sản phẩm, Tải ảnh, Tải video hoặc Văn bản để bắt đầu.'}</p>}</div>;
}
