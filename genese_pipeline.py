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


def _has_detail(value: Any) -> bool:
    """Reject empty and placeholder text as evidence of reviewed terms."""
    if isinstance(value, bool) or value is None:
        return False
    if isinstance(value, (int, float)):
        return value > 0
    if not isinstance(value, str):
        return False
    normalized = value.strip().casefold()
    placeholders = (
        "não verificado", "não verificada", "não verificados", "não verificados;",
        "não informado", "não informada", "nao verificado", "nao verificada",
        "nao informado", "unknown", "not verified", "not provided", "n/a",
    )
    return bool(normalized) and not normalized.startswith(placeholders)


def classify(item: dict[str, Any]) -> dict[str, Any]:
    """Classify a lead without mistaking self-reported fields for verified facts."""
    row = dict(item)
    url = str(row.get("url") or row.get("url_oficial") or "")
    title = str(row.get("programa") or row.get("titulo") or row.get("title") or "Oportunidade sem título")
    official_evidence = row.get("official_evidence_url")
    official_url_present = _https_url(url)
    official_evidence_url_present = _https_url(official_evidence)

    # These flags and details are declarations from a human/source, not
    # independently authenticated facts. Keep the status explicitly manual-review.
    official_source_reviewed = row.get("official_source_verified") is True
    eligibility_flag = (
        row.get("eligibility_verified") is True or row.get("requisitos_verificados") is True
    )
    deadline_flag = row.get("deadline_verified") is True
    payment_terms_flag = row.get("payment_terms_verified") is True
    eligibility_details_present = _has_detail(
        row.get("eligibility_details") or row.get("requisitos") or row.get("idade_minima")
    )
    deadline_details_present = _has_detail(
        row.get("deadline_at") or row.get("deadline") or row.get("deadline_details") or row.get("prazo")
    )
    payment_terms_details_present = _has_detail(
        row.get("payment_terms") or row.get("payment_terms_details") or row.get("contrato_e_pagamento")
    )
    manual_review_completed = row.get("manual_review_completed") is True

    eligibility_reviewed = eligibility_flag and eligibility_details_present
    deadline_reviewed = deadline_flag and deadline_details_present
    payment_terms_reviewed = payment_terms_flag and payment_terms_details_present
    manually_reviewed_opportunity = (
        official_url_present
        and official_evidence_url_present
        and official_source_reviewed
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
    # in this pipeline. A URL, transaction ID, amount, or boolean in JSON is not
    # sufficient evidence of an actual receipt.
    if received_claimed:
        status = "recebimento_declarado_nao_autenticado"
    elif payment_claimed:
        status = "pagamento_declarado_pendente_de_verificacao"
    elif (
        accepted_work_claimed
        and manual_review_completed
        and official_source_reviewed
        and official_evidence_url_present
    ):
        status = "trabalho_aceito_declarado_pagamento_pendente"
    elif manually_reviewed_opportunity:
        status = "oportunidade_revisada_manual_requer_acao_autorizada"
    else:
        status = "pista_nao_verificada"

    row.update({
        "titulo_normalizado": title,
        "url_https_informada": url if official_url_present else None,
        "status_pipeline": status,
        "fonte_oficial_revisada_declarada": bool(official_source_reviewed and manual_review_completed),
        "detalhes_elegibilidade_presentes": eligibility_details_present,
        "detalhes_prazo_presentes": deadline_details_present,
        "detalhes_termos_pagamento_presentes": payment_terms_details_present,
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
            "URLs HTTPS, flags e textos informados não autenticam regras nem pagamentos. "
            "A listagem ou contagem de buscas não é receita."
        ),
    })
    return row


def _next_step(status: str) -> str:
    return {
        "pista_nao_verificada": "Revisar manualmente a fonte oficial, elegibilidade, prazo, escopo e termos de pagamento.",
        "oportunidade_revisada_manual_requer_acao_autorizada": "A revisão manual foi declarada; confirmar os documentos oficiais e obter autorização antes de qualquer ação.",
        "trabalho_aceito_declarado_pagamento_pendente": "Confirmar a aceitação na fonte oficial e acompanhar prazo e comprovante do pagador; não contar como recebido.",
        "pagamento_declarado_pendente_de_verificacao": "Verificar o estado na conta do titular ou no canal oficial do provedor; não contar como recebido.",
        "recebimento_declarado_nao_autenticado": "Conciliar manualmente com o extrato do titular ou integrar verificação autenticada do provedor antes de contabilizar.",
    }[status]


def load_items(paths: list[str]) -> tuple[list[dict[str, Any]], list[str]]:
    """Load bounty and contractor feeds while preserving each input filename."""
    items: list[dict[str, Any]] = []
    errors: list[str] = []
    for raw_path in paths:
        source = Path(raw_path)
        if not source.exists():
            errors.append(f"Arquivo de entrada não encontrado: {source}")
            continue
        try:
            payload = json.loads(source.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            errors.append(f"{source}: {type(exc).__name__}: {exc}")
            continue

        if isinstance(payload, list):
            candidate = payload
        elif isinstance(payload, dict):
            candidate = None
            for key in ("oportunidades", "items", "anuncios"):
                value = payload.get(key)
                if isinstance(value, list):
                    candidate = value
                    break
            if candidate is None:
                errors.append(f"{source}: nenhuma lista oportunidades/items/anuncios encontrada")
                continue
        else:
            errors.append(f"{source}: formato JSON não suportado")
            continue

        for item in candidate:
            if isinstance(item, dict):
                row = dict(item)
                row.setdefault("fonte_arquivo", source.name)
                items.append(row)
    return items, errors


def build_report(items: list[dict[str, Any]]) -> dict[str, Any]:
    rows = [classify(item) for item in items if isinstance(item, dict)]
    counts: dict[str, int] = {}
    items_by_source: dict[str, int] = {}
    for row in rows:
        status = row["status_pipeline"]
        counts[status] = counts.get(status, 0) + 1
        source = str(row.get("fonte_arquivo") or "origem_nao_informada")
        items_by_source[source] = items_by_source.get(source, 0) + 1

    # Deliberately zero: no trusted provider integration or signed receipt ledger
    # is connected to this report yet.
    return {
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "items_reviewed": len(rows),
        "items_by_source": items_by_source,
        "status_counts": counts,
        "confirmed_received_totals_by_currency": {},
        "confirmed_received_count": 0,
        "payment_verification_enabled": False,
        "payment_verification_note": (
            "Nenhuma entrada destes arquivos prova recebimento. Exija conciliação "
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
    parser.add_argument(
        "--input", action="append", dest="inputs", default=None,
        help="Arquivo JSON de entrada; pode ser repetido para combinar fontes.",
    )
    parser.add_argument("--output", default="genese_pipeline_report.json")
    args = parser.parse_args()
    inputs = args.inputs or ["genese_oportunidades.json"]
    items, input_errors = load_items(inputs)
    report = build_report(items)
    report["input_files"] = inputs
    report["input_errors"] = input_errors
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps({key: report[key] for key in (
        "items_reviewed", "items_by_source", "status_counts",
        "confirmed_received_totals_by_currency", "confirmed_received_count",
        "payment_verification_enabled", "input_errors", "safety",
    )}, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
