// Synthetic data generators for all 12 modules

export function generateTimeSeries(n: number, start = 100, volatility = 0.015) {
  const data = [];
  let price = start;
  const now = new Date();
  for (let i = n; i >= 0; i--) {
    const date = new Date(now.getTime() - i * 24 * 60 * 60 * 1000);
    price = price * (1 + (Math.random() - 0.48) * volatility);
    data.push({
      date: date.toISOString().slice(0, 10),
      value: parseFloat(price.toFixed(4)),
      volume: Math.floor(Math.random() * 1000000 + 500000),
    });
  }
  return data;
}

export function generateICTimeSeries(n: number) {
  return Array.from({ length: n }, (_, i) => {
    const date = new Date(Date.now() - (n - i) * 7 * 24 * 60 * 60 * 1000);
    return {
      date: date.toISOString().slice(0, 10),
      ic: parseFloat((Math.random() * 0.14 - 0.02).toFixed(4)),
      rankIC: parseFloat((Math.random() * 0.16 - 0.01).toFixed(4)),
    };
  });
}

export function generateAlphaDecay(n: number) {
  return Array.from({ length: n }, (_, i) => ({
    lag: i + 1,
    ic: parseFloat((0.08 * Math.exp(-i * 0.15) + (Math.random() - 0.5) * 0.01).toFixed(4)),
  }));
}

export function generatePnL(n: number) {
  let cumPnL = 0;
  return Array.from({ length: n }, (_, i) => {
    const daily = Math.round((Math.random() - 0.47) * 2500);
    cumPnL += daily;
    const date = new Date(Date.now() - (n - i) * 24 * 60 * 60 * 1000);
    return {
      date: date.toISOString().slice(0, 10),
      daily,
      cumulative: cumPnL,
    };
  });
}

export function generateDrawdown(pnl: { cumulative: number }[]) {
  let peak = 0;
  return pnl.map((p) => {
    if (p.cumulative > peak) peak = p.cumulative;
    const dd = peak > 0 ? ((p.cumulative - peak) / peak) * 100 : 0;
    return { ...p, drawdown: parseFloat(dd.toFixed(2)) };
  });
}

export function generateFactorReturns(factors: string[], n: number) {
  return Array.from({ length: n }, (_, i) => {
    const date = new Date(Date.now() - (n - i) * 30 * 24 * 60 * 60 * 1000);
    const obj: Record<string, number | string> = { date: date.toISOString().slice(0, 7) };
    factors.forEach((f) => {
      obj[f] = parseFloat(((Math.random() - 0.48) * 3).toFixed(2));
    });
    return obj;
  });
}

export function generatePortfolioWeights(n = 10) {
  const tickers = ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA', 'META', 'TSLA', 'JPM', 'BRK.B', 'XOM'];
  const raw = Array.from({ length: n }, () => Math.random());
  const sum = raw.reduce((a, b) => a + b, 0);
  return tickers.slice(0, n).map((t, i) => ({
    ticker: t,
    weight: parseFloat(((raw[i] / sum) * 100).toFixed(2)),
    signal: parseFloat((Math.random() * 2 - 0.5).toFixed(3)),
    pnl: parseFloat(((Math.random() - 0.45) * 5000).toFixed(0)),
  }));
}

export function generateModelComparison() {
  return [
    { model: 'Ridge Regression', sharpe: 0.82, ic: 0.045, oos: 0.71, trainTime: '2s', params: '127' },
    { model: 'LASSO', sharpe: 0.78, ic: 0.042, oos: 0.74, trainTime: '3s', params: '89' },
    { model: 'Random Forest', sharpe: 1.14, ic: 0.071, oos: 0.68, trainTime: '45s', params: '500 trees' },
    { model: 'XGBoost', sharpe: 1.31, ic: 0.085, oos: 0.72, trainTime: '38s', params: '1200' },
    { model: 'LightGBM', sharpe: 1.38, ic: 0.089, oos: 0.75, trainTime: '22s', params: '900' },
    { model: 'LSTM', sharpe: 1.22, ic: 0.078, oos: 0.65, trainTime: '8min', params: '124K' },
    { model: 'Transformer', sharpe: 1.45, ic: 0.094, oos: 0.70, trainTime: '32min', params: '2.1M' },
    { model: 'Ensemble', sharpe: 1.67, ic: 0.108, oos: 0.78, trainTime: '—', params: 'Meta' },
  ];
}

