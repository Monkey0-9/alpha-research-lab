/
/ QuantAlpha KDB+/Q Vector Analytics Script
/ Production Q time-series expressions for high-frequency bar aggregation, VWAP, Asof Joins, and tick microstructure
\

/ Define canonical trade and quote table schemas
trades: ([] time:`timestamp$(); sym:`symbol$(); price:`float$(); size:`int$(); side:`symbol$());
quotes: ([] time:`timestamp$(); sym:`symbol$(); bid:`float$(); ask:`float$(); bsize:`int$(); asize:`int$());

/ 1. Time-Bar Aggregation (OHLCV + VWAP)
calcBars: {[t; barSize]
    select 
        open: first price, 
        high: max price, 
        low: min price, 
        close: last price, 
        volume: sum size, 
        vwap: size wavg price,
        ticks: count i
    by bar: barSize xbar time, sym from t
 };

/ 2. Volume-Bar Discretization
calcVolBars: {[t; volBucket]
    t: update cumVol: sums size by sym from t;
    select
        open: first price,
        high: max price,
        low: min price,
        close: last price,
        volume: sum size,
        vwap: size wavg price
    by vbar: volBucket xbar cumVol, sym from t
 };

/ 3. Fast Rolling Z-Score Vector Operation
rollZScore: {[prices; window]
    m: mavg[window; prices];
    s: dev[window; prices];
    (prices - m) % (s + 1e-9)
 };

/ 4. Microstructure: High-Frequency Order Flow Imbalance (OFI)
calcOFI: {[q]
    / Delta bid/ask size with price condition
    q: update dbid: deltas bid, dask: deltas ask, dbsize: deltas bsize, dasize: deltas asize from q;
    q: update ofi: ?[dbid > 0; bsize; ?[dbid = 0; dbsize; 0 - bsize]] - ?[dask < 0; asize; ?[dask = 0; dasize; 0 - asize]] from q;
    q
 };

/ 5. Asof Join (AJ) for Precise Trade-Quote Synchronization
syncTradesQuotes: {[t; q]
    / Microsecond-accurate asof-join: matches trade to latest prevailing NBBO quote
    aj[`sym`time; t; q]
 };

/ 6. Effective Spread & Price Impact Analysis
calcEffectiveSpread: {[t; q]
    matched: aj[`sym`time; t; q];
    matched: update mid: 0.5 * (bid + ask) from matched;
    matched: update effSpreadBps: 20000.0 * abs[price - mid] % mid from matched;
    matched: update quoteImbalance: (bsize - asize) % (bsize + asize + 1e-9) from matched;
    matched
 };

/ 7. Cross-Sectional Vector Neutralization & Percentile Ranking
pctRank: {[x]
    (rank x) % (count x - 1)
 };

crossSectionalZScore: {[factors]
    (factors - avg factors) % (dev factors + 1e-9)
 };

/ 8. Information Coefficient (Spearman Rank & Pearson Correlation)
calcIC: {[pred; target]
    cor[pred; target]
 };

calcRankIC: {[pred; target]
    cor[rank pred; rank target]
 };

/ Production IPC listen port
\p 5001
-1 "[OK] QuantAlpha KDB+/Q Institutional Vector Engine online on port 5001";
