'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import ChartContainer from '@/components/ChartContainer';
import ModelComparisonTable from '@/components/ModelComparisonTable';
import TrainingCurve from '@/components/TrainingCurve';
import EnsembleBuilder from '@/components/EnsembleBuilder';
import Badge from '@/components/Badge';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import { Brain, Layers, Cpu, ShieldCheck } from 'lucide-react';

export default function ModelLabPage() {
  const [loading, setLoading] = useState(true);
  const [models, setModels] = useState<types.ModelComparisonItem[]>([]);
  const [trainingCurves, setTrainingCurves] = useState<types.TrainingCurvePoint[]>([]);

  useEffect(() => {
    async function load() {
      try {
        const res = await api.getModelComparison();
        setModels(res.models);

        // Synthetic training loss curve across 30 epochs
        const curves = Array.from({ length: 30 }, (_, i) => ({
          epoch: i + 1,
          train_loss: parseFloat((0.25 * Math.exp(-i * 0.12) + 0.042 + (Math.random() - 0.5) * 0.004).toFixed(4)),
          val_loss: parseFloat((0.27 * Math.exp(-i * 0.10) + 0.051 + (Math.random() - 0.5) * 0.006).toFixed(4)),
          val_ic: parseFloat((0.03 + 0.06 * (1 - Math.exp(-i * 0.15))).toFixed(3))
        }));
        setTrainingCurves(curves);
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  return (
    <ErrorBoundary fallbackTitle="Model Research Lab Interrupted">
      <TerminalHeader title="MODULE 05 // MODEL RESEARCH & ML ENSEMBLE LAB" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* KPI Strip */}
        {loading ? <LoadingSkeleton height="85px" count={1} /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard
              label="Best Single Model"
              value="1.94"
              change="LightGBM OOS"
              positive={true}
              subtext="Out-of-Sample Sharpe"
              status="pass"
            />
            <MetricCard
              label="Ensemble Sharpe"
              value="2.14"
              change="+0.20 Lift"
              positive={true}
              subtext="Diversified Meta-Model"
              status="live"
            />
            <MetricCard
              label="Ensemble Mean IC"
              value="0.104"
              change="IR: 2.35"
              positive={true}
              subtext="Cross-Sectional Rank IC"
              status="pass"
            />
            <MetricCard
              label="Max DD (Ensemble)"
              value="-6.8%"
              change="Limit: -12.0%"
              positive={false}
              subtext="Controlled via Vol Scaling"
              status="pass"
            />
            <MetricCard
              label="Annual Turnover"
              value="24%"
              change="Low Friction"
              positive={true}
              subtext="Monthly Rebalanced"
              status="pass"
            />
            <MetricCard
              label="Meta-Label Precision"
              value="68.4%"
              change="Bet Sizing Filter"
              positive={true}
              subtext="Lopez de Prado Secondary Model"
              status="pass"
            />
          </div>
        )}

        {/* Model Comparison Table */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <Brain size={14} color="#38bdf8" />
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                CROSS-ARCHITECTURE QUANTITATIVE MODEL LEADERBOARD
              </span>
            </div>
            <span className="badge-tag badge-live">OUT-OF-SAMPLE EVALUATED</span>
          </div>
          <div className="terminal-card-body">
            {loading ? <LoadingSkeleton height="180px" /> : (
              <ModelComparisonTable models={models} />
            )}
          </div>
        </div>

        {/* Training Curves & Ensemble Allocator */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
          <ChartContainer
            title="TRAINING & PURGED VALIDATION LOSS CONVERGENCE"
            subtitle="Gradient boosting iteration progression (Early stopping at 35 trees)"
            badge="EARLY STOPPING: BEST 28"
            badgeType="pass"
          >
            {loading ? <LoadingSkeleton height="240px" /> : (
              <TrainingCurve data={trainingCurves} height={240} />
            )}
          </ChartContainer>

          <EnsembleBuilder />
        </div>

        {/* Meta-Labeling & Triple Barrier Architecture */}
        <div className="terminal-card">
          <div className="terminal-card-header">
            <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
              <ShieldCheck size={14} color="#38bdf8" />
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                TRIPLE BARRIER METHOD & META-LABELING SYSTEM ARCHITECTURE
              </span>
            </div>
            <span className="badge-tag badge-live">DE PRADO META-SIZING</span>
          </div>
          <div className="terminal-card-body" style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '0.75rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
            <div style={{ background: '#0a0d14', padding: '0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
              <div style={{ color: '#38bdf8', fontWeight: 600, marginBottom: '0.2rem' }}>BARRIER 1: TAKE-PROFIT</div>
              <div style={{ color: '#94a3b8' }}>Dynamic volatility-adjusted upper horizontal barrier (+2.0σ trailing realized volatility).</div>
            </div>
            <div style={{ background: '#0a0d14', padding: '0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
              <div style={{ color: '#fb7185', fontWeight: 600, marginBottom: '0.2rem' }}>BARRIER 2: STOP-LOSS</div>
              <div style={{ color: '#94a3b8' }}>Lower horizontal risk barrier (-1.5σ) triggered automatically to truncate downside tail risk.</div>
            </div>
            <div style={{ background: '#0a0d14', padding: '0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
              <div style={{ color: '#fbbf24', fontWeight: 600, marginBottom: '0.2rem' }}>BARRIER 3: TIME-EXPIRY</div>
              <div style={{ color: '#94a3b8' }}>Vertical time horizon barrier (21 trading days). Positions unwound if neither price threshold hit.</div>
            </div>
          </div>
        </div>
      </div>
    </ErrorBoundary>
  );
}
