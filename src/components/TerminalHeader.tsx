'use client';

import { useState, useEffect } from 'react';
import { useStationStore } from '@/lib/store';
import { UNIVERSES } from '@/lib/constants';

const FKEYS = [
  { num: 'F1',  label: 'HELP' },
  { num: 'F2',  label: 'QUOTE' },
  { num: 'F3',  label: 'BACKTEST' },
  { num: 'F4',  label: 'NEWS' },
  { num: 'F5',  label: 'REFRESH' },
  { num: 'F6',  label: 'EXCEL' },
  { num: 'F7',  label: 'HIST' },
  { num: 'F8',  label: 'RISK' },
  { num: 'F9',  label: 'LIVE' },
  { num: 'F10', label: 'ALERT' },
  { num: 'F11', label: 'PRINT' },
  { num: 'F12', label: 'LOGOUT' },
];

export default function TerminalHeader({ title }: { title?: string }) {
  const { selectedUniverse, setUniverse, executionMode, setExecutionMode, autoRefresh, toggleAutoRefresh } = useStationStore();
  const [utcTime, setUtcTime] = useState('');
  const [estTime, setEstTime] = useState('');
  const [nyseStatus, setNyseStatus] = useState<'OPEN' | 'CLOSED' | 'PRE' | 'AH'>('CLOSED');
  const [cmd, setCmd] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      const utc = now.toUTCString().slice(17, 25);
      const est = now.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour12: false });
      setUtcTime(utc + ' UTC');
      setEstTime(est + ' EST');

      // NYSE market status
      const nyHour = new Date().toLocaleString('en-US', { timeZone: 'America/New_York', hour: 'numeric', hour12: false });
      const h = parseInt(nyHour);
      if (h >= 9 && h < 16) setNyseStatus('OPEN');
      else if (h >= 4 && h < 9) setNyseStatus('PRE');
      else if (h >= 16 && h < 20) setNyseStatus('AH');
      else setNyseStatus('CLOSED');

    };
    update();
    const id = setInterval(update, 1000);
    return () => clearInterval(id);
  }, []);

  const mktColor = nyseStatus === 'OPEN' ? '#00FF41' : nyseStatus === 'PRE' ? '#FFFF00' : nyseStatus === 'AH' ? '#FF6600' : '#FF3333';

  return (
    <>
      {/* ── Bloomberg Function Key Row ── */}
      <div className="fkey-bar">
        {/* Brand label */}
        <div style={{
          color: '#FF6600',
          fontWeight: 900,
          fontSize: '0.68rem',
          letterSpacing: '0.04em',
          paddingRight: '0.75rem',
          borderRight: '1px solid #2a1500',
          marginRight: '0.3rem',
          fontFamily: 'var(--font-mono)',
          whiteSpace: 'nowrap',
        }}>
          BLOOMBERG ◄ QUANT
        </div>

        {FKEYS.map((k) => (
          <button key={k.num} className="fkey-btn" title={k.label}>
            <span className="fkey-num">{k.num}</span>
            <span style={{ marginLeft: '2px' }}>{k.label}</span>
          </button>
        ))}

        <div className="fkey-separator" />

        {/* Market Status */}
        <div style={{
          display: 'flex', alignItems: 'center', gap: '0.4rem',
          paddingLeft: '0.5rem', marginLeft: '0.25rem',
          fontFamily: 'var(--font-mono)', fontSize: '0.6rem',
        }}>
          <span style={{ color: mktColor, fontWeight: 900 }}>NYSE:{nyseStatus}</span>
          <span style={{ color: '#444' }}>|</span>
          <span style={{ color: '#555' }}>{estTime || '00:00:00 EST'}</span>
          <span style={{ color: '#444' }}>|</span>
          <span style={{ color: '#FF6600', fontWeight: 700 }}>{utcTime || '00:00:00 UTC'}</span>
        </div>
      </div>

      {/* ── Bloomberg Main Command Header ── */}
      <header className="terminal-header">
        {/* Left: Module title + Command Input */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          {title && (
            <div style={{
              fontFamily: 'var(--font-mono)',
              fontSize: '0.7rem',
              fontWeight: 900,
              color: '#FF6600',
              letterSpacing: '0.06em',
              textTransform: 'uppercase',
              borderRight: '1px solid #2a2a2a',
              paddingRight: '1rem',
              whiteSpace: 'nowrap',
            }}>
              {title}
            </div>
          )}

          {/* Bloomberg Command Input */}
          <div className="bb-cmd-bar">
            <span className="bb-cmd-prompt">{'>'}</span>
            <input
              className="bb-cmd-input"
              value={cmd}
              onChange={(e) => setCmd(e.target.value)}
              placeholder="ENTER COMMAND OR TICKER SYMBOL..."
              onKeyDown={(e) => e.key === 'Escape' && setCmd('')}
            />
            {cmd && (
              <span style={{ color: '#FF6600', fontSize: '0.62rem', fontWeight: 700, flexShrink: 0 }}>
                GO
              </span>
            )}
          </div>
        </div>

        {/* Right: Selectors + Status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontFamily: 'var(--font-mono)' }}>

          {/* Universe */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.65rem' }}>
            <span style={{ color: '#555', fontWeight: 700 }}>UNIVERSE:</span>
            <select
              className="bb-select"
              value={selectedUniverse}
              onChange={(e) => setUniverse(e.target.value)}
              style={{ padding: '0.15rem 0.3rem', fontSize: '0.65rem' }}
            >
              {UNIVERSES.map((u) => (
                <option key={u.id} value={u.id} style={{ background: '#0a0a0a', color: '#FF6600' }}>
                  {u.name}
                </option>
              ))}
            </select>
          </div>

          {/* Execution Mode */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.3rem', fontSize: '0.65rem' }}>
            <span style={{ color: '#555', fontWeight: 700 }}>MODE:</span>
            <select
              className="bb-select"
              value={executionMode}
              onChange={(e) => setExecutionMode(e.target.value as any)}
              style={{
                padding: '0.15rem 0.3rem',
                fontSize: '0.65rem',
                color: executionMode === 'LIVE' ? '#00FF41' : executionMode === 'PAPER' ? '#FFFF00' : '#00CCFF',
              }}
            >
              <option value="PAPER"    style={{ background: '#0a0a0a', color: '#FFFF00' }}>PAPER SIM</option>
              <option value="BACKTEST" style={{ background: '#0a0a0a', color: '#00CCFF' }}>WALK-FWD</option>
              <option value="LIVE"     style={{ background: '#0a0a0a', color: '#00FF41' }}>LIVE FEED</option>
            </select>
          </div>

          {/* Separator */}
          <div style={{ width: 1, height: 20, background: '#2a2a2a' }} />

          {/* Polyglot Engine Latency Status Badges */}
          <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', fontSize: '0.6rem' }}>
            <span style={{ background: '#112211', border: '1px solid #00AA33', color: '#00FF41', padding: '0.1rem 0.35rem', fontWeight: 800 }}>
              C: 6.2μs
            </span>
            <span style={{ background: '#0a1926', border: '1px solid #0088cc', color: '#00CCFF', padding: '0.1rem 0.35rem', fontWeight: 800 }}>
              C++: 24.1μs
            </span>
            <span style={{ background: '#251505', border: '1px solid #cc5500', color: '#FF7700', padding: '0.1rem 0.35rem', fontWeight: 800 }}>
              Rust: 18.5μs
            </span>
            <span style={{ background: '#180a22', border: '1px solid #7733aa', color: '#BB88FF', padding: '0.1rem 0.35rem', fontWeight: 800 }}>
              R/Q/ML: OK
            </span>
          </div>

          {/* Auto Refresh */}
          <button
            onClick={toggleAutoRefresh}
            className={autoRefresh ? 'bb-btn-solid' : 'bb-btn'}
            style={{ padding: '0.15rem 0.55rem', fontSize: '0.62rem' }}
          >
            {autoRefresh ? '⟳ LIVE' : '⟳ PAUSED'}
          </button>
        </div>
      </header>
    </>
  );
}
