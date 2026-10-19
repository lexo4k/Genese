#!/usr/bin/env python3
"""GÊNESE PAY: trilha de prontidão jurídica, crédito e receita.

Este módulo organiza preparação e evidências. Não constitui empresa, não gera CPF/CNPJ,
não solicita crédito em nome de terceiros e não cria saldo ou dinheiro.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_DEFAULT = Path("genese_capacidade.json")

LEGAL_CHECKS = {
    "responsavel_legal_definido": "Definir responsável legal adequado para o registro",
    "atividade_e_modelo_definidos": "Definir atividade econômica e modelo de operação",
    "nome_e_endereco_verificados": "Verificar nome empresarial e endereço permitido",
    "registro_oficial_concluido": "Concluir registro na autoridade competente",
    "cadastro_fiscal_confirmado": "Confirmar cadastro fiscal oficial, quando aplicável",
    "conta_empresarial_verificada": "Abrir e verificar conta empresarial, se necessária",
}
CREDIT_CHECKS = {
    "identidade_e_empresa_verificadas": "Concluir verificações de identidade/empresa pelo provedor",
    "receitas_documentadas": "Manter contratos, faturas e receitas recebidas comprováveis",
    "despesas_documentadas": "Manter despesas e obrigações documentadas",
    "historico_pagamentos": "Manter histórico verdadeiro de pagamentos e dívidas",
    "oferta_oficial_de_credito": "Obter proposta de crédito oficial com termos claros",
}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def empty_state() -> dict[str, Any]:
    return {
        "schema_version": 1,
        "created_at": now(),
        "legal_entity": {
            "status": "not_registered",
            "legal_name": None,
            "registration_number": None,
            "checks": {key: False for key in LEGAL_CHECKS},
            "evidence": {},
        },
        "credit": {
            "status": "not_assessed",
            "approved_amount": 0,
            "currency": "BRL",
            "checks": {key: False for key in CREDIT_CHECKS},
            "evidence": {},
        },
        "revenue": {
            "confirmed_received": 0,
            "currency": "BRL",
            "payments": [],
        },
        "audit": [],
        "limitations": [
            "O sistema não cria personalidade jurídica nem identificadores oficiais.",
            "Marcar um item ou inserir uma URL não verifica a evidência automaticamente.",
            "Crédito aprovado e dinheiro recebido só podem ser registrados após confirmação externa.",
        ],
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return empty_state()
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("arquivo inválido; dados existentes não foram sobrescritos") from exc
    if not isinstance(data, dict) or data.get("schema_version") != 1:
        raise ValueError("versão ou estrutura do arquivo não reconhecida")
    for section in ("legal_entity", "credit", "revenue", "audit"):
        if section not in data:
            raise ValueError(f"arquivo incompleto: {section}")
    return data


def save_state(path: Path, state: dict[str, Any]) -> None:
    path.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def update_check(state: dict[str, Any], area: str, check: str, completed: bool,
                 evidence_url: str | None = None) -> dict[str, Any]:
    maps = {"legal": LEGAL_CHECKS, "credit": CREDIT_CHECKS}
    if area not in maps or check not in maps[area]:
        raise ValueError("área ou verificação desconhecida")
    if not isinstance(completed, bool):
        raise ValueError("completed precisa ser true ou false")
    section = state["legal_entity"] if area == "legal" else state["credit"]
    section["checks"][check] = completed
    if evidence_url is not None:
        if not isinstance(evidence_url, str) or not evidence_url.startswith("https://") or any(c.isspace() for c in evidence_url):
            raise ValueError("evidence_url precisa ser uma URL HTTPS")
        section["evidence"][check] = {
            "url": evidence_url,
            "automatically_verified": False,
            "recorded_at": now(),
        }
    if area == "legal":
        section["status"] = "preparation_in_progress"
        if all(section["checks"].values()):
            # A checklist alone is not proof of registration.
            section["status"] = "ready_for_external_review"
    else:
        section["status"] = "preparation_in_progress"
        if all(section["checks"].values()):
            section["status"] = "ready_for_provider_assessment"
    state["audit"].append({
        "event": "check_updated",
        "area": area,
        "check": check,
        "completed": completed,
        "at": now(),
    })
    return state


def record_confirmed_payment(state: dict[str, Any], amount: float, currency: str,
                             external_reference: str, verification_source: str) -> dict[str, Any]:
    if isinstance(amount, bool) or not isinstance(amount, (int, float)) or amount <= 0:
        raise ValueError("amount precisa ser positivo")
    if currency not in {"BRL", "USD", "EUR", "BTC", "USDT", "USDC"}:
        raise ValueError("moeda não permitida")
    for value, name in ((external_reference, "external_reference"),
                        (verification_source, "verification_source")):
        if not isinstance(value, str) or not value.strip():
            raise ValueError(f"{name} é obrigatório")
    if not verification_source.startswith("https://"):
        raise ValueError("verification_source precisa ser HTTPS")
    payment = {
        "amount": round(float(amount), 8 if currency in {"BTC", "USDT", "USDC"} else 2),
        "currency": currency,
        "external_reference": external_reference.strip(),
        "verification_source": verification_source,
        "verification_automated": False,
        "recorded_at": now(),
        "status": "externally_reported_pending_independent_verification",
    }
    state["revenue"]["payments"].append(payment)
    state["audit"].append({"event": "payment_evidence_recorded", "at": now()})
    # Do not increase confirmed_received from user-entered evidence alone.
    return state


def summary(state: dict[str, Any]) -> dict[str, Any]:
    return {
        "legal_entity_status": state["legal_entity"]["status"],
        "legal_registration_number": state["legal_entity"]["registration_number"],
        "credit_status": state["credit"]["status"],
        "credit_approved_amount": state["credit"]["approved_amount"],
        "confirmed_received": state["revenue"]["confirmed_received"],
        "pending_payment_evidence": len(state["revenue"]["payments"]),
        "audit_events": len(state["audit"]),
        "note": "Checklist e referências não substituem confirmação oficial independente.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Prontidão jurídica, crédito e receita do GÊNESE PAY")
    parser.add_argument("--db", type=Path, default=DB_DEFAULT)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    state = load_state(args.db)
    if args.json:
        print(json.dumps({"summary": summary(state), "state": state}, ensure_ascii=False, indent=2))
    else:
        s = summary(state)
        print(f'Jurídico: {s["legal_entity_status"]} | Crédito: {s["credit_status"]} | '
              f'Receita confirmada: {s["confirmed_received"]} {state["revenue"]["currency"]}')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
