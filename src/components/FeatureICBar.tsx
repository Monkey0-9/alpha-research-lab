'use client';
import React from 'react';
import {
  ResponsiveContainer, BarChart, Bar, XAxis, YAxis,
  Tooltip, CartesianGrid, Cell, ReferenceLine
} from 'recharts';

interface FeatureICData {
  feature: string;
  ic: number;
  t_stat: number;
}

export default function FeatureICBar({
  data,
  height = 300,
  threshold = 0.05,
}: {
  data: FeatureICData[];
  height?: number;
  threshold?: number;
}) {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart data={data} layout="vertical" margin={{ top: 5, right: 20, left: 40, bottom: 5 }}>
          <CartesianGrid strokeDasharray="" stroke="#1a1a1a" horizontal={false} />
          <XAxis
            type="number"
            tick={{ fill: '#555', fontSize: 9, fontFamily: 'var(--font-mono)' }}
            axisLine={{ stroke: '#2a2a2a' }}
            tickLine={false}
            tickFormatter={(v) => v.toFixed(2)}
          />
          <YAxis
            type="category"
            dataKey="feature"
            tick={{ fill: '#888', fontSize: 9, fontFamily: 'var(--font-mono)' }}
            width={120}
            tickLine={false}
            axisLine={false}
          />
          <Tooltip
            contentStyle={{
              background: '#0a0500', border: '1px solid #FF6600',
              fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#fff',
            }}
            formatter={(val: any, name: any, item: any) => [
              `IC: ${Number(val).toFixed(3)} | t-stat: ${item.payload.t_stat?.toFixed(2) || '—'}`,
              'INFO COEFFICIENT'
            ]}
          />
          <ReferenceLine
            x={threshold}
            stroke="#00CC33"
            strokeDasharray="3 2"
            label={{ value: `|t|>2.0 CUTOFF`, fill: '#00CC33', fontSize: 9, fontFamily: 'var(--font-mono)', fontWeight: 700 }}
          />
          <ReferenceLine x={0} stroke="#333" />
          <Bar dataKey="ic" radius={[0, 0, 0, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.ic >= threshold ? '#FF6600' : entry.ic > 0 ? '#333333' : '#CC2222'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
