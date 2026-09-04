'use client';
import React from 'react';

export default function LoadingSkeleton({
  height = '120px',
  count = 1,
  label = 'LOADING DATA...',
}: {
  height?: string;
  count?: number;
  label?: string;
}) {
  return (
    <>
      {Array.from({ length: count }).map((_, i) => (
        <div
          key={i}
          style={{
            height,
            background: '#0a0a0a',
            border: '1px solid #1a1a1a',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            gap: '0.5rem',
            fontFamily: 'var(--font-mono)',
            fontSize: '0.65rem',
            color: '#333',
            marginBottom: i < count - 1 ? '4px' : 0,
          }}
        >
          <div
            style={{
              width: '12px',
              height: '12px',
              border: '2px solid #222',
              borderTopColor: '#FF6600',
              borderRadius: '50%',
              animation: 'bbSpin 0.7s linear infinite',
            }}
          />
          <span style={{ color: '#444', fontWeight: 700, letterSpacing: '0.06em' }}>{label}</span>
        </div>
      ))}
    </>
  );
}
