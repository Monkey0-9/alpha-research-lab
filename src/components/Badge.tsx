'use client';
import React from 'react';

export default function Badge({
  label,
  type = 'neutral',
  size = 'md',
}: {
  label: string;
  type?: 'pass' | 'fail' | 'warn' | 'live' | 'paper' | 'neutral' | 'orange' | 'yellow' | 'cyan';
  size?: 'sm' | 'md' | 'lg';
}) {
  const bg: Record<string, string> = {
    pass:    '#00CC33',
    fail:    '#CC2222',
    warn:    '#CC8800',
    live:    '#FF6600',
    paper:   '#886600',
    neutral: '#333333',
    orange:  '#FF6600',
    yellow:  '#CCCC00',
    cyan:    '#0099CC',
  };
  const textColor = type === 'fail' ? '#ffffff' : '#000000';
  const fontSize = size === 'sm' ? '0.55rem' : size === 'lg' ? '0.7rem' : '0.6rem';
  const padding = size === 'sm' ? '0 0.25rem' : '0 0.4rem';

  return (
    <span style={{
      background: bg[type] || '#333',
      color: textColor,
      fontSize,
      fontWeight: 900,
      padding,
      height: size === 'lg' ? '18px' : '15px',
      display: 'inline-flex',
      alignItems: 'center',
      fontFamily: 'var(--font-mono)',
      letterSpacing: '0.05em',
      textTransform: 'uppercase' as const,
      flexShrink: 0,
    }}>
      {label}
    </span>
  );
}
