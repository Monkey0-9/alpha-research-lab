/**
 * Institutional Quantitative Trading System — Type Definitions
 * Covers all 12 Quantitative Pipeline Modules
 */

export interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: string | number;
    color?: string;
    dataKey?: string;
    payload?: Record<string, unknown>;
  }>;
  label?: string | number;
}

export interface MetricCardData {
  label: string;
  value: string | number;
  change?: string;
  deltaBps?: number;
  positive?: boolean;
  subtext?: string;
  benchmark?: string | number;
  status?: 'pass' | 'warn' | 'fail' | 'live' | 'neutral';
}

export interface TimeSeriesPoint {
  date: string;
  [key: string]: string | number;
}

// 01 — Data Infrastructure
export interface DataSourceItem {
  name: string;
  type: string;
  coverage: string;
  frequency: string;
  status: 'ACTIVE' | 'SYNCING' | 'MAINTENANCE';
  latency_ms: number;
  records_count: number;
  last_updated: string;
}

export interface UniverseAsset {
  ticker: string;
  name: string;
  sector: string;
  market_cap_billions: number;
  adv_millions: number;
  status: 'ACTIVE' | 'INACTIVE';
}

export interface DataQualityReport {
  overall_score: number;
  missing_data_pct: number;
  outliers_flagged: number;
  split_adjustments_verified: boolean;
  dividend_adjustments_verified: boolean;
  survivorship_bias_eliminated: boolean;
  pit_compliance_score: number;
  last_audit_timestamp: string;
}

// 02 — Feature Factory
export interface FeatureItem {
  id: string;
  name: string;
  category: 'MOMENTUM' | 'VOLATILITY' | 'MEAN_REVERSION' | 'VOLUME' | 'STATISTICAL' | 'ALTERNATIVE';
  lookback: string;
  ic_mean: number;
  ic_std: number;
  ic_ir: number;
  t_statistic: number;
  status: 'PROMOTED' | 'TESTING' | 'DEPRECATED';
  description: string;
}

export interface FeatureICPoint {
  feature: string;
  ic: number;
  t_stat: number;
  passed: boolean;
}

// 03 — Alpha Discovery
export interface GeneticProgramRun {
  generation: number;
  best_fitness_ic: number;
  avg_fitness_ic: number;
  population_size: number;
  best_formula: string;
  diversity_index: number;
}

export interface AlphaHypothesis {
  id: string;
  name: string;
  author: string;
  economic_rationale: string;
  category: string;
  status: 'IDEATION' | 'BACKTESTING' | 'REJECTED' | 'PROMOTED';
  created_at: string;
}

// 04 — Statistical Engine
export interface MultipleTestingResult {
  family_wise_error_rate: number;
  bonferroni_threshold: number;
  benjamini_hochberg_fdr: number;
  total_hypotheses_tested: number;
  raw_significant_count: number;
  fdr_significant_count: number;
  bonferroni_significant_count: number;
}

export interface DeflatedSharpeRatioResult {
  observed_sharpe: number;
  benchmark_sharpe: number;
  n_independent_trials: number;
  variance_of_sharpes: number;
  skewness: number;
  kurtosis: number;
  dsr_probability: number;
  passed_haircut: boolean;
}

export interface AlphaDecayLag {
  lag_days: number;
  ic: number;
  decay_pct: number;
}

// 05 — Model Research Lab
export interface ModelComparisonItem {
  model_name: string;
  family: string;
  in_sample_sharpe: number;
  out_of_sample_sharpe: number;
  mean_ic: number;
  max_drawdown_pct: number;
  annual_turnover: number;
  training_time_sec: number;
  status: 'CANDIDATE' | 'BASELINE' | 'DEPLOYED';
}

export interface TrainingCurvePoint {
  epoch: number;
  train_loss: number;
  val_loss: number;
  val_ic: number;
}

export interface EnsembleComponent {
  name: string;
  weight: number;
  individual_sharpe: number;
  active: boolean;
}

// 06 — Time-Series Validation
export interface WalkForwardWindow {
  window_idx: number;
  train_start: string;
  train_end: string;
  purge_start: string;
  purge_end: string;
  test_start: string;
  test_end: string;
  in_sample_sharpe: number;
  out_of_sample_sharpe: number;
}

export interface PurgedFold {
  fold: number;
  train_pct: number;
  val_pct: number;
  purged_bars: number;
  embargo_bars: number;
}

