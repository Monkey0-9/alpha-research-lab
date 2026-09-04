'use client';
import React from 'react';
import {
  AreaChart, Area, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine
} from 'recharts';
import type { ChartTooltipProps } from '@/lib/types';

interface DrawdownChartProps {
  data: Array<{ date: string; drawdown: number }>;
  height?: number;
  limitPct?: number;
}

function BBTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  const val = Number(payload[0]?.value ?? 0);
  return (
    <div style={{
      background: '#0a0500', border: '1px solid #FF6600',
      padding: '0.4rem 0.65rem', fontFamily: 'var(--font-mono)', fontSize: '0.65rem',
    }}>
      <div style={{ color: '#FF6600', fontWeight: 700, marginBottom: '0.15rem' }}>{label}</div>
      <div style={{ color: '#FF3333', fontWeight: 700, fontSize: '0.75rem' }}>
        DD: {val.toFixed(2)}%
      </div>
    </div>
  );
}

export default function DrawdownChart({
  data,
  height = 280,
  limitPct = -12.0,
}: DrawdownChartProps) {
  if (!data || data.length === 0) return null;

  return (
    <ResponsiveContainer width="100%" height={height}>
      <AreaChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
        <defs>
          <linearGradient id="ddGrad" x1="0" y1="0" x2="0" y2="1">
            <stop offset="5%" stopColor="#FF3333" stopOpacity={0.3} />
            <stop offset="95%" stopColor="#FF3333" stopOpacity={0.02} />
          </linearGradient>
        </defs>
        <CartesianGrid strokeDasharray="" stroke="#1a1a1a" vertical={false} />
        <XAxis
          dataKey="date"
          tickLine={false}
          axisLine={{ stroke: '#2a2a2a' }}
          tick={{ fill: '#555', fontSize: 10, fontFamily: 'var(--font-mono)' }}
          tickFormatter={(v) => v.slice(5)}
          interval="preserveStartEnd"
        />
        <YAxis
          tickLine={false}
          axisLine={false}
          tick={{ fill: '#555', fontSize: 10, fontFamily: 'var(--font-mono)' }}
          tickFormatter={(v) => `${v.toFixed(1)}%`}
          width={50}
        />
        <Tooltip content={<BBTooltip />} />
        <ReferenceLine y={limitPct} stroke="#FF3333" strokeDasharray="3 2" label={{
          value: `LIMIT ${limitPct}%`,
          fill: '#FF3333',
          fontSize: 9,
          fontFamily: 'var(--font-mono)',
          fontWeight: 700,
        }} />
        <ReferenceLine y={0} stroke="#333" />
        <Area
          type="monotone"
          dataKey="drawdown"
          stroke="#FF3333"
          strokeWidth={1.2}
          fill="url(#ddGrad)"
          dot={false}
        />
      </AreaChart>
    </ResponsiveContainer>
  );
}
