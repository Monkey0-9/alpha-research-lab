'use client';
import React, { Component, ErrorInfo, ReactNode } from 'react';

export default class ErrorBoundary extends Component<
  { children: ReactNode; fallbackTitle?: string },
  { hasError: boolean; error: Error | null }
> {
  public state = { hasError: false, error: null as Error | null };

  public static getDerivedStateFromError(error: Error) {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('QuantAlpha Terminal Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div style={{
          background: '#0a0000', border: '2px solid #CC2222',
          padding: '1.5rem', textAlign: 'center',
          fontFamily: 'var(--font-mono)',
        }}>
          <div style={{ color: '#FF3333', fontSize: '1rem', fontWeight: 900, marginBottom: '0.5rem', letterSpacing: '0.04em' }}>
            ⚠ {(this.props.fallbackTitle || 'PIPELINE COMPONENT ERROR').toUpperCase()}
          </div>
          <div style={{ color: '#666', fontSize: '0.65rem', marginBottom: '1rem', maxWidth: '500px', margin: '0 auto 1rem' }}>
            {this.state.error?.message || 'NUMERICAL ERROR OR UNDEFINED TELEMETRY FRAME.'}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              background: '#CC2222', border: 'none', color: '#fff',
              padding: '0.3rem 0.85rem', fontSize: '0.65rem',
              fontFamily: 'var(--font-mono)', cursor: 'pointer',
              fontWeight: 900, letterSpacing: '0.06em',
            }}
          >
            ↺ REINITIALIZE SUB-PIPELINE
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
