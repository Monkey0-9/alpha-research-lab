export interface ChartTooltipProps {
  active?: boolean;
  payload?: Array<{
    name?: string;
    value?: string | number;
    color?: string;
    dataKey?: string;
    payload?: Record<string, unknown>;
  }>;
  label?: string | number;
}

export interface AlphaCandidate {
  id: string;
  name: string;
  category: string;
  ic: number;
  ic_ir: number;
  sharpe: number;
  turnover: number;
  decay_days: number;
  capacity: string;
  status: 'passed' | 'rejected' | 'candidate';
  description?: string;
}

export interface MetricCardData {
  label: string;
  value: string | number;
  change?: string;
  positive?: boolean;
  subtext?: string;
}

export interface TimeSeriesPoint {
  date: string;
  [key: string]: string | number;
}
