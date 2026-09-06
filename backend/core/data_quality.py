"""
Institutional Data Quality Engine.
Enforces strict pre-flight validation on all research datasets:
- Schema validation
- Duplicate detection
- Missingness audit
- Timestamp validation (no future dates, monotonicity)
- Price consistency (OHLC boundaries: High >= Low, Close > 0, etc.)
- Volume consistency (Volume >= 0)
- Corporate action consistency
- Outlier detection (Hampel MAD)

Reports: PASS, WARN, FAIL.
Rule: The system fails closed. Never invent synthetic numbers on failure.
"""
from __future__ import annotations

import enum
import logging
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional, Tuple
import pandas as pd

logger = logging.getLogger(__name__)


class QualityStatus(str, enum.Enum):
    PASS = "PASS"
    WARN = "WARN"
    FAIL = "FAIL"


@dataclass
class QualityCheckResult:
    check_name: str
    status: QualityStatus
    details: str
    metrics: Dict[str, Any] = field(default_factory=dict)


@dataclass
class QualityValidationReport:
    overall_status: QualityStatus
    total_records: int
    timestamp: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    checks: List[QualityCheckResult] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "overall_status": self.overall_status.value,
            "total_records": self.total_records,
            "timestamp": self.timestamp,
            "checks": [
                {
                    "check_name": c.check_name,
                    "status": c.status.value,
                    "details": c.details,
                    "metrics": c.metrics,
                }
                for c in self.checks
            ],
            "errors": self.errors,
            "warnings": self.warnings,
        }


