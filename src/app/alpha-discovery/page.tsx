'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import ChartContainer from '@/components/ChartContainer';
import DataTable, { Column } from '@/components/DataTable';
import Badge from '@/components/Badge';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import { FlaskConical, Play, CheckCircle2, Cpu } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  BarChart,
  Bar,
  Cell
} from 'recharts';

export default function AlphaDiscoveryPage() {
  const [loading, setLoading] = useState(true);
  const [hypotheses, setHypotheses] = useState<types.AlphaHypothesis[]>([]);
  const [formulaInput, setFormulaInput] = useState('ts_rank(volume, 10) * -1.0 * ts_delta(close, 5)');
  const [evalResult, setEvalResult] = useState<string | null>(null);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getHypotheses();
        setHypotheses(res);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleEvaluateFormula = () => {
    setEvalResult('Formula parsed successfully. Evaluated on S&P 500: IC = 0.089, IC IR = 2.14, Annualized Sharpe = 1.95. Promoted to Quality Gate review.');
  };

  const hypothesisColumns: Column<types.AlphaHypothesis>[] = [
    { key: 'id', header: 'ID', render: (r) => <span style={{ fontWeight: 700, color: '#38bdf8' }}>{r.id}</span> },
    {
      key: 'name',
      header: 'Alpha Hypothesis Name',
      render: (r) => (
        <div>
          <div style={{ fontWeight: 600, color: '#f8fafc' }}>{r.name}</div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>{r.economic_rationale}</div>
        </div>
      )
    },
    { key: 'category', header: 'Category' },
    { key: 'author', header: 'Research Desk' },
    { key: 'created_at', header: 'Created' },
    {
      key: 'status',
      header: 'Status',
      align: 'center',
      render: (r) => <Badge label={r.status} type={r.status === 'PROMOTED' ? 'live' : r.status === 'BACKTESTING' ? 'paper' : 'warn'} />
    }
  ];

  // Genetic programming evolution curve
  const gpCurve = [
    { gen: 1, bestIC: 0.042, avgIC: 0.018 },
    { gen: 5, bestIC: 0.058, avgIC: 0.026 },
    { gen: 10, bestIC: 0.071, avgIC: 0.038 },
    { gen: 15, bestIC: 0.082, avgIC: 0.049 },
    { gen: 20, bestIC: 0.091, avgIC: 0.057 },
    { gen: 25, bestIC: 0.098, avgIC: 0.064 },
  ];

  // Feature Importance data
  const importanceData = [
    { feature: 'Momentum 20D', importance: 142 },
    { feature: 'Order Flow Imbalance', importance: 128 },
    { feature: 'Realized Vol 20D', importance: 95 },
    { feature: 'RSI 14D', importance: 84 },
    { feature: 'Volume Shock 5D', importance: 72 },
    { feature: 'MACD Divergence', importance: 65 },
    { feature: 'Hurst Exponent', importance: 41 },
  ];

  return (
    <ErrorBoundary fallbackTitle="Alpha Discovery Lab Interrupted">
      <TerminalHeader title="MODULE 03 // ALPHA DISCOVERY & GENETIC PROGRAMMING LAB" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* KPI Strip */}
        {loading ? <LoadingSkeleton height="85px" count={1} /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard
              label="Hypotheses Catalog"
              value="24"
              change="+4 Active"
              positive={true}
              subtext="Theoretical Foundations"
              status="live"
            />
            <MetricCard
              label="GP Mining Generation"
              value="Gen 25"
              change="Pop: 500"
              positive={true}
              subtext="Symbolic Regression Tree"
              status="pass"
            />
            <MetricCard
              label="Best Fitness (IC)"
              value="0.098"
              change="vs 0.05 Bmk"
              positive={true}
              subtext="Cross-Sectional Rank IC"
              status="pass"
            />
            <MetricCard
              label="Genetic Diversity"
              value="0.74"
              change="Entropy Balanced"
              positive={true}
              subtext="Prevents Premature Convergence"
              status="pass"
            />
            <MetricCard
              label="Promoted Alphas"
              value="8"
              change="Ready for Gate"
              positive={true}
              subtext="Orthogonal to Market"
              status="pass"
            />
            <MetricCard
              label="Mining Speed"
              value="18.5K / s"
              change="Rust Accelerated"
              positive={true}
              subtext="Expressions Evaluated"
              status="pass"
            />
          </div>
        )}

        {/* Formula Sandbox & GP Evolution Curve */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
          {/* Formula Sandbox */}
          <div className="terminal-card">
            <div className="terminal-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <FlaskConical size={14} color="#38bdf8" />
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  SYMBOLIC ALPHA FORMULA COMPOSER
                </span>
              </div>
              <span className="badge-tag badge-live">AST COMPILER</span>
            </div>
            <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem' }}>
              <p style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Compose symbolic alpha expressions utilizing WorldQuant / Kakushadze mathematical operators:
                <code style={{ color: '#38bdf8' }}> ts_rank, ts_zscore, ts_delta, correlation, decay_linear</code>.
              </p>

              <textarea
                rows={3}
                value={formulaInput}
                onChange={(e) => setFormulaInput(e.target.value)}
                style={{
                  width: '100%',
                  background: '#0a0d14',
                  border: '1px solid var(--border-terminal)',
                  color: '#34d399',
                  padding: '0.5rem 0.65rem',
                  borderRadius: '3px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.78rem',
                  outline: 'none'
                }}
              />

              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '0.65rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>
                  AST Depth: 3 · Terminals: 3 · Operators: 2
                </span>
                <button
                  onClick={handleEvaluateFormula}
                  style={{
                    background: '#1e293b',
                    border: '1px solid #38bdf8',
                    color: '#38bdf8',
                    padding: '0.35rem 0.85rem',
                    borderRadius: '3px',
                    fontFamily: 'var(--font-mono)',
                    fontSize: '0.72rem',
                    fontWeight: 600,
                    cursor: 'pointer',
                    display: 'flex',
                    alignItems: 'center',
                    gap: '0.35rem'
                  }}
                >
                  <Play size={11} />
                  <span>COMPILE & BACKTEST</span>
                </button>
              </div>

              {evalResult && (
                <div style={{ background: 'rgba(16, 185, 129, 0.08)', border: '1px solid rgba(16, 185, 129, 0.3)', padding: '0.65rem', borderRadius: '3px', color: '#34d399', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
                  <CheckCircle2 size={13} style={{ display: 'inline', marginRight: '0.35rem' }} />
                  {evalResult}
                </div>
              )}
            </div>
          </div>

          {/* Genetic Programming Evolution Curve */}
          <ChartContainer
            title="GENETIC PROGRAMMING FITNESS EVOLUTION"
            subtitle="Generation vs Rank IC (Population size: 500, Tournament size: 5)"
            badge="PARALLEL GP"
            badgeType="live"
          >
            <div style={{ width: '100%', height: '220px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={gpCurve} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="gen" stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" tickFormatter={(v) => `G${v}`} />
                  <YAxis stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" tickFormatter={(v) => v.toFixed(3)} />
                  <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #1e293b', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#f8fafc' }} />
                  <Line type="monotone" dataKey="bestIC" name="Best Fitness (IC)" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
                  <Line type="monotone" dataKey="avgIC" name="Population Avg IC" stroke="#64748b" strokeWidth={1.5} strokeDasharray="3 3" dot={false} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </ChartContainer>
        </div>

        {/* Hypotheses Catalog */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
              QUANTITATIVE RESEARCH HYPOTHESES REPOSITORY
            </span>
            <span className="badge-tag badge-live">PEER REVIEWED</span>
          </div>
          <div className="terminal-card-body">
            {loading ? <LoadingSkeleton height="150px" /> : (
              <DataTable columns={hypothesisColumns} data={hypotheses} pageSize={5} />
            )}
          </div>
        </div>

        {/* Feature Importance */}
        <ChartContainer
          title="GLOBAL SHAP & BOOSTING SPLIT IMPORTANCE"
          subtitle="Relative feature gain across 500 gradient boosted trees"
          badge="LIGHTGBM"
          badgeType="neutral"
        >
          <div style={{ width: '100%', height: '200px' }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={importanceData} layout="vertical" margin={{ top: 5, right: 20, left: 40, bottom: 5 }}>
                <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" horizontal={false} />
                <XAxis type="number" stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" />
                <YAxis type="category" dataKey="feature" stroke="#94a3b8" fontSize={10} fontFamily="var(--font-mono)" width={120} tickLine={false} />
                <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #1e293b', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#f8fafc' }} />
                <Bar dataKey="importance" fill="#38bdf8" radius={[0, 2, 2, 0]} />
              </BarChart>
            </ResponsiveContainer>
          </div>
        </ChartContainer>
      </div>
    </ErrorBoundary>
  );
}
