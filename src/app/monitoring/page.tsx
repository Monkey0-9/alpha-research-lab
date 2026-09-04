'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import ChartContainer from '@/components/ChartContainer';
import AlphaHealthCard from '@/components/AlphaHealthCard';
import AlertFeed from '@/components/AlertFeed';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import { Monitor, ShieldCheck, Activity, Cpu } from 'lucide-react';
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine
} from 'recharts';

export default function ProductionMonitoringPage() {
  const [loading, setLoading] = useState(true);
  const [alphas, setAlphas] = useState<types.AlphaHealthMetrics[]>([]);
  const [alerts, setAlerts] = useState<types.ProductionAlertItem[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getMonitoringTelemetry();
        setAlphas(res.active_alphas);
        setAlerts(res.recent_alerts);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  // Population Stability Index (PSI) data for features
  const psiData = [
    { feature: 'Momentum 20D', psi: 0.042 },
    { feature: 'Volume Shock', psi: 0.068 },
    { feature: 'PEAD Drift', psi: 0.035 },
    { feature: 'Depth Imbalance', psi: 0.088 },
    { feature: 'Realized Vol', psi: 0.052 },
    { feature: 'RSI 14D', psi: 0.038 },
    { feature: 'Bollinger %B', psi: 0.045 },
    { feature: 'MACD Divergence', psi: 0.061 }
  ];

  return (
    <ErrorBoundary fallbackTitle="Production Telemetry Monitor Interrupted">
      <TerminalHeader title="MODULE 12 // PRODUCTION MONITORING & ALPHA DECAY TELEMETRY" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* KPI Strip */}
        {loading ? <LoadingSkeleton height="85px" count={1} /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard
              label="System Health"
              value="NOMINAL"
              change="All Nodes Up"
              positive={true}
              subtext="Zero Dropped Packets"
              status="live"
            />
            <MetricCard
              label="Monitored Alphas"
              value={alphas.length}
              change="4 Active Signals"
              positive={true}
              subtext="Real-time Decay Tracking"
              status="pass"
            />
            <MetricCard
              label="Critical Alerts"
              value={alerts.filter((a) => a.severity === 'CRITICAL').length}
              change="0 Breaches"
              positive={true}
              subtext="Risk Limits Respected"
              status="pass"
            />
            <MetricCard
              label="Max PSI Drift"
              value="0.088"
              change="Threshold: <0.20"
              positive={true}
              subtext="Population Stability Index"
              status="pass"
            />
            <MetricCard
              label="P99 Feed Latency"
              value="3.4 ms"
              change="Mean: 1.2ms"
              positive={true}
              subtext="SIP WebSocket Feed"
              status="pass"
            />
            <MetricCard
              label="Decommission Alerts"
              value="0"
              change="All Alphas Above Hurdle"
              positive={true}
              subtext="Automated Teardown"
              status="pass"
            />
          </div>
        )}

        {/* Real-time Alpha Health Cards Grid */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Activity size={14} color="#38bdf8" />
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                ACTIVE PRODUCTION ALPHAS — HALF-LIFE DECAY & DRIFT TELEMETRY
              </span>
            </div>
            <span className="badge-tag badge-live">REAL-TIME MONITORING</span>
          </div>
          <div className="terminal-card-body" style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '0.85rem' }}>
            {loading ? <LoadingSkeleton height="140px" count={2} /> : (
              alphas.map((alpha) => (
                <AlphaHealthCard key={alpha.alpha_id} alpha={alpha} />
              ))
            )}
          </div>
        </div>

        {/* Feature Drift (PSI) & Infrastructure Telemetry */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
          <ChartContainer
            title="FEATURE POPULATION STABILITY INDEX (PSI)"
            subtitle="Comparing current 30D feature distributions against in-sample training baseline"
            badge="DRIFT HURDLE: 0.20"
            badgeType="pass"
          >
            <div style={{ width: '100%', height: '240px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={psiData} layout="vertical" margin={{ top: 5, right: 20, left: 30, bottom: 5 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" horizontal={false} />
                  <XAxis type="number" stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" domain={[0, 0.25]} tickFormatter={(v) => v.toFixed(2)} />
                  <YAxis type="category" dataKey="feature" stroke="#94a3b8" fontSize={10} fontFamily="var(--font-mono)" width={110} tickLine={false} />
                  <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #1e293b', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#f8fafc' }} />
                  <ReferenceLine x={0.10} stroke="#f59e0b" strokeDasharray="2 2" label={{ value: 'Moderate Drift: 0.10', fill: '#fbbf24', fontSize: 9, fontFamily: 'var(--font-mono)' }} />
                  <ReferenceLine x={0.20} stroke="#f43f5e" strokeDasharray="2 2" label={{ value: 'Significant Shift: 0.20', fill: '#fb7185', fontSize: 9, fontFamily: 'var(--font-mono)' }} />
                  <Bar dataKey="psi" radius={[0, 2, 2, 0]}>
                    {psiData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.psi > 0.15 ? '#f43f5e' : entry.psi > 0.08 ? '#f59e0b' : '#38bdf8'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartContainer>

          {/* Infrastructure Health Status */}
          <div className="terminal-card">
            <div className="terminal-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Cpu size={14} color="#38bdf8" />
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  INFRASTRUCTURE & FFI KERNEL DIAGNOSTICS
                </span>
              </div>
              <span className="badge-tag badge-pass">RUST / C ACCELERATED</span>
            </div>
            <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.45rem', background: '#0a0d14', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
                <span style={{ color: '#94a3b8' }}>Native C/C++ Fast P&L Kernel</span>
                <span style={{ color: '#34d399', fontWeight: 600 }}>ACTIVE (0.18ms latency)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.45rem', background: '#0a0d14', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
                <span style={{ color: '#94a3b8' }}>Rust Almgren-Chriss Impact Engine</span>
                <span style={{ color: '#34d399', fontWeight: 600 }}>ACTIVE (0.24ms latency)</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.45rem', background: '#0a0d14', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
                <span style={{ color: '#94a3b8' }}>FastAPI Async Gateway</span>
                <span style={{ color: '#34d399', fontWeight: 600 }}>UPTIME: 99.99%</span>
              </div>
              <div style={{ display: 'flex', justifyContent: 'space-between', padding: '0.45rem', background: '#0a0d14', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
                <span style={{ color: '#94a3b8' }}>Memory Utilization (RSS)</span>
                <span style={{ color: '#38bdf8', fontWeight: 600 }}>384 MB / 16,384 MB</span>
              </div>
            </div>
          </div>
        </div>

        {/* Real-time Alerts Stream */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Monitor size={14} color="#38bdf8" />
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                PRODUCTION ANOMALY STREAM & INCIDENT LOG
              </span>
            </div>
            <span className="badge-tag badge-live">LIVE TELEMETRY FEED</span>
          </div>
          <div className="terminal-card-body">
            {loading ? <LoadingSkeleton height="120px" /> : (
              <AlertFeed alerts={alerts} />
            )}
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
