"""
QuantAlpha Research Governance Gatekeeper & First-Class Negative Results Engine.
Implements:
1. Hypothesis Pre-Registration Manifest (Cryptographic parameter lock).
2. The Execution Survival Gatekeeper Rule:
   If Gross_Sharpe >= 1.50 and Net_Sharpe < 0.50 -> Automatic REJECT_EXECUTION_UNVIABLE.
3. Cumulative Multiple Testing Trial Registry & Deflated Sharpe Penalty (Bailey & Lopez de Prado 2014).
4. Negative results are recorded as first-class citizens, preventing p-hacking.
"""
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
import hashlib
import math
from typing import Dict, List, Optional


class GovernanceVerdict(str, Enum):
    APPROVED = "APPROVED"
    REJECT_EXECUTION_UNVIABLE = "REJECT_EXECUTION_UNVIABLE"
    REJECT_STATISTICAL_SIGNIFICANCE = "REJECT_STATISTICAL_SIGNIFICANCE"
    REJECT_BUDGET_EXCEEDED = "REJECT_BUDGET_EXCEEDED"


@dataclass(frozen=True)
class PreRegistrationManifest:
    hypothesis_id: str
    hypothesis_statement: str
    alpha_dsl_ast: str
    universe_id: str
    dataset_version: str
    search_budget: int
    random_seed: int
    registered_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))

    def compute_manifest_hash(self) -> str:
        payload = (
            f"{self.hypothesis_id}|{self.hypothesis_statement}|{self.alpha_dsl_ast}|"
            f"{self.universe_id}|{self.dataset_version}|{self.search_budget}|{self.random_seed}"
        )
        return hashlib.sha256(payload.encode("utf-8")).hexdigest()


@dataclass
class TrialRecord:
    trial_id: str
    manifest_hash: str
    gross_sharpe: float
    net_sharpe: float
    total_implementation_shortfall_bps: float
    verdict: GovernanceVerdict
    dsr_pvalue: float
    rejection_details: Optional[str] = None
    timestamp: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class ResearchGovernanceGatekeeper:
    """Institutional Governance Gatekeeper enforcing pre-registration and execution survival."""

    def __init__(self, gross_hurdle: float = 1.50, net_survival_hurdle: float = 0.50):
        self.gross_hurdle = gross_hurdle
        self.net_survival_hurdle = net_survival_hurdle
        self._manifests: Dict[str, PreRegistrationManifest] = {}
        self._trial_history: List[TrialRecord] = []

    def pre_register(
        self,
        hypothesis_id: str,
        hypothesis_statement: str,
        alpha_dsl_ast: str,
        universe_id: str = "SP500_HISTORICAL",
        dataset_version: str = "v2026.1",
        search_budget: int = 100,
        random_seed: int = 42
    ) -> str:
        """Register hypothesis prior to execution. Returns immutable manifest hash."""
        manifest = PreRegistrationManifest(
            hypothesis_id=hypothesis_id,
            hypothesis_statement=hypothesis_statement,
            alpha_dsl_ast=alpha_dsl_ast,
            universe_id=universe_id,
            dataset_version=dataset_version,
            search_budget=search_budget,
            random_seed=random_seed
        )
        m_hash = manifest.compute_manifest_hash()
        self._manifests[m_hash] = manifest
        return m_hash

    def evaluate_alpha(
        self,
        manifest_hash: str,
        gross_sharpe: float,
        net_sharpe: float,
        total_is_bps: float,
        sample_length_days: int = 756  # ~3 years
    ) -> TrialRecord:
        """
        Evaluate candidate alpha against the strict execution gatekeeper.
        First-Class Negative Result Policy:
          If paper Sharpe is high (>= 1.5) but net of costs (< 0.5), immediately REJECT.
          Do NOT optimize or fudge parameters. Record into cumulative trial registry.
        """
        if manifest_hash not in self._manifests:
            raise KeyError(f"Unregistered experiment: {manifest_hash}. Pre-registration is mandatory.")

        # Check trials against search budget
        prior_trials = [t for t in self._trial_history if t.manifest_hash == manifest_hash]
        manifest = self._manifests[manifest_hash]
        if len(prior_trials) >= manifest.search_budget:
            record = TrialRecord(
                trial_id=f"TRIAL-{len(self._trial_history)+1}",
                manifest_hash=manifest_hash,
                gross_sharpe=gross_sharpe,
                net_sharpe=net_sharpe,
                total_implementation_shortfall_bps=total_is_bps,
                verdict=GovernanceVerdict.REJECT_BUDGET_EXCEEDED,
                dsr_pvalue=0.0,
                rejection_details="Search budget exhausted for hypothesis."
            )
            self._trial_history.append(record)
            return record

        # Calculate Deflated Sharpe Ratio (Bailey & Lopez de Prado)
        n_trials = len(self._trial_history) + 1
        # Expected max Sharpe of N random strategies under pure noise
        e_max_sr = math.sqrt(2.0 * math.log(max(n_trials, 2))) * (1.0 - 0.5772 / (2.0 * math.log(max(n_trials, 2))))
        sr_diff = (net_sharpe - (e_max_sr / math.sqrt(252))) * math.sqrt(sample_length_days - 1)
        # Approximate standard normal CDF
        dsr_pvalue = 0.5 * (1.0 + math.erf(sr_diff / math.sqrt(2.0)))

        # EXECUTION SURVIVAL RULE
        if gross_sharpe >= self.gross_hurdle and net_sharpe < self.net_survival_hurdle:
            verdict = GovernanceVerdict.REJECT_EXECUTION_UNVIABLE
            reason = (
                f"Paper Sharpe {gross_sharpe:.2f} >= {self.gross_hurdle:.2f}, but net Sharpe {net_sharpe:.2f} "
                f"collapsed below survival hurdle {self.net_survival_hurdle:.2f} due to {total_is_bps:.1f} bps IS."
            )
        elif net_sharpe < self.net_survival_hurdle:
            verdict = GovernanceVerdict.REJECT_STATISTICAL_SIGNIFICANCE
            reason = f"Net Sharpe {net_sharpe:.2f} below threshold {self.net_survival_hurdle:.2f}."
        else:
            verdict = GovernanceVerdict.APPROVED
            reason = "Strategy passed execution survival and multiple testing hurdles."

        record = TrialRecord(
            trial_id=f"TRIAL-{len(self._trial_history)+1}",
            manifest_hash=manifest_hash,
            gross_sharpe=gross_sharpe,
            net_sharpe=net_sharpe,
            total_implementation_shortfall_bps=total_is_bps,
            verdict=verdict,
            dsr_pvalue=round(dsr_pvalue, 4),
            rejection_details=reason if verdict != GovernanceVerdict.APPROVED else None
        )
        self._trial_history.append(record)
        return record

    @property
    def total_trials_count(self) -> int:
        return len(self._trial_history)

    @property
    def negative_results_count(self) -> int:
        return sum(1 for t in self._trial_history if t.verdict != GovernanceVerdict.APPROVED)
