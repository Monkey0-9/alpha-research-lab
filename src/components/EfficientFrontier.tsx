'use client';

import React from 'react';
import {
  ResponsiveContainer,
  ScatterChart,
  Scatter,
  XAxis,
  YAxis,
  ZAxis,
  Tooltip,
  CartesianGrid,
  Cell,
  ReferenceLine
} from 'recharts';

interface PortfolioPoint {
  volatility: number;
  expected_return: number;
  sharpe_ratio: number;
  type?: 'optimal' | 'min_vol' | 'risk_parity' | 'simulated';
}

export default function EfficientFrontier({
  portfolios = [],
  height = 320
}: {
  portfolios?: PortfolioPoint[];
  height?: number;
}) {
  // Generate high-density frontier if empty
  const pts: PortfolioPoint[] = portfolios.length > 0 ? portfolios : (() => {
    const arr: PortfolioPoint[] = [];
    for (let i = 0; i < 120; i++) {
      const vol = 0.08 + Math.random() * 0.16;
      // Markowitz quadratic curve
      const frontierRet = 0.04 + 0.9 * Math.sqrt(Math.max(0, vol - 0.075));
      const ret = frontierRet * (0.65 + Math.random() * 0.35);
      const sharpe = (ret - 0.035) / vol;
      arr.push({
        volatility: parseFloat(vol.toFixed(4)),
        expected_return: parseFloat(ret.toFixed(4)),
        sharpe_ratio: parseFloat(sharpe.toFixed(2)),
        type: 'simulated'
      });
    }
    // Anchor Key Portfolios
    arr.push({ volatility: 0.118, expected_return: 0.198, sharpe_ratio: 1.38, type: 'optimal' });
    arr.push({ volatility: 0.082, expected_return: 0.095, sharpe_ratio: 0.73, type: 'min_vol' });
    arr.push({ volatility: 0.105, expected_return: 0.155, sharpe_ratio: 1.14, type: 'risk_parity' });
    return arr;
  })();

  const optimalPt = pts.find((p) => p.type === 'optimal') || pts[0];
  const minVolPt = pts.find((p) => p.type === 'min_vol') || pts[1];

  return (
    <div style={{ width: '100%', height }}>
      <ResponsiveContainer width="100%" height="100%">
        <ScatterChart margin={{ top: 10, right: 10, left: -10, bottom: 0 }}>
          <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" />
          <XAxis
            type="number"
            dataKey="volatility"
            name="Volatility"
            unit=""
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            label={{ value: 'Annualized Volatility (σ)', position: 'insideBottom', offset: -2, fill: '#64748b', fontSize: 10, fontFamily: 'var(--font-mono)' }}
          />
          <YAxis
            type="number"
            dataKey="expected_return"
            name="Expected Return"
            stroke="#64748b"
            fontSize={10}
            fontFamily="var(--font-mono)"
            tickFormatter={(v) => `${(v * 100).toFixed(0)}%`}
            label={{ value: 'Expected Return (E[R])', angle: -90, position: 'insideLeft', fill: '#64748b', fontSize: 10, fontFamily: 'var(--font-mono)' }}
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
            formatter={(val: any, name: any) => [
              name === 'sharpe_ratio' ? Number(val).toFixed(2) : `${(Number(val) * 100).toFixed(2)}%`,
              name === 'volatility' ? 'Vol (σ)' : name === 'expected_return' ? 'Expected Return' : 'Sharpe'
            ]}
          />
          <Scatter name="Portfolios" data={pts}>
            {pts.map((entry, index) => {
              let fill = '#334155';
              if (entry.type === 'optimal') fill = '#38bdf8';
              else if (entry.type === 'min_vol') fill = '#10b981';
              else if (entry.type === 'risk_parity') fill = '#8b5cf6';
              return <Cell key={`cell-${index}`} fill={fill} r={entry.type !== 'simulated' ? 6 : 2.5} />;
            })}
          </Scatter>
        </ScatterChart>
      </ResponsiveContainer>
    </div>
  );
}