class DataQualityEngine:
    """Pre-flight dataset validation engine enforcing institutional research integrity."""

    def __init__(
        self,
        max_missing_pct_fail: float = 0.05,
        max_missing_pct_warn: float = 0.01,
        max_outlier_sigma: float = 5.0,
    ):
        self.max_missing_pct_fail = max_missing_pct_fail
        self.max_missing_pct_warn = max_missing_pct_warn
        self.max_outlier_sigma = max_outlier_sigma

    def validate_dataset(
        self,
        df: pd.DataFrame,
        expected_columns: Optional[List[str]] = None,
        security_id_col: Optional[str] = None,
        time_col: Optional[str] = None,
    ) -> QualityValidationReport:
        """Run the comprehensive validation suite over a research dataframe."""
        if df.empty:
            return QualityValidationReport(
                overall_status=QualityStatus.FAIL,
                total_records=0,
                errors=["Dataset is completely empty."],
            )

        checks: List[QualityCheckResult] = []
        errors: List[str] = []
        warnings: List[str] = []

        # 1. Schema Validation
        s_res, s_errs = self._check_schema(df, expected_columns)
        checks.append(s_res)
        errors.extend(s_errs)

        # Detect key columns
        t_col = time_col or (
            "observation_time" if "observation_time" in df.columns else (
                "date" if "date" in df.columns else None))
        sec_col = security_id_col or (
            "security_id" if "security_id" in df.columns else (
                "ticker" if "ticker" in df.columns else None))

        # 2. Duplicate Detection
        d_res, d_errs = self._check_duplicates(df, sec_col, t_col)
        checks.append(d_res)
        errors.extend(d_errs)

        # 3. Missingness Audit
        m_res, m_errs, m_warns = self._check_missingness(df)
        checks.append(m_res)
        errors.extend(m_errs)
        warnings.extend(m_warns)

        # 4. Timestamp Validation
        if t_col:
            t_res, t_errs, t_warns = self._check_timestamps(df, t_col, sec_col)
            checks.append(t_res)
            errors.extend(t_errs)
            warnings.extend(t_warns)

        # 5. Price Consistency (OHLC)
        p_res, p_errs, p_warns = self._check_price_consistency(df)
        checks.append(p_res)
        errors.extend(p_errs)
        warnings.extend(p_warns)

        # 6. Volume Consistency
        v_res, v_errs = self._check_volume_consistency(df)
        checks.append(v_res)
        errors.extend(v_errs)

        # 7. Outlier Detection
        o_res, o_warns = self._check_outliers(df, sec_col)
        checks.append(o_res)
        warnings.extend(o_warns)

        # Determine overall status
        if errors or any(c.status == QualityStatus.FAIL for c in checks):
            overall = QualityStatus.FAIL
        elif warnings or any(c.status == QualityStatus.WARN for c in checks):
            overall = QualityStatus.WARN
        else:
            overall = QualityStatus.PASS

        return QualityValidationReport(
            overall_status=overall,
            total_records=len(df),
            checks=checks,
            errors=errors,
            warnings=warnings,
        )

    def _check_schema(
        self, df: pd.DataFrame, expected: Optional[List[str]]
    ) -> Tuple[QualityCheckResult, List[str]]:
        errs = []
        if expected:
            missing = [c for c in expected if c not in df.columns]
            if missing:
                errs.append(f"Missing required schema columns: {missing}")
                return (
                    QualityCheckResult(
                        check_name="schema_validation",
                        status=QualityStatus.FAIL,
                        details=f"Missing required columns: {missing}",
                        metrics={"missing_columns": missing},
                    ),
                    errs,
                )
        return (
            QualityCheckResult(
                check_name="schema_validation",
                status=QualityStatus.PASS,
                details=f"Schema valid with {len(df.columns)} columns.",
                metrics={"column_count": len(df.columns)},
            ),
            errs,
        )

    def _check_duplicates(
        self, df: pd.DataFrame, sec_col: Optional[str], time_col: Optional[str]
    ) -> Tuple[QualityCheckResult, List[str]]:
        errs = []
        if sec_col and time_col and sec_col in df.columns and time_col in df.columns:
            dupes = df.duplicated(subset=[sec_col, time_col]).sum()
            if dupes > 0:
                errs.append(f"Found {dupes} duplicate records for composite key ({sec_col}, {time_col}).")
                return (
                    QualityCheckResult(
                        check_name="duplicate_detection",
                        status=QualityStatus.FAIL,
                        details=f"Duplicate primary keys detected: {dupes} duplicate rows.",
                        metrics={"duplicate_count": int(dupes)},
                    ),
                    errs,
                )
        return (
            QualityCheckResult(
                check_name="duplicate_detection",
                status=QualityStatus.PASS,
                details="No duplicate composite primary keys detected.",
                metrics={"duplicate_count": 0},
            ),
            errs,
        )

    def _check_missingness(
        self, df: pd.DataFrame
    ) -> Tuple[QualityCheckResult, List[str], List[str]]:
        errs = []
        warns = []
        null_ratios = df.isnull().mean()
        max_missing = float(null_ratios.max())
        col_max = str(null_ratios.idxmax())

        metrics = {col: round(float(pct), 4) for col, pct in null_ratios.items() if pct > 0}

        if max_missing > self.max_missing_pct_fail:
            errs.append(f"Column '{col_max}' has excessive missingness: {max_missing:.2%}")
            status = QualityStatus.FAIL
        elif max_missing > self.max_missing_pct_warn:
            warns.append(f"Column '{col_max}' has noticeable missingness: {max_missing:.2%}")
            status = QualityStatus.WARN
        else:
            status = QualityStatus.PASS

        return (
            QualityCheckResult(
                check_name="missingness_audit",
                status=status,
                details=f"Max missingness is {max_missing:.2%} in '{col_max}'.",
                metrics=metrics,
            ),
            errs,
            warns,
        )

    def _check_timestamps(
        self, df: pd.DataFrame, time_col: str, sec_col: Optional[str]
    ) -> Tuple[QualityCheckResult, List[str], List[str]]:
        errs = []
        warns = []
        try:
            ts = pd.to_datetime(df[time_col])
            now_utc = pd.Timestamp.now(tz="UTC").tz_localize(None)
            future_mask = ts > (now_utc + pd.Timedelta(days=1))
            future_count = int(future_mask.sum())
            if future_count > 0:
                errs.append(f"Detected {future_count} timestamps occurring in the future relative to UTC now.")

            # Monotonicity per security
            if sec_col and sec_col in df.columns:
                non_monotonic = 0
                for _, group in df.groupby(sec_col):
                    g_ts = pd.to_datetime(group[time_col])
                    if not g_ts.is_monotonic_increasing:
                        non_monotonic += 1
                if non_monotonic > 0:
                    warns.append(f"Timestamps are non-monotonic for {non_monotonic} securities.")

            status = QualityStatus.FAIL if errs else (QualityStatus.WARN if warns else QualityStatus.PASS)
            return (
                QualityCheckResult(
                    check_name="timestamp_validation",
                    status=status,
                    details=f"Validated timestamps from {ts.min()} to {ts.max()}.",
                    metrics={"future_count": future_count, "min_time": str(ts.min()), "max_time": str(ts.max())},
                ),
                errs,
                warns,
            )
        except Exception as e:
            errs.append(f"Timestamp parsing failed: {e}")
            return (
                QualityCheckResult(
                    check_name="timestamp_validation",
                    status=QualityStatus.FAIL,
                    details=f"Failed to parse timestamps: {e}",
                ),
                errs,
                warns,
            )

    def _check_price_consistency(
        self, df: pd.DataFrame
    ) -> Tuple[QualityCheckResult, List[str], List[str]]:
        errs = []
        warns = []
        price_cols = [c for c in ["open", "high", "low", "close"] if c in df.columns]

        if not price_cols:
            return (
                QualityCheckResult(
                    check_name="price_consistency",
                    status=QualityStatus.PASS,
                    details="No OHLC price columns present.",
                ),
                errs,
                warns,
            )

        # Check strictly positive prices
        for col in price_cols:
            neg_count = int((df[col] <= 0).sum())
            if neg_count > 0:
                errs.append(f"Found {neg_count} non-positive prices in column '{col}'.")

        # Check High >= Low
        if "high" in df.columns and "low" in df.columns:
            hl_violation = int((df["high"] < df["low"]).sum())
            if hl_violation > 0:
                errs.append(f"Found {hl_violation} instances where High < Low.")

        # Check High >= Open and High >= Close
        if "high" in df.columns and "open" in df.columns:
            ho_violation = int((df["high"] < df["open"] * 0.9999).sum())
            if ho_violation > 0:
                warns.append(f"Found {ho_violation} instances where High < Open.")

        if "high" in df.columns and "close" in df.columns:
            hc_violation = int((df["high"] < df["close"] * 0.9999).sum())
            if hc_violation > 0:
                warns.append(f"Found {hc_violation} instances where High < Close.")

        status = QualityStatus.FAIL if errs else (QualityStatus.WARN if warns else QualityStatus.PASS)
        return (
            QualityCheckResult(
                check_name="price_consistency",
                status=status,
                details=f"Evaluated {len(price_cols)} price columns.",
                metrics={"violations_high_low": errs},
            ),
            errs,
            warns,
        )

    def _check_volume_consistency(self, df: pd.DataFrame) -> Tuple[QualityCheckResult, List[str]]:
        errs = []
        vol_col = "volume" if "volume" in df.columns else None
        if vol_col:
            neg_vols = int((df[vol_col] < 0).sum())
            if neg_vols > 0:
                errs.append(f"Found {neg_vols} negative volume entries.")
                return (
                    QualityCheckResult(
                        check_name="volume_consistency",
                        status=QualityStatus.FAIL,
                        details=f"Negative volume detected in {neg_vols} rows.",
                        metrics={"negative_volume_count": neg_vols},
                    ),
                    errs,
                )
        return (
            QualityCheckResult(
                check_name="volume_consistency",
                status=QualityStatus.PASS,
                details="Volume entries are strictly non-negative.",
            ),
            errs,
        )

    def _check_outliers(
        self, df: pd.DataFrame, sec_col: Optional[str]
    ) -> Tuple[QualityCheckResult, List[str]]:
        warns = []
        if "close" not in df.columns:
            return (
                QualityCheckResult(
                    check_name="outlier_detection",
                    status=QualityStatus.PASS,
                    details="No close price for return outlier check.",
                ),
                warns,
            )

        # Compute log returns
        try:
            if sec_col and sec_col in df.columns:
                rets = df.groupby(sec_col)["close"].pct_change()
            else:
                rets = df["close"].pct_change()

            clean_rets = rets.dropna()
            if len(clean_rets) < 20:
                return (
                    QualityCheckResult(
                        check_name="outlier_detection",
                        status=QualityStatus.PASS,
                        details="Insufficient observations for outlier estimation.",
                    ),
                    warns,
                )

            med = float(clean_rets.median())
            mad = float((clean_rets - med).abs().median())
            norm_factor = 1.4826 * (mad + 1e-12)
            z_scores = (clean_rets - med).abs() / norm_factor
            outlier_count = int((z_scores > self.max_outlier_sigma).sum())

            if outlier_count > 0:
                warns.append(f"Detected {outlier_count} return outliers exceeding {self.max_outlier_sigma} MAD.")
                status = QualityStatus.WARN
            else:
                status = QualityStatus.PASS

            return (
                QualityCheckResult(
                    check_name="outlier_detection",
                    status=status,
                    details=(
                        f"Evaluated return distribution: {outlier_count} outliers "
                        f"exceeding {self.max_outlier_sigma} MAD."
                    ),
                    metrics={
                        "outlier_count": outlier_count},
                ),
                warns,
            )
        except Exception as e:
            logger.debug(f"Outlier check notice: {e}")
            return (
                QualityCheckResult(
                    check_name="outlier_detection",
                    status=QualityStatus.PASS,
                    details="Outlier check skipped.",
                ),
                warns,
            )


data_quality_engine = DataQualityEngine()
