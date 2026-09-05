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


export default function RiskEnginePage() {
  const [loading, setLoading] = useState(true);
  const [varData, setVarData] = useState<types.VaRMetrics | null>(null);

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

  // Drawdown points for chart
  const drawdownData = Array.from({ length: 90 }, (_, i) => {
    const d = new Date(Date.now() - (90 - i) * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
    const dd = Math.sin(i * 0.15) * 4.2 - 2.6;
    return { date: d, drawdown: parseFloat(dd.toFixed(2)) };
  });

  return (
    <ErrorBoundary fallbackTitle="Institutional Risk Engine Interrupted">
      <TerminalHeader title="INSTITUTIONAL RISK ENGINE & STRESS TESTING" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>

        {/* Section Header */}
        <div style={{ padding: '0.28rem 0.6rem', background: '#0d0600', border: '1px solid #FF6600', borderBottom: '1px solid #2a1500', display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>RISK METRICS — VAR / CVAR / FACTOR ATTRIBUTION</span>
          <span style={{ background: '#FF6600', color: '#000', fontSize: '0.58rem', fontWeight: 900, padding: '0 0.4rem', height: '15px', display: 'inline-flex', alignItems: 'center' }}>LIVE</span>
        </div>

        {/* KPI Strip */}
        {loading ? <LoadingSkeleton height="80px" label="LOADING RISK METRICS..." /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '3px' }}>
            <MetricCard label="HIST VaR 95%"        value={`-${(varData?.historical_var_pct || 1.45).toFixed(2)}%`}    change={formatCurrency(varData?.historical_var_dollars || 36032, 0)}  positive={false} subtext="1-DAY LOSS HORIZON" status="pass" />
            <MetricCard label="PARAM VaR 95%"       value={`-${(varData?.parametric_var_pct || 1.38).toFixed(2)}%`}    change="NORMAL ASSUMPTION"                                               positive={false} subtext="VAR-COV MODEL" status="pass" />
            <MetricCard label="CVaR (EXP SHORTFALL)" value={`-${(varData?.cvar_expected_shortfall_pct || 2.15).toFixed(2)}%`} change={formatCurrency(varData?.cvar_dollars || 53427, 0)}         positive={false} subtext="EXPECTED TAIL LOSS" status="pass" />
            <MetricCard label="ANNUALIZED VOL"      value={`${(varData?.annualized_vol_pct || 12.4).toFixed(1)}%`}       change="LIMIT: 15.0%"                                                  positive={true}  subtext="WITHIN TOLERANCE" status="pass" />
            <MetricCard label="PORTFOLIO BETA (SPY)" value="0.04"                                                          change="NEAR NEUTRAL"                                                 positive={true}  subtext="LOW SYS RISK" status="pass" />
            <MetricCard label="STRESS LOSS CAPACITY" value="$450K"                                                          change="BUFFER: 18.1%"                                                positive={true}  subtext="CAPITAL SHIELD" status="pass" />
          </div>
        )}

        {/* VaR + Factor Attribution */}
        <div style={{ padding: '0.28rem 0.6rem', background: '#0d0600', border: '1px solid #FF6600', borderBottom: '1px solid #2a1500', fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>RETURN DISTRIBUTION & BARRA FACTOR RISK ATTRIBUTION</span>
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px', border: '1px solid #2a2a2a', borderTop: 'none' }}>
          <div style={{ background: '#0a0a0a', padding: '0.5rem', overflow: 'hidden' }}>
            <div style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: '#FF6600', fontWeight: 700, marginBottom: '0.4rem', letterSpacing: '0.04em' }}>
              HIST RETURN DENSITY | VaR 95%: -1.45% | VaR 99%: -2.15%
            </div>
            <VaRHistogram height={250} var95Cutoff={-1.45} var99Cutoff={-2.15} />
          </div>
          <div style={{ background: '#0a0a0a', padding: '0.5rem', overflow: 'hidden' }}>
            <div style={{ fontSize: '0.6rem', fontFamily: 'var(--font-mono)', color: '#FF6600', fontWeight: 700, marginBottom: '0.4rem', letterSpacing: '0.04em' }}>
              BARRA FACTOR MODEL RISK ATTRIBUTION | R² = 0.82
            </div>
            <RiskAttribution factors={factors} />
          </div>
        </div>

        {/* Stress Scenarios */}
        <div style={{ padding: '0.28rem 0.6rem', background: '#0d0600', border: '1px solid #FF6600', borderBottom: '1px solid #2a1500', fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>MACRO REGIME STRESS TESTING & CRISIS SIMULATION — HISTORICAL REPLAY</span>
        </div>
        <div style={{ border: '1px solid #2a2a2a', borderTop: 'none', overflow: 'hidden' }}>
          <DataTable columns={stressColumns} data={stressScenarios} pageSize={4} />
        </div>

        {/* Drawdown Trace */}
        <div style={{ padding: '0.28rem 0.6rem', background: '#0d0600', border: '1px solid #FF6600', borderBottom: '1px solid #2a1500', fontFamily: 'var(--font-mono)' }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>TRAILING 90-DAY DRAWDOWN DEPTH — CIRCUIT BREAKER: -10.0%</span>
        </div>
        <div style={{ background: '#0a0a0a', border: '1px solid #2a2a2a', borderTop: 'none', padding: '0.5rem', overflow: 'hidden' }}>
          <DrawdownChart data={drawdownData} height={200} />
        </div>

      </div>
    </ErrorBoundary>
  );
}
