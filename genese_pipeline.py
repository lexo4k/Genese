#!/usr/bin/env python3
"""Safe opportunity triage for GÊNESE PAY.

This module ranks public leads for human review. It never probes targets, submits
reports/applications, claims rewards, handles credentials, or initiates payments.
Unknown eligibility, deadlines, payment terms, and evidence remain explicitly unknown.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def classify(item: dict[str, Any]) -> dict[str, Any]:
    """Return a conservative review record; never infer approval or income."""
    row = dict(item)
    url = str(row.get("url") or row.get("url_oficial") or "")
    title = str(row.get("programa") or row.get("titulo") or row.get("title") or "Oportunidade sem título")
    provider_evidence = str(row.get("provider_evidence_url") or "")
    provider_verified = row.get("provider_verified") is True and provider_evidence.startswith("https://")
    amount_valid = isinstance(row.get("received_amount"), (int, float)) and not isinstance(row.get("received_amount"), bool) and row.get("received_amount") >= 0
    currency_valid = isinstance(row.get("received_currency"), str) and len(row.get("received_currency").strip()) == 3
    transaction_valid = bool(str(row.get("transaction_id") or "").strip())
    official_evidence = str(row.get("official_evidence_url") or "")
    explicit_eligibility = (row.get("eligibility_verified") is True or row.get("requisitos_verificados") is True) and official_evidence.startswith("https://")
    explicit_deadline = row.get("deadline_verified") is True and official_evidence.startswith("https://")
    explicit_payment_terms = row.get("payment_terms_verified") is True and official_evidence.startswith("https://")
    explicit_payout = (row.get("payment_confirmed") is True or row.get("pagamento_confirmado") is True) and provider_verified and transaction_valid
    accepted_work = row.get("work_accepted") is True and official_evidence.startswith("https://")
    received = row.get("funds_received") is True and provider_verified and transaction_valid and amount_valid and currency_valid

    if received:
        status = "dinheiro_recebido"
    elif explicit_payout:
        status = "pagamento_confirmado_pelo_provedor"
    elif accepted_work:
        status = "trabalho_aceito_pagamento_pendente"
    elif url.startswith("https://") and explicit_eligibility and explicit_deadline and explicit_payment_terms:
        status = "oportunidade_verificada_requer_acao_autorizada"
    else:
        status = "pista_nao_verificada"

    row.update({
        "titulo_normalizado": title,
        "url_oficial": url if url.startswith("https://") else None,
        "status_pipeline": status,
        "elegibilidade_verificada": explicit_eligibility,
        "prazo_verificado": explicit_deadline,
        "termos_pagamento_verificados": explicit_payment_terms,
        "trabalho_aceito": accepted_work,
        "pagamento_confirmado": explicit_payout,
        "dinheiro_recebido": received,
        "evidencia_oficial_verificada": official_evidence.startswith("https://"),
        "evidencia_pagador_verificada": provider_verified and transaction_valid,
        "receita_contabilizavel": bool(received and amount_valid and currency_valid),
        "proximo_passo": _next_step(status),
        "aviso": "A listagem ou contagem de buscas não é receita. Confirme as regras na fonte oficial.",
    })
    if not row["receita_contabilizavel"]:
        row["receita_contabilizavel"] = False
    return row


def _next_step(status: str) -> str:
    return {
        "pista_nao_verificada": "Revisar manualmente a fonte oficial, elegibilidade, prazo, escopo e termos de pagamento.",
        "oportunidade_verificada_requer_acao_autorizada": "Solicitar aprovação do titular e executar apenas as etapas permitidas pelo programa ou contrato.",
        "trabalho_aceito_pagamento_pendente": "Acompanhar prazo e comprovante do pagador; não contar como dinheiro recebido.",
        "pagamento_confirmado_pelo_provedor": "Conciliar com extrato/registro do titular antes de marcar como recebido.",
        "dinheiro_recebido": "Guardar a evidência de recebimento e conciliar o valor e a moeda.",
    }[status]


def build_report(items: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [classify(item) for item in items if isinstance(item, dict)]
    counts: dict[str, int] = {}
    for row in rows:
        status = row["status_pipeline"]
        counts[status] = counts.get(status, 0) + 1
    received = [row for row in rows if row["receita_contabilizavel"]]
    totals: dict[str, float] = {}
    for row in received:
        currency = str(row["received_currency"]).upper()
        totals[currency] = round(totals.get(currency, 0.0) + float(row["received_amount"]), 8)
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items_reviewed": len(rows),
        "status_counts": counts,
        "confirmed_received_totals_by_currency": totals,
        "confirmed_received_count": len(received),
        "items": rows,
        "safety": {
            "active_target_scanning": False,
            "automatic_submissions": False,
            "automatic_transfers": False,
            "note": "Somente fontes públicas; ação humana e autorização explícita são necessárias quando aplicável.",
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
    print(json.dumps({key: report[key] for key in ("items_reviewed", "status_counts", "confirmed_received_totals_by_currency", "confirmed_received_count", "safety")}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
