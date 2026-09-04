'use client';

import React from 'react';
import { ProductionAlertItem } from '@/lib/types';
import Badge from './Badge';
import { useStationStore } from '@/lib/store';
import { AlertCircle, Check } from 'lucide-react';

export default function AlertFeed({ alerts }: { alerts: ProductionAlertItem[] }) {
  const { acknowledgedAlerts, acknowledgeAlert } = useStationStore();

  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.45rem' }}>
      {alerts.map((a) => {
        const isAck = a.acknowledged || acknowledgedAlerts.includes(a.id);
        return (
          <div
            key={a.id}
            style={{
              display: 'flex',
              alignItems: 'center',
              justifyContent: 'space-between',
              gap: '0.75rem',
              background: '#0a0d14',
              border: `1px solid ${a.severity === 'CRITICAL' ? 'rgba(244, 63, 94, 0.4)' : a.severity === 'WARNING' ? 'rgba(245, 158, 11, 0.3)' : 'var(--border-terminal)'}`,
              padding: '0.45rem 0.75rem',
              borderRadius: '3px',
              opacity: isAck ? 0.6 : 1.0
            }}
          >
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.5rem' }}>
              <Badge
                label={a.severity}
                type={a.severity === 'CRITICAL' ? 'fail' : a.severity === 'WARNING' ? 'warn' : 'live'}
                size="sm"
              />
              <span style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>
                [{a.timestamp}]
              </span>
              <span style={{ fontSize: '0.68rem', fontFamily: 'var(--font-mono)', color: '#38bdf8', fontWeight: 600 }}>
                {a.category}:
              </span>
              <span style={{ fontSize: '0.72rem', color: '#f8fafc' }}>
                {a.message}
              </span>
            </div>

            <button
              onClick={() => acknowledgeAlert(a.id)}
              disabled={isAck}
              style={{
                background: isAck ? 'transparent' : '#161f33',
                border: `1px solid ${isAck ? 'var(--border-terminal)' : '#38bdf8'}`,
                color: isAck ? '#64748b' : '#38bdf8',
                padding: '0.15rem 0.45rem',
                borderRadius: '2px',
                fontSize: '0.62rem',
                fontFamily: 'var(--font-mono)',
                cursor: isAck ? 'default' : 'pointer',
                display: 'flex',
                alignItems: 'center',
                gap: '0.2rem'
              }}
            >
              <Check size={10} />
              <span>{isAck ? 'ACKNOWLEDGED' : 'ACK'}</span>
            </button>
          </div>
        );
      })}
    </div>
  );
}
