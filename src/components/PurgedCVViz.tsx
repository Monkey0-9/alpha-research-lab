'use client';

import React from 'react';

export default function PurgedCVViz() {
  const folds = [
    { fold: 1, valIdx: 0, sharpe: 1.84, ic: 0.082 },
    { fold: 2, valIdx: 1, sharpe: 1.92, ic: 0.088 },
    { fold: 3, valIdx: 2, sharpe: 1.76, ic: 0.075 },
    { fold: 4, valIdx: 3, sharpe: 2.05, ic: 0.094 },
    { fold: 5, valIdx: 4, sharpe: 1.95, ic: 0.089 },
  ];

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.6rem' }}>
      <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#94a3b8', marginBottom: '0.2rem' }}>
        <span>5-Fold Purged & Embargoed Cross-Validation Scheme (No Leakage)</span>
        <span style={{ color: '#38bdf8' }}>Purge Gap: 5 Days · Embargo: 1%</span>
      </div>

      {folds.map((f) => (
        <div key={f.fold} style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <span style={{ width: '50px', fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>
            FOLD {f.fold}
          </span>
          <div style={{ flex: 1, display: 'flex', height: '18px', borderRadius: '2px', overflow: 'hidden', border: '1px solid #1e293b' }}>
            {[0, 1, 2, 3, 4].map((blockIdx) => {
              const isVal = blockIdx === f.valIdx;
              return (
                <div
                  key={blockIdx}
                  style={{
                    flex: 1,
                    background: isVal ? '#38bdf8' : '#111827',
                    borderRight: blockIdx < 4 ? '1px solid #1e293b' : 'none',
                    display: 'flex',
                    alignItems: 'center',
                    justifyContent: 'center',
                    fontSize: '0.58rem',
                    fontFamily: 'var(--font-mono)',
                    color: isVal ? '#080a0f' : '#64748b',
                    fontWeight: isVal ? 700 : 400
                  }}
                >
                  {isVal ? 'TEST VAL' : 'TRAIN'}
                </div>
              );
            })}
          </div>
          <div style={{ width: '130px', textAlign: 'right', fontSize: '0.68rem', fontFamily: 'var(--font-mono)' }}>
            <span style={{ color: '#94a3b8' }}>Sharpe: </span>
            <strong style={{ color: '#34d399' }}>{f.sharpe.toFixed(2)}</strong>
            <span style={{ color: '#64748b', marginLeft: '0.4rem' }}>(IC {f.ic.toFixed(3)})</span>
          </div>
        </div>
      ))}
    </div>
  );
}
