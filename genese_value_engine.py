"""GÊNESE value discovery and verification engine.

This module tracks candidate opportunities; it does not create money, exploit
systems, access private accounts, or initiate payments. A candidate becomes
receivable only when its issuer/source and redemption path are independently
confirmed.
"""
from __future__ import annotations

from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from typing import Iterable, Protocol
from urllib.parse import urlparse


def _is_https_url(value: str | None) -> bool:
    if not value:
        return False
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


@dataclass(frozen=True)
class ValueCandidate:
    candidate_id: str
    source_name: str
    source_url: str
    description: str
    amount_minor: int | None = None
    currency: str = "BRL"
    evidence_url: str | None = None
    issuer_reference: str | None = None
    redemption_method: str | None = None
    source_confirmed: bool = False
    authorization_confirmed: bool = False


@dataclass(frozen=True)
class Evaluation:
    candidate_id: str
    status: str
    checks: tuple[str, ...]
    evaluated_at: str

    @property
    def is_receivable(self) -> bool:
        return self.status == "verified_receivable"


class CandidateSource(Protocol):
    """An explicitly configured, authorized source of candidate opportunities."""

    name: str

    def discover(self) -> Iterable[ValueCandidate]:
        """Return candidate records with source evidence, never assumed cash."""
        ...


class ValueDiscoveryEngine:
    """Evidence-first evaluator for possible legitimate receivables."""

    def evaluate(self, candidate: ValueCandidate) -> Evaluation:
        checks: list[str] = []
        failures: list[str] = []

        if candidate.candidate_id.strip():
            checks.append("candidate_id_present")
        else:
            failures.append("missing_candidate_id")

        if candidate.source_name.strip() and _is_https_url(candidate.source_url):
            checks.append("source_identified")
        else:
            failures.append("source_not_verifiable")

        if candidate.description.strip():
            checks.append("description_present")
        else:
            failures.append("missing_description")

        if candidate.amount_minor is not None and candidate.amount_minor > 0:
            checks.append("positive_amount")
        else:
            failures.append("amount_not_confirmed")

        if candidate.currency.strip():
            checks.append("currency_present")
        else:
            failures.append("missing_currency")

        if _is_https_url(candidate.evidence_url):
            checks.append("evidence_link_present")
        else:
            failures.append("missing_verifiable_evidence")

        if candidate.issuer_reference and candidate.issuer_reference.strip():
            checks.append("issuer_reference_present")
        else:
            failures.append("missing_issuer_reference")

        if candidate.redemption_method and candidate.redemption_method.strip():
            checks.append("redemption_path_present")
        else:
            failures.append("missing_redemption_path")

        if candidate.source_confirmed:
            checks.append("source_confirmation_recorded")
        else:
            failures.append("source_not_confirmed")

        if candidate.authorization_confirmed:
            checks.append("authorization_recorded")
        else:
            failures.append("authorization_not_confirmed")

        status = "verified_receivable" if not failures else "needs_verification"
        return Evaluation(
            candidate_id=candidate.candidate_id,
            status=status,
            checks=tuple(checks + failures),
            evaluated_at=datetime.now(timezone.utc).isoformat(),
        )

    def scan(self, sources: Iterable[CandidateSource]) -> list[Evaluation]:
        """Evaluate candidates returned by configured sources; never assumes payout."""
        results: list[Evaluation] = []
        for source in sources:
            for candidate in source.discover():
                results.append(self.evaluate(candidate))
        return results

    @staticmethod
    def payout_eligibility(evaluation: Evaluation) -> bool:
        """A verified candidate may be reviewed for redemption; this is not a payout."""
        return evaluation.is_receivable

    @staticmethod
    def to_dict(evaluation: Evaluation) -> dict[str, object]:
        return asdict(evaluation)
