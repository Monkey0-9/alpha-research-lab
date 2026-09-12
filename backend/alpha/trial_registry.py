"""
QuantAlpha Alpha Trial Registry & False Discovery Governance (Phase 8).
Maintains an immutable, sequential audit trail of all evaluated alpha hypotheses
(e.g., TRIAL-000001 ... TRIAL-010000), explicitly recording accepted, overfit,
and negative/failed trials to prevent survivorship and selection bias in research.
"""
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
import json
from pathlib import Path
from typing import Any, Dict, List, Optional


class TrialStatus(Enum):
    ACCEPTED = "ACCEPTED"
    REJECTED = "REJECTED"
    OVERFIT = "OVERFIT"
    CORRELATED = "CORRELATED_REDUNDANT"
    ECONOMIC_VIOLATION = "ECONOMIC_VIOLATION"


@dataclass
class AlphaTrialRecord:
    trial_id: str  # Format: TRIAL-000001
    expression: str
    hypothesis: str
    dataset_id: str
    in_sample_period: str
    out_of_sample_period: str
    in_sample_sharpe: float
    out_of_sample_sharpe: float
    deflated_sharpe_ratio: float
    pbo: float  # Probability of Backtest Overfitting [0, 1]
    turnover_annual: float
    complexity_penalty: float
    status: str
    rejection_reason: Optional[str] = None
    created_at_utc: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())


class AlphaTrialRegistry:
    """
    Institutional registry logging every quantitative alpha search trial.
    """

    def __init__(self, storage_path: Optional[Path] = None):
        self.storage_path = Path(storage_path) if storage_path else Path("data/alpha_trials.json")
        self._trials: List[AlphaTrialRecord] = []
        self._load_trials()

    def _load_trials(self):
        if self.storage_path.exists():
            try:
                with open(self.storage_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self._trials = [AlphaTrialRecord(**item) for item in data]
            except Exception:
                self._trials = []

    def save_trials(self):
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.storage_path, "w", encoding="utf-8") as f:
            json.dump([asdict(t) for t in self._trials], f, indent=2)

    def next_trial_id(self) -> str:
        count = len(self._trials) + 1
        return f"TRIAL-{count:06d}"

    def register_trial(
        self,
        expression: str,
        hypothesis: str,
        dataset_id: str,
        in_sample_period: str,
        out_of_sample_period: str,
        in_sample_sharpe: float,
        out_of_sample_sharpe: float,
        pbo: float,
        deflated_sharpe_ratio: float,
        turnover_annual: float = 2.5,
        complexity_penalty: float = 0.0,
        min_oos_sharpe_threshold: float = 0.5,
        max_pbo_threshold: float = 0.40
    ) -> AlphaTrialRecord:
        """
        Evaluates and registers a trial. Automatically assigns status based on statistical governance.
        """
        trial_id = self.next_trial_id()

        # Decision rule:
        status = TrialStatus.ACCEPTED
        rejection_reason = None

        if pbo > max_pbo_threshold:
            status = TrialStatus.OVERFIT
            rejection_reason = f"PBO failure: PBO {pbo:.3f} exceeded threshold {max_pbo_threshold:.3f}"
        elif out_of_sample_sharpe < min_oos_sharpe_threshold:
            status = TrialStatus.REJECTED
            rejection_reason = (
                f"OOS performance degradation: OOS Sharpe {out_of_sample_sharpe:.3f} < threshold {min_oos_sharpe_threshold:.3f}"
            )
        elif deflated_sharpe_ratio < 0.90:
            status = TrialStatus.REJECTED
            rejection_reason = f"Deflated Sharpe Ratio failure: DSR {deflated_sharpe_ratio:.3f} < 0.90"

        record = AlphaTrialRecord(
            trial_id=trial_id,
            expression=expression,
            hypothesis=hypothesis,
            dataset_id=dataset_id,
            in_sample_period=in_sample_period,
            out_of_sample_period=out_of_sample_period,
            in_sample_sharpe=in_sample_sharpe,
            out_of_sample_sharpe=out_of_sample_sharpe,
            deflated_sharpe_ratio=deflated_sharpe_ratio,
            pbo=pbo,
            turnover_annual=turnover_annual,
            complexity_penalty=complexity_penalty,
            status=status.value,
            rejection_reason=rejection_reason,
        )

        self._trials.append(record)
        self.save_trials()
        return record

    def get_summary_statistics(self) -> Dict[str, Any]:
        """Calculates registry-level false discovery metrics across all logged trials."""
        total = len(self._trials)
        if total == 0:
            return {"total_trials": 0}

        accepted = [t for t in self._trials if t.status == TrialStatus.ACCEPTED.value]
        rejected = [t for t in self._trials if t.status in (TrialStatus.REJECTED.value, TrialStatus.OVERFIT.value)]

        return {
            "total_trials": total,
            "accepted_count": len(accepted),
            "rejected_count": len(rejected),
            "acceptance_rate": round(len(accepted) / total, 4),
            "mean_in_sample_sharpe": round(sum(t.in_sample_sharpe for t in self._trials) / total, 3),
            "mean_out_of_sample_sharpe": round(sum(t.out_of_sample_sharpe for t in self._trials) / total, 3),
            "mean_pbo": round(sum(t.pbo for t in self._trials) / total, 3),
        }
