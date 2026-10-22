const labels = Object.freeze({
  chrome_crashpad_failed: 'Chrome dừng khi khởi tạo bộ báo lỗi.',
  driver_version_mismatch: 'Phiên bản ChromeDriver không tương thích.',
  profile_in_use: 'Profile Chrome đang được sử dụng.',
  browser_permission_denied: 'Tiến trình trình duyệt thiếu quyền cần thiết.',
  chrome_binary_missing: 'Chưa tìm thấy Chrome đã cấu hình.',
  chrome_start_crashed: 'Chrome dừng trước khi khởi tạo xong.',
  browser_start_unknown: 'Chưa xác định được nguyên nhân khởi động Chrome.',
  worker_spawn_failed: 'Chưa tạo được tiến trình đọc trình duyệt.',
  worker_exit_failed: 'Tiến trình đọc trình duyệt kết thúc bất thường.',
  worker_invalid_output: 'Tiến trình đọc trình duyệt chưa trả dữ liệu hợp lệ.',
  worker_timeout: 'Tiến trình đọc trình duyệt vượt thời gian.',
  worker_io_failed: 'Gián đoạn trao đổi với tiến trình trình duyệt.',
  worker_execution_failed: 'Tiến trình trình duyệt chưa hoàn tất xử lý.',
  collection_spawn_failed: 'Chưa tạo được tiến trình thu thập.',
  collection_exit_failed: 'Tiến trình thu thập kết thúc bất thường.',
  collection_invalid_output: 'Tiến trình thu thập chưa trả dữ liệu hợp lệ.',
  collection_timeout: 'Tiến trình thu thập vượt thời gian.',
  collection_io_failed: 'Gián đoạn trao đổi với tiến trình thu thập.',
});
const version = value => typeof value === 'string' && /^\d{1,4}\.\d{1,6}\.\d{1,8}\.\d{1,6}$/.test(value) ? value : null;

// Render only known codes and numeric versions, never server log/message blobs.
export function collectorDiagnosticItems(data) {
  if (!data || typeof data !== 'object') return [];
  const found = []; const seen = new Set();
  function add(diagnostic, fallback, collector) {
    const code = diagnostic?.code ?? fallback;
    if (typeof code !== 'string' || !Object.hasOwn(labels, code)) return;
    const source = collector === 'collection' ? 'collection' : 'selenium';
    const key = `${source}:${code}`;
    if (seen.has(key)) return;
    seen.add(key);
    found.push({ code, message: labels[code], source,
      driverVersion: version(diagnostic?.driver_version_from_log),
      browserVersion: version(diagnostic?.browser_version_from_error) });
  }
  if (Array.isArray(data.attempts)) for (const item of data.attempts.slice(0, 8)) {
    if (item && ['selenium', 'collection'].includes(item.collector)) add(item.diagnostics, item.diagnostic_code, item.collector);
  }
  add(data.diagnostics, null, data.diagnostics?.stage === 'collection' ? 'collection' : 'selenium');
  return found;
}
