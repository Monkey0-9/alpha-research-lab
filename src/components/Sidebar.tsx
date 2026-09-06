'use client';

import Link from 'next/link';
import { usePathname } from 'next/navigation';
import { useState, useEffect } from 'react';

const MODULES = [
  { href: '/',                  label: 'EXECUTIVE DASHBOARD',    key: 'DASH' },
  { href: '/data',              label: 'DATA INFRASTRUCTURE',     key: 'DATA' },
  { href: '/features',          label: 'FEATURE / SIGNAL FACTORY',key: 'FEAT' },
  { href: '/alpha-discovery',   label: 'ALPHA DISCOVERY LAB',     key: 'ALPH' },
  { href: '/statistical-engine',label: 'STATISTICAL ENGINE',      key: 'STAT' },
  { href: '/model-lab',         label: 'MODEL RESEARCH LAB',      key: 'MODL' },
  { href: '/validation',        label: 'TS VALIDATION ENGINE',    key: 'VALD' },
  { href: '/quality-gate',      label: 'ALPHA QUALITY GATE',      key: 'QUAL' },
  { href: '/portfolio',         label: 'PORTFOLIO CONSTRUCTION',  key: 'PORT' },
  { href: '/execution',         label: 'EXECUTION RESEARCH',      key: 'EXEC' },
  { href: '/risk',              label: 'INSTITUTIONAL RISK',      key: 'RISK' },
  { href: '/live-research',     label: 'LIVE PAPER TRADING',      key: 'LIVE' },
  { href: '/native-engine',     label: 'KDB+/Q & C NATIVE LAB',   key: 'NTV' },
  { href: '/monitoring',        label: 'PRODUCTION TELEMETRY',    key: 'TELE' },
];

export default function Sidebar() {
  const pathname = usePathname();
  const [utcTime, setUtcTime] = useState('');
  const [estTime, setEstTime] = useState('');
  const [uptime, setUptime] = useState(0);

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().slice(17, 25));
      setEstTime(now.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour12: false }));
      setUptime((u) => u + 1);
    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const fmtUptime = (s: number) => {
    const h = Math.floor(s / 3600).toString().padStart(2, '0');
    const m = Math.floor((s % 3600) / 60).toString().padStart(2, '0');
    const sec = (s % 60).toString().padStart(2, '0');
    return `${h}:${m}:${sec}`;
  };

  return (
    <aside className="sidebar">
      {/* Bloomberg Logo Header */}
      <div className="sidebar-header">
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div>
            <div style={{ fontSize: '0.85rem', fontWeight: 900, letterSpacing: '0.06em', color: '#000000', fontFamily: 'var(--font-mono)', lineHeight: 1 }}>
              QUANT<span style={{ color: '#1a0900' }}>ALPHA</span>
            </div>
            <div style={{ fontSize: '0.58rem', color: '#3d1a00', fontFamily: 'var(--font-mono)', letterSpacing: '0.08em', marginTop: '1px', fontWeight: 700 }}>
              INSTITUTIONAL TERMINAL v2.4
            </div>
          </div>
          <div style={{
            background: '#000',
            color: '#FF6600',
            fontSize: '0.58rem',
            fontWeight: 900,
            padding: '0.15rem 0.4rem',
            letterSpacing: '0.06em',
            border: '1px solid #000',
          }}>
            PRO
          </div>
        </div>
      </div>

      {/* Time bar */}
      <div style={{
        padding: '0.25rem 0.75rem',
        background: '#050300',
        borderBottom: '1px solid var(--bb-border-2)',
        display: 'flex',
        alignItems: 'center',
        justifyContent: 'space-between',
        fontSize: '0.6rem',
        fontFamily: 'var(--font-mono)',
      }}>
        <span style={{ color: '#FF6600', fontWeight: 700 }}>{utcTime || '00:00:00'} UTC</span>
        <span style={{ color: '#666' }}>|</span>
        <span style={{ color: '#888' }}>{estTime || '00:00:00'} EST</span>
      </div>

      {/* Nav Section Label */}
      <div className="nav-section-title">
        ◀ RESEARCH PIPELINE ▶
      </div>

      {/* Navigation */}
      <div className="sidebar-scroll">
        {MODULES.map((mod) => {
          const isActive = pathname === mod.href;
          return (
            <Link
              key={mod.href}
              href={mod.href}
              className={`nav-link ${isActive ? 'active' : ''}`}
            >
              {/* Module label */}
              <span style={{
                flex: 1,
                fontSize: '0.68rem',
                fontFamily: 'var(--font-mono)',
                fontWeight: isActive ? 700 : 500,
                letterSpacing: '0.02em',
                textOverflow: 'ellipsis',
                overflow: 'hidden',
                whiteSpace: 'nowrap',
              }}>
                {mod.label}
              </span>
              {/* Active indicator */}
              {isActive && (
                <span style={{
                  fontSize: '0.6rem',
                  fontFamily: 'var(--font-mono)',
                  color: '#FFFF00',
                  fontWeight: 900,
                  flexShrink: 0,
                  marginLeft: '0.25rem',
                }}>
                  ◄
                </span>
              )}
            </Link>
          );
        })}
      </div>

      {/* Footer — system status */}
      <div style={{
        padding: '0.4rem 0.6rem',
        borderTop: '2px solid #FF6600',
        background: '#050300',
        display: 'flex',
        flexDirection: 'column',
        gap: '0.2rem',
        fontSize: '0.6rem',
        fontFamily: 'var(--font-mono)',
      }}>
        {/* Status row */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem' }}>
            <span className="bb-dot bb-dot-green" style={{ width: 6, height: 6, borderRadius: 0 }} />
            <span style={{ color: '#00FF41', fontWeight: 700 }}>ENGINE ONLINE</span>
          </div>
          <span style={{ color: '#FF6600', fontWeight: 700 }}>0.4ms</span>
        </div>
        {/* AUM / Memory */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#555' }}>
          <span>MEM: 384/16384MB</span>
          <span>AUM: $2.48M</span>
        </div>
        {/* Uptime */}
        <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', color: '#444' }}>
          <span>UPTIME: {fmtUptime(uptime)}</span>
          <span style={{ color: '#FF6600' }}>FFI:RUST+C+Q</span>
        </div>
      </div>
    </aside>
  );
}
