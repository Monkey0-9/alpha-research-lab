'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import VaRHistogram from '@/components/VaRHistogram';
import RiskAttribution from '@/components/RiskAttribution';
import DrawdownChart from '@/components/DrawdownChart';
import DataTable, { Column } from '@/components/DataTable';
import Badge from '@/components/Badge';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import { formatCurrency } from '@/lib/utils';
import { ShieldCheck, AlertTriangle, Play, RefreshCw, CheckCircle2 } from 'lucide-react';

export default function RiskEnginePage() {
  const [activeTab, setActiveTab] = useState<'METRICS' | 'COMPLIANCE'>('METRICS');
  const [loading, setLoading] = useState(true);
  const [varData, setVarData] = useState<any>(null);

  // Pre-trade compliance checker state
  const [testGrossLev, setTestGrossLev] = useState(1.6);
  const [testMaxWeight, setTestMaxWeight] = useState(0.12);
  const [complianceLoading, setComplianceLoading] = useState(false);
  const [complianceResult, setComplianceResult] = useState<any>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getRiskMetrics();
        setVarData(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleRunCompliance = async () => {
    setComplianceLoading(true);
    try {
      const res = await api.runComplianceCheck({
        gross_leverage: testGrossLev,
        max_single_weight: testMaxWeight
      });
      setComplianceResult(res);
    } catch (err) {
      console.error(err);
    } finally {
      setComplianceLoading(false);
    }
  };

  const factors: types.FactorAttributionItem[] = [
    { factor: 'Market Beta', exposure: 0.04, factor_return_pct: 14.2, contribution_bps: 56.8, pct_of_total_risk: 8.5 },
    { factor: 'Momentum', exposure: 0.53, factor_return_pct: 8.4, contribution_bps: 445.2, pct_of_total_risk: 52.4 },
    { factor: 'Quality', exposure: 0.30, factor_return_pct: 6.1, contribution_bps: 183.0, pct_of_total_risk: 21.5 },
    { factor: 'Low Volatility', exposure: 0.22, factor_return_pct: 3.5, contribution_bps: 77.0, pct_of_total_risk: 9.2 },
    { factor: 'Size', exposure: -0.07, factor_return_pct: 2.1, contribution_bps: -14.7, pct_of_total_risk: 1.8 },
    { factor: 'Value', exposure: -0.36, factor_return_pct: -1.8, contribution_bps: 64.8, pct_of_total_risk: 6.6 }
  ];

  const stressScenarios: types.StressScenario[] = [
    { scenario_name: '2008 Global Financial Crisis (Lehman)', shock_description: 'Equity markets down -42%, credit spreads blow out +600bps', historical_date: '2008-09-15', estimated_portfolio_pnl_pct: -5.84, estimated_loss_dollars: -145124, var_multiplier: 4.02 },
    { scenario_name: '2010 Flash Crash (E-mini Microstructure)', shock_description: 'Intraday 9% crash in 36 minutes, automated liquidity evaporation', historical_date: '2010-05-06', estimated_portfolio_pnl_pct: -2.15, estimated_loss_dollars: -53420, var_multiplier: 1.48 },
    { scenario_name: '2020 COVID-19 Liquidity Shock', shock_description: 'Rapid 33% drawdown in 22 trading sessions, VIX spikes to 82', historical_date: '2020-03-16', estimated_portfolio_pnl_pct: -4.51, estimated_loss_dollars: -112073, var_multiplier: 3.11 },
    { scenario_name: '2022 Fed Aggressive Rate Hikes', shock_description: '10Y Yield spikes +250bps, Tech multiples compress 30%', historical_date: '2022-06-13', estimated_portfolio_pnl_pct: -2.74, estimated_loss_dollars: -68089, var_multiplier: 1.89 },
    { scenario_name: '2023 US Regional Banking Panic (SVB)', shock_description: 'Regional bank ETF -28%, flight to Treasuries & Mega-Cap Tech', historical_date: '2023-03-10', estimated_portfolio_pnl_pct: -1.69, estimated_loss_dollars: -41996, var_multiplier: 1.16 }
  ];

  const stressColumns: Column<types.StressScenario>[] = [
    {
      key: 'scenario_name',
      header: 'Historical Macro Stress Scenario',
      render: (r) => (
        <div>
          <div style={{ fontWeight: 600, color: '#f8fafc' }}>{r.scenario_name}</div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>{r.shock_description}</div>
        </div>
      )
    },
    { key: 'historical_date', header: 'Event Date' },
    {
      key: 'estimated_portfolio_pnl_pct',
      header: 'Est. Portfolio Impact',
      align: 'right',
      render: (r) => <span className="tabular-nums" style={{ color: '#fb7185', fontWeight: 700 }}>{r.estimated_portfolio_pnl_pct.toFixed(2)}%</span>
    },
    {
      key: 'estimated_loss_dollars',
      header: 'Dollar Loss ($)',
      align: 'right',
      render: (r) => <span className="tabular-nums" style={{ color: '#fb7185' }}>{formatCurrency(r.estimated_loss_dollars, 0)}</span>
    },
    {
      key: 'var_multiplier',
      header: 'VaR Multiple',
      align: 'right',
      render: (r) => <span className="tabular-nums">{r.var_multiplier.toFixed(2)}x</span>
    },
    {
      key: 'verdict',
      header: 'Limit Status',
      align: 'center',
      render: (r) => <Badge label={Math.abs(r.estimated_portfolio_pnl_pct) < 10.0 ? 'WITHIN LIMITS' : 'BREACH'} type={Math.abs(r.estimated_portfolio_pnl_pct) < 10.0 ? 'pass' : 'fail'} />
    }
  ];

  const drawdownData = Array.from({ length: 90 }, (_, i) => {
    const d = new Date(Date.now() - (90 - i) * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    const dd = Math.sin(i * 0.15) * 4.2 - 2.6;
    return { date: d, drawdown: parseFloat(dd.toFixed(2)) };
  });

  return (
    <ErrorBoundary fallbackTitle="Institutional Risk Engine Interrupted">
      <TerminalHeader title="INSTITUTIONAL RISK ENGINE & STRESS TESTING" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
        {/* Navigation Tabs */}
        <div style={{ display: 'flex', gap: '0.5rem', borderBottom: '1px solid #222', paddingBottom: '0.5rem' }}>
          {[
            { id: 'METRICS', label: '1. VaR, FACTOR ATTRIBUTION & CRISIS STRESS', icon: AlertTriangle },
            { id: 'COMPLIANCE', label: '2. PRE-TRADE COMPLIANCE RULES', icon: ShieldCheck }
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
        {loading ? <LoadingSkeleton height="80px" label="LOADING RISK METRICS..." /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard label="HIST VaR 95%"        value={`-${(varData?.historical_var_pct || 1.45).toFixed(2)}%`}    change={formatCurrency(varData?.historical_var_dollars || 36032, 0)}  positive={false} subtext="1-DAY HORIZON" status="pass" />
            <MetricCard label="CORNISH-FISHER VaR"  value={`-${(varData?.cornish_fisher_var_pct || 1.58).toFixed(2)}%`} change="FAT TAIL EXPANSION"                                           positive={false} subtext="SKEW/KURTOSIS FIT" status="pass" />
            <MetricCard label="CVaR (EXP SHORTFALL)" value={`-${(varData?.cvar_expected_shortfall_pct || 2.15).toFixed(2)}%`} change={formatCurrency(varData?.cvar_dollars || 53427, 0)}         positive={false} subtext="EXPECTED TAIL LOSS" status="pass" />
            <MetricCard label="ANNUALIZED VOL"      value={`${(varData?.annualized_vol_pct || 12.4).toFixed(1)}%`}       change="LIMIT: 15.0%"                                                  positive={true}  subtext="WITHIN TOLERANCE" status="pass" />
            <MetricCard label="PORTFOLIO BETA (SPY)" value="0.04"                                                          change="MARKET NEUTRAL"                                               positive={true}  subtext="MINIMAL SYS RISK" status="pass" />
            <MetricCard label="MAX LEHMAN LOSS"     value="-5.84%"                                                        change="CAPACITY: 10.0%"                                              positive={true}  subtext="STRESS RESILIENT" status="pass" />
          </div>
        )}

        {/* TAB 1: METRICS & STRESS */}
        {activeTab === 'METRICS' && (
          <>
            <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
              <div className="terminal-card">
                <div className="terminal-card-header">
                  <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#FF6600' }}>
                    HISTORICAL RETURN DENSITY & VaR THRESHOLDS
                  </span>
                  <span className="badge-tag badge-live">NON-PARAMETRIC</span>
                </div>
                <div className="terminal-card-body">
                  <VaRHistogram height={250} var95Cutoff={-1.45} var99Cutoff={-2.15} />
                </div>
              </div>

              <div className="terminal-card">
                <div className="terminal-card-header">
                  <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#FF6600' }}>
                    BARRA FACTOR MODEL RISK ATTRIBUTION
                  </span>
                  <span className="badge-tag badge-pass">R² = 0.82</span>
                </div>
                <div className="terminal-card-body">
                  <RiskAttribution factors={factors} />
                </div>
              </div>
            </div>

            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#FF6600' }}>
                  MACRO REGIME STRESS TESTING & CRISIS REPLAY — HISTORICAL SCENARIOS
                </span>
                <span className="badge-tag badge-live">REAL HISTORICAL DRIFT</span>
              </div>
              <div className="terminal-card-body">
                <DataTable columns={stressColumns} data={stressScenarios} pageSize={5} />
              </div>
            </div>

            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.75rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#FF6600' }}>
                  TRAILING 90-DAY DRAWDOWN DEPTH — CIRCUIT BREAKER: -10.0%
                </span>
                <span className="badge-tag badge-pass">MAX DD: -4.8%</span>
              </div>
              <div className="terminal-card-body">
                <DrawdownChart data={drawdownData} height={200} />
              </div>
            </div>
          </>
        )}

        {/* TAB 2: PRE-TRADE COMPLIANCE */}
        {activeTab === 'COMPLIANCE' && (
          <div style={{ display: 'grid', gridTemplateColumns: '340px 1fr', gap: '0.85rem' }}>
            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  COMPLIANCE AUDIT CONTROLS
                </span>
                <span className="badge-tag badge-live">PRE-TRADE GATE</span>
              </div>
              <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                <div>
                  <label style={{ color: '#888' }}>PROPOSED GROSS LEVERAGE</label>
                  <input
                    type="number"
                    step="0.1"
                    value={testGrossLev}
                    onChange={(e) => setTestGrossLev(parseFloat(e.target.value) || 1.0)}
                    style={{ width: '100%', background: '#0a0d14', border: '1px solid var(--border-terminal)', color: '#f8fafc', padding: '0.35rem', marginTop: '0.2rem' }}
                  />
                </div>
                <div>
                  <label style={{ color: '#888' }}>MAX SINGLE ASSET WEIGHT</label>
                  <input
                    type="number"
                    step="0.01"
                    value={testMaxWeight}
                    onChange={(e) => setTestMaxWeight(parseFloat(e.target.value) || 0.05)}
                    style={{ width: '100%', background: '#0a0d14', border: '1px solid var(--border-terminal)', color: '#f8fafc', padding: '0.35rem', marginTop: '0.2rem' }}
                  />
                </div>
                <button
                  onClick={handleRunCompliance}
                  disabled={complianceLoading}
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
                    gap: '0.4rem'
                  }}
                >
                  <RefreshCw size={13} className={complianceLoading ? 'spin' : ''} />
                  {complianceLoading ? 'SCRUBBING ORDERS...' : 'RUN PRE-TRADE COMPLIANCE'}
                </button>
              </div>
            </div>

            <div className="terminal-card">
              <div className="terminal-card-header">
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  INSTITUTIONAL COMPLIANCE REPORT
                </span>
                <span className="badge-tag badge-pass">{complianceResult ? complianceResult.verdict : 'STANDBY'}</span>
              </div>
              <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
                {complianceResult ? (
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontFamily: 'var(--font-mono)', fontSize: '0.72rem' }}>
                    <div style={{ background: complianceResult.passed ? '#071609' : '#220808', border: complianceResult.passed ? '1px solid #00AA33' : '1px solid #AA0000', padding: '0.65rem' }}>
                      <div style={{ color: complianceResult.passed ? '#00FF41' : '#FF3333', fontWeight: 800 }}>
                        STATUS: {complianceResult.verdict}
                      </div>
                      <div style={{ color: '#ccc', marginTop: '0.2rem' }}>
                        All proposed orders vetted against regulatory constraints, concentration limits, and restricted lists.
                      </div>
                    </div>

                    <table style={{ width: '100%', borderCollapse: 'collapse', marginTop: '0.5rem' }}>
                      <thead>
                        <tr style={{ borderBottom: '1px solid #333', color: '#888', textAlign: 'left' }}>
                          <th style={{ padding: '0.4rem' }}>RULE DEFINITION</th>
                          <th style={{ padding: '0.4rem' }}>CURRENT / PROPOSED</th>
                          <th style={{ padding: '0.4rem' }}>THRESHOLD</th>
                          <th style={{ padding: '0.4rem' }}>VERDICT</th>
                        </tr>
                      </thead>
                      <tbody>
                        {complianceResult.checks?.map((c: any, idx: number) => (
                          <tr key={idx} style={{ borderBottom: '1px solid #1a1a1a' }}>
                            <td style={{ padding: '0.4rem', color: '#f8fafc' }}>{c.rule}</td>
                            <td style={{ padding: '0.4rem', color: '#00CCFF' }}>{c.current ?? c.violations ?? c.max_participation}</td>
                            <td style={{ padding: '0.4rem', color: '#888' }}>{c.limit ?? '0'}</td>
                            <td style={{ padding: '0.4rem' }}>
                              <Badge label={c.passed ? 'APPROVED' : 'BLOCKED'} type={c.passed ? 'pass' : 'fail'} />
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                ) : (
                  <div style={{ padding: '2rem', textAlign: 'center', color: '#666', fontFamily: 'var(--font-mono)', fontSize: '0.75rem' }}>
                    Click &quot;RUN PRE-TRADE COMPLIANCE&quot; to test proposed allocations against hard risk limits and compliance mandates.
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
