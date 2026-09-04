'use client';

import { useState, useEffect } from 'react';
import { useStationStore } from '@/lib/store';
import { UNIVERSES } from '@/lib/constants';
import { Globe, RefreshCw, Cpu, Activity } from 'lucide-react';

export default function TerminalHeader({ title }: { title?: string }) {
  const { selectedUniverse, setUniverse, executionMode, setExecutionMode, autoRefresh, toggleAutoRefresh } = useStationStore();
  const [utcTime, setUtcTime] = useState('');
  const [estTime, setEstTime] = useState('');

  useEffect(() => {
    const update = () => {
      const now = new Date();
      setUtcTime(now.toUTCString().slice(17, 25) + ' UTC');
      setEstTime(
        now.toLocaleTimeString('en-US', { timeZone: 'America/New_York', hour12: false }) + ' EST'
      );
    };
    update();
    const interval = setInterval(update, 1000);
    return () => clearInterval(interval);
  }, []);

  return (
    <header className="terminal-header">
      <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
        {title && (
          <span style={{ fontFamily: 'var(--font-mono)', fontSize: '0.78rem', fontWeight: 600, color: '#f8fafc', letterSpacing: '0.04em' }}>
            {title}
          </span>
        )}

        {/* Universe Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#0f1420', padding: '0.2rem 0.6rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
          <Globe size={12} color="#94a3b8" />
          <span style={{ fontSize: '0.68rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>UNIVERSE:</span>
          <select
            value={selectedUniverse}
            onChange={(e) => setUniverse(e.target.value)}
            style={{ background: 'transparent', color: '#38bdf8', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', border: 'none', outline: 'none', cursor: 'pointer', fontWeight: 600 }}
          >
            {UNIVERSES.map((u) => (
              <option key={u.id} value={u.id} style={{ background: '#0d1117', color: '#f8fafc' }}>
                {u.name}
              </option>
            ))}
          </select>
        </div>

        {/* Execution Mode Selector */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.35rem', background: '#0f1420', padding: '0.2rem 0.6rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
          <Activity size={12} color="#94a3b8" />
          <span style={{ fontSize: '0.68rem', color: '#64748b', fontFamily: 'var(--font-mono)' }}>MODE:</span>
          <select
            value={executionMode}
            onChange={(e) => setExecutionMode(e.target.value as any)}
            style={{ background: 'transparent', color: executionMode === 'LIVE' ? '#34d399' : '#c084fc', fontSize: '0.72rem', fontFamily: 'var(--font-mono)', border: 'none', outline: 'none', cursor: 'pointer', fontWeight: 600 }}
          >
            <option value="PAPER" style={{ background: '#0d1117', color: '#c084fc' }}>PAPER SIMULATOR</option>
            <option value="BACKTEST" style={{ background: '#0d1117', color: '#38bdf8' }}>WALK-FORWARD BACKTEST</option>
            <option value="LIVE" style={{ background: '#0d1117', color: '#34d399' }}>LIVE CANARY FEED</option>
          </select>
        </div>
      </div>

      <div style={{ display: 'flex', alignItems: 'center', gap: '1.25rem' }}>
        {/* Engine status */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem', fontSize: '0.7rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
          <Cpu size={12} color="#34d399" />
          <span>NATIVE C/RUST ACCELERATOR</span>
          <span className="badge-tag badge-pass" style={{ fontSize: '0.58rem', padding: '0.05rem 0.25rem' }}>ONLINE</span>
        </div>

        {/* Clocks */}
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem', fontFamily: 'var(--font-mono)', fontSize: '0.7rem' }}>
          <span style={{ color: '#94a3b8' }}>{estTime || '16:00:00 EST'}</span>
          <span style={{ color: '#64748b' }}>|</span>
          <span style={{ color: '#38bdf8', fontWeight: 600 }}>{utcTime || '21:00:00 UTC'}</span>
        </div>

        {/* Auto Refresh Toggle */}
        <button
          onClick={toggleAutoRefresh}
          style={{
            background: autoRefresh ? 'rgba(56, 189, 248, 0.1)' : 'transparent',
            border: `1px solid ${autoRefresh ? 'rgba(56, 189, 248, 0.4)' : 'var(--border-terminal)'}`,
            padding: '0.25rem 0.5rem',
            borderRadius: '3px',
            color: autoRefresh ? '#38bdf8' : '#64748b',
            display: 'flex',
            alignItems: 'center',
            gap: '0.35rem',
            fontSize: '0.68rem',
            fontFamily: 'var(--font-mono)',
            cursor: 'pointer'
          }}
        >
          <RefreshCw size={11} className={autoRefresh ? 'animate-spin' : ''} style={{ animationDuration: '4s' }} />
          <span>{autoRefresh ? 'STREAMING' : 'PAUSED'}</span>
        </button>
      </div>
    </header>
  );
}
