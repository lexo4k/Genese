#!/usr/bin/env python3
"""Prioriza oportunidades públicas de recompensas autorizadas para revisão humana.

Não varre alvos, não explora falhas, não acessa contas e não movimenta criptoativos.
Um programa listado não significa que há saldo abandonado nem pagamento garantido.
"""
from __future__ import annotations
import json
import sys
from datetime import datetime, timezone
from genese_autonomo import SOURCES, fetch, parse_programs

KEYWORDS = (
    "crypto", "cryptocurrency", "bitcoin", "btc", "ethereum", "eth",
    "blockchain", "web3", "wallet", "exchange", "defi", "token",
    "smart contract", "solana", "polygon", "lightning", "payment",
)

def main() -> int:
    try:
        status, body = fetch(SOURCES["programas_publicos"], timeout=12, retries=3)
        if status != 200:
            raise RuntimeError(f"Catálogo respondeu HTTP {status}")
        rows = parse_programs(body.decode("utf-8", errors="replace"), limit=5000)
        for row in rows:
            searchable = " ".join((row["programa"], row["url"], row["escopo"])).lower()
            row["relevancia"] = sum(1 for word in KEYWORDS if word in searchable)
            row["tipo"] = "cripto/web3" if row["relevancia"] else "outro"
        rows.sort(key=lambda r: (-r["relevancia"], r["programa"].lower()))
        report = {
            "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            "fonte": SOURCES["programas_publicos"],
            "programas_publicos_lidos": len(rows),
            "oportunidades_cripto_web3": sum(r["relevancia"] > 0 for r in rows),
            "oportunidades": rows,
            "ganhos_confirmados": 0,
            "pagamento_automatico": False,
            "limites": [
                "A lista contém programas públicos de recompensa, não fundos perdidos identificados.",
                "Somente testar ativos expressamente incluídos no escopo e seguir as regras do programa.",
                "O pagamento depende de uma falha válida, relatório aceito e decisão do programa.",
                "Nenhuma conta é acessada e nenhum saldo é movimentado por este coletor."
            ]
        }
        output = json.dumps(report, ensure_ascii=False, indent=2)
        print(output)
        with open("genese_oportunidades.json", "w", encoding="utf-8") as f:
            f.write(output + "\n")
        return 0
    except Exception as exc:
        print(json.dumps({
            "erro": f"{type(exc).__name__}: {exc}",
            "ganhos_confirmados": 0,
            "pagamento_automatico": False
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2

if __name__ == "__main__":
    raise SystemExit(main())
