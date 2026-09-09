"""
Reproduction Certificate & Alpha Evidence Card.
Provides multi-metric Level-5 reproduction verification records and ASCII institutional report cards.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Dict, Any, List


@dataclass
class ReproductionCheckItem:
    name: str
    passed: bool
    reference_value: Any
    reproduced_value: Any
    detail: str = ""


@dataclass
class ReproductionCertificate:
    """
    Level-5 Multi-Metric Reproduction Certificate.
    Verifies that an independent execution on a separate environment yields exact matching.
    """
    experiment_id: str
    reproduced_at: str = field(default_factory=lambda: datetime.now(timezone.utc).isoformat())
    environment_hash: str = ""
    git_sha: str = ""
    items: List[ReproductionCheckItem] = field(default_factory=list)
    final_result: str = "REPRODUCTION_FAILED"  # REPRODUCED_EXACTLY or REPRODUCTION_FAILED

    @property
    def is_exact(self) -> bool:
        return self.final_result == "REPRODUCED_EXACTLY" and all(item.passed for item in self.items)

    @property
    def passed(self) -> bool:
        return self.is_exact

    def evaluate(self) -> None:
        """Evaluate overall certificate state across all items."""
        if self.items and all(item.passed for item in self.items):
            self.final_result = "REPRODUCED_EXACTLY"
        else:
            self.final_result = "REPRODUCTION_FAILED"

    def render_ascii(self) -> str:
        lines = [
            "╔══════════════════════════════════════════════════════════════╗",
            "║               LEVEL-5 REPRODUCTION CERTIFICATE               ║",
            "╠══════════════════════════════════════════════════════════════╣",
            f"║ Experiment ID: {self.experiment_id[:45]:<46}║",
            f"║ Reproduced At: {self.reproduced_at[:45]:<46}║",
            "╠══════════════════════════════════════════════════════════════╣",
        ]
        for item in self.items:
            status = "PASS" if item.passed else "FAIL"
            lines.append(f"║ {item.name:<32} {status:>26} ║")
        lines.append("╠══════════════════════════════════════════════════════════════╣")
        lines.append(f"║ FINAL RESULT: {self.final_result:<46} ║")
        lines.append("╚══════════════════════════════════════════════════════════════╝")
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "experiment_id": self.experiment_id,
            "reproduced_at": self.reproduced_at,
            "environment_hash": self.environment_hash,
            "git_sha": self.git_sha,
            "final_result": self.final_result,
            "is_exact": self.is_exact,
            "items": [
                {
                    "name": it.name,
                    "passed": it.passed,
                    "reference": str(it.reference_value),
                    "reproduced": str(it.reproduced_value),
                    "detail": it.detail,
                }
                for it in self.items
            ],
            "ascii_certificate": self.render_ascii(),
        }


@dataclass
class AlphaEvidenceCard:
    """
    Research Evidence Card for institutional governance decisions.
    Aggregates statistical, validation, execution, risk, and falsification evidence.
    """
    alpha_id: str
    hypothesis: str
    expression: str
    ast_hash: str
    dataset_id: str
    universe_id: str
    is_period: str
    oos_period: str
    # Metrics
    ic: float = 0.0
    icir: float = 0.0
    sharpe: float = 0.0
    dsr: float = 0.0
    pbo: float = 0.0
    fdr: float = 0.0
    reality_check_pvalue: float = 0.0
    spa_pvalue: float = 0.0
    # Execution & Risk
    turnover: float = 0.0
    transaction_cost_bps: float = 0.0
    capacity_millions: float = 0.0
    max_factor_exposure: float = 0.0
    max_alpha_correlation: float = 0.0
    decay_half_life_days: float = 0.0
    regime_stability_score: float = 0.0
    # Verification
    falsification_status: str = "PASS"
    reproduction_status: str = "PASS"
    evidence_chain_verified: bool = True
    final_decision: str = "INSUFFICIENT_EVIDENCE"  # APPROVE / REJECT / INSUFFICIENT_EVIDENCE
    reason: str = ""

    def render_ascii(self) -> str:
        width = 46
        inner_w = width - 2
        lines = [
            "╔" + "═" * inner_w + "╗",
            f"║{'ALPHA EVIDENCE CARD':^{inner_w}}║",
            "╠" + "═" * inner_w + "╣",
            f"║ Alpha ID:    {self.alpha_id[:30]:<{inner_w - 15}}║",
            f"║ Hypothesis:  {self.hypothesis[:30]:<{inner_w - 15}}║",
            f"║ Expression:  {self.expression[:30]:<{inner_w - 15}}║",
            f"║ AST Hash:    {self.ast_hash[:30]:<{inner_w - 15}}║",
            f"║ Dataset:     {self.dataset_id[:30]:<{inner_w - 15}}║",
            f"║ Universe:    {self.universe_id[:30]:<{inner_w - 15}}║",
            f"║ IS Period:   {self.is_period[:30]:<{inner_w - 15}}║",
            f"║ OOS Period:  {self.oos_period[:30]:<{inner_w - 15}}║",
            "╟" + "─" * inner_w + "╢",
            f"║ IC:          {self.ic:>8.4f}     ICIR:    {self.icir:>8.4f}  ║",
            f"║ Sharpe:      {self.sharpe:>8.2f}     DSR:     {self.dsr * 100:>7.1f}%  ║",
            f"║ PBO:         {self.pbo * 100:>7.1f}%     FDR:     {self.fdr * 100:>7.1f}%  ║",
            f"║ Reality Chk: {self.reality_check_pvalue:>8.4f}     SPA:     {self.spa_pvalue:>8.4f}  ║",
            "╟" + "─" * inner_w + "╢",
            f"║ Turnover:    {self.turnover * 100:>7.1f}%     Cost:    {self.transaction_cost_bps:>6.1f} bps║",
            f"║ Capacity:    ${self.capacity_millions:>6.1f}M     Max Factor: {self.max_factor_exposure:>5.2f}  ║",
            f"║ Alpha Corr:  {self.max_alpha_correlation:>8.2f}     Half-life:{self.decay_half_life_days:>6.1f}d  ║",
            f"║ Regime Stab: {self.regime_stability_score:>8.2f}                         ║",
            "╟" + "─" * inner_w + "╢",
            f"║ Falsification: {self.falsification_status:<12} Reproduction: {self.reproduction_status:<7}║",
            f"║ Chain Verified: {'YES' if self.evidence_chain_verified else 'NO':<30}║",
            "╠" + "═" * inner_w + "╣",
            f"║ FINAL DECISION: {self.final_decision:<27}║",
            "╚" + "═" * inner_w + "╝",
        ]
        return "\n".join(lines)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "alpha_id": self.alpha_id,
            "hypothesis": self.hypothesis,
            "expression": self.expression,
            "ast_hash": self.ast_hash,
            "dataset_id": self.dataset_id,
            "universe_id": self.universe_id,
            "is_period": self.is_period,
            "oos_period": self.oos_period,
            "metrics": {
                "ic": self.ic,
                "icir": self.icir,
                "sharpe": self.sharpe,
                "dsr": self.dsr,
                "pbo": self.pbo,
                "fdr": self.fdr,
                "reality_check_pvalue": self.reality_check_pvalue,
                "spa_pvalue": self.spa_pvalue,
            },
            "execution_and_risk": {
                "turnover": self.turnover,
                "transaction_cost_bps": self.transaction_cost_bps,
                "capacity_millions": self.capacity_millions,
                "max_factor_exposure": self.max_factor_exposure,
                "max_alpha_correlation": self.max_alpha_correlation,
                "decay_half_life_days": self.decay_half_life_days,
                "regime_stability_score": self.regime_stability_score,
            },
            "verification": {
                "falsification_status": self.falsification_status,
                "reproduction_status": self.reproduction_status,
                "evidence_chain_verified": self.evidence_chain_verified,
            },
            "final_decision": self.final_decision,
            "reason": self.reason,
            "ascii_card": self.render_ascii(),
        }
