'use client';

import { useEffect, useState, useRef } from 'react';

export interface PortfolioTelemetry {
  type: string;
  timestamp: string;
  nav: number;
  cash: number;
  long_mv: number;
  short_mv: number;
  is_balanced: boolean;
  audit_entries: number;
}

export function usePortfolioWebSocket(initialNav: number = 2485000.0) {
  const [telemetry, setTelemetry] = useState<PortfolioTelemetry>({
    type: 'PORTFOLIO_TELEMETRY',
    timestamp: new Date().toISOString(),
    nav: initialNav,
    cash: initialNav * 0.15,
    long_mv: initialNav * 0.95,
    short_mv: initialNav * 0.10,
    is_balanced: true,
    audit_entries: 84
  });
  const [connected, setConnected] = useState(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    let reconnectTimer: NodeJS.Timeout;
    let isMounted = true;

    function connect() {
      if (typeof window === 'undefined') return;

      const wsProtocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:';
      // If running on next.js dev (port 3000), backend is on 8000
      const wsHost = window.location.port === '3000'
        ? `${window.location.hostname}:8000`
        : window.location.host;
      const wsUrl = `${wsProtocol}//${wsHost}/ws/portfolio`;

      try {
        const ws = new WebSocket(wsUrl);
        wsRef.current = ws;

        ws.onopen = () => {
          if (isMounted) setConnected(true);
        };

        ws.onmessage = (event) => {
          if (!isMounted) return;
          try {
            const data = JSON.parse(event.data);
            if (data.type === 'PORTFOLIO_TELEMETRY') {
              setTelemetry(data);
            }
          } catch {
            // Ignore non-json frames
          }
        };

        ws.onclose = () => {
          if (isMounted) {
            setConnected(false);
            reconnectTimer = setTimeout(connect, 3000);
          }
        };

        ws.onerror = () => {
          if (isMounted) setConnected(false);
        };
      } catch {
        if (isMounted) {
          setConnected(false);
          reconnectTimer = setTimeout(connect, 5000);
        }
      }
    }

    connect();

    return () => {
      isMounted = false;
      clearTimeout(reconnectTimer);
      if (wsRef.current) {
        wsRef.current.close();
      }
    };
  }, [initialNav]);

  return { telemetry, connected };
}
