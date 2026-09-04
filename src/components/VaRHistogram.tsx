'use client';
import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, Cell, ReferenceLine
} from 'recharts';

export default function VaRHistogram({
  height = 240,
  var95Cutoff = -1.45,
  var99Cutoff = -2.15,
  cvarCutoff = -1.82,
}: {
  height?: number;
  var95Cutoff?: number;
  var99Cutoff?: number;
  cvarCutoff?: number;
}) {
  const bins = [
    { ret: -3.5, count: 4 }, { ret: -3.0, count: 9 }, { ret: -2.5, count: 22 },
    { ret: -2.0, count: 58 }, { ret: -1.5, count: 145 }, { ret: -1.0, count: 380 },
    { ret: -0.5, count: 720 }, { ret: 0.0, count: 1150 }, { ret: 0.5, count: 1380 },
    { ret: 1.0, count: 980 }, { ret: 1.5, count: 520 }, { ret: 2.0, count: 240 },
    { ret: 2.5, count: 85 }, { ret: 3.0, count: 28 }, { ret: 3.5, count: 8 },
  ];

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={bins} margin={{ top: 10, right: 10, left: -20, bottom: 0 }} barSize={14}>
          <CartesianGrid strokeDasharray="" stroke="#1a1a1a" vertical={false} />
          <XAxis
            dataKey="ret"
            tick={{ fill: '#555', fontSize: 9, fontFamily: 'var(--font-mono)' }}
            axisLine={{ stroke: '#2a2a2a' }}
            tickLine={false}
            tickFormatter={(v) => `${v > 0 ? '+' : ''}${v}%`}
          />
          <YAxis
            tick={{ fill: '#555', fontSize: 9, fontFamily: 'var(--font-mono)' }}
            axisLine={false}
            tickLine={false}
          />
          <Tooltip
            contentStyle={{
              background: '#0a0500', border: '1px solid #FF6600',
              fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#fff',
            }}
            formatter={(val: any) => [`${val} DAYS`, 'FREQUENCY']}
            labelFormatter={(label) => `RETURN BIN: ${label}%`}
          />
          <ReferenceLine
            x={var95Cutoff}
            stroke="#FF6600"
            strokeDasharray="3 2"
            label={{ value: `VaR 95%`, fill: '#FF6600', fontSize: 9, fontFamily: 'var(--font-mono)', fontWeight: 700 }}
          />
          <ReferenceLine
            x={var99Cutoff}
            stroke="#FF3333"
            strokeDasharray="3 2"
            label={{ value: `VaR 99%`, fill: '#FF3333', fontSize: 9, fontFamily: 'var(--font-mono)', fontWeight: 700 }}
          />
          <Bar dataKey="count" radius={[0, 0, 0, 0]}>
            {bins.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={
                  entry.ret <= var99Cutoff ? '#CC2222' :
                  entry.ret <= var95Cutoff ? '#FF6600' :
                  entry.ret <= 0 ? '#555555' : '#1a4a1a'
                }
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
