#!/usr/bin/env python3
"""GÊNESE PAY: contratos de recompensa com financiador e pagamento verificáveis.

Este módulo não cria obrigações para terceiros nem movimenta dinheiro. Ele registra
ofertas de pagadores que aceitam expressamente os termos, exige evidência de
financiamento/compromisso antes de chamar a oferta de garantida e mantém estados
separados para entrega, aprovação e pagamento comprovado.
"""
from __future__ import annotations

import argparse
import json
import secrets
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

DB_DEFAULT = Path("contratos_recompensa.json")
ALLOWED_SCHEMES = ("https://",)


def now() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds")


def _text(value: Any, name: str, limit: int = 2000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{name} é obrigatório")
    value = value.strip()
    if len(value) > limit:
        raise ValueError(f"{name} excede {limit} caracteres")
    return value


def _positive_amount(value: Any) -> float:
    if isinstance(value, bool) or not isinstance(value, (int, float)) or value <= 0:
        raise ValueError("valor da recompensa precisa ser um número positivo")
    if value > 10_000_000:
        raise ValueError("valor excede o limite permitido")
    return round(float(value), 2)


def _https_url(value: Any, name: str) -> str:
    value = _text(value, name, 2000)
    if not value.startswith(ALLOWED_SCHEMES) or any(ch.isspace() for ch in value):
        raise ValueError(f"{name} precisa ser uma URL HTTPS válida")
    return value


def new_offer(data: dict[str, Any]) -> dict[str, Any]:
    """Create a draft offer; it is NOT guaranteed until the payer accepts and funds it."""
    if not isinstance(data, dict):
        raise ValueError("a oferta precisa ser um objeto")
    currency = _text(data.get("moeda", "BRL"), "moeda", 3).upper()
    if currency not in {"BRL", "USD", "EUR"}:
        raise ValueError("moeda aceita: BRL, USD ou EUR")
    return {
        "id": secrets.token_hex(8),
        "criado_em": now(),
        "pagador": _text(data.get("pagador"), "pagador", 160),
        "contato_pagador": _text(data.get("contato_pagador"), "contato_pagador", 250),
        "termos_url": _https_url(data.get("termos_url"), "termos_url"),
        "trabalho": _text(data.get("trabalho"), "trabalho", 3000),
        "criterios_aceitacao": _text(data.get("criterios_aceitacao"), "criterios_aceitacao", 3000),
        "valor": _positive_amount(data.get("valor")),
        "moeda": currency,
        "prazo_utc": _text(data.get("prazo_utc"), "prazo_utc", 80),
        "pagamento_metodo": _text(data.get("pagamento_metodo"), "pagamento_metodo", 200),
        "status": "rascunho",
        "aceite_pagador": None,
        "prova_fundos": None,
        "entrega": None,
        "aprovacao": None,
        "pagamento": None,
        "historico": [{"evento": "rascunho_criado", "em": now()}],
    }


def _event(offer: dict[str, Any], name: str, details: dict[str, Any]) -> None:
    offer["historico"].append({"evento": name, "em": now(), **details})


def accept_offer(offer: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    """Record explicit payer acceptance; requires an HTTPS-verifiable evidence URL."""
    if offer.get("status") != "rascunho":
        raise ValueError("somente rascunhos podem ser aceitos")
    if data.get("aceitou") is not True:
        raise ValueError("o aceite explícito do pagador é obrigatório")
    evidence = _https_url(data.get("evidencia_aceite_url"), "evidencia_aceite_url")
    signer = _text(data.get("nome_responsavel"), "nome_responsavel", 200)
    offer["aceite_pagador"] = {
        "aceitou": True,
        "nome_responsavel": signer,
        "evidencia_url": evidence,
        "registrado_em": now(),
    }
    offer["status"] = "aceito_sem_fundos_verificados"
    _event(offer, "aceite_pagador_registrado", {"evidencia_url": evidence})
    return offer


def record_funding(offer: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    """Only mark reward secured when an external proof/reference is supplied.

    The program records the evidence URL/reference; it does not verify a bank or
    escrow balance automatically. Status makes that limitation explicit.
    """
    if offer.get("status") != "aceito_sem_fundos_verificados":
        raise ValueError("a oferta precisa ter aceite registrado antes")
    proof = _https_url(data.get("evidencia_fundos_url"), "evidencia_fundos_url")
    reference = _text(data.get("referencia_fundos"), "referencia_fundos", 250)
    offer["prova_fundos"] = {
        "evidencia_url": proof,
        "referencia": reference,
        "verificacao_automatica": False,
        "registrado_em": now(),
    }
    offer["status"] = "recompensa_comprometida_pendente_verificacao_externa"
    _event(offer, "prova_de_fundos_informada", {"referencia": reference})
    return offer


def submit_work(offer: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    if offer.get("status") != "recompensa_comprometida_pendente_verificacao_externa":
        raise ValueError("é necessário aceite e evidência de fundos antes da entrega")
    url = _https_url(data.get("entrega_url"), "entrega_url")
    summary = _text(data.get("resumo"), "resumo", 3000)
    offer["entrega"] = {"url": url, "resumo": summary, "enviado_em": now()}
    offer["status"] = "entrega_enviada_aguardando_aprovacao"
    _event(offer, "trabalho_entregue", {"url": url})
    return offer


def review_work(offer: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    if offer.get("status") != "entrega_enviada_aguardando_aprovacao":
        raise ValueError("não existe entrega aguardando aprovação")
    approved = data.get("aprovado")
    if not isinstance(approved, bool):
        raise ValueError("aprovado precisa ser true ou false")
    reviewer = _text(data.get("nome_revisor"), "nome_revisor", 200)
    evidence = _https_url(data.get("evidencia_aprovacao_url"), "evidencia_aprovacao_url")
    offer["aprovacao"] = {
        "aprovado": approved,
        "nome_revisor": reviewer,
        "evidencia_url": evidence,
        "registrado_em": now(),
    }
    offer["status"] = "aprovado_aguardando_pagamento" if approved else "rejeitado"
    _event(offer, "entrega_avaliada", {"aprovado": approved, "evidencia_url": evidence})
    return offer


def record_payment(offer: dict[str, Any], data: dict[str, Any]) -> dict[str, Any]:
    if offer.get("status") != "aprovado_aguardando_pagamento":
        raise ValueError("somente uma entrega aprovada pode ser marcada como paga")
    proof = _https_url(data.get("comprovante_url"), "comprovante_url")
    txid = _text(data.get("referencia_transacao"), "referencia_transacao", 250)
    amount = _positive_amount(data.get("valor_pago"))
    if amount < offer["valor"]:
        raise ValueError("valor pago é inferior à recompensa contratada")
    offer["pagamento"] = {
        "comprovante_url": proof,
        "referencia_transacao": txid,
        "valor_pago": amount,
        "moeda": offer["moeda"],
        "registrado_em": now(),
        "confirmacao_automatica": False,
    }
    offer["status"] = "pagamento_informado_pendente_confirmacao_externa"
    _event(offer, "pagamento_informado", {"referencia_transacao": txid, "valor_pago": amount})
    return offer


def confirmed_payment(offer: dict[str, Any], external_confirmation: dict[str, Any]) -> dict[str, Any]:
    """Require a separate external reconciliation reference to confirm receipt."""
    if offer.get("status") != "pagamento_informado_pendente_confirmacao_externa":
        raise ValueError("não há pagamento aguardando confirmação externa")
    ref = _text(external_confirmation.get("referencia_confirmacao"), "referencia_confirmacao", 250)
    evidence = _https_url(external_confirmation.get("evidencia_confirmacao_url"), "evidencia_confirmacao_url")
    offer["pagamento"]["confirmacao_externa"] = {
        "referencia": ref,
        "evidencia_url": evidence,
        "confirmado_em": now(),
    }
    offer["status"] = "pagamento_confirmado_por_evidencia_registrada"
    _event(offer, "confirmacao_externa_registrada", {"referencia": ref})
    return offer


def load_db(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        if not isinstance(data, dict) or not isinstance(data.get("ofertas"), list):
            raise ValueError("formato de banco inválido")
        return data
    except FileNotFoundError:
        return {"produto": "GENESE PAY", "ofertas": []}


def save_db(path: Path, db: dict[str, Any]) -> None:
    path.write_text(json.dumps(db, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def main() -> int:
    parser = argparse.ArgumentParser(description="Registro de ofertas e recompensas com evidências.")
    parser.add_argument("--db", default=str(DB_DEFAULT))
    parser.add_argument("action", choices=["list", "new"])
    parser.add_argument("--json", help="arquivo JSON com os campos da nova oferta")
    args = parser.parse_args()
    path = Path(args.db)
    db = load_db(path)
    if args.action == "new":
        if not args.json:
            parser.error("--json é obrigatório para action=new")
        try:
            data = json.loads(Path(args.json).read_text(encoding="utf-8"))
            offer = new_offer(data)
        except (OSError, json.JSONDecodeError, ValueError) as exc:
            parser.error(str(exc))
        db["ofertas"].append(offer)
        save_db(path, db)
        print(json.dumps({"id": offer["id"], "status": offer["status"], "valor": offer["valor"], "moeda": offer["moeda"]}, ensure_ascii=False))
    else:
        print(json.dumps(db, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
