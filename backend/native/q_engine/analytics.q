/
/ QuantAlpha KDB+/Q Vector Analytics Script
/ Production Q time-series expressions for high-frequency bar aggregation, VWAP, and tick analytics
\

/ Bar aggregation: OHLCV from tick trades
calcBar: {[trades; barSize]
    select 
        open: first price, 
        high: max price, 
        low: min price, 
        close: last price, 
        volume: sum size, 
        vwap: size wavg price 
    by bar: barSize xbar time, sym from trades
 };

/ Fast rolling Z-Score in Q
rollZScore: {[prices; window]
    m: mavg[window; prices];
    s: dev[window; prices];
    (prices - m) % (s + 1e-9)
 };

/ Realized volatility
realizedVol: {[returns; window]
    sqrt[252] * mdev[window; returns]
 };

/ Bid-Ask Effective Spread calculation
effectiveSpread: {[trades; quotes]
    aj[`sym`time; trades; quotes]
 };

/ Information Coefficient in Q
calcIC: {[pred; target]
    cor[pred; target]
 };

/ Server listen port for IPC
\p 5001
-1 "QuantAlpha Q Analytics Engine initialized on port 5001";
