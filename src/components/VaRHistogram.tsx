'use client';

import React from 'react';
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

export default function VaRHistogram({
  height = 240,
  var95Cutoff = -1.45,
  var99Cutoff = -2.15,
  cvarCutoff = -1.82
}: {
  height?: number;
  var95Cutoff?: number;
  var99Cutoff?: number;
  cvarCutoff?: number;
}) {
  // Return distribution bins
  const bins = [
    { ret: -3.5, count: 4, tail: true },
    { ret: -3.0, count: 9, tail: true },
    { ret: -2.5, count: 22, tail: true },
    { ret: -2.0, count: 58, tail: true },
    { ret: -1.5, count: 145, tail: true },
    { ret: -1.0, count: 380, tail: false },
    { ret: -0.5, count: 720, tail: false },
    { ret: 0.0, count: 1150, tail: false },
    { ret: 0.5, count: 1380, tail: false },
    { ret: 1.0, count: 980, tail: false },
    { ret: 1.5, count: 520, tail: false },
    { ret: 2.0, count: 240, tail: false },
    { ret: 2.5, count: 85, tail: false },
    { ret: 3.0, count: 28, tail: false },
    { ret: 3.5, count: 8, tail: false }
  ];

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={bins} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="ret"
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}%`}
          />
          <YAxis stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" />
          <Tooltip
            contentStyle={{
              background: '#0d1117',
              border: '1px solid #1e293b',
              borderRadius: '3px',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: '#f8fafc'
            }}
            formatter={(val: any) => [`${val} days`, 'Frequency']}
            labelFormatter={(label) => `Daily Return Bin: ${label}%`}
          />
          <ReferenceLine x={var95Cutoff} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: `VaR 95%: ${var95Cutoff}%`, fill: '#fbbf24', fontSize: 10, fontFamily: 'var(--font-mono)' }} />
          <ReferenceLine x={var99Cutoff} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: `VaR 99%: ${var99Cutoff}%`, fill: '#fb7185', fontSize: 10, fontFamily: 'var(--font-mono)' }} />
          <Bar dataKey="count" radius={[2, 2, 0, 0]}>
            {bins.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.ret <= var99Cutoff ? '#f43f5e' : entry.ret <= var95Cutoff ? '#f59e0b' : '#38bdf8'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
