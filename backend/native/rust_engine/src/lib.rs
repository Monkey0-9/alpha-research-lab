//! Rust Engine for Ultra-Fast Alpha Metrics & Backtesting
//! Exposes C-compatible FFI ABI for zero-overhead Python ctypes bindings.

use std::slice;

#[no_mangle]
pub extern "C" fn rust_sharpe_ratio(returns_ptr: *const f64, len: usize, periods: f64) -> f64 {
    if len < 2 || returns_ptr.is_null() {
        return 0.0;
    }
    let returns = unsafe { slice::from_raw_parts(returns_ptr, len) };
    let mean: f64 = returns.iter().sum::<f64>() / (len as f64);
    let variance: f64 = returns.iter().map(|&x| (x - mean).powi(2)).sum::<f64>() / ((len - 1) as f64);
    let std = variance.sqrt();
    if std < 1e-9 {
        return 0.0;
    }
    (mean / std) * periods.sqrt()
}

#[no_mangle]
pub extern "C" fn rust_max_drawdown(equity_ptr: *const f64, len: usize) -> f64 {
    if len < 2 || equity_ptr.is_null() {
        return 0.0;
    }
    let equity = unsafe { slice::from_raw_parts(equity_ptr, len) };
    let mut peak = equity[0];
    let mut max_dd = 0.0;

    for &val in equity.iter() {
        if val > peak {
            peak = val;
        }
        if peak > 1e-9 {
            let dd = (peak - val) / peak;
            if dd > max_dd {
                max_dd = dd;
            }
        }
    }
    max_dd
}

#[no_mangle]
pub extern "C" fn rust_cvar_historical(returns_ptr: *const f64, len: usize, alpha: f64) -> f64 {
    if len < 5 || returns_ptr.is_null() || alpha <= 0.0 || alpha >= 1.0 {
        return 0.0;
    }
    let returns = unsafe { slice::from_raw_parts(returns_ptr, len) };
    let mut sorted = returns.to_vec();
    sorted.sort_by(|a, b| a.partial_cmp(b).unwrap_or(std::cmp::Ordering::Equal));

    let cutoff_idx = ((len as f64) * alpha).ceil() as usize;
    let cutoff = cutoff_idx.clamp(1, len);
    let tail_sum: f64 = sorted[..cutoff].iter().sum();
    -(tail_sum / (cutoff as f64))
}

#[no_mangle]
pub extern "C" fn rust_fast_backtest_pnl(
    returns_ptr: *const f64,
    positions_ptr: *const f64,
    out_pnl_ptr: *mut f64,
    len: usize,
    fee_bps: f64,
) -> f64 {
    if len == 0 || returns_ptr.is_null() || positions_ptr.is_null() || out_pnl_ptr.is_null() {
        return 0.0;
    }
    let returns = unsafe { slice::from_raw_parts(returns_ptr, len) };
    let positions = unsafe { slice::from_raw_parts(positions_ptr, len) };
    let out_pnl = unsafe { slice::from_raw_parts_mut(out_pnl_ptr, len) };

    let fee_rate = fee_bps / 10000.0;
    let mut prev_pos = 0.0;
    let mut cum_pnl = 0.0;

    for i in 0..len {
        let pos = positions[i];
        let turnover = (pos - prev_pos).abs();
        let cost = turnover * fee_rate;
        let day_pnl = pos * returns[i] - cost;
        out_pnl[i] = day_pnl;
        cum_pnl += day_pnl;
        prev_pos = pos;
    }

    cum_pnl
}
