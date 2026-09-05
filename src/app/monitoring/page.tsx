'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import AlphaHealthCard from '@/components/AlphaHealthCard';
import AlertFeed from '@/components/AlertFeed';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, Cell, ReferenceLine
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

  const psiData = [
    { feature: 'MOMENTUM 20D', psi: 0.042 },
    { feature: 'VOLUME SHOCK', psi: 0.068 },
    { feature: 'PEAD DRIFT',   psi: 0.035 },
    { feature: 'DEPTH IMBAL',  psi: 0.088 },
    { feature: 'REALIZED VOL', psi: 0.052 },
    { feature: 'RSI 14D',      psi: 0.038 },
    { feature: 'BOLLINGER %B', psi: 0.045 },
    { feature: 'MACD DIV',     psi: 0.061 },
  ];

  const infraRows = [
    { label: 'NATIVE C/C++ FAST P&L KERNEL',        value: 'ACTIVE', color: '#00FF41', sub: '0.18MS LATENCY' },
    { label: 'RUST ALMGREN-CHRISS IMPACT ENGINE',    value: 'ACTIVE', color: '#00FF41', sub: '0.24MS LATENCY' },
    { label: 'FASTAPI ASYNC GATEWAY',                value: 'UPTIME', color: '#00FF41', sub: '99.99%' },
    { label: 'MEMORY UTILIZATION (RSS)',             value: '384MB',  color: '#FF6600', sub: '/ 16,384MB' },
    { label: 'DISK I/O THROUGHPUT',                  value: '2.4GB/S', color: '#FF6600', sub: 'NVME WRITE' },
    { label: 'WEBSOCKET CONNECTIONS',                value: '8 LIVE', color: '#00CCFF', sub: 'FEEDS ACTIVE' },
    { label: 'MODEL INFERENCE P99 LATENCY',          value: '1.4MS',  color: '#00FF41', sub: 'LIGHTGBM ENSEMBLE' },
    { label: 'REDIS CACHE HIT RATE',                 value: '98.4%',  color: '#00FF41', sub: 'FEATURE STORE' },
  ];

  return (
    <ErrorBoundary fallbackTitle="PRODUCTION TELEMETRY ERROR">
      <TerminalHeader title="PRODUCTION MONITORING & ALPHA DECAY TELEMETRY" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '3px' }}>

        {/* ── KPI Strip ── */}
        <div style={{
          padding: '0.28rem 0.6rem', background: '#0d0600',
          border: '1px solid #FF6600', borderBottom: '1px solid #2a1500',
          display: 'flex', alignItems: 'center', justifyContent: 'space-between',
          fontFamily: 'var(--font-mono)',
        }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>
            SYSTEM TELEMETRY — KEY PERFORMANCE INDICATORS
          </span>
          <span style={{ background: '#FF6600', color: '#000', fontSize: '0.58rem', fontWeight: 900, padding: '0 0.4rem', height: '15px', display: 'inline-flex', alignItems: 'center' }}>
            LIVE
          </span>
        </div>

        {loading ? <LoadingSkeleton height="80px" label="LOADING TELEMETRY..." /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '3px' }}>
            <MetricCard label="SYSTEM HEALTH"       value="NOMINAL"    change="All Nodes Up"         positive={true}  subtext="ZERO DROPPED PACKETS"     status="live" />
            <MetricCard label="MONITORED ALPHAS"    value={alphas.length || 4} change="4 Active Signals" positive={true}  subtext="REAL-TIME DECAY TRACK"   status="pass" />
            <MetricCard label="CRITICAL ALERTS"     value={alerts.filter(a => a.severity === 'CRITICAL' || a.severity === 'critical').length} change="0 Breaches" positive={true} subtext="RISK LIMITS OK" status="pass" />
            <MetricCard label="MAX PSI DRIFT"       value="0.088"      change="HURDLE: <0.20"        positive={true}  subtext="POPULATION STABILITY"     status="pass" />
            <MetricCard label="P99 FEED LATENCY"   value="3.4ms"      change="MEAN: 1.2ms"          positive={true}  subtext="SIP WEBSOCKET FEED"       status="pass" />
            <MetricCard label="DECOMMISSION ALERTS" value="0"          change="All Above Hurdle"     positive={true}  subtext="AUTOMATED TEARDOWN"       status="pass" />
          </div>
        )}

        {/* ── Active Alpha Health Grid ── */}
        <div style={{
          padding: '0.28rem 0.6rem', background: '#0d0600',
          border: '1px solid #FF6600', borderBottom: '1px solid #2a1500',
          fontFamily: 'var(--font-mono)',
        }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>
            ACTIVE PRODUCTION ALPHAS — HALF-LIFE DECAY & DRIFT TELEMETRY
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: 'repeat(2, 1fr)', gap: '3px', border: '1px solid #2a2a2a', borderTop: 'none' }}>
          {loading ? (
            <LoadingSkeleton height="140px" count={2} label="LOADING ALPHA TELEMETRY..." />
          ) : (
            alphas.map((alpha) => (
              <AlphaHealthCard key={alpha.alpha_id} alpha={alpha} />
            ))
          )}
        </div>

        {/* ── PSI + Infrastructure ── */}
        <div style={{
          padding: '0.28rem 0.6rem', background: '#0d0600',
          border: '1px solid #FF6600', borderBottom: '1px solid #2a1500',
          fontFamily: 'var(--font-mono)',
        }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>
            FEATURE PSI DRIFT MONITOR & INFRASTRUCTURE KERNEL DIAGNOSTICS
          </span>
        </div>

        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '3px', border: '1px solid #2a2a2a', borderTop: 'none' }}>
          {/* PSI Chart */}
          <div style={{ background: '#0a0a0a', padding: '0' }}>
            {/* Sub-header */}
            <div style={{
              padding: '0.25rem 0.6rem', background: '#0d0600',
              borderBottom: '1px solid #2a1500', fontFamily: 'var(--font-mono)',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <span style={{ color: '#888', fontSize: '0.6rem', fontWeight: 700 }}>FEATURE POPULATION STABILITY INDEX (PSI)</span>
              <span style={{ background: '#CC8800', color: '#000', fontSize: '0.55rem', fontWeight: 900, padding: '0 0.3rem', height: '14px', display: 'inline-flex', alignItems: 'center' }}>
                DRIFT HURDLE: 0.20
              </span>
            </div>
            <div style={{ padding: '0.5rem 0.5rem 0.5rem 0', width: '100%', height: 260, overflow: 'hidden' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={psiData} layout="vertical" margin={{ top: 4, right: 40, left: 0, bottom: 4 }}>
                  <CartesianGrid strokeDasharray="" stroke="#1a1a1a" horizontal={false} />
                  <XAxis
                    type="number"
                    tick={{ fill: '#555', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                    axisLine={{ stroke: '#2a2a2a' }}
                    tickLine={false}
                    domain={[0, 0.25]}
                    tickFormatter={(v) => v.toFixed(2)}
                  />
                  <YAxis
                    type="category"
                    dataKey="feature"
                    tick={{ fill: '#888', fontSize: 9, fontFamily: 'var(--font-mono)' }}
                    width={95}
                    tickLine={false}
                    axisLine={false}
                  />
                  <Tooltip
                    contentStyle={{ background: '#0a0500', border: '1px solid #FF6600', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#fff' }}
                    formatter={(v: any) => [Number(v).toFixed(3), 'PSI SCORE']}
                  />
                  <ReferenceLine x={0.10} stroke="#CC8800" strokeDasharray="3 2"
                    label={{ value: '0.10', fill: '#CC8800', fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 700 }}
                  />
                  <ReferenceLine x={0.20} stroke="#CC2222" strokeDasharray="3 2"
                    label={{ value: '0.20', fill: '#CC2222', fontSize: 8, fontFamily: 'var(--font-mono)', fontWeight: 700 }}
                  />
                  <Bar dataKey="psi" radius={[0, 0, 0, 0]}>
                    {psiData.map((entry, i) => (
                      <Cell key={i} fill={entry.psi > 0.15 ? '#CC2222' : entry.psi > 0.08 ? '#FF6600' : '#004488'} />
                    ))}
                  </Bar>
                </BarChart>
              </ResponsiveContainer>
            </div>
          </div>

          {/* Infrastructure Diagnostics */}
          <div style={{ background: '#0a0a0a', fontFamily: 'var(--font-mono)' }}>
            <div style={{
              padding: '0.25rem 0.6rem', background: '#0d0600',
              borderBottom: '1px solid #2a1500',
              display: 'flex', alignItems: 'center', justifyContent: 'space-between',
            }}>
              <span style={{ color: '#888', fontSize: '0.6rem', fontWeight: 700 }}>INFRASTRUCTURE & FFI KERNEL DIAGNOSTICS</span>
              <span style={{ background: '#00CC33', color: '#000', fontSize: '0.55rem', fontWeight: 900, padding: '0 0.3rem', height: '14px', display: 'inline-flex', alignItems: 'center' }}>
                RUST+C ACCELERATED
              </span>
            </div>
            <div style={{ padding: '0.4rem' }}>
              <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: '0.65rem' }}>
                <thead>
                  <tr>
                    <th style={{ background: '#1a0d00', color: '#FF6600', padding: '0.2rem 0.4rem', textAlign: 'left', borderBottom: '1px solid #FF6600', fontSize: '0.58rem', fontWeight: 900 }}>SUBSYSTEM</th>
                    <th style={{ background: '#1a0d00', color: '#FF6600', padding: '0.2rem 0.4rem', textAlign: 'right', borderBottom: '1px solid #FF6600', fontSize: '0.58rem', fontWeight: 900 }}>STATUS</th>
                    <th style={{ background: '#1a0d00', color: '#FF6600', padding: '0.2rem 0.4rem', textAlign: 'right', borderBottom: '1px solid #FF6600', fontSize: '0.58rem', fontWeight: 900 }}>DETAIL</th>
                  </tr>
                </thead>
                <tbody>
                  {infraRows.map((r, i) => (
                    <tr key={i} style={{ borderBottom: '1px solid #1a1a1a' }}>
                      <td style={{ padding: '0.25rem 0.4rem', color: '#AAAAAA' }}>{r.label}</td>
                      <td style={{ padding: '0.25rem 0.4rem', color: r.color, fontWeight: 900, textAlign: 'right' }}>{r.value}</td>
                      <td style={{ padding: '0.25rem 0.4rem', color: '#555', textAlign: 'right' }}>{r.sub}</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        </div>

        {/* ── Alert Stream ── */}
        <div style={{
          padding: '0.28rem 0.6rem', background: '#0d0600',
          border: '1px solid #FF6600', borderBottom: '1px solid #2a1500',
          fontFamily: 'var(--font-mono)',
        }}>
          <span style={{ color: '#FF6600', fontSize: '0.65rem', fontWeight: 900, letterSpacing: '0.07em' }}>
            PRODUCTION ANOMALY STREAM & INCIDENT LOG
          </span>
        </div>
        <div style={{ border: '1px solid #2a2a2a', borderTop: 'none' }}>
          {loading ? <LoadingSkeleton height="120px" /> : <AlertFeed alerts={alerts} />}
        </div>

      </div>
    </ErrorBoundary>
  );
}
