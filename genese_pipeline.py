#!/usr/bin/env python3
"""Safe opportunity triage for GÊNESE PAY.

Public opportunity data is untrusted input. This module does not independently
verify official pages or payment providers, so fields in a JSON row can never,
by themselves, establish that money was received. It never probes targets,
submits reports/applications, claims rewards, handles credentials, or initiates
payments.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _https_url(value: Any) -> bool:
    return isinstance(value, str) and value.startswith("https://") and len(value) > 8


def classify(item: dict[str, Any]) -> dict[str, Any]:
    """Classify a lead without mistaking self-reported fields for verified facts."""
    row = dict(item)
    url = str(row.get("url") or row.get("url_oficial") or "")
    title = str(row.get("programa") or row.get("titulo") or row.get("title") or "Oportunidade sem título")
    official_evidence = row.get("official_evidence_url")
    official_url_present = _https_url(url)
    official_evidence_url_present = _https_url(official_evidence)

    # These flags are annotations supplied by a human/source, not independently
    # authenticated facts. Require an explicit manual-review marker to promote a lead.
    eligibility_reviewed = (
        row.get("eligibility_verified") is True or row.get("requisitos_verificados") is True
    )
    deadline_reviewed = row.get("deadline_verified") is True
    payment_terms_reviewed = row.get("payment_terms_verified") is True
    manual_review_completed = row.get("manual_review_completed") is True
    verified_opportunity = (
        official_url_present
        and official_evidence_url_present
        and manual_review_completed
        and eligibility_reviewed
        and deadline_reviewed
        and payment_terms_reviewed
    )

    accepted_work_claimed = row.get("work_accepted") is True
    payment_claimed = (
        row.get("payment_confirmed") is True or row.get("pagamento_confirmado") is True
    )
    received_claimed = row.get("funds_received") is True

    # No authenticated provider adapter or signed receipt ledger is implemented
    # in this pipeline. A URL, transaction ID, amount, or boolean in the public
    # opportunities JSON is not sufficient evidence of an actual receipt.
    if received_claimed:
        status = "recebimento_declarado_nao_autenticado"
    elif payment_claimed:
        status = "pagamento_declarado_pendente_de_verificacao"
    elif accepted_work_claimed and manual_review_completed and official_evidence_url_present:
        status = "trabalho_aceito_pagamento_pendente"
    elif verified_opportunity:
        status = "oportunidade_verificada_requer_acao_autorizada"
    else:
        status = "pista_nao_verificada"

    row.update({
        "titulo_normalizado": title,
        "url_oficial": url if official_url_present else None,
        "status_pipeline": status,
        "elegibilidade_revisada": bool(eligibility_reviewed and manual_review_completed),
        "prazo_revisado": bool(deadline_reviewed and manual_review_completed),
        "termos_pagamento_revisados": bool(payment_terms_reviewed and manual_review_completed),
        "revisao_manual_declarada": manual_review_completed,
        "evidencia_oficial_url_https": official_evidence_url_present,
        "trabalho_aceito_declarado": accepted_work_claimed,
        "pagamento_declarado": payment_claimed,
        "recebimento_declarado": received_claimed,
        "evidencia_pagador_autenticada": False,
        "dinheiro_recebido": False,
        "receita_contabilizavel": False,
        "proximo_passo": _next_step(status),
        "aviso": (
            "URLs HTTPS e campos informados não autenticam regras nem pagamentos. "
            "A listagem ou contagem de buscas não é receita."
        ),
    })
    return row


def _next_step(status: str) -> str:
    return {
        "pista_nao_verificada": "Revisar manualmente a fonte oficial, elegibilidade, prazo, escopo e termos de pagamento.",
        "oportunidade_verificada_requer_acao_autorizada": "Obter autorização do titular e seguir somente as etapas permitidas pelo programa ou contrato.",
        "trabalho_aceito_pagamento_pendente": "Confirmar a aceitação na fonte oficial e acompanhar prazo e comprovante do pagador; não contar como recebido.",
        "pagamento_declarado_pendente_de_verificacao": "Verificar o estado na conta do titular ou no canal oficial do provedor; não contar como recebido.",
        "recebimento_declarado_nao_autenticado": "Conciliar manualmente com o extrato do titular ou integrar verificação autenticada do provedor antes de contabilizar.",
    }[status]


def build_report(items: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [classify(item) for item in items if isinstance(item, dict)]
    counts: dict[str, int] = {}
    for row in rows:
        status = row["status_pipeline"]
        counts[status] = counts.get(status, 0) + 1

    # Deliberately zero: no trusted provider integration or signed receipt ledger
    # is connected to this report yet.
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items_reviewed": len(rows),
        "status_counts": counts,
        "confirmed_received_totals_by_currency": {},
        "confirmed_received_count": 0,
        "payment_verification_enabled": False,
        "payment_verification_note": (
            "Nenhuma entrada deste arquivo prova recebimento. Exija conciliação "
            "por integração autenticada do provedor antes de registrar receita."
        ),
        "items": rows,
        "safety": {
            "active_target_scanning": False,
            "automatic_submissions": False,
            "automatic_transfers": False,
            "note": "Somente pistas públicas; ação humana e autorização explícita são necessárias quando aplicável.",
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Classifica pistas públicas do GÊNESE sem inventar receita.")
    parser.add_argument("--input", default="genese_oportunidades.json", help="JSON com uma lista em oportunidades/items/anuncios")
    parser.add_argument("--output", default="genese_pipeline_report.json")
    args = parser.parse_args()
    source = Path(args.input)
    if not source.exists():
        report = build_report([])
        report["input_error"] = f"Arquivo de entrada não encontrado: {source}"
    else:
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
            if isinstance(payload, list):
                items = payload
            elif isinstance(payload, dict):
                candidate = payload.get("oportunidades", payload.get("items", payload.get("anuncios", [])))
                items = candidate if isinstance(candidate, list) else []
            else:
                items = []
            report = build_report(items)
        except (OSError, json.JSONDecodeError) as exc:
            report = build_report([])
            report["input_error"] = f"{type(exc).__name__}: {exc}"
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "items_reviewed", "status_counts", "confirmed_received_totals_by_currency",
        "confirmed_received_count", "payment_verification_enabled", "safety"
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
