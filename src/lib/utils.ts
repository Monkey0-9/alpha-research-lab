/**
 * Institutional Quantitative Formatters & Utilities
 * Monospace Tabular Number Formatting, Status Badges, and Financial Math
 */

export function formatCurrency(value: number, decimals = 2): string {
  if (value === undefined || value === null || isNaN(value)) return '$0.00';
  const prefix = value < 0 ? '-$' : '$';
  return `${prefix}${Math.abs(value).toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  })}`;
}

export function formatPercent(value: number, decimals = 2, showSign = true): string {
  if (value === undefined || value === null || isNaN(value)) return '0.00%';
  const sign = showSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(decimals)}%`;
}

export function formatBps(value: number, showSign = true): string {
  if (value === undefined || value === null || isNaN(value)) return '0.0 bps';
  const sign = showSign && value > 0 ? '+' : '';
  return `${sign}${value.toFixed(1)} bps`;
}

export function formatNumber(value: number, decimals = 2): string {
  if (value === undefined || value === null || isNaN(value)) return '0.00';
  return value.toLocaleString('en-US', {
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals
  });
}

export function formatCompact(value: number): string {
  if (value === undefined || value === null || isNaN(value)) return '0';
  if (Math.abs(value) >= 1_000_000_000) {
    return `${(value / 1_000_000_000).toFixed(2)}B`;
  }
  if (Math.abs(value) >= 1_000_000) {
    return `${(value / 1_000_000).toFixed(2)}M`;
  }
  if (Math.abs(value) >= 1_000) {
    return `${(value / 1_000).toFixed(1)}K`;
  }
  return value.toString();
}

export function getStatusBadgeClass(status: string): string {
  const s = status.toUpperCase();
  if (s.includes('PASS') || s === 'ACTIVE' || s === 'HEALTHY' || s === 'LIVE') {
    return 'badge-pass';
  }
  if (s.includes('WARN') || s === 'DEGRADING' || s === 'TESTING' || s === 'SYNCING') {
    return 'badge-warn';
  }
  if (s.includes('FAIL') || s === 'DECOMMISSION_ALERT' || s === 'CRITICAL' || s === 'REJECTED') {
    return 'badge-fail';
  }
  if (s === 'PAPER' || s === 'CANDIDATE') {
    return 'badge-paper';
  }
  return 'badge-neutral';
}

export function getDeltaColor(val: number): string {
  if (val > 0) return 'text-emerald-400';
  if (val < 0) return 'text-rose-400';
  return 'text-slate-400';
}
