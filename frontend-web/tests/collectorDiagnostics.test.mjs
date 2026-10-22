import test from 'node:test';
import assert from 'node:assert/strict';
import { collectorDiagnosticItems } from '../src/lib/collectorDiagnostics.js';

test('HTTP fallback still displays the Selenium attempt diagnostic', () => {
  const rows = collectorDiagnosticItems({ collection_status: 'reviews_collected', attempts: [
    { collector: 'selenium', diagnostics: { code: 'chrome_crashpad_failed' } }, { collector: 'http', status: 'reviews_collected' }] });
  assert.equal(rows.length, 1); assert.equal(rows[0].code, 'chrome_crashpad_failed');
});
test('failed analysis and old code-only attempts are supported without duplicates', () => {
  const rows = collectorDiagnosticItems({ diagnostics: { code: 'worker_timeout' },
    attempts: [{ collector: 'selenium', diagnostic_code: 'worker_timeout' }] });
  assert.equal(rows.length, 1);
});
test('arbitrary logs, versions and prototype keys cannot reach display items', () => {
  const rows = collectorDiagnosticItems({ diagnostics: { code: 'driver_version_mismatch', raw_log: 'synthetic-private',
    browser_version_from_error: 'synthetic-private', driver_version_from_log: '155.0.8059.84', configuration: { path: 'C:/private' } } });
  assert.equal(rows[0].driverVersion, '155.0.8059.84'); assert.equal(rows[0].browserVersion, null);
  assert.ok(!JSON.stringify(rows).includes('synthetic-private')); assert.ok(!JSON.stringify(rows).includes('C:/private'));
  assert.deepEqual(collectorDiagnosticItems({ diagnostics: { code: '__proto__' } }), []);
});
test('malformed input is ignored and outer worker errors are labelled separately', () => {
  assert.deepEqual(collectorDiagnosticItems({ attempts: 'synthetic-private', diagnostics: [] }), []);
  const rows = collectorDiagnosticItems({ diagnostics: { code: 'collection_spawn_failed', stage: 'collection' } });
  assert.equal(rows[0].source, 'collection');
});
