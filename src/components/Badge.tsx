'use client';

import React from 'react';
import { getStatusBadgeClass } from '@/lib/utils';

interface BadgeProps {
  label: string;
  type?: 'pass' | 'warn' | 'fail' | 'live' | 'paper' | 'neutral' | string;
  size?: 'sm' | 'md';
}

export default function Badge({ label, type, size = 'md' }: BadgeProps) {
  const badgeClass = type ? `badge-${type.toLowerCase()}` : getStatusBadgeClass(label);
  const padding = size === 'sm' ? '0.1rem 0.35rem' : '0.15rem 0.5rem';
  const fontSize = size === 'sm' ? '0.62rem' : '0.68rem';

  return (
    <span className={`badge-tag ${badgeClass}`} style={{ padding, fontSize }}>
      {label}
    </span>
  );
}
