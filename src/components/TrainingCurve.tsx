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
import { TrainingCurvePoint } from '@/lib/types';

export default function TrainingCurve({
  data,
  height = 240
}: {
  data: TrainingCurvePoint[];
  height?: number;
}) {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <LineChart data={data} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" vertical={false} />
          <XAxis
            dataKey="epoch"
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickLine={false}
          />
          <YAxis
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickLine={false}
            tickFormatter={(v) => v.toFixed(3)}
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
          />
          <Legend wrapperStyle={{ fontFamily: 'var(--font-mono)', fontSize: '11px', paddingTop: '6px' }} />
          <Line
            type="monotone"
            dataKey="train_loss"
            name="Train Loss (MSE)"
            stroke="#38bdf8"
            strokeWidth={1.5}
            dot={false}
          />
          <Line
            type="monotone"
            dataKey="val_loss"
            name="Val Loss (Purged CV)"
            stroke="#f59e0b"
            strokeWidth={1.5}
            dot={false}
          />
        </LineChart>
      </ResponsiveContainer>
    </div>
  );
}
