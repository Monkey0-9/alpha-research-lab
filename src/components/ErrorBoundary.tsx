'use client';

import React, { Component, ErrorInfo, ReactNode } from 'react';
import { AlertOctagon, RotateCcw } from 'lucide-react';

interface Props {
  children: ReactNode;
  fallbackTitle?: string;
}

interface State {
  hasError: boolean;
  error: Error | null;
}

export default class ErrorBoundary extends Component<Props, State> {
  public state: State = {
    hasError: false,
    error: null
  };

  public static getDerivedStateFromError(error: Error): State {
    return { hasError: true, error };
  }

  public componentDidCatch(error: Error, errorInfo: ErrorInfo) {
    console.error('QuantAlpha Terminal Error:', error, errorInfo);
  }

  public render() {
    if (this.state.hasError) {
      return (
        <div className="terminal-card" style={{ padding: '1.5rem', textAlign: 'center', borderColor: '#f43f5e' }}>
          <div style={{ display: 'flex', justifyContent: 'center', marginBottom: '0.75rem' }}>
            <AlertOctagon size={28} color="#f43f5e" />
          </div>
          <div style={{ fontSize: '0.95rem', fontWeight: 600, color: '#f8fafc', fontFamily: 'var(--font-mono)', marginBottom: '0.35rem' }}>
            {this.props.fallbackTitle || 'Quantitative Pipeline Component Interrupted'}
          </div>
          <div style={{ fontSize: '0.72rem', color: '#94a3b8', fontFamily: 'var(--font-mono)', marginBottom: '1rem', maxWidth: '500px', margin: '0 auto 1rem auto' }}>
            {this.state.error?.message || 'A numerical error or undefined telemetry frame occurred.'}
          </div>
          <button
            onClick={() => this.setState({ hasError: false, error: null })}
            style={{
              display: 'inline-flex',
              alignItems: 'center',
              gap: '0.4rem',
              background: '#161f33',
              border: '1px solid #38bdf8',
              color: '#38bdf8',
              padding: '0.35rem 0.85rem',
              borderRadius: '3px',
              fontSize: '0.72rem',
              fontFamily: 'var(--font-mono)',
              cursor: 'pointer',
              fontWeight: 600
            }}
          >
            <RotateCcw size={12} />
            <span>REINITIALIZE SUB-PIPELINE</span>
          </button>
        </div>
      );
    }
    return this.props.children;
  }
}
