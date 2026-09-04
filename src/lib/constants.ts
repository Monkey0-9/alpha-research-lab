/**
 * Institutional Quantitative Trading Constants
 * Terminal Palette, System Limits, Risk Cutoffs, and Mathematical Definitions
 */

export const TERMINAL_COLORS = {
  bgPrimary: '#080a0f',
  bgSecondary: '#0d1117',
  bgCard: '#111827',
  bgCardHover: '#161f33',
  borderSubtle: '#1e293b',
  borderAccent: '#3b82f6',
  textPrimary: '#f8fafc',
  textSecondary: '#94a3b8',
  textMuted: '#64748b',
  accentBlue: '#3b82f6',
  accentEmerald: '#10b981',
  accentAmber: '#f59e0b',
  accentRose: '#f43f5e',
  accentPurple: '#8b5cf6',
  accentCyan: '#06b6d4',
  chartGrid: '#1e293b',
  benchmark: '#64748b'
};

export const UNIVERSES = [
  { id: 'sp500', name: 'S&P 500 Top Liquid 100', count: 100, assetClass: 'US Large Cap Equity' },
  { id: 'nasdaq100', name: 'Nasdaq 100 Tech Momentum', count: 100, assetClass: 'Tech & Growth' },
  { id: 'russell2000', name: 'Russell 2000 Small Cap Vol', count: 200, assetClass: 'US Small Cap' },
  { id: 'multiasset', name: 'Global Multi-Asset Macro', count: 45, assetClass: 'FX / Rates / Equities' }
];

export const QUALITY_GATE_THRESHOLDS = {
  minSharpe: 1.50,
  minIC: 0.05,
  minDSR: 0.95,
  maxDrawdown: 0.12,
  minHalfLifeDays: 5.0,
  maxTurnover: 0.40,
  minCapacityUSD: 50_000_000
};

export const RISK_LIMITS = {
  maxVaR95DailyPct: 2.50,
  maxCVaR95DailyPct: 3.50,
  maxAnnualVolPct: 15.0,
  maxDrawdownWatermarkPct: 10.0,
  maxGrossLeverage: 2.0,
  maxSingleAssetWeightPct: 10.0,
  maxSectorExposurePct: 25.0
};

export const MARKET_REGIMES = [
  { id: 'bull_low_vol', name: 'Bull Quiet (Low Volatility)', betaTilt: 1.1, vol: '11.2%', prob: 0.58, status: 'CURRENT' },
  { id: 'bear_high_vol', name: 'Bear Volatile (Flight to Quality)', betaTilt: 0.6, vol: '24.8%', prob: 0.18, status: 'STANDBY' },
  { id: 'range_bound', name: 'Choppy Sideways / Mean-Reverting', betaTilt: 0.9, vol: '14.5%', prob: 0.16, status: 'STANDBY' },
  { id: 'liquidity_stress', name: 'Liquidity Squeeze / Crisis', betaTilt: 0.3, vol: '38.4%', prob: 0.08, status: 'STANDBY' }
];

export const PIPELINE_STAGES = [
  { id: 'ingest', label: '01 Ingestion', status: 'PASS', latency: '42ms', records: '1.24M' },
  { id: 'features', label: '02 Features', status: 'PASS', latency: '88ms', features: '148' },
  { id: 'alpha', label: '03 Discovery', status: 'PASS', latency: '310ms', candidates: '24' },
  { id: 'stat', label: '04 Stats Engine', status: 'PASS', latency: '19ms', passedDSR: '8' },
  { id: 'model', label: '05 Model Lab', status: 'PASS', latency: '540ms', ensembleSharpe: '2.14' },
  { id: 'validation', label: '06 Purged CV', status: 'PASS', latency: '120ms', oosDegradation: '-4.2%' },
  { id: 'gate', label: '07 Quality Gate', status: 'PASS', latency: '15ms', promoted: '4' },
  { id: 'portfolio', label: '08 Portfolio Opt', status: 'PASS', latency: '65ms', turnover: '18.4%' },
  { id: 'execution', label: '09 Smart Execution', status: 'PASS', latency: '12ms', slippage: '1.4bps' },
  { id: 'risk', label: '10 Risk Attrib', status: 'PASS', latency: '28ms', var95: '1.45%' },
  { id: 'live', label: '11 Live Paper', status: 'LIVE', latency: '8ms', activeOrders: '12' },
  { id: 'monitor', label: '12 Telemetry', status: 'LIVE', latency: '2ms', psiStatus: 'NOMINAL' }
];
