'use client';

import React from 'react';
import DataTable, { Column } from './DataTable';
import Badge from './Badge';
import { PortfolioHoldingItem } from '@/lib/types';
import { formatCurrency, formatPercent } from '@/lib/utils';

export default function PositionTable({ holdings }: { holdings: PortfolioHoldingItem[] }) {
  const columns: Column<PortfolioHoldingItem>[] = [
    {
      key: 'ticker',
      header: 'Ticker',
      render: (r) => (
        <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
          <span style={{ fontWeight: 700, color: '#f8fafc' }}>{r.ticker}</span>
          <Badge label={r.side} type={r.side === 'LONG' ? 'pass' : 'fail'} size="sm" />
        </div>
      )
    },
    {
      key: 'weight_pct',
      header: 'Weight',
      align: 'right',
      render: (r) => <span className="tabular-nums">{r.weight_pct.toFixed(2)}%</span>
    },
    {
      key: 'shares',
      header: 'Quantity',
      align: 'right',
      render: (r) => <span className="tabular-nums">{r.shares.toLocaleString()}</span>
    },
    {
      key: 'entry_price',
      header: 'Entry Price',
      align: 'right',
      render: (r) => <span className="tabular-nums">{formatCurrency(r.entry_price)}</span>
    },
    {
      key: 'market_price',
      header: 'Mark Price',
      align: 'right',
      render: (r) => <span className="tabular-nums" style={{ color: '#f8fafc', fontWeight: 600 }}>{formatCurrency(r.market_price)}</span>
    },
    {
      key: 'market_value',
      header: 'Notional Value',
      align: 'right',
      render: (r) => <span className="tabular-nums">{formatCurrency(r.market_value, 0)}</span>
    },
    {
      key: 'unrealized_pnl',
      header: 'Unrealized PnL',
      align: 'right',
      render: (r) => {
        const isPos = r.unrealized_pnl >= 0;
        return (
          <span
            className="tabular-nums"
            style={{ fontWeight: 700, color: isPos ? '#34d399' : '#fb7185' }}
          >
            {formatCurrency(r.unrealized_pnl, 2)}
          </span>
        );
      }
    },
    {
      key: 'marginal_risk_pct',
      header: 'Risk Contribution',
      align: 'right',
      render: (r) => <span className="tabular-nums">{r.marginal_risk_pct.toFixed(1)}%</span>
    }
  ];

  return <DataTable columns={columns} data={holdings} searchKey="ticker" searchPlaceholder="Filter ticker..." pageSize={10} />;
}
