import React, { useEffect, useState } from 'react';
import { Link } from 'react-router-dom';
import { Link2, ImagePlus, Video, FileText, ArrowRight, Loader2, ShieldCheck, AlertCircle, Clock, Download } from 'lucide-react';
import { api, formatApiError } from '../lib/api';
import ReviewCheck from './ReviewCheck';
import './inspector.css';

const root = '/api/product-links';
const platforms = { shopee: 'Shopee', tiktok_shop: 'TikTok Shop', lazada: 'Lazada', upload: 'Ảnh / video của bạn' };
const verdicts = { insufficient_data: 'Chưa đủ cơ sở kết luận', signals_detected: 'Có dấu hiệu cần kiểm tra', no_obvious_signals: 'Chưa thấy dấu hiệu rõ trong mẫu', technical_signals: 'Có dấu hiệu kỹ thuật cần xem' };
const examples = [
  ['Shopee', 'https://shopee.vn/product/1556630007/51200696506'],
  ['TikTok Shop', 'https://shop.tiktok.com/vn/pdp/ao-so-mi-o-dai-tay-form-rong-vai-lua-han-chong-nhan-unisex/1730096415976294875'],
  ['Lazada', 'https://www.lazada.vn/products/pdp-i13326005147-s116386241186.html'],
];

