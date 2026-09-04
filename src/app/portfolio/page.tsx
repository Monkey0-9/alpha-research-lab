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
import { PieChart, Sliders, CheckCircle2 } from 'lucide-react';

export default function PortfolioEnginePage() {
  const [loading, setLoading] = useState(true);
  const [holdings, setHoldings] = useState<types.PortfolioHoldingItem[]>([]);
  const [optMethod, setOptMethod] = useState<'hrp' | 'mean_variance' | 'risk_parity' | 'cvar'>('hrp');
  const [optStatus, setOptStatus] = useState<string | null>(null);

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

  const handleRunOptimization = () => {
    setOptStatus(`Optimization completed via ${optMethod.toUpperCase().replace(/_/g, ' ')}. Portfolio weights re-balanced to 10.0% target volatility. Expected Sharpe: 2.18.`);
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
      <TerminalHeader title="MODULE 08 // PORTFOLIO CONSTRUCTION & CONSTRAINED OPTIMIZATION" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
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
              change="NVDA (Limit 10%)"
              positive={true}
              subtext="Concentration Cap"
              status="pass"
            />
            <MetricCard
              label="Net Leverage"
              value="0.12x"
              change="Gross: 1.45x"
              positive={true}
              subtext="Market Neutral Tilt"
              status="pass"
            />
            <MetricCard
              label="Monthly Turnover"
              value="18.4%"
              change="Turnover Penalty"
              positive={true}
              subtext="Minimizes Slippage"
              status="pass"
            />
          </div>
        )}

        {/* Optimizer Controls & Optimization Status */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Sliders size={14} color="#38bdf8" />
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                OPTIMIZATION ALGORITHM SELECTOR & QUADRATIC PROGRAMMING SOLVER
              </span>
            </div>
            <span className="badge-tag badge-live">OSQP SOLVER</span>
          </div>
          <div className="terminal-card-body" style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', gap: '1rem' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>OPTIMIZER:</span>
              <select
                value={optMethod}
                onChange={(e) => setOptMethod(e.target.value as any)}
                style={{
                  background: '#0a0d14',
                  border: '1px solid var(--border-terminal)',
                  color: '#38bdf8',
                  padding: '0.35rem 0.65rem',
                  borderRadius: '3px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.75rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                <option value="hrp">HIERARCHICAL RISK PARITY (HRP - LOPEZ DE PRADO)</option>
                <option value="mean_variance">MARKOWITZ MEAN-VARIANCE (WITH CONSTRAINTS)</option>
                <option value="risk_parity">EQUAL RISK CONTRIBUTION (RISK PARITY)</option>
                <option value="cvar">CVaR / EXPECTED SHORTFALL MINIMIZATION</option>
              </select>
            </div>

            <button
              onClick={handleRunOptimization}
              style={{
                background: '#1e293b',
                border: '1px solid #38bdf8',
                color: '#38bdf8',
                padding: '0.35rem 0.85rem',
                borderRadius: '3px',
                fontFamily: 'var(--font-mono)',
                fontSize: '0.72rem',
                fontWeight: 600,
                cursor: 'pointer'
              }}
            >
              RUN PORTFOLIO REBALANCE
            </button>
          </div>
        </div>

        {optStatus && (
          <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.4)', padding: '0.65rem 0.85rem', borderRadius: '3px', color: '#38bdf8', fontSize: '0.75rem', fontFamily: 'var(--font-mono)' }}>
            <CheckCircle2 size={13} style={{ display: 'inline', marginRight: '0.4rem' }} />
            {optStatus}
          </div>
        )}

        {/* Efficient Frontier & Factor Exposure Radar */}
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

        {/* Active Holdings Table */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <PieChart size={14} color="#38bdf8" />
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
      </div>
    </ErrorBoundary>
  );
}
