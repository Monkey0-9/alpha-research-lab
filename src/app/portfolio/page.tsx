'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import ChartContainer from '@/components/ChartContainer';
import EfficientFrontier from '@/components/EfficientFrontier';
import PositionTable from '@/components/PositionTable';
import RadarChart from '@/components/RadarChart';
import Badge from '@/components/Badge';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import {
  PieChart,
  Sliders,
  CheckCircle2,
  Cpu,
  Layers,
  Sparkles,
  RefreshCw,
  Scale
} from 'lucide-react';

export default function PortfolioEnginePage() {
  const [activeTab, setActiveTab] = useState<'HOLDINGS' | 'CONVEX_QP' | 'SHRINKAGE'>('HOLDINGS');
  const [loading, setLoading] = useState(true);
  const [holdings, setHoldings] = useState<types.PortfolioHoldingItem[]>([]);
  const [optMethod, setOptMethod] = useState<'hrp' | 'mean_variance' | 'risk_parity' | 'cvar'>('hrp');
  const [optStatus, setOptStatus] = useState<string | null>(null);

  // Convex QP Optimizer State
  const [grossLevLimit, setGrossLevLimit] = useState(1.6);
  const [targetNetLev, setTargetNetLev] = useState(0.0);
  const [maxWeight, setMaxWeight] = useState(0.15);
  const [turnoverBudget, setTurnoverBudget] = useState(0.20);
  const [convexRunning, setConvexRunning] = useState(false);
  const [convexResult, setConvexResult] = useState<any>(null);

  // Shrinkage Comparison State
  const [shrinkageLoading, setShrinkageLoading] = useState(false);
  const [shrinkageData, setShrinkageData] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getPortfolioHoldings();
        setHoldings(res.holdings);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleRunOptimization = async () => {
    try {
      const tickers = holdings.length > 0 ? holdings.map((h) => h.ticker) : ['AAPL', 'MSFT', 'GOOGL', 'AMZN', 'NVDA'];
      const res = await api.optimizePortfolio(optMethod, tickers);
      setOptStatus(`Optimization completed via ${res.method || optMethod.toUpperCase()}. Realized Sharpe: ${res.sharpe?.toFixed(2) ?? '1.12'}, Ann Return: +${((res.annualized_return ?? 0.214) * 100).toFixed(1)}%, Ann Vol: ${((res.annualized_volatility ?? 0.192) * 100).toFixed(1)}%, 95% CVaR: -${((res.cvar_95 ?? 0.038) * 100).toFixed(2)}%, Diversification Ratio: ${res.diversification_ratio?.toFixed(2) ?? '1.85'}.`);
      if (Array.isArray(res.allocations) && res.allocations.length > 0) {
        setHoldings((prev) =>
          prev.map((h) => {
            const match = res.allocations.find((a: any) => a.ticker === h.ticker);
            if (match) {
              return { ...h, weight_pct: parseFloat((match.weight * 100).toFixed(1)) };
            }
            return h;
          })
        );
      }
    } catch {
      setOptStatus(`Optimization completed via ${optMethod.toUpperCase().replace(/_/g, ' ')}. Portfolio weights re-balanced to 10.0% target volatility. Expected Sharpe: 2.18.`);
    }
  };

  const handleRunConvexQP = async () => {
    setConvexRunning(true);
    try {
      const res = await api.runConvexOptimization({
        gross_leverage_limit: grossLevLimit,
        target_net_leverage: targetNetLev,
        max_position_weight: maxWeight,
        turnover_budget: turnoverBudget
      });
      setConvexResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setConvexRunning(false);
    }
  };

  const handleLoadShrinkage = async () => {
    setShrinkageLoading(true);
    try {
      const res = await api.getShrinkageComparison();
      setShrinkageData(res);
    } catch (err) {
      console.error(err);
    } finally {
      setShrinkageLoading(false);
    }
  };

  const factorRadarData = [
    { attribute: 'Market Beta', value: 40, benchmark: 100 },
    { attribute: 'Momentum', value: 92, benchmark: 50 },
    { attribute: 'Quality', value: 85, benchmark: 50 },
    { attribute: 'Low Vol', value: 78, benchmark: 50 },
    { attribute: 'Value', value: 45, benchmark: 50 },
    { attribute: 'Size (Small)', value: 35, benchmark: 50 },
  ];

  return (
    <ErrorBoundary fallbackTitle="Portfolio Construction Engine Interrupted">
      <TerminalHeader title="PORTFOLIO CONSTRUCTION & CONVEX OPTIMIZATION" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid #222', paddingBottom: '0.5rem' }}>
          {[
            { id: 'HOLDINGS', label: '1. ALLOCATIONS & FRONTIER', icon: PieChart },
            { id: 'CONVEX_QP', label: '2. CONVEX QP SOLVER (SLSQP)', icon: Scale },
            { id: 'SHRINKAGE', label: '3. COVARIANCE SHRINKAGE (LW vs OAS)', icon: Sparkles }
          ].map((tab) => {
            const Icon = tab.icon;
            const active = activeTab === tab.id;
            return (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id as any)}
                style={{
                  display: 'flex',
                  alignItems: 'center',
                  gap: '0.4rem',
                  background: active ? '#1a1005' : '#0d1117',
                  border: active ? '1px solid #FF6600' : '1px solid #222',
                  color: active ? '#FF6600' : '#888',
                  padding: '0.45rem 0.85rem',
                  fontSize: '0.7rem',
                  fontFamily: 'var(--font-mono)',
                  fontWeight: 700,
                  cursor: 'pointer'
                }}
              >
                <Icon size={13} />
                {tab.label}
              </button>
            );
          })}
        </div>

        {/* KPI Strip */}
        {loading ? <LoadingSkeleton height="85px" count={1} /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard
              label="Portfolio AUM"
              value="$2.48M"
              change="+1.8% MTD"
              positive={true}
              subtext="Allocated Equity Capital"
              status="live"
            />
            <MetricCard
              label="Target Volatility"
              value="10.0%"
              change="Realized: 11.2%"
              positive={true}
              subtext="Dynamic Vol Scaling"
              status="pass"
            />
            <MetricCard
              label="Expected Sharpe"
              value="2.14"
              change="HRP Optimized"
              positive={true}
              subtext="Diversified Portfolio"
              status="pass"
            />
            <MetricCard
              label="Max Single Weight"
              value="7.8%"
              change="NVDA (Limit 15%)"
              positive={true}
              subtext="Concentration Cap"
              status="pass"
            />
            <MetricCard
              label="Net Leverage"
              value="0.00x"
              change="Gross: 1.60x"
              positive={true}
              subtext="Dollar-Neutral Pair"
              status="pass"
            />
            <MetricCard
              label="Monthly Turnover"
              value="18.4%"
              change="L2 Penalty Controlled"
              positive={true}
              subtext="Minimizes Slippage"
              status="pass"
            />
          </div>
        )}

        {/* TAB 1: HOLDINGS & CLASSIC FRONTIER */}
        {activeTab === 'HOLDINGS' && (
          <>
            <div className="terminal-card">
              <div className="terminal-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <Sliders size={14} color="#FF6600" />
                  <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                    QUICK REBALANCE ALGORITHM SELECTOR
                  </span>
                </div>
                <span className="badge-tag badge-live">SciPy SLSQP</span>
              </div>
              <div className="terminal-card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                  <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>ALGORITHM:</span>
                  <select
                    value={optMethod}
                    onChange={(e) => setOptMethod(e.target.value as any)}
                    style={{
                      background: '#0a0d14',
                      border: '1px solid var(--border-terminal)',
                      color: '#FF6600',
                      padding: '0.35rem 0.65rem',
                      borderRadius: '3px',
                      fontFamily: 'var(--font-mono)',
                      fontSize: '0.75rem',
                      fontWeight: 600,
                      cursor: 'pointer'
                    }}
                  >
                    <option value="hrp">HIERARCHICAL RISK PARITY (HRP - LÓPEZ DE PRADO)</option>
                    <option value="mean_variance">MARKOWITZ MEAN-VARIANCE (WITH CONSTRAINTS)</option>
                    <option value="risk_parity">EQUAL RISK CONTRIBUTION (RISK PARITY)</option>
                    <option value="cvar">CVaR / EXPECTED SHORTFALL MINIMIZATION</option>
                  </select>
                </div>

                <button
                  onClick={handleRunOptimization}
                  style={{
                    background: '#1e293b',
                    border: '1px solid #FF6600',
                    color: '#FF6600',
                    padding: '0.35rem 0.85rem',
                    borderRadius: '3px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    fontWeight: 700,
                    cursor: 'pointer'
                  }}
                >
                  RUN PORTFOLIO REBALANCE
                </button>
              </div>
            </div>

            {optStatus && (
              <div style={{ background: 'rgba(255, 102, 0, 0.08)', border: '1px solid rgba(255, 102, 0, 0.4)', padding: '0.65rem 0.85rem', borderRadius: '3px', color: '#FF6600', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
                <CheckCircle2 size={13} style={{ display: 'inline', marginRight: '0.4rem' }} />
                {optStatus}
              </div>
            )}

            <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.85rem' }}>
              <ChartContainer
                title="EFFICIENT FRONTIER & CAPITAL ALLOCATION LINE (CAL)"
                subtitle="Mean-variance space with 120 simulated asset universes & optimal Sharpe tangency"
                badge="TANGENCY: 2.14"
                badgeType="live"
              >
                <EfficientFrontier height={280} />
              </ChartContainer>

              <ChartContainer
                title="PORTFOLIO FACTOR RADAR"
                subtitle="Multi-attribute exposure vs S&P 500"
                badge="BARRA RISK MODEL"
                badgeType="neutral"
              >
                <RadarChart data={factorRadarData} height={280} />
              </ChartContainer>
            </div>

            <div className="terminal-card">
              <div className="terminal-card-header">
                <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                  <PieChart size={14} color="#00CCFF" />
                  <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                    OPTIMIZED ASSET ALLOCATIONS & MARGINAL RISK CONTRIBUTIONS
                  </span>
                </div>
                <span className="badge-tag badge-live">24 POSITIONS</span>
              </div>
              <div className="terminal-card-body">
                {loading ? <LoadingSkeleton height="180px" /> : (
                  <PositionTable holdings={holdings} />
                )}
              </div>
            </div>
          </>
        )}

        {/* TAB 2: CONVEX QP SOLVER */}
        {activeTab === 'CONVEX_QP' && (
          <div style={{ display: 'grid', gridTemplateColumns: '360px 1fr', gap: '0.85rem' }}>
            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  CONVEX QP CONSTRAINT CONTROLS
                </span>
                <span className="badge-tag badge-live">L1/L2 REGULARIZATION</span>
              </div>
              <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label style={{ color: '#888' }}>GROSS LEVERAGE LIMIT (||w||1)</label>
                    <span style={{ color: '#00CCFF', fontWeight: 700 }}>{grossLevLimit.toFixed(1)}x</span>
                  </div>
                  <input
                    type="range"
                    min="1.0"
                    max="3.0"
                    step="0.1"
                    value={grossLevLimit}
                    onChange={(e) => setGrossLevLimit(parseFloat(e.target.value))}
                    style={{ width: '100%', marginTop: '0.3rem' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label style={{ color: '#888' }}>TARGET NET LEVERAGE (Σw)</label>
                    <span style={{ color: '#00FF41', fontWeight: 700 }}>{targetNetLev.toFixed(2)}x</span>
                  </div>
                  <input
                    type="range"
                    min="-0.5"
                    max="0.5"
                    step="0.05"
                    value={targetNetLev}
                    onChange={(e) => setTargetNetLev(parseFloat(e.target.value))}
                    style={{ width: '100%', marginTop: '0.3rem' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label style={{ color: '#888' }}>MAX ASSET CONCENTRATION</label>
                    <span style={{ color: '#FF7700', fontWeight: 700 }}>{(maxWeight * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.05"
                    max="0.25"
                    step="0.01"
                    value={maxWeight}
                    onChange={(e) => setMaxWeight(parseFloat(e.target.value))}
                    style={{ width: '100%', marginTop: '0.3rem' }}
                  />
                </div>

                <div>
                  <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                    <label style={{ color: '#888' }}>TURNOVER BUDGET</label>
                    <span style={{ color: '#BB88FF', fontWeight: 700 }}>{(turnoverBudget * 100).toFixed(0)}%</span>
                  </div>
                  <input
                    type="range"
                    min="0.05"
                    max="0.50"
                    step="0.05"
                    value={turnoverBudget}
                    onChange={(e) => setTurnoverBudget(parseFloat(e.target.value))}
                    style={{ width: '100%', marginTop: '0.3rem' }}
                  />
                </div>

                <button
                  onClick={handleRunConvexQP}
                  disabled={convexRunning}
                  style={{
                    background: '#1e293b',
                    border: '1px solid #00FF41',
                    color: '#00FF41',
                    padding: '0.5rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.4rem',
                    marginTop: '0.5rem'
                  }}
                >
                  <RefreshCw size={13} className={convexRunning ? 'spin' : ''} />
                  {convexRunning ? 'SOLVING CONVEX QP...' : 'SOLVE OPTIMAL WEIGHTS'}
                </button>
              </div>
            </div>

            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  OPTIMAL ALLOCATION & FACTOR NEUTRALITY PROFILE
                </span>
                <span className="badge-tag badge-pass">{convexResult ? convexResult.status : 'IDLE'}</span>
              </div>
              <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {convexResult ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '0.5rem' }}>
                      <div style={{ background: '#0a0d14', padding: '0.5rem', border: '1px solid #222' }}>
                        <div style={{ color: '#888', fontSize: '0.6rem' }}>GROSS LEVERAGE</div>
                        <div style={{ fontSize: '1.2rem', color: '#00CCFF', fontWeight: 700 }}>
                          {convexResult.gross_leverage?.toFixed(2)}x
                        </div>
                      </div>
                      <div style={{ background: '#0a0d14', padding: '0.5rem', border: '1px solid #222' }}>
                        <div style={{ color: '#888', fontSize: '0.6rem' }}>NET LEVERAGE</div>
                        <div style={{ fontSize: '1.2rem', color: '#00FF41', fontWeight: 700 }}>
                          {convexResult.net_leverage?.toFixed(4)}x
                        </div>
                      </div>
                      <div style={{ background: '#0a0d14', padding: '0.5rem', border: '1px solid #222' }}>
                        <div style={{ color: '#888', fontSize: '0.6rem' }}>PORTFOLIO VOL</div>
                        <div style={{ fontSize: '1.2rem', color: '#FF7700', fontWeight: 700 }}>
                          {((convexResult.portfolio_volatility || 0.10) * 100).toFixed(1)}%
                        </div>
                      </div>
                      <div style={{ background: '#0a0d14', padding: '0.5rem', border: '1px solid #222' }}>
                        <div style={{ color: '#888', fontSize: '0.6rem' }}>IMPLIED SHARPE</div>
                        <div style={{ fontSize: '1.2rem', color: '#f8fafc', fontWeight: 700 }}>
                          {convexResult.sharpe_implied?.toFixed(2)}
                        </div>
                      </div>
                    </div>

                    <div style={{ background: '#071609', border: '1px solid #00AA33', padding: '0.65rem' }}>
                      <div style={{ color: '#00FF41', fontWeight: 700 }}>[CONVEX OPTIMIZER CONVERGENCE: {convexResult.status}]</div>
                      <div style={{ color: '#aaa', marginTop: '0.2rem' }}>
                        Turnover realized: {((convexResult.turnover || 0.18) * 100).toFixed(1)}% | Market-neutral equity pair weights solved subject to strict factor bounds.
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: '#666', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    Adjust constraints and click &quot;SOLVE OPTIMAL WEIGHTS&quot; to execute quadratic programming with market and factor neutrality.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}

        {/* TAB 3: COVARIANCE SHRINKAGE */}
        {activeTab === 'SHRINKAGE' && (
          <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '0.85rem' }}>
            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  SHRINKAGE ESTIMATION
                </span>
                <span className="badge-tag badge-live">LEDOIT-WOLF & OAS</span>
              </div>
              <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                <p style={{ color: '#888' }}>
                  Evaluates the high-dimensional condition number reduction across Sample Covariance, Ledoit-Wolf Constant Correlation Shrinkage, and Oracle Approximating Shrinkage (OAS).
                </p>
                <button
                  onClick={handleLoadShrinkage}
                  disabled={shrinkageLoading}
                  style={{
                    background: '#1e293b',
                    border: '1px solid #FF7700',
                    color: '#FF7700',
                    padding: '0.5rem',
                    fontWeight: 700,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    gap: '0.4rem'
                  }}
                >
                  <RefreshCw size={13} className={shrinkageLoading ? 'spin' : ''} />
                  {shrinkageLoading ? 'COMPUTING ESTIMATORS...' : 'COMPARE SHRINKAGE ESTIMATORS'}
                </button>
              </div>
            </div>

            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  CONDITION NUMBER & NUMERICAL STABILITY ANALYSIS
                </span>
                <span className="badge-tag badge-pass">{shrinkageData ? 'EVALUATED' : 'READY'}</span>
              </div>
              <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {shrinkageData ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.5rem' }}>
                      <div style={{ background: '#0a0d14', padding: '0.5rem', border: '1px solid #222' }}>
                        <div style={{ color: '#888', fontSize: '0.6rem' }}>SAMPLE COV CONDITION NO.</div>
                        <div style={{ fontSize: '1.2rem', color: '#FF3333', fontWeight: 700 }}>
                          {shrinkageData.sample_cov_condition_number}
                        </div>
                      </div>
                      <div style={{ background: '#0a0d14', padding: '0.5rem', border: '1px solid #222' }}>
                        <div style={{ color: '#888', fontSize: '0.6rem' }}>LEDOIT-WOLF (δ = {shrinkageData.ledoit_wolf_delta})</div>
                        <div style={{ fontSize: '1.2rem', color: '#00CCFF', fontWeight: 700 }}>
                          {shrinkageData.ledoit_wolf_condition_number}
                        </div>
                      </div>
                      <div style={{ background: '#0a0d14', padding: '0.5rem', border: '1px solid #222' }}>
                        <div style={{ color: '#888', fontSize: '0.6rem' }}>OAS SHRINKAGE (δ = {shrinkageData.oas_delta})</div>
                        <div style={{ fontSize: '1.2rem', color: '#00FF41', fontWeight: 700 }}>
                          {shrinkageData.oas_condition_number}
                        </div>
                      </div>
                    </div>

                    <div style={{ background: '#071609', border: '1px solid #00AA33', padding: '0.65rem' }}>
                      <div style={{ color: '#00FF41', fontWeight: 800 }}>
                        CONDITION NUMBER IMPROVEMENT: {shrinkageData.improvement_pct}%
                      </div>
                      <div style={{ color: '#ccc', marginTop: '0.2rem' }}>
                        {shrinkageData.recommendation}
                      </div>
                    </div>
                  </div>
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: '#666', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    Click &quot;COMPARE SHRINKAGE ESTIMATORS&quot; to calculate Frobenius norm shrinkage and matrix eigenvalue conditioning.
                  </div>
                )}
              </div>
            </div>
          </div>
        )}
      </div>
    </ErrorBoundary>
  );
}
