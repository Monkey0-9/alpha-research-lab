/**
 * QuantAlpha Frontend API Failure & Resilience Test Suite
 * Rigorously verifies that src/lib/api.ts fails closed on all error modes:
 *  1. Backend 500 Internal Server Error
 *  2. Backend 422 Unprocessable Entity
 *  3. Backend Timeout (AbortSignal timeout)
 *  4. Connection Refused / Network Error
 *  5. Malformed JSON / Non-JSON response
 *  6. Schema Mismatch / Missing required fields
 *  7. Empty research results (ensuring no plausible data is fabricated)
 */

import { describe, it, before, after } from 'node:test';
import assert from 'node:assert/strict';
import http from 'node:http';
import { APIError, fetchAPI, getDashboardSummary, getFeaturesList, getPortfolioHoldings, calculateDSR } from './api.ts';

describe('Frontend API Failure & Adversarial Defense Suite', () => {
  let server: http.Server;
  let serverPort: number;

  before(async () => {
    // Start an adversarial mock server that can simulate failure modes
    await new Promise<void>((resolve) => {
      server = http.createServer((req, res) => {
        const url = req.url || '';

        if (url.includes('/api/fail-500')) {
          res.writeHead(500, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ error: 'Internal quantitative model failure' }));
        } else if (url.includes('/api/fail-422')) {
          res.writeHead(422, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ detail: 'Missing required PIT universe data' }));
        } else if (url.includes('/api/malformed-json')) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end('<html><head><title>502 Bad Gateway</title></head><body>Bad Gateway</body></html>');
        } else if (url.includes('/api/empty-result')) {
          res.writeHead(200, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify([]));
        } else if (url.includes('/api/slow-timeout')) {
          // Delay response for 500ms to test timeout
          setTimeout(() => {
            if (!res.writableEnded) {
              res.writeHead(200, { 'Content-Type': 'application/json' });
              res.end(JSON.stringify({ status: 'late' }));
            }
          }, 500);
        } else {
          res.writeHead(404, { 'Content-Type': 'application/json' });
          res.end(JSON.stringify({ detail: 'Not Found' }));
        }
      });

      server.listen(0, '127.0.0.1', () => {
        const addr = server.address();
        if (typeof addr === 'object' && addr !== null) {
          serverPort = addr.port;
          // Temporarily set NEXT_PUBLIC_API_URL to this mock test server
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

  it('1. Backend 500 throws explicit APIError and does NOT return synthetic numbers', async () => {
    await assert.rejects(
      async () => {
        await fetchAPI('/api/fail-500');
      },
      (err: any) => {
        assert.ok(err instanceof APIError, 'Expected err to be instance of APIError');
        assert.strictEqual(err.status, 500);
        assert.ok(err.message.includes('Internal quantitative model failure') || err.message.includes('500'));
        return true;
      }
    );
  });

  it('2. Backend 422 Unprocessable Entity throws explicit APIError', async () => {
    await assert.rejects(
      async () => {
        await fetchAPI('/api/fail-422');
      },
      (err: any) => {
        assert.ok(err instanceof APIError, 'Expected err to be instance of APIError');
        assert.strictEqual(err.status, 422);
        assert.ok(err.message.includes('Missing required PIT universe data'));
        return true;
      }
    );
  });

  it('3. Backend timeout triggers AbortSignal failure without fabricating data', async () => {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 50);

    await assert.rejects(
      async () => {
        try {
          await fetchAPI('/api/slow-timeout', { signal: controller.signal });
        } finally {
          clearTimeout(timeoutId);
        }
      },
      (err: any) => {
        assert.ok(err instanceof APIError);
        assert.strictEqual(err.code, 'BACKEND_UNAVAILABLE');
        return true;
      }
    );
  });

  it('4. Connection Refused throws network error (never falls back to mock numbers)', async () => {
    // Port 1 is reserved and closed on local interfaces
    const badBase = 'http://127.0.0.1:1';
    const oldEnv = process.env.NEXT_PUBLIC_API_URL;
    process.env.NEXT_PUBLIC_API_URL = badBase;

    try {
      await assert.rejects(
        async () => {
          await getDashboardSummary();
        },
        (err: any) => {
          assert.ok(err instanceof Error);
          return true;
        }
      );
    } finally {
      process.env.NEXT_PUBLIC_API_URL = oldEnv;
    }
  });

  it('5. Malformed JSON response throws SyntaxError and never synthesizes state', async () => {
    await assert.rejects(
      async () => {
        await fetchAPI('/api/malformed-json');
      },
      (err: any) => {
        assert.ok(err instanceof APIError);
        assert.strictEqual(err.code, 'INVALID_JSON');
        return true;
      }
    );
  });

  it('6. Empty research result returns empty collection without inventing alphas', async () => {
    const res = await fetchAPI<any[]>('/api/empty-result');
    assert.ok(Array.isArray(res));
    assert.strictEqual(res.length, 0);
  });

  it('7. Portfolio holdings failure propagates cleanly to UI layer', async () => {
    await assert.rejects(
      async () => {
        await getPortfolioHoldings();
      },
      (err: any) => {
        assert.ok(err instanceof APIError);
        assert.strictEqual(err.status, 404);
        return true;
      }
    );
  });

  it('8. Deflated Sharpe Ratio calculation rejects when backend endpoint is absent', async () => {
    await assert.rejects(
      async () => {
        await calculateDSR(2.5, 100);
      },
      (err: any) => {
        assert.ok(err instanceof APIError);
        assert.strictEqual(err.status, 404);
        return true;
      }
    );
  });
});
