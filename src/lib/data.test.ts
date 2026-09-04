import { describe, it } from 'node:test';
import assert from 'node:assert/strict';
import {
  generateTimeSeries,
  generateICTimeSeries,
  generateAlphaDecay,
  generatePnL,
  generateDrawdown,
  generateFactorReturns,
  generatePortfolioWeights,
  generateModelComparison,
  generateRiskMetrics,
  generateAlphaCandidates,
  generateMonitoringAlerts,
} from './data.ts';

describe('Data Generators and Quantitative Calculation Utilities', () => {
  it('generateTimeSeries creates correct series length with valid dates and values', () => {
    const data = generateTimeSeries(30, 100, 0.02);
    assert.strictEqual(data.length, 31);
    assert.ok(data[0].date.match(/^\d{4}-\d{2}-\d{2}$/));
    assert.ok(data[0].value > 0);
    assert.ok(data[0].volume >= 500000);
  });

  it('generateICTimeSeries produces valid IC and rankIC metrics', () => {
    const data = generateICTimeSeries(10);
    assert.strictEqual(data.length, 10);
    for (const pt of data) {
      assert.ok(typeof pt.ic === 'number');
      assert.ok(typeof pt.rankIC === 'number');
      assert.ok(!Number.isNaN(pt.ic));
      assert.ok(!Number.isNaN(pt.rankIC));
      assert.ok(pt.date.match(/^\d{4}-\d{2}-\d{2}$/));
    }
  });

  it('generateAlphaDecay returns lags with decaying trend', () => {
    const decay = generateAlphaDecay(20);
    assert.strictEqual(decay.length, 20);
    assert.strictEqual(decay[0].lag, 1);
    assert.strictEqual(decay[19].lag, 20);
    // Early lag should generally have higher IC than late lag
    assert.ok(decay[0].ic > decay[19].ic - 0.05);
  });

  it('generatePnL produces cumulative series consistent with daily returns', () => {
    const pnl = generatePnL(15);
    assert.strictEqual(pnl.length, 15);
    let running = 0;
    for (const day of pnl) {
      running += day.daily;
      assert.ok(Math.abs(running - day.cumulative) < 2.0);
    }
  });

  it('generateDrawdown calculates peak-to-trough drawdown correctly', () => {
    const mockPnl = [
      { cumulative: 100 },
      { cumulative: 150 },
      { cumulative: 120 }, // -20% from peak of 150
      { cumulative: 90 },  // -40% from peak of 150
      { cumulative: 160 }, // New peak
    ];
    const dd = generateDrawdown(mockPnl);
    assert.strictEqual(dd.length, 5);
    assert.strictEqual(dd[0].drawdown, 0);
    assert.strictEqual(dd[1].drawdown, 0);
    assert.strictEqual(dd[2].drawdown, -20);
    assert.strictEqual(dd[3].drawdown, -40);
    assert.strictEqual(dd[4].drawdown, 0);
  });

  it('generateFactorReturns provides factors for requested horizons', () => {
    const factors = ['Value', 'Momentum', 'Quality', 'Size'];
    const ret = generateFactorReturns(factors, 6);
    assert.strictEqual(ret.length, 6);
    for (const f of factors) {
      assert.ok(typeof ret[0][f] === 'number');
    }
  });

  it('generatePortfolioWeights outputs weights that sum to ~100%', () => {
    const weights = generatePortfolioWeights(10);
    assert.strictEqual(weights.length, 10);
    const sum = weights.reduce((acc, w) => acc + w.weight, 0);
    assert.ok(Math.abs(sum - 100) < 1.0, `Weights sum was ${sum}`);
    assert.ok(weights[0].ticker.length > 0);
  });

  it('generateModelComparison provides comprehensive algorithm performance records', () => {
    const models = generateModelComparison();
    assert.ok(models.length >= 8);
    const ensemble = models.find((m) => m.model === 'Ensemble');
    assert.ok(ensemble);
    assert.ok(ensemble.sharpe > 1.5);
  });

  it('generateRiskMetrics returns coherent risk parameters', () => {
    const risk = generateRiskMetrics();
    assert.ok(risk.var95 < 0);
    assert.ok(risk.var99 < risk.var95);
    assert.ok(risk.cvar95 < risk.var95);
    assert.ok(risk.sharpe > 1.0);
    assert.ok(risk.maxDrawdown < 0);
  });

  it('generateAlphaCandidates returns ranked candidate pool with statuses', () => {
    const rawCandidates = generateAlphaCandidates(false);
    assert.ok(rawCandidates.length > 5);
    assert.ok(rawCandidates.some((c) => c.status === 'pass'));
    assert.ok(rawCandidates.some((c) => c.status === 'fail'));

    const candidates = generateAlphaCandidates();
    assert.strictEqual(candidates.length, 8);
    assert.ok(candidates.every((c) => c.status === 'pass'));
    assert.ok(candidates.every((c) => c.sharpe > 1.2));
  });

  it('generateMonitoringAlerts contains structured alert events', () => {
    const alerts = generateMonitoringAlerts();
    assert.ok(alerts.length >= 4);
    assert.ok(alerts.some((a) => a.type === 'error'));
    assert.ok(alerts.some((a) => a.type === 'warning'));
  });
});
