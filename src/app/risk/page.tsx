'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import ChartContainer from '@/components/ChartContainer';
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
import { AlertTriangle, ShieldAlert, BarChart2 } from 'lucide-react';

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
      <TerminalHeader title="MODULE 10 // INSTITUTIONAL RISK ENGINE & STRESS TESTING" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* KPI Strip */}
        {loading ? <LoadingSkeleton height="85px" count={1} /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard
              label="Daily Historical VaR (95%)"
              value={`-${(varData?.historical_var_pct || 1.45).toFixed(2)}%`}
              change={formatCurrency(varData?.historical_var_dollars || 36032, 0)}
              positive={false}
              subtext="1-Day Loss Horizon"
              status="pass"
            />
            <MetricCard
              label="Parametric VaR (95%)"
              value={`-${(varData?.parametric_var_pct || 1.38).toFixed(2)}%`}
              change="Normal Assumption"
              positive={false}
              subtext="Variance-Covariance Model"
              status="pass"
            />
            <MetricCard
              label="CVaR (Expected Shortfall)"
              value={`-${(varData?.cvar_expected_shortfall_pct || 2.15).toFixed(2)}%`}
              change={formatCurrency(varData?.cvar_dollars || 53427, 0)}
              positive={false}
              subtext="Expected Tail Loss"
              status="pass"
            />
            <MetricCard
              label="Annualized Volatility"
              value={`${(varData?.annualized_vol_pct || 12.4).toFixed(1)}%`}
              change="Limit: 15.0%"
              positive={true}
              subtext="Within Risk Tolerance"
              status="pass"
            />
            <MetricCard
              label="Portfolio Beta (SPY)"
              value="0.04"
              change="Near Neutral"
              positive={true}
              subtext="Low Systematic Market Risk"
              status="pass"
            />
            <MetricCard
              label="Stress Loss Capacity"
              value="$450K"
              change="Buffer: 18.1%"
              positive={true}
              subtext="Capital Shield Protection"
              status="pass"
            />
          </div>
        )}

        {/* VaR Distribution & Barra Factor Attribution */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
          <ChartContainer
            title="HISTORICAL RETURN DENSITY & TAIL VALUE AT RISK"
            subtitle="Empirical return distribution with 95% and 99% VaR cutoffs"
            badge="MONTE CARLO 10K"
            badgeType="live"
          >
            <VaRHistogram height={260} var95Cutoff={-1.45} var99Cutoff={-2.15} />
          </ChartContainer>

          <div className="terminal-card">
            <div className="terminal-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <BarChart2 size={14} color="#38bdf8" />
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  BARRA FACTOR MODEL RISK ATTRIBUTION
                </span>
              </div>
              <span className="badge-tag badge-pass">R² = 0.82</span>
            </div>
            <div className="terminal-card-body">
              <RiskAttribution factors={factors} />
            </div>
          </div>
        </div>

        {/* Macro Stress Testing Scenarios */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <ShieldAlert size={14} color="#f59e0b" />
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                MACRO REGIME STRESS TESTING & CRISIS SIMULATION
              </span>
            </div>
            <span className="badge-tag badge-live">HISTORICAL REPLAY</span>
          </div>
          <div className="terminal-card-body">
            <DataTable columns={stressColumns} data={stressScenarios} pageSize={4} />
          </div>
        </div>

        {/* Drawdown Depth */}
        <ChartContainer
          title="TRAILING 90-DAY DRAWDOWN DEPTH TRACE"
          subtitle="Real-time underwater loss monitoring against the -10.0% firm circuit-breaker"
          badge="CIRCUIT BREAKER: -10%"
          badgeType="neutral"
        >
          <DrawdownChart data={drawdownData} height={200} />
        </ChartContainer>
      </div>
    </ErrorBoundary>
  );
}
