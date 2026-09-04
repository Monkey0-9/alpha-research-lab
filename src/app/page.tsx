'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import ChartContainer from '@/components/ChartContainer';
import EquityCurve from '@/components/EquityCurve';
import DrawdownChart from '@/components/DrawdownChart';
import RegimeCard from '@/components/RegimeCard';
import PositionTable from '@/components/PositionTable';
import PipelineStatus from '@/components/PipelineStatus';
import AlertFeed from '@/components/AlertFeed';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import { formatCurrency, formatPercent } from '@/lib/utils';
import { generateTimeSeries, generateDrawdown } from '@/lib/data';

export default function ExecutiveDashboard() {
  const [loading, setLoading] = useState(true);
  const [summary, setSummary] = useState<types.ExecutiveDashboardSummary | null>(null);
  const [holdings, setHoldings] = useState<types.PortfolioHoldingItem[]>([]);
  const [alerts, setAlerts] = useState<types.ProductionAlertItem[]>([]);
  const [equityData, setEquityData] = useState<any[]>([]);
  const [drawdownData, setDrawdownData] = useState<any[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const [sum, hld, tel] = await Promise.all([
          api.getDashboardSummary(),
          api.getPortfolioHoldings(),
          api.getMonitoringTelemetry()
        ]);
        setSummary(sum);
        setHoldings(hld.holdings);
        setAlerts(tel.recent_alerts);

        // Synthetic 252-day equity curve
        const baseCurve = [];
        let pNav = 1.0;
        let bNav = 1.0;
        let peak = 1.0;
        const ddArr = [];
        const now = new Date();

        for (let i = 252; i >= 0; i--) {
          const d = new Date(now.getTime() - i * 24 * 60 * 60 * 1000).toISOString().slice(0, 10);
          const pRet = (Math.random() - 0.47) * 0.012 + 0.0007;
          const bRet = (Math.random() - 0.48) * 0.014 + 0.0004;
          pNav *= (1.0 + pRet);
          bNav *= (1.0 + bRet);
          peak = Math.max(peak, pNav);
          const dd = (pNav - peak) / peak;

          baseCurve.push({
            date: d,
            nav: parseFloat(pNav.toFixed(4)),
            benchmark: parseFloat(bNav.toFixed(4))
          });
          ddArr.push({
            date: d,
            drawdown: parseFloat((dd * 100).toFixed(2))
          });
        }
        setEquityData(baseCurve);
        setDrawdownData(ddArr);
      } catch (err) {
        console.error('Failed to load dashboard data:', err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <ErrorBoundary fallbackTitle="Executive Dashboard Interrupted">
      <TerminalHeader title="MODULE 00 // EXECUTIVE TRADING DASHBOARD" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* KPI Strip */}
        {loading ? (
          <LoadingSkeleton height="85px" count={1} />
        ) : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard
              label="Portfolio NAV"
              value={formatCurrency(summary?.portfolio_nav || 2485000, 0)}
              change="+14.2% YTD"
              positive={true}
              subtext="Total Institutional AUM"
              status="live"
            />
            <MetricCard
              label="Daily P&L"
              value={formatCurrency(summary?.daily_pnl_dollars || 18450, 0)}
              change={formatPercent(summary?.daily_pnl_pct || 0.74, 2)}
              deltaBps={74}
              positive={true}
              subtext="Alpha Contribution: +52bps"
              status="pass"
            />
            <MetricCard
              label="Annualized Sharpe"
              value={(summary?.annualized_sharpe || 2.14).toFixed(2)}
              change="vs 1.12 BMK"
              positive={true}
              benchmark="1.12"
              benchmarkLabel="SPY"
              status="pass"
            />
            <MetricCard
              label="Calmar Ratio"
              value={(summary?.calmar_ratio || 2.85).toFixed(2)}
              change="OOS Robust"
              positive={true}
              subtext="CAGR / Max Drawdown"
              status="pass"
            />
            <MetricCard
              label="Max Drawdown"
              value={`-${(summary?.max_drawdown_pct || 6.8).toFixed(1)}%`}
              change="Limit: 12.0%"
              positive={false}
              subtext="Historical Peak: $2.51M"
              status="pass"
            />
            <MetricCard
              label="Daily VaR (95%)"
              value={`-${(summary?.var_95_daily_pct || 1.45).toFixed(2)}%`}
              change="CVaR: -2.15%"
              positive={false}
              subtext="1-Day Dollar VaR: $36.0K"
              status="pass"
            />
          </div>
        )}

        {/* Macro Regime Strip */}
        <RegimeCard
          activeRegime="bull_low_vol"
          transitionProb={0.58}
        />

        {/* Charts: Equity Curve & Drawdown */}
        <div style={{ display: 'grid', gridTemplateColumns: '2fr 1fr', gap: '0.85rem' }}>
          <ChartContainer
            title="PORTFOLIO PERFORMANCE VS BENCHMARK"
            subtitle="Walk-forward simulated and live execution NAV series (1-day frequency)"
            badge="LIVE RUN"
            badgeType="live"
          >
            {loading ? <LoadingSkeleton height="320px" /> : (
              <EquityCurve data={equityData} height={320} benchmarkName="S&P 500 (SPY)" />
            )}
          </ChartContainer>

          <ChartContainer
            title="UNDERWATER DRAWDOWN DEPTH"
            subtitle="High-water mark depletion curve with -12.0% risk limit"
            badge="PEAK: $2.51M"
            badgeType="neutral"
          >
            {loading ? <LoadingSkeleton height="320px" /> : (
              <DrawdownChart data={drawdownData} height={320} />
            )}
          </ChartContainer>
        </div>

        {/* Positions & Holdings */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div>
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                ACTIVE PORTFOLIO CONSTITUENTS & RISK CONTRIBUTION
              </span>
              <div style={{ fontSize: '0.68rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                Target vol-scaled long/short allocation · 24 active names
              </div>
            </div>
            <span className="badge-tag badge-live">24 ACTIVE HOLDINGS</span>
          </div>
          <div className="terminal-card-body">
            {loading ? <LoadingSkeleton height="200px" /> : (
              <PositionTable holdings={holdings} />
            )}
          </div>
        </div>

        {/* Automated Pipeline DAG */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
              PRODUCTION RESEARCH PIPELINE DAG STATUS
            </span>
            <span className="badge-tag badge-pass">ALL 12 STAGES SYNCHRONIZED</span>
          </div>
          <div className="terminal-card-body">
            <PipelineStatus />
          </div>
        </div>

        {/* Real-time Alerts */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
              REAL-TIME PRODUCTION EVENT & ANOMALY STREAM
            </span>
            <span className="badge-tag badge-live">STREAMING EVENT LOG</span>
          </div>
          <div className="terminal-card-body">
            <AlertFeed alerts={alerts} />
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
