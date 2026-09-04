'use client';

import React from 'react';
import DataTable, { Column } from './DataTable';
import Badge from './Badge';
import { ModelComparisonItem } from '@/lib/types';

export default function ModelComparisonTable({ models }: { models: ModelComparisonItem[] }) {
  const columns: Column<ModelComparisonItem>[] = [
    {
      key: 'model_name',
      header: 'Model Architecture',
      render: (r) => (
        <div>
          <div style={{ fontWeight: 600, color: '#f8fafc' }}>{r.model_name}</div>
          <div style={{ fontSize: '0.65rem', color: '#64748b' }}>{r.family}</div>
        </div>
      )
    },
    {
      key: 'in_sample_sharpe',
      header: 'IS Sharpe',
      align: 'right',
      render: (r) => <span className="tabular-nums">{r.in_sample_sharpe.toFixed(2)}</span>
    },
    {
      key: 'out_of_sample_sharpe',
      header: 'OOS Sharpe',
      align: 'right',
      render: (r) => (
        <span
          className="tabular-nums"
          style={{
            fontWeight: 700,
            color: r.out_of_sample_sharpe >= 1.8 ? '#34d399' : r.out_of_sample_sharpe >= 1.5 ? '#38bdf8' : '#94a3b8'
          }}
        >
          {r.out_of_sample_sharpe.toFixed(2)}
        </span>
      )
    },
    {
      key: 'mean_ic',
      header: 'Mean IC',
      align: 'right',
      render: (r) => <span className="tabular-nums">{(r.mean_ic * 100).toFixed(1)}%</span>
    },
    {
      key: 'max_drawdown_pct',
      header: 'Max DD',
      align: 'right',
      render: (r) => <span className="tabular-nums" style={{ color: '#fb7185' }}>-{r.max_drawdown_pct.toFixed(1)}%</span>
    },
    {
      key: 'annual_turnover',
      header: 'Turnover',
      align: 'right',
      render: (r) => <span className="tabular-nums">{(r.annual_turnover * 100).toFixed(0)}%</span>
    },
    {
      key: 'training_time_sec',
      header: 'Fit Time',
      align: 'right',
      render: (r) => <span className="tabular-nums">{r.training_time_sec.toFixed(1)}s</span>
    },
    {
      key: 'status',
      header: 'Status',
      align: 'center',
      render: (r) => <Badge label={r.status} type={r.status === 'DEPLOYED' ? 'live' : r.status === 'BASELINE' ? 'neutral' : 'paper'} />
    }
  ];

  return <DataTable columns={columns} data={models} pageSize={10} />;
}
