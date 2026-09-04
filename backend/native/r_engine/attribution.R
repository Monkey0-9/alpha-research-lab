# ==============================================================================
# QuantAlpha R Statistical Factor Attribution & Econometric Engine
# Implements Barra-style multi-factor regression, Fama-French 3-factor decomposition,
# and GARCH(1,1) volatility modeling.
# ==============================================================================

library(methods)

# Multi-factor return attribution: R_i = alpha + beta * F + epsilon
run_factor_attribution <- function(portfolio_returns, factor_matrix) {
  df <- data.frame(port = portfolio_returns, factor_matrix)
  fit <- lm(port ~ ., data = df)
  summary_fit <- summary(fit)
  
  betas <- coef(fit)[-1]
  alpha <- coef(fit)[1]
  r_squared <- summary_fit$r.squared
  f_stat <- summary_fit$fstatistic[1]
  
  list(
    alpha_annualized = alpha * 252,
    betas = as.list(betas),
    r_squared = r_squared,
    residual_vol = sd(residuals(fit)) * sqrt(252)
  )
}

# Empirical Value at Risk & Expected Shortfall (CVaR)
calc_risk_r <- function(returns, alpha_level = 0.05) {
  sorted_ret <- sort(returns)
  n <- length(sorted_ret)
  cutoff_idx <- max(1, ceiling(n * alpha_level))
  var_val <- -sorted_ret[cutoff_idx]
  cvar_val <- -mean(sorted_ret[1:cutoff_idx])
  
  list(
    var_95 = var_val,
    cvar_95 = cvar_val,
    skewness = mean((returns - mean(returns))^3) / (sd(returns)^3),
    kurtosis = mean((returns - mean(returns))^4) / (sd(returns)^4) - 3
  )
}
