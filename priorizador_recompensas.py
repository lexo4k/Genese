#!/usr/bin/env python3
"""Prioriza programas públicos de recompensa para revisão humana.

A pontuação mede apenas correspondência textual. Não prova vulnerabilidade,
saldo, elegibilidade, pagamento ou autorização para testar qualquer ativo.
"""
from __future__ import annotations

import json
import sys
from datetime import datetime, timezone
from typing import Any

from genese_autonomo import SOURCES, fetch, parse_programs

KEYWORDS = (
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth",
    "blockchain", "web3", "wallet", "exchange", "defi", "token",
    "smart contract", "solana", "polygon", "lightning", "payment",
)


def rank_programs(rows: list[dict[str, str]]) -> list[dict[str, Any]]:
    """Return a ranked copy; ranking is a hint, never a claim of available money."""
    ranked: list[dict[str, Any]] = []
    for row in rows:
        searchable = " ".join(
            (row.get("programa", ""), row.get("url", ""), row.get("escopo", ""))
        ).lower()
        score = sum(1 for word in KEYWORDS if word in searchable)
        ranked.append({
            **row,
            "relevancia": score,
            "tipo": "cripto/web3" if score else "outro",
            "status_financeiro": "nao_verificado",
            "proximo_passo": (
                "Abrir o programa oficial, confirmar escopo e regras de recompensa; "
                "testar somente com autorização explícita."
            ),
        })
    return sorted(ranked, key=lambda row: (-row["relevancia"], row["programa"].lower()))


def build_report(rows: list[dict[str, Any]]) -> dict[str, Any]:
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": SOURCES["programas_publicos"],
        "programas_publicos_lidos": len(rows),
        "oportunidades_cripto_web3": sum(row["relevancia"] > 0 for row in rows),
        "oportunidades": rows,
        "ganhos_confirmados": 0,
        "varredura_de_toda_a_internet": False,
        "varredura_ativa_de_alvos": False,
        "pagamento_automatico": False,
        "pagamento_pix_automatico": False,
        "motivo_sem_pix_automatico": (
            "A listagem não cria direito a pagamento. Recompensas dependem de "
            "validação e pagamento oficial pelo programa; a chave Pix, sozinha, "
            "não autoriza nem inicia transferências."
        ),
        "limites": [
            "A lista contém programas públicos, não fundos perdidos identificados.",
            "Testes somente em ativos expressamente incluídos no escopo e conforme as regras.",
            "O pagamento depende de uma submissão válida, aceite e decisão do programa.",
            "Nenhuma conta é acessada e nenhum saldo é movimentado por este coletor.",
            "O catálogo é uma fonte pública limitada, não uma varredura de toda a internet.",
            "Correspondência por palavra-chave não comprova dinheiro disponível nem pagamento por Pix.",
        ],
    }


def main() -> int:
    try:
        status, body = fetch(SOURCES["programas_publicos"], timeout=12, retries=3)
        if status != 200:
            raise RuntimeError(f"Catálogo respondeu HTTP {status}")
        source_rows = parse_programs(body.decode("utf-8", errors="replace"), limit=5000)
        rows = rank_programs(source_rows)
        report = build_report(rows)
        output = json.dumps(report, ensure_ascii=False, indent=2)
        print(output)
        with open("genese_oportunidades.json", "w", encoding="utf-8") as file:
            file.write(output + "\n")
        return 0
    except Exception as exc:
        print(json.dumps({
            "erro": f"{type(exc).__name__}: {exc}",
            "ganhos_confirmados": 0,
            "pagamento_automatico": False,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
