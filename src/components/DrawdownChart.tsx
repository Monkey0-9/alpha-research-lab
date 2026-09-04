'use client';

import React from 'react';
import {
  ResponsiveContainer,
  AreaChart,
  Area,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';

interface DrawdownPoint {
  date: string;
  drawdown: number; // e.g. -0.05 for -5% or -5.0
}

interface DrawdownChartProps {
  data: DrawdownPoint[];
  height?: number;
}

export default function DrawdownChart({ data, height = 200 }: DrawdownChartProps) {
  // Normalize if drawdown is fraction vs percentage
  const formattedData = data.map((d) => ({
    date: d.date,
    drawdown: Math.abs(d.drawdown) <= 1.0 ? -(Math.abs(d.drawdown) * 100) : -(Math.abs(d.drawdown))
  }));

  const maxDrawdown = Math.min(...formattedData.map((d) => d.drawdown));

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <AreaChart data={formattedData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <defs>
            <linearGradient id="drawdownGradient" x1="0" y1="0" x2="0" y2="1">
              <stop offset="5%" stopColor="#f43f5e" stopOpacity={0.4} />
              <stop offset="95%" stopColor="#f43f5e" stopOpacity={0.02} />
            </linearGradient>
          </defs>
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
            domain={['auto', 0]}
            tickFormatter={(v) => `${v.toFixed(1)}%`}
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
            formatter={(value: any) => [`${Number(value).toFixed(2)}%`, 'Underwater Depth']}
          />
          <ReferenceLine y={maxDrawdown} stroke="#f43f5e" strokeDasharray="3 3" label={{ value: `Max DD: ${maxDrawdown.toFixed(2)}%`, fill: '#fb7185', fontSize: 10, fontFamily: 'var(--font-mono)', position: 'insideBottomLeft' }} />
          <Area
            type="monotone"
            dataKey="drawdown"
            stroke="#f43f5e"
            strokeWidth={1.5}
            fillOpacity={1}
            fill="url(#drawdownGradient)"
          />
        </AreaChart>
      </ResponsiveContainer>
    </div>
  );
}
