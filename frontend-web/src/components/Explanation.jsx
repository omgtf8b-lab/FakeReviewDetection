import React, { useState } from 'react';
import { api } from '../lib/api';

export default function Explanation({ content, modelVersion }) {
  const [data, setData] = useState(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  async function explain() {
    setBusy(true); setError('');
    try { setData(await api.post('/api/workspace/explain', { content, model_version: modelVersion || null })); }
    catch (e) { setError(e.message); }
    finally { setBusy(false); }
  }
  const weights = new Map((data?.features || []).map(f => [f.token.toLowerCase(), f.weight]));
  return <section className="card" style={{ marginTop: 20 }}>
    <h3>Vì sao mô hình đưa ra kết quả này?</h3>
    <p>Đỏ: tăng dự đoán lớp fake. Xanh: giảm dự đoán lớp fake. Đây là giải thích cục bộ của mô hình.</p>
    <button className="btn btn-primary" disabled={busy || !content} onClick={explain}>{busy ? 'Đang chạy LIME…' : 'Giải thích bằng LIME'}</button>
    {error && <p role="alert">{error}</p>}
    {data && <>
      <p style={{ lineHeight: 2, marginTop: 20 }}>{content.split(/(\b\w+\b)/).map((word, i) => {
        const weight = weights.get(word.toLowerCase());
        return <span key={i} title={weight === undefined ? '' : `Đóng góp: ${weight.toFixed(4)}`} style={weight === undefined ? {} : { background: weight > 0 ? '#fee2e2' : '#dcfce7', color: '#172033', padding: '2px 0' }}>{word}</span>;
      })}</p>
      <div style={{ display: 'flex', flexWrap: 'wrap', gap: 8 }}>{data.features.map(f => <span key={f.token} style={{ background: f.weight > 0 ? '#fee2e2' : '#dcfce7', color: '#172033', padding: 8, borderRadius: 8 }}>{f.token}: {f.weight > 0 ? '+' : ''}{f.weight.toFixed(3)}</span>)}</div>
      <p className="text-muted">LIME · {data.samples} mẫu nhiễu · độ khớp cục bộ {data.local_fidelity.toFixed(3)}. {data.note}</p>
    </>}
  </section>;
}
