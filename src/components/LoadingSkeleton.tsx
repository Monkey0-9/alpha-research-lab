'use client';

import React from 'react';

export default function LoadingSkeleton({ height = '120px', count = 1 }: { height?: string; count?: number }) {
  return (
    <div style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', width: '100%' }}>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={{
            height,
            width: '100%',
            background: 'linear-gradient(90deg, #0d1117 25%, #161f33 50%, #0d1117 75%)',
            backgroundSize: '200% 100%',
            animation: 'skeleton-pulse 1.6s infinite linear',
            borderRadius: '4px',
            border: '1px solid var(--border-terminal)'
          }}
        />
      ))}
      <style jsx>{`
        @keyframes skeleton-pulse {
          0% { background-position: 200% 0; }
          100% { background-position: -200% 0; }
        }
      `}</style>
    </div>
  );
}
