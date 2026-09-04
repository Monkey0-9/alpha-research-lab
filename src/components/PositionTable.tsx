'use client';
import React from 'react';
import DataTable, { Column } from './DataTable';
import { PortfolioHoldingItem } from '@/lib/types';
import { formatCurrency } from '@/lib/utils';

export default function PositionTable({ holdings }: { holdings: PortfolioHoldingItem[] }) {
  const columns: Column<PortfolioHoldingItem>[] = [
    {
      key: 'ticker',
      header: 'TICKER',
      width: '80px',
      render: (r) => (
        <span style={{ color: '#FF6600', fontWeight: 900, fontSize: '0.72rem' }}>{r.ticker}</span>
      )
    },
    {
      key: 'side',
      header: 'SIDE',
      width: '50px',
      render: (r) => (
        <span style={{
          background: r.side === 'LONG' ? '#00CC33' : '#CC2222',
          color: '#000',
          padding: '0 0.3rem',
          fontSize: '0.6rem',
          fontWeight: 900,
          fontFamily: 'var(--font-mono)',
        }}>
          {r.side}
        </span>
      )
    },
    {
      key: 'weight_pct',
      header: 'WT%',
      align: 'right',
      render: (r) => <span style={{ color: '#AAAAAA' }}>{r.weight_pct.toFixed(2)}%</span>
    },
    {
      key: 'shares',
      header: 'QTY',
      align: 'right',
      render: (r) => <span>{r.shares.toLocaleString()}</span>
    },
    {
      key: 'entry_price',
      header: 'ENTRY',
      align: 'right',
      render: (r) => <span style={{ color: '#666' }}>{formatCurrency(r.entry_price)}</span>
    },
    {
      key: 'market_price',
      header: 'MARK',
      align: 'right',
      render: (r) => <span style={{ color: '#FFFFFF', fontWeight: 700 }}>{formatCurrency(r.market_price)}</span>
    },
    {
      key: 'market_value',
      header: 'NOTIONAL',
      align: 'right',
      render: (r) => <span style={{ color: '#AAAAAA' }}>{formatCurrency(r.market_value, 0)}</span>
    },
    {
      key: 'unrealized_pnl',
      header: 'UNREAL P&L',
      align: 'right',
      render: (r) => {
        const isPos = r.unrealized_pnl >= 0;
        return (
          <span style={{ fontWeight: 700, color: isPos ? '#00FF41' : '#FF3333' }}>
            {isPos ? '+' : ''}{formatCurrency(r.unrealized_pnl, 0)}
          </span>
        );
      }
    },
    {
      key: 'marginal_risk_pct',
      header: 'RISK CONTRIB',
      align: 'right',
      render: (r) => (
        <span style={{ color: '#FF6600' }}>{r.marginal_risk_pct.toFixed(1)}%</span>
      )
    }
  ];

  return (
    <DataTable
      columns={columns}
      data={holdings}
      searchKey="ticker"
      searchPlaceholder="SEARCH TICKER..."
      pageSize={12}
    />
  );
}
