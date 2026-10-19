#!/usr/bin/env python3
"""GÊNESE PAY: transforma pistas públicas em fichas de fontes pagadoras a validar.

Este módulo NÃO cria dinheiro nem transforma uma pista em pagador confirmado.
Gera um plano verificável para cada oportunidade encontrada pelo motor existente.
"""
from __future__ import annotations

import argparse
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

DEFAULT_INPUT = Path("genese_receita.json")
DEFAULT_OUTPUT = Path("fontes_pagadoras.json")


def _safe_https(url: Any) -> bool:
    if not isinstance(url, str):
        return False
    try:
        parsed = urlparse(url)
        return parsed.scheme == "https" and bool(parsed.netloc)
    except ValueError:
        return False


def build_payer_cards(report: dict[str, Any]) -> dict[str, Any]:
    """Create one actionable validation card per unique HTTPS opportunity."""
    opportunities = report.get("oportunidades", [])
    if not isinstance(opportunities, list):
        opportunities = []

    cards: list[dict[str, Any]] = []
    seen: set[str] = set()
    for item in opportunities:
        if not isinstance(item, dict):
            continue
        url = item.get("url")
        title = item.get("titulo")
        if not _safe_https(url) or url in seen:
            continue
        seen.add(url)
        source = str(item.get("fonte") or "Fonte pública não classificada")
        cards.append({
            "nome": str(title or "Oportunidade sem título"),
            "url": url,
            "origem": source,
            "tipo_de_fonte": (
                "bug_bounty_ou_recompensa"
                if any(term in (source + " " + str(title)).casefold()
                       for term in ("bounty", "recompensa", "reward", "issue"))
                else "oportunidade_publica_a_classificar"
            ),
            "status": "precisa_validacao",
            "pagador_confirmado": False,
            "valor_confirmado": None,
            "metodo_de_pagamento": "confirmar nas regras oficiais",
            "provas_necessarias": [
                "Página oficial e regras atuais do programa",
                "Elegibilidade e escopo autorizados",
                "Critérios de aceitação e valor da recompensa",
                "Método, mínimo e prazo de pagamento",
                "Comprovante externo do pagamento após conclusão e aprovação",
            ],
            "proximas_acoes": [
                "Abrir o link HTTPS e verificar se o programa continua ativo",
                "Ler as regras oficiais e confirmar que a participação é permitida",
                "Executar somente a tarefa autorizada e dentro do escopo",
                "Submeter o trabalho pelos canais oficiais, se elegível",
                "Atualizar para pagamento_confirmado apenas com comprovante verificável",
            ],
            "aviso": "Esta ficha é um plano de validação, não uma oferta garantida nem receita.",
        })

    return {
        "produto": "GENESE PAY",
        "gerado_em_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fichas_geradas": len(cards),
        "pagadores_confirmados": 0,
        "receita_confirmada": 0,
        "fichas": cards,
        "regra": "Nunca contar uma oportunidade como dinheiro recebido sem prova externa confiável.",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera fichas de fontes pagadoras a validar.")
    parser.add_argument("--input", default=str(DEFAULT_INPUT), help="relatório de oportunidades JSON")
    parser.add_argument("--output", default=str(DEFAULT_OUTPUT), help="arquivo de fichas JSON")
    args = parser.parse_args()
    try:
        data = json.loads(Path(args.input).read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError) as exc:
        parser.error(f"não foi possível ler o relatório de entrada: {exc}")
    if not isinstance(data, dict):
        parser.error("o relatório de entrada precisa ser um objeto JSON")
    result = build_payer_cards(data)
    Path(args.output).write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Fichas geradas: {result['fichas_geradas']}")
    print("Pagadores confirmados: 0 (exigem prova externa de pagamento)")
    print(f"Arquivo: {args.output}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
