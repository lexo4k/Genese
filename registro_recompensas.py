#!/usr/bin/env python3
"""Registro auditável de recompensas legítimas do GÊNESE.

Este módulo não procura/explora vulnerabilidades, não acessa contas e não movimenta
fundos. Ele mantém um registro local e só contabiliza pagamentos marcados como pagos
com uma URL HTTPS de evidência fornecida pelo operador.
"""
from __future__ import annotations

import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
from urllib.parse import urlparse
from typing import Any

DEFAULT_DB = Path(os.environ.get("GENESE_REWARDS_DB", "recompensas_registro.json"))


def now() -> str:
    return datetime.now(timezone.utc).isoformat()


def valid_https_url(value: str) -> bool:
    parsed = urlparse(value)
    return parsed.scheme == "https" and bool(parsed.netloc)


def load_db(path: Path = DEFAULT_DB) -> dict[str, Any]:
    if not path.exists():
        return {"schema_version": 1, "updated_at": now(), "rewards": []}
    data = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(data, dict) or not isinstance(data.get("rewards"), list):
        raise ValueError("Formato de registro inválido.")
    return data


def save_db(data: dict[str, Any], path: Path = DEFAULT_DB) -> None:
    data["updated_at"] = now()
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_reward(data: dict[str, Any], title: str, url: str) -> str:
    if not title.strip():
        raise ValueError("O título não pode ficar vazio.")
    if not valid_https_url(url):
        raise ValueError("A URL da oportunidade precisa usar HTTPS.")
    if any(item["url"] == url for item in data["rewards"]):
        raise ValueError("Essa URL já está registrada.")
    next_id = max((int(item["id"]) for item in data["rewards"]), default=0) + 1
    data["rewards"].append({
        "id": next_id,
        "title": title.strip(),
        "url": url,
        "status": "encontrada",
        "valor_aprovado": None,
        "moeda": None,
        "evidencia_aprovacao": None,
        "evidencia_pagamento": None,
        "criada_em": now(),
        "aprovada_em": None,
        "paga_em": None,
    })
    return str(next_id)


def approve_reward(data: dict[str, Any], reward_id: int, amount: float, currency: str, evidence_url: str) -> None:
    item = _get_reward(data, reward_id)
    if item["status"] == "paga":
        raise ValueError("Uma recompensa paga não pode voltar para aprovada.")
    if amount <= 0:
        raise ValueError("O valor aprovado deve ser maior que zero.")
    if not currency.strip() or len(currency.strip()) > 10:
        raise ValueError("Informe um código de moeda válido, por exemplo BRL ou USD.")
    if not valid_https_url(evidence_url):
        raise ValueError("A evidência de aprovação precisa usar HTTPS.")
    item.update({
        "status": "aprovada",
        "valor_aprovado": round(float(amount), 8),
        "moeda": currency.strip().upper(),
        "evidencia_aprovacao": evidence_url,
        "aprovada_em": now(),
    })


def mark_paid(data: dict[str, Any], reward_id: int, evidence_url: str) -> None:
    item = _get_reward(data, reward_id)
    if item["status"] != "aprovada":
        raise ValueError("Só uma recompensa aprovada pode ser marcada como paga.")
    if not item.get("valor_aprovado") or not item.get("evidencia_aprovacao"):
        raise ValueError("Faltam valor e evidência oficial de aprovação.")
    if not valid_https_url(evidence_url):
        raise ValueError("A evidência de pagamento precisa usar HTTPS.")
    item.update({
        "status": "paga",
        "evidencia_pagamento": evidence_url,
        "paga_em": now(),
    })


def _get_reward(data: dict[str, Any], reward_id: int) -> dict[str, Any]:
    for item in data["rewards"]:
        if int(item["id"]) == reward_id:
            return item
    raise ValueError(f"Recompensa ID {reward_id} não encontrada.")


def summary(data: dict[str, Any]) -> dict[str, Any]:
    paid: dict[str, float] = {}
    for item in data["rewards"]:
        if item["status"] == "paga":
            currency = item["moeda"]
            paid[currency] = round(paid.get(currency, 0.0) + float(item["valor_aprovado"]), 8)
    return {
        "oportunidades_registradas": len(data["rewards"]),
        "aprovadas_aguardando_pagamento": sum(x["status"] == "aprovada" for x in data["rewards"]),
        "pagamentos_confirmados_por_moeda": paid,
        "observacao": "Somente itens marcados como pagos com URL HTTPS de evidência entram no total. O registro não verifica a autenticidade da página nem o saldo bancário.",
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Livro auditável de recompensas legítimas do GÊNESE")
    parser.add_argument("--db", type=Path, default=DEFAULT_DB, help="caminho do arquivo JSON local")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("listar", help="listar oportunidades e seus estados")
    sub.add_parser("resumo", help="mostrar pagamentos registrados")
    add = sub.add_parser("adicionar", help="registrar oportunidade pública")
    add.add_argument("--titulo", required=True)
    add.add_argument("--url", required=True)
    approve = sub.add_parser("aprovar", help="registrar valor e evidência de aprovação oficial")
    approve.add_argument("--id", type=int, required=True)
    approve.add_argument("--valor", type=float, required=True)
    approve.add_argument("--moeda", required=True)
    approve.add_argument("--evidencia-url", required=True)
    paid = sub.add_parser("pagar", help="registrar pagamento com evidência oficial")
    paid.add_argument("--id", type=int, required=True)
    paid.add_argument("--evidencia-url", required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        data = load_db(args.db)
        if args.command == "adicionar":
            reward_id = add_reward(data, args.titulo, args.url)
            save_db(data, args.db)
            print(json.dumps({"ok": True, "id": reward_id, "status": "encontrada"}, ensure_ascii=False))
        elif args.command == "aprovar":
            approve_reward(data, args.id, args.valor, args.moeda, args.evidencia_url)
            save_db(data, args.db)
            print(json.dumps({"ok": True, "id": args.id, "status": "aprovada", "receita_confirmada": False}, ensure_ascii=False))
        elif args.command == "pagar":
            mark_paid(data, args.id, args.evidencia_url)
            save_db(data, args.db)
            print(json.dumps({"ok": True, "id": args.id, "status": "paga", "resumo": summary(data)}, ensure_ascii=False))
        elif args.command == "listar":
            print(json.dumps(data, ensure_ascii=False, indent=2))
        elif args.command == "resumo":
            print(json.dumps(summary(data), ensure_ascii=False, indent=2))
        return 0
    except (OSError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"ok": False, "erro": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
