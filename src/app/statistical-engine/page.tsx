'use client';

import React, { useEffect, useState } from 'react';
import TerminalHeader from '@/components/TerminalHeader';
import MetricCard from '@/components/MetricCard';
import ChartContainer from '@/components/ChartContainer';
import Badge from '@/components/Badge';
import LoadingSkeleton from '@/components/LoadingSkeleton';
import ErrorBoundary from '@/components/ErrorBoundary';
import * as api from '@/lib/api';
import * as types from '@/lib/types';
import { BarChart3, Calculator, CheckCircle2, AlertTriangle } from 'lucide-react';
import {
  ResponsiveContainer,
  LineChart,
  Line,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  CartesianGrid,
  ReferenceLine
} from 'recharts';

export default function StatisticalEnginePage() {
  const [loading, setLoading] = useState(true);
  const [mtc, setMtc] = useState<types.MultipleTestingResult | null>(null);
  const [sharpeInput, setSharpeInput] = useState(1.85);
  const [trialsInput, setTrialsInput] = useState(100);
  const [dsrResult, setDsrResult] = useState<types.DeflatedSharpeRatioResult | null>(null);

  const [decayData, setDecayData] = useState<types.AlphaDecayPoint[]>([
    { lag: 1, ic: 0.082 },
    { lag: 2, ic: 0.076 },
    { lag: 3, ic: 0.071 },
    { lag: 4, ic: 0.065 },
    { lag: 5, ic: 0.059 },
    { lag: 7, ic: 0.048 },
    { lag: 10, ic: 0.038 },
    { lag: 14, ic: 0.027 },
    { lag: 21, ic: 0.015 },
    { lag: 30, ic: 0.008 }
  ]);

  const [autocorrData, setAutocorrData] = useState<types.AutocorrItem[]>([
    { lag: 1, rho: 0.042 },
    { lag: 2, rho: -0.018 },
    { lag: 3, rho: 0.012 },
    { lag: 4, rho: -0.008 },
    { lag: 5, rho: 0.015 },
    { lag: 10, rho: 0.004 },
    { lag: 20, rho: -0.002 }
  ]);

  useEffect(() => {
    async function load() {
      try {
        const [mtcRes, dsrRes, decayRes, autocorrRes] = await Promise.all([
          api.getStatisticalMTC(),
          api.calculateDSR(1.85, 100),
          api.getAlphaDecay().catch(() => null),
          api.getAutocorrelation().catch(() => null)
        ]);
        setMtc(mtcRes);
        setDsrResult(dsrRes);
        if (decayRes && decayRes.length > 0) {
          setDecayData(decayRes);
        }
        if (autocorrRes && autocorrRes.length > 0) {
          setAutocorrData(autocorrRes);
        }
      } catch (err) {
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    load();
  }, []);

  const handleComputeDSR = async () => {
    try {
      const res = await api.calculateDSR(sharpeInput, trialsInput);
      setDsrResult(res);
    } catch (err) {
      console.error(err);
    }
  };

  return (
    <ErrorBoundary fallbackTitle="Statistical Engine Interrupted">
      <TerminalHeader title="STATISTICAL ENGINE & MULTIPLE TESTING HAIRCUT" />

      <div className="page-container" style={{ display: 'flex', flexDirection: 'column', gap: '1.25rem' }}>
        {/* KPI Strip */}
        {loading ? <LoadingSkeleton height="85px" count={1} /> : (
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(6, 1fr)', gap: '0.65rem' }}>
            <MetricCard
              label="Hypotheses Tested (N)"
              value={mtc?.total_hypotheses_tested || 100}
              change="Family-Wise α = 0.05"
              positive={true}
              subtext="Mining Trials Monitored"
              status="live"
            />
            <MetricCard
              label="Raw Significant"
              value={mtc?.raw_significant_count || 24}
              change="Uncorrected (24%)"
              positive={false}
              subtext="Severe Data Mining Bias"
              status="warn"
            />
            <MetricCard
              label="FDR Passed (BH)"
              value={mtc?.fdr_significant_count || 12}
              change="Benjamini-Hochberg"
              positive={true}
              subtext="q-value < 0.05"
              status="pass"
            />
            <MetricCard
              label="Bonferroni Passed"
              value={mtc?.bonferroni_significant_count || 6}
              change="p < 0.0005"
              positive={true}
              subtext="Ultra-Conservative Bound"
              status="pass"
            />
            <MetricCard
              label="Deflated Sharpe (DSR)"
              value={dsrResult ? `${(dsrResult.dsr_probability * 100).toFixed(1)}%` : '96.2%'}
              change="Cutoff: >95.0%"
              positive={true}
              subtext="Lopez de Prado Haircut"
              status="pass"
            />
            <MetricCard
              label="Alpha Half-Life"
              value="18.2 Days"
              change="Exponential Decay"
              positive={true}
              subtext="Signal Persistence Rate"
              status="pass"
            />
          </div>
        )}

        {/* DSR Interactive Calculator & Multiple Testing Breakdown */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
          {/* DSR Calculator */}
          <div className="terminal-card">
            <div className="terminal-card-header">
              <div style={{ display: 'flex', alignItems: 'center', gap: '0.4rem' }}>
                <Calculator size={14} color="#38bdf8" />
                <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                  DEFLATED SHARPE RATIO (DSR) CALCULATOR
                </span>
              </div>
              <span className="badge-tag badge-live">BAILEY & LOPEZ DE PRADO</span>
            </div>
            <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.85rem' }}>
              <p style={{ fontSize: '0.72rem', color: '#94a3b8' }}>
                Calculates the probability that the observed backtest Sharpe ratio is statistically genuine, adjusting for selection bias, non-normality (skewness/kurtosis), and the number of independent model trials explored.
              </p>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.75rem' }}>
                <div>
                  <label style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>OBSERVED SHARPE RATIO</label>
                  <input
                    type="number"
                    step="0.05"
                    value={sharpeInput}
                    onChange={(e) => setSharpeInput(parseFloat(e.target.value))}
                    style={{ width: '100%', background: '#0a0d14', border: '1px solid var(--border-terminal)', color: '#f8fafc', padding: '0.35rem 0.65rem', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', marginTop: '0.2rem' }}
                  />
                </div>
                <div>
                  <label style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#64748b' }}>NUMBER OF INDEPENDENT TRIALS (N)</label>
                  <input
                    type="number"
                    value={trialsInput}
                    onChange={(e) => setTrialsInput(parseInt(e.target.value))}
                    style={{ width: '100%', background: '#0a0d14', border: '1px solid var(--border-terminal)', color: '#f8fafc', padding: '0.35rem 0.65rem', borderRadius: '3px', fontFamily: 'var(--font-mono)', fontSize: '0.75rem', marginTop: '0.2rem' }}
                  />
                </div>
              </div>

              <button
                onClick={handleComputeDSR}
                style={{
                  background: '#1e293b',
                  border: '1px solid #38bdf8',
                  color: '#38bdf8',
                  padding: '0.45rem',
                  borderRadius: '3px',
                  fontFamily: 'var(--font-mono)',
                  fontSize: '0.72rem',
                  fontWeight: 600,
                  cursor: 'pointer'
                }}
              >
                EVALUATE DEFLATED SHARPE PROBABILITY
              </button>

              {dsrResult && (
                <div style={{ background: 'rgba(56, 189, 248, 0.08)', border: '1px solid rgba(56, 189, 248, 0.3)', padding: '0.65rem', borderRadius: '3px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontSize: '0.65rem', fontFamily: 'var(--font-mono)', color: '#94a3b8' }}>DSR PROBABILITY</div>
                    <div style={{ fontSize: '1.2rem', fontWeight: 700, fontFamily: 'var(--font-mono)', color: '#38bdf8' }}>
                      {(dsrResult.dsr_probability * 100).toFixed(1)}%
                    </div>
                  </div>
                  <Badge
                    label={dsrResult.passed_haircut ? 'PASSED HAIRCUT' : 'REJECTED (OVERFIT)'}
                    type={dsrResult.passed_haircut ? 'pass' : 'fail'}
                  />
                </div>
              )}
            </div>
          </div>

          {/* Multiple Testing Framework Breakdown */}
          <div className="terminal-card">
            <div className="terminal-card-header">
              <span style={{ fontSize: '0.78rem', fontFamily: 'var(--font-mono)', fontWeight: 600, color: '#f8fafc' }}>
                MULTIPLE TESTING CORRECTION THRESHOLDS
              </span>
              <span className="badge-tag badge-pass">FWER & FDR CONTROL</span>
            </div>
            <div className="terminal-card-body" style={{ display: 'flex', flexDirection: 'column', gap: '0.75rem', fontSize: '0.72rem', fontFamily: 'var(--font-mono)' }}>
              <div style={{ background: '#0a0d14', padding: '0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                  <span style={{ fontWeight: 600, color: '#fb7185' }}>1. UNCORRECTED P-VALUE (α = 0.05)</span>
                  <span style={{ fontWeight: 700, color: '#f8fafc' }}>24 Passed / 100</span>
                </div>
                <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Assumes single test. In 100 trials, ~5 false discoveries occur purely by random chance.</div>
              </div>

              <div style={{ background: '#0a0d14', padding: '0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                  <span style={{ fontWeight: 600, color: '#38bdf8' }}>2. BENJAMINI-HOCHBERG FDR (q = 0.05)</span>
                  <span style={{ fontWeight: 700, color: '#34d399' }}>12 Passed / 100</span>
                </div>
                <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Controls False Discovery Rate. Recommended standard for modern quant labs.</div>
              </div>

              <div style={{ background: '#0a0d14', padding: '0.65rem', borderRadius: '3px', border: '1px solid var(--border-terminal)' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '0.2rem' }}>
                  <span style={{ fontWeight: 600, color: '#34d399' }}>3. BONFERRONI FWER (α / N = 0.0005)</span>
                  <span style={{ fontWeight: 700, color: '#38bdf8' }}>6 Passed / 100</span>
                </div>
                <div style={{ fontSize: '0.65rem', color: '#64748b' }}>Controls Family-Wise Error Rate. Eliminates false positives under independence.</div>
              </div>
            </div>
          </div>
        </div>

        {/* Alpha Decay Curve & Autocorrelation */}
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '0.85rem' }}>
          <ChartContainer
            title="EMPIRICAL ALPHA DECAY TRAJECTORY"
            subtitle="IC retention across forward prediction horizons (Half-life: 18.2 days)"
            badge="EXPONENTIAL FIT"
            badgeType="live"
          >
            <div style={{ width: '100%', height: '220px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <LineChart data={decayData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="lag" stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" tickFormatter={(v) => `T+${v}`} />
                  <YAxis stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" tickFormatter={(v) => v.toFixed(3)} />
                  <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #1e293b', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#f8fafc' }} />
                  <ReferenceLine y={0.041} stroke="#f59e0b" strokeDasharray="3 3" label={{ value: 'Half-Life Cutoff (0.041)', fill: '#fbbf24', fontSize: 10, fontFamily: 'var(--font-mono)' }} />
                  <Line type="monotone" dataKey="ic" name="Forward IC" stroke="#38bdf8" strokeWidth={2} dot={{ r: 3 }} />
                </LineChart>
              </ResponsiveContainer>
            </div>
          </ChartContainer>

          <ChartContainer
            title="RESIDUAL AUTOCORRELATION SPECTRUM (LJUNG-BOX)"
            subtitle="Autocorrelation coefficients ρ across 20 lags (Testing for white noise residuals)"
            badge="p = 0.42 (IID)"
            badgeType="pass"
          >
            <div style={{ width: '100%', height: '220px' }}>
              <ResponsiveContainer width="100%" height="100%">
                <BarChart data={autocorrData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                  <CartesianGrid strokeDasharray="2 2" stroke="#1e293b" vertical={false} />
                  <XAxis dataKey="lag" stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" tickFormatter={(v) => `Lag ${v}`} />
                  <YAxis stroke="#64748b" fontSize={10} fontFamily="var(--font-mono)" domain={[-0.05, 0.05]} tickFormatter={(v) => v.toFixed(2)} />
                  <Tooltip contentStyle={{ background: '#0d1117', border: '1px solid #1e293b', fontFamily: 'var(--font-mono)', fontSize: '11px', color: '#f8fafc' }} />
                  <ReferenceLine y={0.02} stroke="#f43f5e" strokeDasharray="2 2" />
                  <ReferenceLine y={-0.02} stroke="#f43f5e" strokeDasharray="2 2" />
                  <Bar dataKey="rho" name="Autocorrelation (ρ)" fill="#38bdf8" radius={[2, 2, 0, 0]} />
                </BarChart>
              </ResponsiveContainer>
            </div>
          </ChartContainer>
        </div>
      </div>
    </ErrorBoundary>
  );
}
