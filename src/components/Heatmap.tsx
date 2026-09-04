'use client';

import React from 'react';

interface HeatmapProps {
  labels: string[];
  matrix: number[][];
  title?: string;
}

export default function Heatmap({ labels, matrix, title }: HeatmapProps) {
  // Color interpolator for correlation (-1.0 to +1.0)
  const getCellColor = (val: number) => {
    if (val > 0) {
      // Blue/cyan intensity
      const alpha = Math.min(Math.abs(val), 1.0);
      return `rgba(56, 189, 248, ${alpha * 0.85 + 0.1})`;
    } else {
      // Rose intensity
      const alpha = Math.min(Math.abs(val), 1.0);
      return `rgba(244, 63, 94, ${alpha * 0.85 + 0.1})`;
    }
  };

  return (
    <div style={{ overflowX: 'auto', width: '100%' }}>
      {title && (
        <div style={{ fontSize: '0.72rem', fontFamily: 'var(--font-mono)', color: 'var(--text-muted)', marginBottom: '0.5rem', fontWeight: 600 }}>
          {title}
        </div>
      )}
      <table style={{ borderCollapse: 'collapse', fontFamily: 'var(--font-mono)', fontSize: '0.68rem', width: '100%' }}>
        <thead>
          <tr>
            <th style={{ padding: '0.35rem', background: '#0a0d14', border: '1px solid var(--border-terminal)' }} />
            {labels.map((l) => (
              <th key={l} style={{ padding: '0.35rem 0.5rem', background: '#0f1420', border: '1px solid var(--border-terminal)', color: '#94a3b8', fontWeight: 600 }}>
                {l}
              </th>
            ))}
          </tr>
        </thead>
        <tbody>
          {matrix.map((row, rIdx) => (
            <tr key={labels[rIdx] || rIdx}>
              <td style={{ padding: '0.35rem 0.5rem', background: '#0f1420', border: '1px solid var(--border-terminal)', color: '#94a3b8', fontWeight: 600 }}>
                {labels[rIdx]}
              </td>
              {row.map((val, cIdx) => (
                <td
                  key={cIdx}
                  title={`${labels[rIdx]} vs ${labels[cIdx]}: ${val.toFixed(2)}`}
                  style={{
                    padding: '0.35rem 0.5rem',
                    textAlign: 'center',
                    border: '1px solid var(--border-terminal)',
                    background: getCellColor(val),
                    color: Math.abs(val) > 0.4 ? '#ffffff' : '#94a3b8',
                    fontWeight: rIdx === cIdx ? 700 : 500
                  }}
                >
                  {val.toFixed(2)}
                </td>
              ))}
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}
