'use client';

import React from 'react';

interface WindowItem {
  window: number;
  train: string;
  purge: string;
  test: string;
  isSharpe: number;
  oosSharpe: number;
  degradation: string;
}

export default function WalkForwardTimeline() {
  const windows: WindowItem[] = [
    { window: 1, train: '2020 Q1 - 2021 Q4 (504d)', purge: '10d Gap', test: '2022 Q1 (63d)', isSharpe: 2.12, oosSharpe: 1.84, degradation: '-13.2%' },
    { window: 2, train: '2020 Q1 - 2022 Q1 (567d)', purge: '10d Gap', test: '2022 Q2 (63d)', isSharpe: 2.18, oosSharpe: 1.91, degradation: '-12.4%' },
    { window: 3, train: '2020 Q1 - 2022 Q2 (630d)', purge: '10d Gap', test: '2022 Q3 (63d)', isSharpe: 2.05, oosSharpe: 1.78, degradation: '-13.1%' },
    { window: 4, train: '2020 Q1 - 2022 Q3 (693d)', purge: '10d Gap', test: '2022 Q4 (63d)', isSharpe: 2.22, oosSharpe: 2.04, degradation: '-8.1%' },
    { window: 5, train: '2020 Q1 - 2022 Q4 (756d)', purge: '10d Gap', test: '2023 Q1 (63d)', isSharpe: 2.25, oosSharpe: 2.12, degradation: '-5.7%' },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.65rem' }}>
      {windows.map((w) => (
        <div
          key={w.window}
          style={{
            background: '#0a0d14',
            border: '1px solid var(--border-terminal)',
            borderRadius: '3px',
            padding: '0.65rem 0.85rem'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.45rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <span style={{ fontWeight: 700, color: '#38bdf8' }}>WINDOW {w.window}</span>
              <span style={{ color: '#94a3b8' }}>Test: {w.test}</span>
            </div>
            <div style={{ display: 'flex', gap: '0.75rem' }}>
              <span>IS Sharpe: <strong style={{ color: '#f8fafc' }}>{w.isSharpe.toFixed(2)}</strong></span>
              <span>OOS Sharpe: <strong style={{ color: '#34d399' }}>{w.oosSharpe.toFixed(2)}</strong></span>
              <span style={{ color: '#fbbf24' }}>Degradation: {w.degradation}</span>
            </div>
          </div>

          {/* Graphical timeline bar */}
          <div style={{ display: 'flex', height: '14px', borderRadius: '2px', overflow: 'hidden', border: '1px solid #1e293b' }}>
            <div style={{ flex: 8, background: '#1e293b', color: '#94a3b8', fontSize: '0.58rem', fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', justifyContent: 'center' }}>
              TRAIN (EXPANDING)
            </div>
            <div style={{ width: '12px', background: '#f59e0b', opacity: 0.6 }} title="Purged Gap" />
            <div style={{ flex: 2, background: '#0284c7', color: '#ffffff', fontSize: '0.58rem', fontFamily: 'var(--font-mono)', display: 'flex', alignItems: 'center', justifyContent: 'center', fontWeight: 600 }}>
              OOS EVAL
            </div>
          </div>
        </div>
      ))}
    </div>
  );
}
