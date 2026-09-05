# Independent R Statistical Validation Engine
# Performs numerical equivalence validation for DSR, HAC, and FDR

suppressPackageStartupMessages({
  library(jsonlite)
})

args <- commandArgs(trailingOnly = TRUE)
if (length(args) < 2) {
  cat('{"status": "ERROR", "message": "Insufficient arguments"}\n')
  quit(status = 1)
}

operation <- args[1]
payload_json <- args[2]

payload <- fromJSON(payload_json)

if (operation == "dsr") {
  sr <- as.numeric(payload$observed_sr)
  trials <- as.numeric(payload$num_trials)
  t_len <- as.numeric(payload$sample_length)
  var_trials <- if (!is.null(payload$sr_variance)) as.numeric(payload$sr_variance) else 0.5
  skew <- if (!is.null(payload$skewness)) as.numeric(payload$skewness) else 0.0
  kurt <- if (!is.null(payload$kurtosis)) as.numeric(payload$kurtosis) else 3.0
  
  euler <- 0.5772156649
  z1 <- qnorm(1 - 1 / max(2, trials))
  z2 <- qnorm(1 - 1 / (max(2, trials) * exp(1)))
  expected_max <- sqrt(var_trials) * ((1 - euler) * z1 + euler * z2)
  
  sr_daily <- sr / sqrt(252)
  term <- 1 - skew * sr_daily + ((kurt - 1) / 4) * (sr_daily^2)
  se_sr <- sqrt(max(1e-6, term) / (t_len - 1)) * sqrt(252)
  
  z_stat <- (sr - expected_max) / max(1e-6, se_sr)
  dsr <- pnorm(z_stat)
  p_val <- 1 - dsr
  
  res <- list(
    status = "SUCCESS",
    operation = "dsr",
    expected_max = round(expected_max, 4),
    dsr = round(dsr, 4),
    p_value = round(p_val, 4)
  )
  cat(toJSON(res, auto_unbox = TRUE))
  
} else if (operation == "fdr") {
  p_vals <- as.numeric(payload$p_values)
  q <- as.numeric(payload$q)
  
  adjusted_p <- p.adjust(p_vals, method = "BH")
  sig <- adjusted_p <= q
  
  res <- list(
    status = "SUCCESS",
    operation = "fdr",
    significant_mask = as.list(sig),
    significant_count = sum(sig)
  )
  cat(toJSON(res, auto_unbox = TRUE))
  
} else {
  cat('{"status": "ERROR", "message": "Unknown operation"}\n')
  quit(status = 1)
}
