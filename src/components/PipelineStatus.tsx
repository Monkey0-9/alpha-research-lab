'use client';

import React from 'react';
import { PIPELINE_STAGES } from '@/lib/constants';
import Badge from './Badge';

export default function PipelineStatus() {
  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.5rem', width: '100%' }}>
      {PIPELINE_STAGES.map((s) => (
        <div
          key={s.id}
          style={{
            background: '#0a0d14',
            border: '1px solid var(--border-terminal)',
            padding: '0.5rem 0.65rem',
            borderRadius: '3px'
          }}
        >
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
            <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
              {s.label}
            </span>
            <Badge label={s.status} type={s.status === 'LIVE' ? 'live' : 'pass'} size="sm" />
          </div>
          <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', fontSize: '0.62rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>
            <span>LATENCY: <strong style={{ color: '#34d399' }}>{s.latency}</strong></span>
            <span>{Object.entries(s).filter(([k]) => !['id', 'label', 'status', 'latency'].includes(k)).map(([k, v]) => `${k.toUpperCase()}: ${v}`).join(' ')}</span>
          </div>
        </div>
      ))}
    </div>
  );
}