// 07 — Alpha Quality Gate
export interface AlphaCandidate {
  id: string;
  name: string;
  category: string;
  ic: number;
  ic_ir: number;
  sharpe: number;
  dsr_stat: number;
  max_drawdown: number;
  turnover: number;
  decay_days: number;
  capacity: string;
  status: 'passed' | 'rejected' | 'candidate';
  description?: string;
  checks?: {
    sharpe_pass: boolean;
    ic_pass: boolean;
    dsr_pass: boolean;
    drawdown_pass: boolean;
    decay_pass: boolean;
  };
}

// 08 — Portfolio Construction
export interface EfficientFrontierPortfolio {
  volatility: number;
  expected_return: number;
  sharpe_ratio: number;
  is_optimal?: boolean;
  is_min_vol?: boolean;
  is_risk_parity?: boolean;
}

export interface PortfolioHoldingItem {
  ticker: string;
  weight_pct: number;
  shares: number;
  entry_price: number;
  market_price: number;
  market_value: number;
  unrealized_pnl: number;
  marginal_risk_pct: number;
  side: 'LONG' | 'SHORT';
}

// 09 — Execution Research
export interface ExecutionAlgoItem {
  name: string;
  type: 'TWAP' | 'VWAP' | 'ALMGREN_CHRISS' | 'PERCENT_OF_VOLUME';
  avg_slippage_bps: number;
  tracking_error_bps: number;
  fill_rate_pct: number;
  market_impact_bps: number;
  total_volume_usd: string;
}

export interface AlmgrenChrissTrajectoryPoint {
  t_interval: number;
  time_label: string;
  shares_remaining: number;
  pct_executed: number;
  expected_impact_bps: number;
}

// 10 — Risk Engine
export interface VaRMetrics {
  confidence: number;
  portfolio_value: number;
  historical_var_pct: number;
  historical_var_dollars: number;
  parametric_var_pct: number;
  parametric_var_dollars: number;
  cvar_expected_shortfall_pct: number;
  cvar_dollars: number;
  annualized_vol_pct: number;
}

export interface FactorAttributionItem {
  factor: string;
  exposure: number;
  factor_return_pct: number;
  contribution_bps: number;
  pct_of_total_risk: number;
}

export interface StressScenario {
  scenario_name: string;
  shock_description: string;
  historical_date: string;
  estimated_portfolio_pnl_pct: number;
  estimated_loss_dollars: number;
  var_multiplier: number;
}

// 11 — Live Research
export interface LiveStrategyStatus {
  strategy_id: string;
  strategy_name: string;
  universe: string;
  allocated_capital: number;
  current_equity: number;
  live_sharpe: number;
  realized_pnl_today: number;
  unrealized_pnl: number;
  open_positions: number;
  execution_mode: 'PAPER' | 'DRY_RUN' | 'CANARY' | 'PRODUCTION';
  status: 'ACTIVE' | 'HALTED' | 'REBALANCING';
}

export interface LiveSignalFeedItem {
  timestamp: string;
  ticker: string;
  side: 'BUY' | 'SELL' | 'CLOSE';
  strength: number;
  predicted_return_bps: number;
  urgency: 'HIGH' | 'MEDIUM' | 'LOW';
  confidence_score: number;
}

// 12 — Production Monitoring
export interface AlphaHealthMetrics {
  alpha_id: string;
  name: string;
  current_ic: number;
  initial_ic: number;
  half_life_days: number;
  psi_drift_score: number;
  status: 'HEALTHY' | 'DEGRADING' | 'DECOMMISSION_ALERT';
  sharpe_ratio: number;
  days_live: number;
}

export interface ProductionAlertItem {
  id: string;
  timestamp: string;
  severity: 'CRITICAL' | 'WARNING' | 'INFO' | 'critical' | 'warning' | 'info' | 'success';
  category?: 'ALPHA_DECAY' | 'FEATURE_DRIFT' | 'RISK_BREACH' | 'EXECUTION_SLIPPAGE' | 'DATA_LATENCY';
  module?: string;
  message: string;
  acknowledged: boolean;
}

// 00 — Executive Dashboard
export interface ExecutiveDashboardSummary {
  portfolio_nav: number;
  daily_pnl_dollars: number;
  daily_pnl_pct: number;
  annualized_sharpe: number;
  calmar_ratio: number;
  information_ratio: number;
  max_drawdown_pct: number;
  annualized_vol_pct: number;
  current_regime: string;
  active_alphas_count: number;
  open_positions_count: number;
  var_95_daily_pct: number;
  cvar_95_daily_pct: number;
}
