'use client';

import React from 'react';
import {
  ResponsiveContainer,
  RadarChart as RechartsRadarChart,
  PolarGrid,
  PolarAngleAxis,
  PolarRadiusAxis,
  Radar,
  Tooltip
} from 'recharts';

interface RadarDataPoint {
  attribute: string;
  value: number;
  benchmark?: number;
}

export default function RadarChart({
  data,
  height = 260
}: {
  data: RadarDataPoint[];
  height?: number;
}) {
  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <RechartsRadarChart data={data}>
          <PolarGrid stroke="#1e293b" />
          <PolarAngleAxis
            dataKey="attribute"
            stroke="#94a3b8"
            fontSize={10}
            fontFamily="var(--font-mono)"
          />
          <PolarRadiusAxis
            stroke="#64748b"
            fontSize={9}
            fontFamily="var(--font-mono)"
            tick={false}
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
          <Radar
            name="Portfolio Score"
            dataKey="value"
            stroke="#38bdf8"
            fill="#38bdf8"
            fillOpacity={0.3}
          />
          {data[0]?.benchmark !== undefined && (
            <Radar
              name="Benchmark (SPY)"
              dataKey="benchmark"
              stroke="#64748b"
              fill="#64748b"
              fillOpacity={0.15}
            />
          )}
        </RechartsRadarChart>
      </ResponsiveContainer>
    </div>
  );
}
