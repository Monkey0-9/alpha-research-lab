'use client';

import React from 'react';
import type { ProductionAlertItem } from '@/lib/types';

interface AlertFeedProps {
  alerts?: ProductionAlertItem[];
}

const SEVERITY_STYLE: Record<string, { color: string; label: string }> = {
  critical: { color: '#FF3333', label: 'CRIT' },
  warning:  { color: '#FF6600', label: 'WARN' },
  info:     { color: '#00CCFF', label: 'INFO' },
  success:  { color: '#00FF41', label: 'PASS' },
};

const FALLBACK_ALERTS: ProductionAlertItem[] = [
  { id: 'a1', timestamp: new Date().toISOString(), message: 'DSR GATE PASSED — MOMENTUM_REVERSAL v2.1 approved for staging deployment', severity: 'success', module: 'QUALITY GATE', acknowledged: false },
  { id: 'a2', timestamp: new Date(Date.now() - 120000).toISOString(), message: 'ALPHA DECAY DETECTED — STATARB_SECTOR IC falling below 0.03 threshold, auto-refit queued', severity: 'warning', module: 'MONITORING', acknowledged: false },
  { id: 'a3', timestamp: new Date(Date.now() - 300000).toISOString(), message: 'DRAWDOWN LIMIT BREACH — Portfolio equity at -6.8%, 56.7% of max DD limit consumed', severity: 'warning', module: 'RISK ENGINE', acknowledged: false },
  { id: 'a4', timestamp: new Date(Date.now() - 600000).toISOString(), message: 'FFI ENGINE STATUS — Rust accelerator v1.8.2 compiled, C kernel loaded, memory mapped 384MB', severity: 'info', module: 'INFRASTRUCTURE', acknowledged: true },
  { id: 'a5', timestamp: new Date(Date.now() - 900000).toISOString(), message: 'BACKTEST COMPLETE — Walk-forward Sharpe 2.14 > 1.50 threshold, promoted to paper trading', severity: 'success', module: 'BACKTESTER', acknowledged: true },
];

function fmtTime(iso: string) {
  try {
    const d = new Date(iso);
    return d.toLocaleTimeString('en-US', { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
  } catch { return '--:--:--'; }
}

function timeDiff(iso: string) {
  const diff = Math.floor((Date.now() - new Date(iso).getTime()) / 1000);
  if (diff < 60) return `${diff}S AGO`;
  if (diff < 3600) return `${Math.floor(diff/60)}M AGO`;
  return `${Math.floor(diff/3600)}H AGO`;
}

export default function AlertFeed({ alerts }: AlertFeedProps) {
  const items = (alerts && alerts.length > 0 ? alerts : FALLBACK_ALERTS);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: 0 }}>
      {/* Header */}
      <div style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '0.25rem 0.6rem',
        background: '#0d0600', borderBottom: '1px solid #FF6600',
        fontFamily: 'var(--font-mono)', fontSize: '0.6rem',
      }}>
        <span style={{ color: '#FF6600', fontWeight: 700 }}>EVENT LOG — {items.length} EVENTS</span>
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
          {['CRIT', 'WARN', 'INFO', 'PASS'].map((s) => (
            <span key={s} style={{ color: '#555', fontSize: '0.58rem' }}>[{s}]</span>
          ))}
        </div>
      </div>

      {/* Feed items */}
      {items.map((alert) => {
        const sev = SEVERITY_STYLE[alert.severity] || SEVERITY_STYLE.info;
        return (
          <div key={alert.id} className="bb-feed-item" style={{ opacity: alert.acknowledged ? 0.5 : 1 }}>
            {/* Severity badge */}
            <span style={{
              background: sev.color,
              color: '#000',
              fontSize: '0.58rem',
              fontWeight: 900,
              padding: '0 0.3rem',
              height: '16px',
              display: 'inline-flex',
              alignItems: 'center',
              flexShrink: 0,
              fontFamily: 'var(--font-mono)',
              letterSpacing: '0.04em',
            }}>
              {sev.label}
            </span>

            {/* Timestamp */}
            <span className="bb-feed-time" style={{ flexShrink: 0, minWidth: '70px' }}>
              {fmtTime(alert.timestamp)}
            </span>

            {/* Module */}
            <span style={{
              color: '#555', fontSize: '0.6rem', fontFamily: 'var(--font-mono)',
              flexShrink: 0, minWidth: '90px', fontWeight: 700,
            }}>
              [{alert.module || 'SYSTEM'}]
            </span>

            {/* Message */}
            <span className="bb-feed-msg" style={{ flex: 1, fontSize: '0.68rem' }}>
              {alert.message}
            </span>

            {/* Time diff */}
            <span style={{ color: '#444', fontSize: '0.58rem', flexShrink: 0, fontFamily: 'var(--font-mono)' }}>
              {timeDiff(alert.timestamp)}
            </span>

            {/* Ack */}
            {alert.acknowledged && (
              <span style={{
                color: '#333', fontSize: '0.58rem', flexShrink: 0,
                fontFamily: 'var(--font-mono)', fontWeight: 700,
              }}>
                ACK
              </span>
            )}
          </div>
        );
      })}
    </div>
  );
}