export function generateRiskMetrics() {
  return {
    var95: -2.34,
    var99: -3.81,
    cvar95: -3.12,
    cvar99: -5.44,
    beta: 0.42,
    volatility: 14.7,
    sharpe: 1.67,
    maxDrawdown: -8.3,
    calmar: 2.14,
    sortino: 2.31,
  };
}

export function generateAlphaCandidates(optimized: boolean = true) {
  if (optimized) {
    return [
      { id: 'A001', name: 'Momentum Reversal 21D', ic: 0.092, sharpe: 1.51, decay: 18, status: 'pass', category: 'Price' },
      { id: 'A002', name: 'EV/EBITDA Zscore', ic: 0.076, sharpe: 1.34, decay: 35, status: 'pass', category: 'Fundamental' },
      { id: 'A003', name: 'Order Flow Imbalance', ic: 0.112, sharpe: 1.89, decay: 9, status: 'pass', category: 'Microstructure' },
      { id: 'A004', name: 'Earnings Surprise Drift', ic: 0.084, sharpe: 1.48, decay: 24, status: 'pass', category: 'Event' },
      { id: 'A005', name: 'Vol Surface Skew', ic: 0.081, sharpe: 1.42, decay: 14, status: 'pass', category: 'Options' },
      { id: 'A006', name: 'Insider Net Buy', ic: 0.085, sharpe: 1.39, decay: 52, status: 'pass', category: 'Alternative' },
      { id: 'A007', name: 'Short Interest Ratio', ic: 0.078, sharpe: 1.36, decay: 32, status: 'pass', category: 'Sentiment' },
      { id: 'A008', name: 'Macro Beta Timing', ic: 0.068, sharpe: 1.28, decay: 65, status: 'pass', category: 'Macro' },
    ];
  }
  return [
    { id: 'A001', name: 'Momentum Reversal 21D', ic: 0.087, sharpe: 1.43, decay: 15, status: 'pass', category: 'Price' },
    { id: 'A002', name: 'EV/EBITDA Zscore', ic: 0.062, sharpe: 1.12, decay: 30, status: 'pass', category: 'Fundamental' },
    { id: 'A003', name: 'Order Flow Imbalance', ic: 0.105, sharpe: 1.78, decay: 5, status: 'pass', category: 'Microstructure' },
    { id: 'A004', name: 'Earnings Surprise Drift', ic: 0.078, sharpe: 1.34, decay: 20, status: 'pass', category: 'Event' },
    { id: 'A005', name: 'Vol Surface Skew', ic: 0.071, sharpe: 1.21, decay: 10, status: 'pass', category: 'Options' },
    { id: 'A006', name: 'Insider Net Buy', ic: 0.054, sharpe: 0.91, decay: 45, status: 'fail', category: 'Alternative' },
    { id: 'A007', name: 'Short Interest Ratio', ic: 0.048, sharpe: 0.87, decay: 25, status: 'fail', category: 'Sentiment' },
    { id: 'A008', name: 'Macro Beta Timing', ic: 0.033, sharpe: 0.62, decay: 60, status: 'fail', category: 'Macro' },
  ];
}

export function generateMonitoringAlerts() {
  return [
    { type: 'error', message: 'Alpha A003 decay accelerated — IC dropped 40% in 5 days', time: '2m ago' },
    { type: 'warning', message: 'Data feed OHLCV latency +320ms above threshold', time: '8m ago' },
    { type: 'warning', message: 'Model drift detected: LightGBM feature distribution shift', time: '15m ago' },
    { type: 'success', message: 'Risk limits within bounds: Vol 14.7% vs limit 20%', time: '22m ago' },
    { type: 'error', message: 'Execution slippage breached: 3.8bps vs 2.5bps limit', time: '1h ago' },
  ];
}
