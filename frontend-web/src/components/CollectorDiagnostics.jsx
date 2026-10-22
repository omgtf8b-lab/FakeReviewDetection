import React from 'react';
import { collectorDiagnosticItems } from '../lib/collectorDiagnostics';

export default function CollectorDiagnostics({ data }) {
  const items = collectorDiagnosticItems(data);
  if (!items.length) return null;
  return <section className="inspect-warning" aria-label="Chẩn đoán thu thập">
    <strong>Thông tin lần thử thu thập</strong>
    {items.map(item => <p key={`${item.source}:${item.code}`}>
      {item.source === 'collection' ? 'Bộ thu thập' : 'Trình duyệt'}: {item.message} <code>{item.code}</code>
      {item.driverVersion && <> · Driver {item.driverVersion}</>}
      {item.browserVersion && <> · Chrome {item.browserVersion}</>}
    </p>)}
    <small>Lỗi kỹ thuật này không xác nhận sàn chặn truy cập hoặc sản phẩm có đánh giá giả.</small>
  </section>;
}
