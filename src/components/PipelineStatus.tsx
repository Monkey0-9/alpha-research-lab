'use client';
import React, { useEffect, useState } from 'react';
import { PIPELINE_STAGES } from '@/lib/constants';
import * as api from '@/lib/api';

const STATUS_STYLE: Record<string, { bg: string; color: string }> = {
  LIVE:      { bg: '#FF6600', color: '#000' },
  PASS:      { bg: '#00CC33', color: '#000' },
  HEALTHY:   { bg: '#00CC33', color: '#000' },
  RUNNING:   { bg: '#FFFF00', color: '#000' },
  SYNCING:   { bg: '#0099CC', color: '#000' },
  PENDING:   { bg: '#333333', color: '#AAAAAA' },
  WARNING:   { bg: '#FF9900', color: '#000' },
  ERROR:     { bg: '#CC2222', color: '#fff' },
};

export default function PipelineStatus() {
  const [stages, setStages] = useState(PIPELINE_STAGES);

  useEffect(() => {
    async function loadPipeline() {
      try {
        const liveMods = await api.getDashboardPipeline();
        if (Array.isArray(liveMods) && liveMods.length > 0) {
          setStages((prev) =>
            prev.map((s, idx) => {
              const live = liveMods[idx];
              if (!live) return s;
              return {
                ...s,
                status: live.status === 'HEALTHY' ? 'LIVE' : live.status,
                latency: `${live.latency_ms ? live.latency_ms.toFixed(1) : '12.5'}ms`,
                label: live.name || s.label
              };
            })
          );
        }
      } catch (err) {
        // Retain baseline stages if offline
      }
    }
    loadPipeline();
  }, []);

  return (
    <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '3px', width: '100%' }}>
      {stages.map((s, idx) => {
        const sty = STATUS_STYLE[s.status] || STATUS_STYLE.PASS;
        return (
          <div
            key={s.id}
            style={{
              background: '#0a0a0a',
              border: '1px solid #2a2a2a',
              padding: '0.45rem 0.55rem',
              position: 'relative',
              fontFamily: 'var(--font-mono)',
            }}
          >
            {/* Stage number badge */}
            <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '0.25rem' }}>
              <span style={{
                background: '#1a1a1a', color: '#555',
                fontSize: '0.55rem', fontWeight: 700,
                padding: '0 0.25rem',
              }}>
                S{String(idx + 1).padStart(2, '0')}
              </span>
              <span style={{
                background: sty.bg, color: sty.color,
                fontSize: '0.55rem', fontWeight: 900,
                padding: '0 0.3rem',
              }}>
                {s.status}
              </span>
            </div>

            {/* Stage label */}
            <div style={{
              fontSize: '0.65rem', fontWeight: 700,
              color: '#FFFFFF', letterSpacing: '0.01em',
              marginBottom: '0.2rem',
              lineHeight: 1.2,
            }}>
              {s.label.toUpperCase()}
            </div>

            {/* Latency */}
            <div style={{ fontSize: '0.58rem', color: '#444' }}>
              LAT: <span style={{ color: '#00FF41', fontWeight: 700 }}>{s.latency}</span>
            </div>

            {/* Connection arrow */}
            {idx < PIPELINE_STAGES.length - 1 && (
              <div style={{
                position: 'absolute', right: '-8px', top: '50%',
                transform: 'translateY(-50%)',
                color: '#FF6600', fontSize: '0.7rem',
                zIndex: 1, fontWeight: 900,
              }}>
                ►
              </div>
            )}
          </div>
        );
      })}
    </div>
  );
}
