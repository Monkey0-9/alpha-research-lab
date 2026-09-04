'use client';

import { useEffect, useRef, useState } from 'react';

const TICKERS = [
  { sym: 'SPY',   price: '582.47', chg: '+1.23', pct: '+0.21%', pos: true },
  { sym: 'QQQ',   price: '497.81', chg: '+2.14', pct: '+0.43%', pos: true },
  { sym: 'AAPL',  price: '231.45', chg: '-0.87', pct: '-0.38%', pos: false },
  { sym: 'NVDA',  price: '138.92', chg: '+4.15', pct: '+3.08%', pos: true },
  { sym: 'MSFT',  price: '445.22', chg: '+1.05', pct: '+0.24%', pos: true },
  { sym: 'GOOGL', price: '194.73', chg: '-0.44', pct: '-0.23%', pos: false },
  { sym: 'META',  price: '577.18', chg: '+8.31', pct: '+1.46%', pos: true },
  { sym: 'AMZN',  price: '214.56', chg: '+2.22', pct: '+1.05%', pos: true },
  { sym: 'TSLA',  price: '248.74', chg: '-5.63', pct: '-2.21%', pos: false },
  { sym: 'BRK.B', price: '468.11', chg: '+0.88', pct: '+0.19%', pos: true },
  { sym: 'JPM',   price: '247.32', chg: '+1.44', pct: '+0.59%', pos: true },
  { sym: 'GS',    price: '584.90', chg: '+3.77', pct: '+0.65%', pos: true },
  { sym: 'VIX',   price: '13.42',  chg: '-0.31', pct: '-2.26%', pos: false },
  { sym: 'TLT',   price: '95.18',  chg: '-0.55', pct: '-0.57%', pos: false },
  { sym: 'GLD',   price: '241.77', chg: '+1.88', pct: '+0.78%', pos: true },
  { sym: 'BTC',   price: '68,420', chg: '+1,240', pct: '+1.84%', pos: true },
  { sym: 'EUR/USD', price: '1.0847', chg: '+0.0012', pct: '+0.11%', pos: true },
  { sym: 'DXY',   price: '104.52', chg: '-0.23',  pct: '-0.22%', pos: false },
];

export default function BloombergTicker() {
  // Duplicate for seamless loop
  const items = [...TICKERS, ...TICKERS];

  return (
    <div className="bb-ticker">
      {/* Label */}
      <div style={{
        display: 'flex', alignItems: 'center', gap: '0.4rem',
        padding: '0 0.6rem',
        borderRight: '1px solid #FF6600',
        flexShrink: 0,
        background: '#FF6600',
        height: '100%',
      }}>
        <span style={{ color: '#000', fontSize: '0.6rem', fontWeight: 900, fontFamily: 'var(--font-mono)', letterSpacing: '0.08em' }}>
          ◄ LIVE
        </span>
      </div>

      {/* Scrolling ticker */}
      <div style={{ overflow: 'hidden', flex: 1, height: '100%', display: 'flex', alignItems: 'center' }}>
        <div className="bb-ticker-inner">
          {items.map((t, i) => (
            <span key={i} className="bb-ticker-item">
              <span className="bb-ticker-sym">{t.sym}</span>
              <span className="bb-ticker-price">{t.price}</span>
              <span className={`bb-ticker-chg ${t.pos ? 'pos' : 'neg'}`}>
                {t.chg} ({t.pct})
              </span>
              <span style={{ color: '#2a2a2a', marginLeft: '0.5rem' }}>│</span>
            </span>
          ))}
        </div>
      </div>
    </div>
  );
}
