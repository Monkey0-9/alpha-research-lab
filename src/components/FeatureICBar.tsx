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

interface FeatureICData {
  feature: string;
  ic: number;
  t_stat: number;
}

export default function FeatureICBar({
  data,
  height = 300,
  threshold = 0.05
}: {
  data: FeatureICData[];
  height?: number;
  threshold?: number;
}) {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <BarChart
          data={data}
          layout="vertical"
          margin={{ top: 5, right: 20, left: 40, bottom: 5 }}
        >
          <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" horizontal={false} />
          <XAxis
            type="number"
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickFormatter={(v) => v.toFixed(2)}
          />
          <YAxis
            type="category"
            dataKey="feature"
            stroke="#94a3b8"
            fontSize={10}
            fontFamily="var(--font-mono)"
            width={120}
            tickLine={false}
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
            formatter={(val: any, name: any, item: any) => [
              `IC: ${Number(val).toFixed(3)} (t-stat: ${item.payload.t_stat?.toFixed(2) || '2.4'})`,
              'Predictive Power'
            ]}
          />
          <ReferenceLine x={threshold} stroke="#34d399" strokeDasharray="3 3" label={{ value: `Target IC: ${threshold}`, fill: '#34d399', fontSize: 10, fontFamily: 'var(--font-mono)' }} />
          <ReferenceLine x={0} stroke="#475569" />
          <Bar dataKey="ic" radius={[0, 2, 2, 0]}>
            {data.map((entry, index) => (
              <Cell
                key={`cell-${index}`}
                fill={entry.ic >= threshold ? '#38bdf8' : entry.ic > 0 ? '#1e293b' : '#f43f5e'}
              />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
