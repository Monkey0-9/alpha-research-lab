'use client';

import { useEffect, useState } from 'react';
import { AreaChart, Area, BarChart, Bar, LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from 'recharts';
import { Database, CheckCircle2, AlertTriangle, Clock, Layers, GitBranch, RefreshCw, Filter } from 'lucide-react';
import { generateTimeSeries } from '@/lib/data';

const dataSources = [
  { name: 'Tick / Trades', icon: '⚡', status: 'live', latency: '2ms', records: '4.2B', freshness: '0s', color: '#10b981' },
  { name: 'Order Book L2', icon: '📖', status: 'live', latency: '1ms', records: '890M', freshness: '0s', color: '#3b82f6' },
  { name: 'OHLCV Daily', icon: '📊', status: 'live', latency: '15ms', records: '62M', freshness: '1d', color: '#8b5cf6' },
  { name: 'Corporate Actions', icon: '🏢', status: 'live', latency: '200ms', records: '2.1M', freshness: '1d', color: '#f59e0b' },
  { name: 'Fundamentals', icon: '📋', status: 'live', latency: '1s', records: '38M', freshness: '3mo', color: '#06b6d4' },
  { name: 'Estimates', icon: '🎯', status: 'live', latency: '500ms', records: '18M', freshness: '1d', color: '#f97316' },
  { name: 'Macro Data', icon: '🌐', status: 'live', latency: '2s', records: '5.4M', freshness: '1d', color: '#ec4899' },
  { name: 'News / NLP', icon: '📰', status: 'live', latency: '800ms', records: '240M', freshness: '1min', color: '#a78bfa' },
  { name: 'Alternative Data', icon: '🛰️', status: 'warning', latency: '5s', records: '12M', freshness: '1d', color: '#f59e0b' },
  { name: 'Options Chain', icon: '🔗', status: 'live', latency: '10ms', records: '890M', freshness: '0s', color: '#10b981' },
];

const qualityMetrics = [
  { metric: 'Null Rate', value: '0.12%', target: '<0.5%', status: 'pass' },
  { metric: 'Schema Drift', value: '0', target: '0', status: 'pass' },
  { metric: 'Staleness (p99)', value: '1.2d', target: '<2d', status: 'pass' },
  { metric: 'Duplicate Rate', value: '0.003%', target: '<0.01%', status: 'pass' },
  { metric: 'Outlier Rate', value: '0.8%', target: '<1%', status: 'pass' },
  { metric: 'Coverage', value: '99.1%', target: '>98%', status: 'pass' },
  { metric: 'Alt Data Delay', value: '5.1s', target: '<3s', status: 'fail' },
];

const pipelineSteps = [
  { name: 'Raw Ingestion', desc: 'Multi-source streaming pipeline', status: 'done' },
  { name: 'Data Quality Engine', desc: 'Null checks, outliers, schema validation', status: 'done' },
  { name: 'Point-in-Time Store', desc: 'Temporal join engine, no look-ahead', status: 'active' },
  { name: 'Versioned Datasets', desc: 'Immutable snapshots with git-like versioning', status: 'active' },
  { name: 'Data Lineage / Provenance', desc: 'Full audit trail per field per time point', status: 'pending' },
];

const CustomTooltip = ({ active, payload, label }: any) => {
  if (active && payload && payload.length) {
    return (
      <div style={{ background: 'var(--bg-card)', border: '1px solid var(--border-subtle)', borderRadius: 8, padding: '0.6rem 0.9rem' }}>
        <p style={{ fontSize: '0.7rem', color: 'var(--text-muted)', marginBottom: 4 }}>{label}</p>
        {payload.map((p: any, i: number) => (
          <p key={i} style={{ fontSize: '0.8rem', fontFamily: 'JetBrains Mono', color: p.color || '#3b82f6' }}>
            {p.name}: {p.value?.toLocaleString()}
          </p>
        ))}
      </div>
    );
  }
  return null;
};

export default function DataPage() {
  const [tickData, setTickData] = useState<any[]>([]);
  const [volumeData, setVolumeData] = useState<any[]>([]);
  const [activeSource, setActiveSource] = useState(0);

  useEffect(() => {
    fetch('/api/data/ohlcv?ticker=AAPL&start=2023-01-01&end=2023-12-31')
      .then(r => r.json())
      .then(json => {
        if (json && json.data && json.data.length > 0) {
          const transformed = json.data.map((d: any) => ({
            date: d.date,
            value: d.close,
            open: d.open,
            high: d.high,
            low: d.low,
            close: d.close,
            volume: d.volume,
          }));
          setTickData(transformed.slice(-40));
          setVolumeData(transformed.slice(-20));
        } else {
          const ts = generateTimeSeries(60, 180, 0.008);
          setTickData(ts.slice(-40));
          setVolumeData(ts.slice(-20).map(d => ({ ...d, volume: 1500000 })));
        }
      })
      .catch(() => {
        const ts = generateTimeSeries(60, 180, 0.008);
        setTickData(ts.slice(-40));
        setVolumeData(ts.slice(-20).map(d => ({ ...d, volume: 1500000 })));
      });
  }, []);

  return (
    <div className="page-container">
      <div className="page-header">
        <div className="page-header-badge"><Database size={10} /> 01 — Data Infrastructure</div>
        <h1>Data Infrastructure</h1>
        <p>Multi-source market data pipeline with point-in-time semantics, quality controls, versioning, and full data lineage.</p>
      </div>

      {/* Stats Row */}
      <div className="grid-4" style={{ marginBottom: '1.5rem' }}>
        {[
          { label: 'Total Records', value: '6.4B+', color: '#3b82f6' },
          { label: 'Data Sources', value: '10', color: '#10b981' },
          { label: 'Quality Score', value: '98.7%', color: '#8b5cf6' },
          { label: 'PIT Latency', value: '< 2ms', color: '#f59e0b' },
        ].map(m => (
          <div key={m.label} className="card" style={{ padding: '1rem' }}>
            <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)', textTransform: 'uppercase', letterSpacing: '0.07em', marginBottom: '0.4rem' }}>{m.label}</div>
            <div className="metric-value" style={{ color: m.color, fontSize: '1.6rem' }}>{m.value}</div>
          </div>
        ))}
      </div>

      <div className="grid-2" style={{ marginBottom: '1.5rem' }}>
        {/* Data Sources */}
        <div className="card">
          <div className="card-header">
            <span className="card-title">Data Sources</span>
            <button className="btn btn-ghost" style={{ fontSize: '0.72rem', padding: '0.3rem 0.6rem' }}>
              <RefreshCw size={11} /> Refresh
            </button>
          </div>
          <div style={{ display: 'grid', gap: '0.4rem' }}>
            {dataSources.map((src, i) => (
              <div
                key={src.name}
                onClick={() => setActiveSource(i)}
                style={{
                  display: 'flex', alignItems: 'center', gap: '0.75rem',
                  padding: '0.5rem 0.75rem',
                  borderRadius: 8, cursor: 'pointer',
                  background: activeSource === i ? `${src.color}12` : 'var(--bg-secondary)',
                  border: `1px solid ${activeSource === i ? `${src.color}30` : 'var(--border-subtle)'}`,
                  transition: 'all 0.15s',
                }}
              >
                <span style={{ fontSize: '1rem' }}>{src.icon}</span>
                <div style={{ flex: 1 }}>
                  <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{src.name}</div>
                  <div style={{ fontSize: '0.68rem', color: 'var(--text-muted)', fontFamily: 'JetBrains Mono' }}>
                    {src.records} records · {src.freshness} lag
                  </div>
                </div>
                <div style={{ textAlign: 'right' }}>
                  <div style={{ fontSize: '0.7rem', fontFamily: 'JetBrains Mono', color: src.color }}>{src.latency}</div>
                  <span className={`status-dot ${src.status === 'live' ? 'live' : 'warning'}`} />
                </div>
              </div>
            ))}
          </div>
        </div>

        {/* Charts + Pipeline */}
        <div style={{ display: 'flex', flexDirection: 'column', gap: '1rem' }}>
          <div className="card">
            <div className="card-header">
              <span className="card-title">Live Price Feed — {dataSources[activeSource].name}</span>
              <span className="badge badge-blue">Streaming</span>
            </div>
            <ResponsiveContainer width="100%" height={150}>
              <AreaChart data={tickData}>
                <defs>
                  <linearGradient id="feedGrad" x1="0" y1="0" x2="0" y2="1">
                    <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                    <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                  </linearGradient>
                </defs>
                <CartesianGrid strokeDasharray="3 3" stroke="rgba(255,255,255,0.04)" />
                <XAxis dataKey="date" tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} interval={9} />
                <YAxis tick={{ fontSize: 9, fill: '#475569' }} tickLine={false} axisLine={false} />
                <Tooltip content={<CustomTooltip />} />
                <Area type="monotone" dataKey="value" name="Price" stroke="#3b82f6" strokeWidth={1.5} fill="url(#feedGrad)" />
              </AreaChart>
            </ResponsiveContainer>
          </div>

          <div className="card">
            <div className="card-header">
              <span className="card-title">Ingestion Pipeline</span>
              <span className="badge badge-violet">DAG</span>
            </div>
            {pipelineSteps.map((s, i) => (
              <div key={i}>
                <div className={`pipeline-step ${s.status}`}>
                  <div style={{
                    width: 22, height: 22, borderRadius: '50%',
                    background: s.status === 'done' ? '#10b98122' : s.status === 'active' ? '#3b82f622' : 'var(--bg-secondary)',
                    border: `1px solid ${s.status === 'done' ? '#10b981' : s.status === 'active' ? '#3b82f6' : 'var(--border-subtle)'}`,
                    display: 'flex', alignItems: 'center', justifyContent: 'center',
                    fontSize: '0.6rem', fontWeight: 700, flexShrink: 0,
                    color: s.status === 'done' ? '#10b981' : s.status === 'active' ? '#3b82f6' : 'var(--text-muted)',
                  }}>
                    {s.status === 'done' ? '✓' : s.status === 'active' ? '●' : i + 1}
                  </div>
                  <div style={{ flex: 1 }}>
                    <div style={{ fontSize: '0.8rem', fontWeight: 600, color: 'var(--text-primary)' }}>{s.name}</div>
                    <div style={{ fontSize: '0.7rem', color: 'var(--text-muted)' }}>{s.desc}</div>
                  </div>
                  <span className={`badge ${s.status === 'done' ? 'badge-emerald' : s.status === 'active' ? 'badge-blue' : 'badge-muted'}`}>{s.status}</span>
                </div>
                {i < pipelineSteps.length - 1 && <div className="pipeline-connector">↓</div>}
              </div>
            ))}
          </div>
        </div>
      </div>

      {/* Data Quality */}
      <div className="card">
        <div className="card-header">
          <span className="card-title">Data Quality Engine — Quality Gate Results</span>
          <span className="badge badge-emerald"><Filter size={10} /> 6/7 Passing</span>
        </div>
        <table className="data-table">
          <thead>
            <tr>
              <th>Quality Metric</th>
              <th>Current Value</th>
              <th>Target</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {qualityMetrics.map((q) => (
              <tr key={q.metric}>
                <td style={{ color: 'var(--text-primary)', fontFamily: 'inherit' }}>{q.metric}</td>
                <td>{q.value}</td>
                <td style={{ color: 'var(--text-muted)' }}>{q.target}</td>
                <td>
                  {q.status === 'pass'
                    ? <span className="badge badge-emerald"><CheckCircle2 size={10} /> Pass</span>
                    : <span className="badge badge-rose"><AlertTriangle size={10} /> Fail</span>
                  }
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
}
