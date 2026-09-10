/**
 * QuantAlpha API Client Error Contract & Integrity Test Suite
 * Validates fail-closed semantics across all failure modes:
 *  A. Backend 500 -> ApiError with status = 500
 *  B. Backend 503 -> ApiError with status = 503
 *  C. Backend Unreachable -> ApiError with code = BACKEND_UNAVAILABLE
 *  D. Invalid JSON -> ApiError with code = INVALID_JSON
 *  E. HTTP 422 -> ApiError with status = 422
 *  F. Valid Response -> Typed result matching contract
 *  G. Explicit Empty Result -> Empty state, zero invented results
 */

import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { ApiError } from './api-error.ts';
import { fetchAPI, getDashboardSummary, getFeaturesList, getPortfolioHoldings } from './api.ts';

describe('Frontend API Error Contract & Fail-Closed Test Suite', () => {
  let server: http.Server;
  let serverPort: number;

  before(async () => {
    await new Promise<void>((resolve) => {
      server = http.createServer((req, res) => {
        const url = req.url || '';

        if (url.includes('/api/mock-500')) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Internal solver singular matrix error', code: 'SOLVER_FAILURE' }));
        } else if (url.includes('/api/mock-503')) {
          res.writeHead(503, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Data feed upstream gateway temporarily down', code: 'SERVICE_UNAVAILABLE' }));
        } else if (url.includes('/api/mock-422')) {
          res.writeHead(422, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            detail: {
              code: 'UNIVERSE_DATA_UNAVAILABLE',
              message: 'No valid universe data is available for the requested assets.'
            }
          }));
        } else if (url.includes('/api/invalid-json')) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end('<html><head><title>502 Bad Gateway</title></head><body>Bad Gateway</body></html>');
        } else if (url.includes('/api/valid-typed')) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({
            status: 'ok',
            data: {
              portfolio_nav: 2485000.0,
              daily_pnl_dollars: 18450.0,
              daily_pnl_pct: 0.74,
              annualized_sharpe: 2.14,
              current_regime: 'Bull Quiet'
            }
          }));
        } else if (url.includes('/api/empty-result')) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify([]));
        } else {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ detail: 'Endpoint not found' }));
        }
      });

      server.listen(0, '127.0.0.1', () => {
        const addr = server.address();
        if (typeof addr === 'object' && addr !== null) {
          serverPort = addr.port;
          process.env.NEXT_PUBLIC_API_URL = `http://127.0.0.1:${serverPort}`;
        }
        resolve();
      });
    });
  });

  after(async () => {
    await new Promise<void>((resolve) => {
      server.close(() => resolve());
    });
  });

  // A. Backend 500
  it('A. Backend 500 returns ApiError with status = 500', async () => {
    await assert.rejects(
      async () => {
        await fetchAPI('/api/mock-500');
      },
      (err: any) => {
        assert.ok(err instanceof ApiError, 'Expected ApiError');
        assert.strictEqual(err.status, 500);
        assert.strictEqual(err.code, 'SOLVER_FAILURE');
        assert.ok(err.message.includes('Internal solver singular matrix error'));
        return true;
      }
    );
  });

  // B. Backend 503
  it('B. Backend 503 returns ApiError with status = 503', async () => {
    await assert.rejects(
      async () => {
        await fetchAPI('/api/mock-503');
      },
      (err: any) => {
        assert.ok(err instanceof ApiError, 'Expected ApiError');
        assert.strictEqual(err.status, 503);
        assert.strictEqual(err.code, 'SERVICE_UNAVAILABLE');
        assert.ok(err.message.includes('upstream gateway'));
        return true;
      }
    );
  });

  // C. Backend Unreachable
  it('C. Backend unreachable returns ApiError with code = BACKEND_UNAVAILABLE', async () => {
    // Point to an unallocated port that actively refuses connections
    const unreachableUrl = 'http://127.0.0.1:1';
    const oldEnv = process.env.NEXT_PUBLIC_API_URL;
    process.env.NEXT_PUBLIC_API_URL = unreachableUrl;

    try {
      await assert.rejects(
        async () => {
          await fetchAPI('/api/dashboard/summary');
        },
        (err: any) => {
          assert.ok(err instanceof ApiError, 'Expected ApiError');
          assert.strictEqual(err.status, null);
          assert.strictEqual(err.code, 'BACKEND_UNAVAILABLE');
          assert.strictEqual(err.message, 'Backend unavailable');
          return true;
        }
      );
    } finally {
      process.env.NEXT_PUBLIC_API_URL = oldEnv;
    }
  });

  // D. Invalid JSON
  it('D. Invalid JSON response returns ApiError with code = INVALID_JSON', async () => {
    await assert.rejects(
      async () => {
        await fetchAPI('/api/invalid-json');
      },
      (err: any) => {
        assert.ok(err instanceof ApiError, 'Expected ApiError');
        assert.strictEqual(err.status, 200);
        assert.strictEqual(err.code, 'INVALID_JSON');
        assert.strictEqual(err.message, 'Invalid API response');
        return true;
      }
    );
  });

  // E. HTTP 422
  it('E. HTTP 422 returns ApiError with status = 422 and structured code', async () => {
    await assert.rejects(
      async () => {
        await fetchAPI('/api/mock-422');
      },
      (err: any) => {
        assert.ok(err instanceof ApiError, 'Expected ApiError');
        assert.strictEqual(err.status, 422);
        assert.strictEqual(err.code, 'UNIVERSE_DATA_UNAVAILABLE');
        assert.ok(err.message.includes('No valid universe data is available'));
        return true;
      }
    );
  });

  // F. Valid Response
  it('F. Valid response returns typed result without modification', async () => {
    const res = await fetchAPI<{ status: string; data: { portfolio_nav: number } }>('/api/valid-typed');
    assert.strictEqual(res.status, 'ok');
    assert.strictEqual(res.data.portfolio_nav, 2485000.0);
  });

  // G. Explicit Empty Result
  it('G. Explicit empty result returns empty collection without inventing numbers', async () => {
    const res = await fetchAPI<any[]>('/api/empty-result');
    assert.ok(Array.isArray(res));
    assert.strictEqual(res.length, 0);
  });
});
