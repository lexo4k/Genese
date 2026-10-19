#!/usr/bin/env python3
"""GÊNESE PAY: identidade técnica e trilha auditável do agente autônomo.

Este módulo identifica o software, registra decisões e controla tarefas locais.
Não representa pessoa física/jurídica, não cria CPF, não assume obrigações legais,
não acessa contas de terceiros e não movimenta dinheiro.
"""
from __future__ import annotations

import argparse
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

AGENT_ID = "genese-pay-agent-v1"
AGENT_NAME = "GÊNESE PAY"
DB_DEFAULT = Path("agente_auditoria.json")
ALLOWED_TASK_TYPES = {"discover_public_opportunity", "prepare_digital_product", "review_offer"}
STATUSES = {"queued", "running", "completed", "blocked", "failed"}


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _required_text(value: Any, name: str, limit: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} é obrigatório")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{name} excede {limit} caracteres")
    return value


def new_task(data: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(data, dict):
        raise ValueError("a tarefa precisa ser um objeto")
    task_type = _required_text(data.get("tipo"), "tipo", 80)
    if task_type not in ALLOWED_TASK_TYPES:
        raise ValueError("tipo de tarefa não permitido")
    return {
        "id": secrets.token_hex(8),
        "agent_id": AGENT_ID,
        "tipo": task_type,
        "objetivo": _required_text(data.get("objetivo"), "objetivo"),
        "fonte_url": data.get("fonte_url"),
        "status": "queued",
        "criado_em": now(),
        "atualizado_em": now(),
        "resultado": None,
        "efeito_externo": False,
        "receita_confirmada": 0,
        "historico": [{"evento": "tarefa_criada", "em": now()}],
    }


def transition(task: dict[str, Any], status: str, note: str) -> dict[str, Any]:
    if status not in STATUSES:
        raise ValueError("status inválido")
    if task.get("status") not in {"queued", "running"}:
        raise ValueError("somente tarefas na fila ou em execução podem mudar de estado")
    note = _required_text(note, "nota", 2000)
    task["status"] = status
    task["atualizado_em"] = now()
    task["resultado"] = note
    task["historico"].append({"evento": "status_alterado", "status": status, "nota": note, "em": now()})
    # Nunca inferir receita de uma tarefa ou de um texto inserido.
    task["receita_confirmada"] = 0
    return task


def load_db(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"agent_id": AGENT_ID, "agent_name": AGENT_NAME, "tasks": [], "audit": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        raise ValueError("arquivo de auditoria inválido; nenhum dado foi sobrescrito") from exc
    if not isinstance(data, dict) or data.get("agent_id") != AGENT_ID or not isinstance(data.get("tasks"), list):
        raise ValueError("arquivo de auditoria não corresponde a este agente")
    data.setdefault("audit", [])
    return data


def save_db(path: Path, data: dict[str, Any]) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def add_task(db: dict[str, Any], task: dict[str, Any]) -> None:
    db["tasks"].append(task)
    db["audit"].append({"evento": "tarefa_adicionada", "task_id": task["id"], "em": now()})


def main() -> int:
    parser = argparse.ArgumentParser(description="Identidade técnica e auditoria local do GÊNESE PAY")
    parser.add_argument("--db", type=Path, default=DB_DEFAULT)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--new-task", choices=sorted(ALLOWED_TASK_TYPES))
    parser.add_argument("--goal", help="Objetivo da tarefa")
    args = parser.parse_args()
    db = load_db(args.db)
    if args.new_task:
        task = new_task({"tipo": args.new_task, "objetivo": args.goal or ""})
        add_task(db, task)
        save_db(args.db, db)
    result = {
        "agent_id": AGENT_ID,
        "agent_name": AGENT_NAME,
        "agent_kind": "software_agent",
        "legal_person": False,
        "cpf": None,
        "can_move_money": False,
        "confirmed_revenue": 0,
        "task_count": len(db["tasks"]),
        "tasks": db["tasks"],
        "audit_events": len(db["audit"]),
        "limitations": [
            "identidade técnica não é identidade civil",
            "nenhuma tarefa comprova pagamento",
            "receita só pode ser contabilizada após confirmação independente",
        ],
    }
    print(json.dumps(result, ensure_ascii=False, indent=2) if args.json else
          f'{AGENT_NAME} | ID: {AGENT_ID} | tarefas: {len(db["tasks"])} | receita confirmada: 0')
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
