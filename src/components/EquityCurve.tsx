'use client';

import React from 'react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  Legend
} from 'recharts';

interface EquityPoint {
  date: string;
  nav: number;
  benchmark?: number;
  drawdown?: number;
}

interface EquityCurveProps {
  data: EquityPoint[];
  height?: number;
  benchmarkName?: string;
}

export default function EquityCurve({
  data,
  height = 320,
  benchmarkName = 'S&P 500 (SPY)'
}: EquityCurveProps) {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="date"
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickLine={false}
            dy={5}
          />
          <YAxis
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickLine={false}
            domain={['auto', 'auto']}
            tickFormatter={(v) => v.toFixed(2)}
          />
          <Tooltip
            contentStyle={{
              background: '#0d1117',
              border: '1px solid #1e293b',
              borderRadius: '3px',
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              color: '#f8fafc'
            }}
            formatter={(value: any, name: any) => [
              typeof value === 'number' ? value.toFixed(4) : value,
              name === 'nav' ? 'QuantAlpha Portfolio' : name
            ]}
          />
          <Legend
            wrapperStyle={{
              fontFamily: 'var(--font-mono)',
              fontSize: '11px',
              paddingTop: '8px'
            }}
          />
          <Line
            type="monotone"
            dataKey="nav"
            name="QuantAlpha Portfolio"
            stroke="#38bdf8"
            strokeWidth={2}
            dot={false}
            activeDot={{ r: 4, stroke: '#38bdf8', strokeWidth: 1, fill: '#ffffff' }}
          />
          {data[0]?.benchmark !== undefined && (
            <Line
              type="monotone"
              dataKey="benchmark"
              name={benchmarkName}
              stroke="#64748b"
              strokeWidth={1.5}
              strokeDasharray="4 4"
              dot={false}
            />
          )}
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
