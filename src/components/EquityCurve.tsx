'use client';
import React from 'react';
import {
  ComposedChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, ReferenceLine, Legend
} from 'recharts';
import type { ChartTooltipProps } from '@/lib/types';

interface EquityCurveProps {
  data: Array<{ date: string; nav: number; benchmark: number }>;
  height?: number;
  benchmarkName?: string;
}

function BBTooltip({ active, payload, label }: ChartTooltipProps) {
  if (!active || !payload?.length) return null;
  return (
    <div style={{
      background: '#0a0500', border: '1px solid #FF6600',
      padding: '0.4rem 0.65rem', fontFamily: 'var(--font-mono)', fontSize: '0.65rem',
    }}>
      <div style={{ color: '#FF6600', fontWeight: 700, marginBottom: '0.3rem', borderBottom: '1px solid #2a1500', paddingBottom: '0.2rem' }}>
        {label}
      </div>
      {payload.map((p: any, i: number) => (
        <div key={i} style={{ display: 'flex', gap: '0.75rem', color: p.color || '#fff', justifyContent: 'space-between' }}>
          <span style={{ color: '#888' }}>{p.name?.toUpperCase()}</span>
          <span style={{ fontWeight: 700 }}>{typeof p.value === 'number' ? p.value.toFixed(4) : p.value}</span>
        </div>
      ))}
    </div>
  );
}

export default function EquityCurve({
  data,
  height = 280,
  benchmarkName = 'S&P 500',
}: EquityCurveProps) {
  if (!data || data.length === 0) {
    return (
      <div style={{ height, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#444', fontFamily: 'var(--font-mono)', fontSize: '0.65rem' }}>
        AWAITING NAV DATA STREAM...
      </div>
    );
  }

  return (
    <ResponsiveContainer width="100%" height={height}>
      <ComposedChart data={data} margin={{ top: 4, right: 8, bottom: 4, left: 0 }}>
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
          tickFormatter={(v) => v.toFixed(2)}
          width={50}
        />
        <Tooltip content={<BBTooltip />} />
        <ReferenceLine y={1.0} stroke="#333333" strokeDasharray="4 2" />
        <Legend
          wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: '0.62rem', color: '#666', paddingTop: '0.3rem' }}
          formatter={(value) => value.toUpperCase()}
        />
        <Line
          type="monotone"
          dataKey="nav"
          name="Portfolio NAV"
          stroke="#FF6600"
          dot={false}
          strokeWidth={1.5}
          activeDot={{ r: 3, fill: '#FF6600', stroke: '#000', strokeWidth: 1 }}
        />
        <Line
          type="monotone"
          dataKey="benchmark"
          name={benchmarkName}
          stroke="#444444"
          dot={false}
          strokeWidth={1}
          strokeDasharray="4 2"
          activeDot={{ r: 3, fill: '#444', stroke: '#000' }}
        />
      </ComposedChart>
    </ResponsiveContainer>
  );
}
