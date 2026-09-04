'use client';

import { useEffect, useState } from 'react';
import {
  BarChart, Bar, AreaChart, Area, LineChart, Line,
  XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid, ReferenceLine
} from 'recharts';
import { Zap, TrendingUp, TrendingDown, Activity } from 'lucide-react';
import { generateTimeSeries } from '@/lib/data';

const slippageData = Array.from({ length: 30 }, (_, i) => ({
  day: `D-${30 - i}`,
  slippage: parseFloat((Math.random() * 4 + 0.5).toFixed(2)),
  target: 2.5,
}));

const fillQuality = [
  { venue: 'NYSE', fillRate: 98.4, avgSlippage: 1.2, volume: '42%', latency: '1.8ms', color: '#10b981' },
  { venue: 'NASDAQ', fillRate: 97.9, avgSlippage: 1.5, volume: '31%', latency: '1.4ms', color: '#3b82f6' },
  { venue: 'BATS', fillRate: 96.2, avgSlippage: 2.1, volume: '18%', latency: '2.3ms', color: '#8b5cf6' },
  { venue: 'IEX', fillRate: 99.1, avgSlippage: 0.8, volume: '9%', latency: '0.9ms', color: '#f59e0b' },
];

const impactModel = Array.from({ length: 20 }, (_, i) => {
  const pctAdv = (i + 1) * 0.5;
  return {
    pctAdv,
    predicted: parseFloat((0.3 * Math.sqrt(pctAdv) + 0.1 * pctAdv).toFixed(3)),
    realized: parseFloat((0.3 * Math.sqrt(pctAdv) + 0.1 * pctAdv + (Math.random() - 0.5) * 0.5).toFixed(3)),
  };
});

