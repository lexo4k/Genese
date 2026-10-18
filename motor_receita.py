#!/usr/bin/env python3
"""GÊNESE: motor de descoberta de oportunidades públicas de receita legítima.

Consulta apenas diretórios públicos e issues públicas. Não testa alvos, não envia
propostas, não cria contas, não acessa carteiras privadas e não executa pagamentos.
Resultados são pistas para avaliação, nunca dinheiro confirmado.
"""
from __future__ import annotations

import argparse
import json
import re
import sys
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

from genese_autonomo import SOURCES, fetch, parse_programs

GITHUB_SEARCH = "https://api.github.com/search/issues?q={query}&per_page=100"
OUT_FILE = Path("genese_receita.json")
MONEY_RE = re.compile(r"(?:\$\s?\d|\d+\s?(?:usd|usdt|usdc|btc|eth|dollars?)|bounty|reward|prize|recompensa|premio|prêmio)", re.I)
CRYPTO_RE = re.compile(r"(crypto|bitcoin|\bbtc\b|ethereum|\beth\b|web3|blockchain|wallet|defi|solana|smart contract|lightning)", re.I)
QUERIES = (
    '"bounty" is:issue is:open',
    '"reward" is:issue is:open',
    '"paid" "issue" is:issue is:open',
)


def _github_issues(payload: str) -> list[dict[str, Any]]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    items = data.get("items", []) if isinstance(data, dict) else []
    if not isinstance(items, list):
        return []
    results: list[dict[str, Any]] = []
    seen: set[str] = set()
    for issue in items:
        if not isinstance(issue, dict) or issue.get("pull_request"):
            continue
        url = issue.get("html_url")
        title = issue.get("title")
        body = issue.get("body") or ""
        if not isinstance(url, str) or not url.startswith("https://github.com/"):
            continue
        if not isinstance(title, str) or url in seen:
            continue
        text = title + " " + body
        if not MONEY_RE.search(text):
            continue
        seen.add(url)
        results.append({
            "titulo": title.strip(),
            "url": url,
            "fonte": "GitHub Issues público",
            "repositorio": (issue.get("repository_url") or "").removeprefix("https://api.github.com/repos/"),
            "sinal_de_recompensa": "texto menciona recompensa ou valor; não verificado",
            "relevancia_cripto": bool(CRYPTO_RE.search(text)),
            "valor_confirmado": None,
            "status": "nao_verificado",
            "acao": "Abrir a issue e confirmar regras, valor, elegibilidade e atividade antes de participar.",
        })
    return results


def collect_opportunities() -> dict[str, Any]:
    checked_at = datetime.now(timezone.utc).isoformat(timespec="seconds")
    report: dict[str, Any] = {
        "produto": "GÊNESE",
        "timestamp_utc": checked_at,
        "fontes_consultadas": [],
        "oportunidades": [],
        "resumo": {
            "fontes_ok": 0,
            "candidatas_encontradas": 0,
            "candidatas_cripto_web3": 0,
            "receita_confirmada": 0,
            "saldo_binance_consultado": False,
            "transferencia_executada": False,
        },
        "seguranca": [
            "Não há exploração automática nem teste de sistemas.",
            "Participar apenas quando as regras e a autorização forem explícitas.",
            "Texto que menciona bounty/reward não comprova valor, elegibilidade ou pagamento.",
            "Nenhuma chave privada, senha, API key de conta ou seed phrase é solicitada.",
            "Receita e saldo só são contabilizados após evidência externa confiável.",
        ],
    }
    merged: dict[str, dict[str, Any]] = {}

    # Catálogo público de programas que declaram oferecer bug bounty.
    try:
        status, body = fetch(SOURCES["programas_publicos"], timeout=12, retries=2)
        programs = parse_programs(body.decode("utf-8", errors="replace"), limit=5000) if status == 200 else []
        for row in programs:
            url = row.get("url", "")
            merged[url] = {
                "titulo": row.get("programa", "Programa público"),
                "url": url,
                "fonte": "Diretório público de bug bounty",
                "escopo_publicado": row.get("escopo", ""),
                "sinal_de_recompensa": "programa listado no diretório; recompensa e regras devem ser confirmadas no site oficial",
                "relevancia_cripto": bool(CRYPTO_RE.search(" ".join(row.values()))),
                "valor_confirmado": None,
                "status": "nao_verificado",
                "acao": "Ler o programa oficial e respeitar integralmente o escopo e as regras.",
            }
        report["fontes_consultadas"].append({"nome": "diretorio_bug_bounty", "ok": status == 200, "itens": len(programs)})
        report["resumo"]["fontes_ok"] += int(status == 200)
    except Exception as exc:
        report["fontes_consultadas"].append({"nome": "diretorio_bug_bounty", "ok": False, "erro": f"{type(exc).__name__}: {exc}"})

    # Issues públicas: filtra menções de recompensa, mas não presume que sejam ofertas válidas.
    issues_found = 0
    for query in QUERIES:
        url = GITHUB_SEARCH.format(query=quote(query, safe=""))
        try:
            status, body = fetch(url, timeout=12, retries=2)
            items = _github_issues(body.decode("utf-8", errors="replace")) if status == 200 else []
            for item in items:
                merged.setdefault(item["url"], item)
            issues_found += len(items)
            report["fontes_consultadas"].append({"nome": "github_issues", "consulta": query, "ok": status == 200, "itens": len(items)})
            report["resumo"]["fontes_ok"] += int(status == 200)
        except Exception as exc:
            report["fontes_consultadas"].append({"nome": "github_issues", "consulta": query, "ok": False, "erro": f"{type(exc).__name__}: {exc}"})

    opportunities = sorted(
        merged.values(),
        key=lambda item: (not item.get("relevancia_cripto", False), item.get("titulo", "").casefold()),
    )
    report["oportunidades"] = opportunities
    report["resumo"].update({
        "candidatas_encontradas": len(opportunities),
        "candidatas_cripto_web3": sum(bool(item.get("relevancia_cripto")) for item in opportunities),
        "issues_com_sinal_de_recompensa": issues_found,
        "receita_confirmada": 0,
    })
    report["interpretacao"] = (
        "O motor encontrou pistas públicas para investigação. Nenhuma delas é receita "
        "confirmada: o GÊNESE não afirma elegibilidade, não envia submissões e não movimenta dinheiro."
    )
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="GÊNESE: descoberta de oportunidades públicas de receita")
    parser.add_argument("--json", action="store_true", help="imprimir o relatório completo em JSON")
    parser.add_argument("--output", default=str(OUT_FILE), help="arquivo de saída JSON")
    args = parser.parse_args()
    report = collect_opportunities()
    Path(args.output).write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    if args.json:
        print(json.dumps(report, ensure_ascii=False, indent=2))
    else:
        print("GÊNESE | MOTOR DE DESCOBERTA")
        print("Fontes consultadas:", len(report["fontes_consultadas"]))
        print("Candidatas encontradas:", report["resumo"]["candidatas_encontradas"])
        print("Relacionadas a cripto/Web3:", report["resumo"]["candidatas_cripto_web3"])
        print("Receita confirmada: R$ 0,00 (nenhuma comprovada nesta execução)")
        print("Relatório salvo em:", args.output)
    return 0 if report["resumo"]["fontes_ok"] else 2


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("GÊNESE encerrado pelo usuário.", file=sys.stderr)
        raise SystemExit(130)