export function InspectionResult({ job, onReplay }) {
  const [snapshotError,setSnapshotError]=useState('');
  const result = job?.result;
  if (!result) return null;
  if (job.status === 'failed') return <div className="inspect-warning" role="alert"><p>{result.message}</p>{result.snapshot_id && onReplay && <button className="btn btn-outline" onClick={()=>onReplay(result.snapshot_id)}>Phân tích lại dữ liệu đã lưu</button>}</div>;
  const s = result.summary || {};
  const provenance=result.provenance || {};
  const manual=['user_supplied_review_import','user_written_review'].includes(result.source);
  const browserCapture=result.source==='browser_page_import';
  async function downloadDataset(){
    try{const value=await api.get(`${root}/snapshots/${provenance.snapshot_id}`);const url=URL.createObjectURL(new Blob([JSON.stringify(value,null,2)],{type:'application/json'}));const a=document.createElement('a');a.href=url;a.download=`du-lieu-thu-thap-${provenance.snapshot_id}.json`;a.click();URL.revokeObjectURL(url);setSnapshotError('');}
    catch(e){setSnapshotError(e.message);}
  }
  const media = result.source === 'user_upload';
  const count = media ? s.observed_files : s.observed_reviews;
  function download() {
    const url = URL.createObjectURL(new Blob([JSON.stringify(job, null, 2)], { type: 'application/json' }));
    const a = document.createElement('a'); a.href = url; a.download = `kiem-tra-${job.id}.json`; a.click(); URL.revokeObjectURL(url);
  }
  return <section className="inspect-result" aria-live="polite">
    <div className="inspect-section-title"><div><span className="inspect-eyebrow">KẾT QUẢ KIỂM TRA #{job.id}</span><h2>{result.product?.name || (result.identity?.product_id ? `Sản phẩm #${result.identity.product_id}` : 'Kết quả từ dữ liệu bạn gửi')}</h2><p>{platforms[job.platform]} · {browserCapture ? 'Bản thu thập từ trình duyệt do bạn cung cấp — chưa xác minh độc lập' : manual ? 'Dữ liệu dự phòng do người dùng nhập — chưa xác minh nguồn' : media ? 'Kiểm tra tệp cục bộ' : 'Dữ liệu công khai truy cập được'}</p></div><button className="btn btn-outline" onClick={download}><Download size={16} /> Lưu kết quả</button></div>
    {provenance.mode==='snapshot' && <p className="inspect-warning">Kết quả phân tích bản lưu được lưu lúc {new Date(provenance.captured_at).toLocaleString('vi-VN')}. Lần này không lấy dữ liệu mới từ sàn.</p>}
    {provenance.snapshot_id && <div className="work-toolbar"><button className="btn btn-outline" onClick={downloadDataset}>Tải dữ liệu nguồn đã lưu</button>{!!result.reviews?.length && onReplay && <button className="btn btn-outline" onClick={()=>onReplay(provenance.snapshot_id)}>Phân tích lại bản lưu</button>}<small>Thu thập: {new Date(provenance.captured_at).toLocaleString('vi-VN')}</small></div>}
    {browserCapture && <p className="inspect-muted">Chỉ gồm bình luận đã tải trong trình duyệt. Thời điểm thu thập do tiện ích khai báo: {result.client_captured_at ? new Date(result.client_captured_at).toLocaleString('vi-VN') : 'Không cung cấp'}. Thời điểm lưu phía trên là lúc server nhận dữ liệu.</p>}
    {!!result.attempts?.length && <p className="inspect-muted">Các lần thử thu thập: {result.attempts.map(a=>`${a.collector}: ${a.status}`).join(' → ')}. Lỗi khởi động Chrome trên server không đồng nghĩa sàn từ chối quyền đọc.</p>}
    {snapshotError && <p role="alert">{snapshotError}</p>}
    <div className={`inspect-verdict ${s.reviews_with_signals || s.files_with_signals ? 'attention' : ''}`}><ShieldCheck size={24} /><div><strong>{verdicts[s.verdict] || 'Chưa có kết luận'}</strong><p>{media ? 'Kiểm tra kỹ thuật ảnh/video; chưa xác minh thật/giả.' : 'Nhận định áp dụng cho mẫu review đọc được, không xác nhận hàng thật/hàng giả.'}</p></div></div>
    {result.collection_message && <p className="inspect-warning">{result.collection_message}</p>}
    {result.storage?.persisted_before_analysis && <p className="inspect-muted">Đã lưu dữ liệu vào database nội bộ trước khi phân tích. Mã bản lưu: {result.storage.snapshot_id}.</p>}
    <div className="inspect-metrics">
      <div><span>{media ? 'Tệp đã đọc' : 'Review đã đọc'}</span><strong>{count ?? 0}</strong></div>
      <div><span>{media ? 'Tệp có dấu hiệu kỹ thuật' : 'Review có dấu hiệu cần kiểm tra'}</span><strong>{media ? s.files_with_signals ?? 0 : s.reviews_with_signals ?? 0}</strong></div>
      <div><span>{media ? 'Tỷ lệ tệp có dấu hiệu' : 'Tỷ lệ review có dấu hiệu'}</span><strong>{s.signal_percentage == null ? 'Chưa có số liệu' : `${s.signal_percentage}%`}</strong></div>
    </div>
    <p className="inspect-muted">{media ? 'Tỷ lệ tính trong nhóm tệp bạn vừa gửi.' : `Tính trên ${count ?? 0} review lấy được${s.reported_total ? ` / ${s.reported_total} lượt đánh giá do nguồn báo cáo` : '; chưa xác minh tổng số review'}.`} Đây không phải xác suất sản phẩm hoặc nội dung là giả.</p>
    {result.product?.description && <details><summary>Thông tin mô tả từ nguồn</summary><p>{result.product.description}</p></details>}
    {!!result.observations?.aspects?.length && <section className="inspect-evidence"><h3>Những điều được nhắc đến về sản phẩm</h3><p className="inspect-muted">{result.observations.method}</p>{result.observations.aspects.map(group=><article key={group.aspect}><strong>{group.aspect}</strong><p>{group.mentions} nội dung không trùng nhắc đến · {group.positive_mentions} có từ ngữ tích cực · {group.negative_mentions} có từ ngữ tiêu cực.</p>{group.evidence.map(item=><blockquote key={item.review_id}>Review #{item.review_id}: {item.quote}</blockquote>)}</article>)}</section>}
    {!!result.reviews?.length && <div className="inspect-evidence"><h3>Bình luận và bằng chứng</h3>{result.reviews.map((r, i) => <article key={r.id || i}><div className="inspect-review-heading"><strong>Review #{r.id}</strong><span>{r.rating ? `${r.rating}/5 sao` : 'Không có số sao'} · {r.signals.length ? 'Cần kiểm tra thêm' : 'Chưa thấy dấu hiệu rõ'}</span></div><p>{r.text || '(Review không có văn bản)'}</p>{r.signals.map((x, j) => <p className="inspect-signal" key={j}>• {x.message}</p>)}{r.nlp ? <p className="inspect-muted">Model tiếng Anh OR/CG: P(nội dung sinh tự động) {(r.nlp.fake_probability * 100).toFixed(1)}%. Không phải xác suất gian lận.</p> : <p className="inspect-muted">Chưa chấm điểm NLP cho văn bản này; dấu hiệu hiển thị là kiểm tra theo quy tắc.</p>}<small>{r.images?.length || 0} ảnh · {r.videos?.length || 0} video đính kèm</small></article>)}</div>}
    {!!result.files?.length && <div className="inspect-evidence"><h3>Chi tiết tệp</h3>{result.files.map((f, i) => <article key={i}><strong>{f.name}</strong><p>{f.kind === 'video' ? `Video ${f.duration_seconds}s · đã đọc ${f.frames_sampled} khung hình mẫu` : `Ảnh ${f.width} × ${f.height} px · ${f.format}`}</p>{f.signals.length ? f.signals.map((x, j) => <p className="inspect-signal" key={j}>• {x.message}</p>) : <p>Chưa phát hiện dấu hiệu kỹ thuật trong phạm vi đã kiểm tra.</p>}</article>)}</div>}
    {result.media && <details><summary>Ảnh và video trong review</summary><p>{result.media.image_references} tham chiếu ảnh; {result.media.video_references} tham chiếu video; đã tải kiểm tra {result.media.images_inspected} ảnh.</p>{result.media.duplicate_groups.map((g, i) => <p key={i}>Dấu hiệu tái sử dụng ({g.method}): review {g.review_ids.join(', ')}.</p>)}<p>{result.media.note}</p>{result.media.errors.map((e, i) => <p key={i}>{e.reason}</p>)}</details>}
    <details className="inspect-limits"><summary>Phạm vi và điều chưa thể kết luận</summary>{result.limitations?.map((x, i) => <p key={i}>• {x}</p>)}</details>
  </section>;
}

export default function ProductInspector({ historyOnly = false }) {
  const [mode, setMode] = useState('link');
  const [url, setUrl] = useState('');
  const [files, setFiles] = useState([]);
  const [job, setJob] = useState(null);
  const [history, setHistory] = useState([]);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState('');
  const [inspectImages, setInspectImages] = useState(false);
  const [manualText,setManualText]=useState('');
  const [manualRating,setManualRating]=useState(5);
  const [manualName,setManualName]=useState('');
  const pending = ['queued', 'running'].includes(job?.status);
  useEffect(() => { let active = true; api.get(root).then(v => { if (active) setHistory(v); }).catch(e => { if (active) setError(formatApiError(e)); }); return () => { active = false; }; }, []);
  useEffect(() => {
    if (!pending) return;
    let active = true;
    const timer = setTimeout(async () => {
      try { const next = await api.get(`${root}/${job.id}`); if (active) { setJob(next); if (!['queued', 'running'].includes(next.status)) setHistory(await api.get(root)); } }
      catch (e) { if (active) { setError(formatApiError(e)); setJob({ ...job, status: 'failed', result: { message: 'Chưa tải được kết quả. Mở lại từ lịch sử để kiểm tra.' } }); } }
    }, 1500);
    return () => { active = false; clearTimeout(timer); };
  }, [job, pending]);
  async function execute(fn) {
    setBusy(true); setError(''); setJob(null);
    try { const next = await fn(); setJob(next); setHistory(await api.get(root)); }
    catch (e) { setError(formatApiError(e, 'Chưa kiểm tra được dữ liệu này.')); }
    finally { setBusy(false); }
  }
  async function submit(e) {
    e.preventDefault();
    if (mode === 'link') return execute(() => api.post(root, { url: url.trim(), limit: 50, inspect_images: inspectImages }));
    if (!files.length) { setError('Vui lòng chọn ảnh hoặc video trước.'); return; }
    if (files.length > 6 || files.some(f => f.size > 40000000) || files.reduce((n, f) => n + f.size, 0) > 60000000) { setError('Tối đa 6 tệp, mỗi tệp 40 MB và tổng 60 MB.'); return; }
    const form = new FormData(); files.forEach(file => form.append('files', file));
    return execute(() => api.upload(root + '/media', form));
  }
  async function writeReview(){
    if(!url.trim() || !manualText.trim()){setError('Nhập link sản phẩm và nội dung review dự phòng trước.');return;}
    return execute(()=>api.post(root+'/import',{url:url.trim(),input_method:'form',product_name:manualName,reviews:[{id:'entry-'+Date.now(),text:manualText.trim(),rating:manualRating,language:'unknown'}]}));
  }
  async function importReviews(file) {
    if (!file) return;
    if (file.size > 2000000) { setError('File review tối đa 2 MB.'); return; }
    try {
      const value = JSON.parse(await file.text());
      const rows = Array.isArray(value) ? value : value?.reviews;
      if (!Array.isArray(rows) || !rows.length) throw new Error('File phải chứa nội dung bình luận, không chỉ đường link. Dùng tiện ích Chrome hoặc nhập nội dung bình luận trực tiếp.');
      const importedUrl=value?.url || url.trim();
      if(!importedUrl)throw new Error('Điền link sản phẩm tương ứng hoặc chọn file có link do tiện ích xuất.');
      const browser=value?.collector==='fake-review-reader-v1';
      setUrl(importedUrl);
      await execute(() => api.post(root + '/import', { url: importedUrl, reviews: rows, product_name: value.product_name || '', inspect_images: inspectImages, input_method:browser?'browser':'file', captured_at:browser?value.captured_at:null }));
    } catch (e) { setError(e.message || 'Không đọc được JSON.'); }
  }

  return <div className="inspector">
    {!historyOnly && <><header className="inspect-hero"><span className="inspect-eyebrow">KIỂM TRA TRƯỚC KHI MUA</span><h1>Hiểu sản phẩm hơn.<br /><span>Xem điều đáng lưu ý.</span></h1><p>Dán link sản phẩm hoặc gửi ảnh, video. Xem những dấu hiệu cần kiểm tra cùng bằng chứng để tự tin cân nhắc.</p><div className="inspect-platforms"><span>Shopee</span><span>TikTok Shop</span><span>Lazada</span></div></header>
      <section className="inspect-input"><nav aria-label="Loại dữ liệu kiểm tra">{[['link', Link2, 'Link sản phẩm'], ['image', ImagePlus, 'Tải ảnh'], ['video', Video, 'Tải video'], ['text', FileText, 'Văn bản']].map(([key, Icon, label]) => <button key={key} type="button" className={mode === key ? 'active' : ''} disabled={busy || pending} onClick={() => { setMode(key); setFiles([]); setError(''); }}><Icon size={18} />{label}</button>)}</nav>
        {mode !== 'text' && <form onSubmit={submit}>
          {mode === 'link' ? <><label htmlFor="product-link">Link sản phẩm muốn kiểm tra</label><div className="inspect-link-row"><Link2 size={20} /><input id="product-link" type="url" required maxLength={2000} placeholder="Dán link Shopee, TikTok Shop hoặc Lazada…" value={url} onChange={e => setUrl(e.target.value)} disabled={busy || pending} /><button className="btn btn-primary" disabled={busy || pending}>{busy || pending ? <Loader2 className="spin" size={18} /> : <ArrowRight size={18} />}Kiểm tra</button></div><div className="inspect-examples"><span>Link bạn đã gửi:</span>{examples.map(([name, link]) => <button type="button" key={name} disabled={busy || pending} onClick={() => setUrl(link)}>{name}</button>)}</div><label className="inspect-checkbox"><input type="checkbox" checked={inspectImages} onChange={e => setInspectImages(e.target.checked)} /> Kiểm tra trùng lặp của tối đa 8 ảnh công khai lấy được</label><p className="inspect-muted">Số review đọc được phụ thuộc quyền truy cập của sàn. Không vượt trang đăng nhập hoặc CAPTCHA.</p><details open><summary>Thu thập từ Chrome — khi server không đọc được review</summary><p>Mở trang sản phẩm trong Chrome, mở phần Đánh giá rồi dùng tiện ích để đọc các bình luận đã tải. Tải file thu thập và nhập ngay bên dưới; không cần gõ lại từng review. Không đảm bảo đọc được mọi trang/sàn.</p><p><a href="/browser-reader.zip" download>Tải tiện ích Chrome</a> · <a href="/browser-reader-guide.html" target="_blank" rel="noreferrer">Hướng dẫn cài và sử dụng</a></p><label>Nhập bản thu thập từ Chrome<input type="file" accept=".json,application/json" disabled={busy || pending} onChange={e=>{importReviews(e.target.files[0]);e.target.value='';}} /></label><p className="inspect-muted">Chỉ gồm review hiển thị đã tải. Nguồn do bạn cung cấp, server chưa xác minh độc lập. Tiện ích cần cài một lần trong Chrome.</p></details><details><summary>Nhập nội dung bình luận — dùng khi không đọc được từ sàn</summary><p>Giữ link sản phẩm ở ô phía trên, rồi sao chép nội dung bình luận từ sàn vào ô bên dưới. Chỉ dán lại link sẽ không có dữ liệu để phân tích. Nội dung bạn nhập sẽ được lưu và phân tích; không được coi là review vừa lấy từ sàn hay nhãn thật/giả đã xác minh.</p><label>Tên sản phẩm (tùy chọn, do bạn nhập)<input className="form-input" maxLength={300} value={manualName} onChange={e=>setManualName(e.target.value)} /></label><label>Nội dung bình luận<textarea placeholder="Ví dụ: Mình đã dùng một tuần, vải khá mỏng nhưng đường may đều…" className="form-input" maxLength={5000} value={manualText} onChange={e=>setManualText(e.target.value)} /></label><label>Số sao<select className="form-input" value={manualRating} onChange={e=>setManualRating(Number(e.target.value))}>{[1,2,3,4,5].map(n=><option key={n} value={n}>{n} sao</option>)}</select></label><button type="button" className="btn btn-outline" disabled={busy || pending} onClick={writeReview}>Lưu và phân tích review dự phòng</button></details><details><summary>Nâng cao: tải file JSON chứa danh sách bình luận</summary><p>Đây là file chứa nội dung review, không phải file chỉ chứa link sản phẩm. Có thể nhập tối đa 200 review cho kiểm thử/dự phòng. Kết quả sẽ ghi rõ đây là dữ liệu bạn cung cấp.</p><a href="/review-import.example.json" download>Tải mẫu JSON minh họa</a><input aria-label="Nhập file review JSON" type="file" accept=".json,application/json" disabled={busy || pending} onChange={e => importReviews(e.target.files[0])} /></details></> : <><label className="inspect-drop" htmlFor="media-files">{mode === 'image' ? <ImagePlus size={34} /> : <Video size={34} />}<strong>{mode === 'image' ? 'Chọn ảnh sản phẩm / ảnh nhận xét' : 'Chọn video sản phẩm / video nhận xét'}</strong><span>Tối đa 6 tệp · 40 MB/tệp · 60 MB/lần · video tối đa 5 phút</span><input id="media-files" key={mode} type="file" multiple accept={mode === 'image' ? 'image/jpeg,image/png,image/webp,image/gif' : 'video/mp4,video/webm,video/quicktime,video/x-msvideo'} onChange={e => setFiles([...e.target.files])} disabled={busy || pending} /></label>{files.map((f, i) => <p key={i}>{f.name} · {(f.size / 1000000).toFixed(1)} MB</p>)}<p className="inspect-muted">Kiểm tra kỹ thuật và dấu hiệu trùng lặp. Chưa xác minh AI/deepfake, hàng thật/hàng giả hoặc người thật.</p><button className="btn btn-primary" disabled={busy || pending || !files.length}>{busy ? 'Đang đọc tệp…' : 'Phân tích tệp đã chọn'}</button></>}
        </form>}
      </section>{mode === 'text' && <ReviewCheck />}</>}
    {error && <p className="inspect-warning" role="alert"><AlertCircle size={18} /> {error}</p>}
    {pending && <p className="inspect-progress" role="status"><Loader2 className="spin" size={20} /> Đang thử trình duyệt và nguồn công khai (tối đa 105 giây cho thu thập). Sau đó hệ thống phân tích dữ liệu lấy được. Bạn có thể mở lại từ lịch sử.</p>}
    <InspectionResult job={job} onReplay={sid=>execute(()=>api.post(`${root}/snapshots/${sid}/analyze`))} />
    <section className="inspect-history"><div className="inspect-section-title"><div><span className="inspect-eyebrow">CHỈ HIỂN THỊ LỊCH SỬ CỦA BẠN</span><h2>{historyOnly ? 'Lịch sử kiểm tra' : 'Những lần kiểm tra gần đây'}</h2></div><button className="btn btn-outline" onClick={() => api.get(root).then(setHistory).catch(e => setError(e.message))}>Làm mới</button></div>{history.length ? history.map(row => <button className="inspect-history-row" key={row.id} onClick={() => { setJob(row); setError(''); }}><Clock size={18} /><span><strong>{row.result?.product?.name || (row.platform === 'upload' ? row.result?.files?.[0]?.name : row.url) || `Lần kiểm tra #${row.id}`}</strong><small>{platforms[row.platform]} · {new Date(row.created_at).toLocaleString('vi-VN')}</small></span><span>{['queued','running'].includes(row.status) ? 'Đang xử lý' : row.status === 'failed' ? 'Chưa hoàn tất' : verdicts[row.result?.summary?.verdict] || 'Xem kết quả'}</span><ArrowRight size={18} /></button>) : <p className="inspect-muted">Chưa có lần kiểm tra nào. Bắt đầu bằng một link, ảnh hoặc video.</p>}<Link to="/text-history">Xem lịch sử phân tích văn bản</Link></section>
  </div>;
}