const orderTypes = [
  { type: 'TWAP', desc: 'Time-weighted average price execution', avgSlippage: '1.8bps', bestFor: 'Low-urgency, large orders' },
  { type: 'VWAP', desc: 'Volume-weighted average price execution', avgSlippage: '1.4bps', bestFor: 'Medium urgency, follows volume' },
  { type: 'IS', desc: 'Implementation shortfall minimization', avgSlippage: '2.2bps', bestFor: 'High alpha-decay signals' },
  { type: 'POV', desc: 'Percent-of-volume participation', avgSlippage: '1.6bps', bestFor: 'Liquid, high-cap names' },
  { type: 'Arrival', desc: 'Minimize vs. arrival price', avgSlippage: '1.9bps', bestFor: 'Short-lived alpha signals' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#f43f5e' }}>
            {p.name}: {p.value}{typeof p.value === 'number' && p.name.includes('bps') ? '' : ''}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function ExecutionPage() {
  const [activeVenue, setActiveVenue] = useState(0);

  const breached = slippageData.filter(d => d.slippage > 2.5).length;

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><Zap size={10} /> 09 — Execution Research</div>
        <h1>Execution Research</h1>
        <p>Analyse market impact, slippage costs, fill quality, and order routing to minimize transaction costs and preserve alpha through execution.</p>
      </div>

      {/* Summary Stats */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Avg Slippage', value: '1.9bps', change: '+0.4bps vs limit', positive: false, color: '#f43f5e' },
          { label: 'Fill Rate', value: '97.9%', change: '+0.3% MoM', positive: true, color: '#10b981' },
          { label: 'Market Impact', value: '1.2bps', change: '-0.1bps', positive: true, color: '#3b82f6' },
          { label: 'Venue Score', value: '91/100', change: 'IEX top', positive: true, color: '#8b5cf6' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.5rem' }}>{m.value}</div>
            <div className={`metric-change ${m.positive ? 'positive' : 'negative'}`} style={{ marginTop: '0.25rem' }}>
              {m.positive ? <TrendingUp size={10} style={{ display: 'inline', marginRight: 3 }} /> : <TrendingDown size={10} style={{ display: 'inline', marginRight: 3 }} />}
              {m.change}
            </div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Slippage time series */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Daily Slippage vs Limit (bps)</span>
            <span className={`badge ${breached > 3 ? 'badge-rose' : 'badge-amber'}`}>
              {breached} Breaches (30d)
            </span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <BarChart data={slippageData}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="day" tick={{ fontSize: 8, fill: '#475569' }} tickLine={false} axisLine={false} interval={4} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={v => `${v}bps`} />
              <Tooltip content={<CustomTooltip />} />
              <ReferenceLine y={2.5} stroke="#f43f5e" strokeDasharray="4 2" label={{ value: 'Limit 2.5bps', fill: '#f43f5e', fontSize: 9 }} />
              <Bar dataKey="slippage" name="Slippage (bps)" radius={[3, 3, 0, 0]} fill="#f97316" />
            </BarChart>
          </ResponsiveContainer>
        </div>

        {/* Venue Performance */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Venue Performance</span>
            <span className="badge badge-blue"><Activity size={10} /> Smart Router</span>
          </div>
          <div style={{ display: 'grid', gap: '0.5rem' }}>
            {fillQuality.map((v, i) => (
              <div
                key={v.venue}
                onClick={() => setActiveVenue(i)}
                style={{
                  padding: '0.6rem 0.85rem', borderRadius: 8, cursor: 'pointer',
                  background: activeVenue === i ? `${v.color}12` : 'var(--bg-secondary)',
                  border: `1px solid ${activeVenue === i ? `${v.color}30` : 'var(--border-subtle)'}`,
                  transition: 'all 0.15s',
                }}
              >
                <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.4rem' }}>
                  <span style={{ fontSize: '0.85rem', fontWeight: 700, color: v.color }}>{v.venue}</span>
                  <div style={{ display: 'flex', gap: '0.75rem' }}>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>Vol: {v.volume}</span>
                    <span style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: 'var(--text-muted)' }}>{v.latency}</span>
                  </div>
                </div>
                <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)', marginBottom: '0.2rem' }}>Fill Rate</div>
                    <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
                      <div className="progress-bar" style={{ flex: 1 }}>
                        <div className="progress-fill" style={{ width: `${v.fillRate}%`, background: v.color }} />
                      </div>
                      <span style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: v.color }}>{v.fillRate}%</span>
                    </div>
                  </div>
                  <div style={{ textAlign: 'right' }}>
                    <div style={{ fontSize: '0.65rem', color: 'var(--text-muted)' }}>Avg Slip</div>
                    <div style={{ fontSize: '0.85rem', fontWeight: 700, fontFamily: 'JetBrains Mono', color: v.avgSlippage < 2 ? '#10b981' : '#f59e0b' }}>{v.avgSlippage}bps</div>
                  </div>
                </div>
              </div>
            ))}
          </div>
        </div>
      </div>

      <div className="grid-2">
        {/* Market Impact Model */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Market Impact Model (√ADV)</span>
            <span className="badge badge-violet">Almgren-Chriss</span>
          </div>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={impactModel}>
              <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
              <XAxis dataKey="pctAdv" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} label={{ value: '% ADV', position: 'insideBottom', offset: -2, fontSize: 9, fill: '#475569' }} />
              <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} tickFormatter={v => `${v}bps`} />
              <Tooltip content={<CustomTooltip />} />
              <Line type="monotone" dataKey="predicted" name="Predicted (bps)" stroke="#3b82f6" strokeWidth={2} dot={false} />
              <Line type="monotone" dataKey="realized" name="Realized (bps)" stroke="#f97316" strokeWidth={1.5} dot={false} strokeDasharray="4 2" />
            </LineChart>
          </ResponsiveContainer>
        </div>

        {/* Order Type Selection */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Execution Algorithm Selector</span>
            <span className="badge badge-amber"><Zap size={10} /> 5 Algos</span>
          </div>
          <div style={{ display: 'grid', gap: '0.4rem' }}>
            {orderTypes.map(o => (
              <div key={o.type} className="pipeline-step" style={{ padding: '0.6rem 0.85rem' }}>
                <div style={{ minWidth: 55 }}>
                  <span style={{ fontSize: '0.8rem', fontWeight: 700, color: '#f97316', fontFamily: 'JetBrains Mono' }}>{o.type}</span>
                </div>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.75rem', color: 'var(--text-primary)' }}>{o.desc}</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', marginTop: '0.1rem' }}>{o.bestFor}</div>
                </div>
                <span style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: '#10b981', whiteSpace: 'nowrap' }}>{o.avgSlippage}</span>
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  );
}
