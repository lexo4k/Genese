#!/usr/bin/env python3
"""GÊNESE: diagnóstico de rede e descoberta de programas públicos de recompensa.

Consulta fontes públicas e autorizadas. Não explora sistemas, não acessa contas,
não inventa saldo e não executa pagamentos.
"""
from __future__ import annotations
import argparse
import json
import os
import socket
import subprocess
import sys
import time
from datetime import datetime, timezone
from typing import Any

USER_AGENT = "GENESE-Autonomo/1.1 (public-source-check)"
TIMEOUT = max(1, int(os.environ.get("GENESE_TIMEOUT", "8")))
RETRIES = max(1, int(os.environ.get("GENESE_RETRIES", "2")))
SOURCES = {
    "programas_publicos": "https://raw.githubusercontent.com/projectdiscovery/public-bugbounty-programs/main/dist/data.json",
    "conversao_usd_brl": "https://api.frankfurter.dev/v1/latest?base=USD&symbols=BRL",
    "teste_https": "https://www.python.org/",
}

def fetch(url: str, timeout: int = TIMEOUT, retries: int = RETRIES) -> tuple[int, bytes]:
    last_error: Exception | None = None
    for attempt in range(retries):
        try:
            result = subprocess.run(
                ["curl", "--silent", "--show-error", "--location",
                 "--connect-timeout", str(max(1, min(timeout, 5))),
                 "--max-time", str(max(1, timeout)),
                 "--user-agent", USER_AGENT,
                 "--write-out", "\nGENESE_HTTP_STATUS:%{http_code}", url],
                capture_output=True, timeout=max(2, timeout + 2), check=False,
            )
            marker = b"\nGENESE_HTTP_STATUS:"
            if marker not in result.stdout:
                detail = result.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(detail or f"curl terminou com código {result.returncode}")
            body, status_text = result.stdout.rsplit(marker, 1)
            status = int(status_text.strip() or "0")
            if result.returncode != 0 and status == 0:
                detail = result.stderr.decode("utf-8", errors="replace").strip()
                raise RuntimeError(detail or f"curl terminou com código {result.returncode}")
            if status >= 400:
                raise RuntimeError(f"HTTP {status}")
            return status, body[:2_000_000]
        except (subprocess.TimeoutExpired, OSError, RuntimeError, ValueError) as exc:
            last_error = exc
        if attempt < retries - 1:
            time.sleep(min(2 ** attempt, 4))
    raise RuntimeError(f"Falha após {retries} tentativas: {type(last_error).__name__}: {last_error}")

def check_dns(host: str, attempts: int = RETRIES) -> dict[str, Any]:
    start = time.monotonic()
    last_error: Exception | None = None
    for attempt in range(max(1, attempts)):
        try:
            result = subprocess.run(
                ["getent", "ahostsv4", host], capture_output=True, text=True,
                timeout=2, check=False,
            )
            ips = sorted({line.split()[0] for line in result.stdout.splitlines() if line.split()})
            if result.returncode == 0 and ips:
                return {"ok": True, "host": host, "ips": ips, "tentativas": attempt + 1,
                        "ms": round((time.monotonic() - start) * 1000)}
            last_error = RuntimeError(result.stderr.strip() or "getent não encontrou endereço")
        except (subprocess.TimeoutExpired, OSError) as exc:
            last_error = exc
        if attempt < attempts - 1:
            time.sleep(min(2 ** attempt, 4))
    return {"ok": False, "host": host, "tentativas": max(1, attempts),
            "ms": round((time.monotonic() - start) * 1000),
            "error": f"{type(last_error).__name__}: {last_error}"}

def parse_programs(payload: str, limit: int = 30) -> list[dict[str, str]]:
    try:
        data = json.loads(payload)
    except json.JSONDecodeError:
        return []
    if isinstance(data, dict):
        data = data.get("programs", data.get("data", []))
    if not isinstance(data, list):
        return []
    rows: list[dict[str, str]] = []
    seen: set[str] = set()
    for item in data:
        if not isinstance(item, dict) or item.get("bounty") is not True:
            continue
        name, url = item.get("name"), item.get("url")
        if not isinstance(name, str) or not isinstance(url, str) or not url.startswith("https://") or url in seen:
            continue
        seen.add(url)
        domains = item.get("domains", [])
        rows.append({"programa": name.strip(), "url": url,
                     "escopo": ", ".join(domains) if isinstance(domains, list) else ""})
        if len(rows) >= limit:
            break
    return rows

def run_once() -> dict[str, Any]:
    report: dict[str, Any] = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "rede": {}, "oportunidades": [], "cambio": None,
        "saldo_confirmado": None, "receita_confirmada": 0,
        "transferencia": {"executada": False, "motivo": "Não há receita comprovada nem integração de pagamento autorizada."},
    }
    for host in ("raw.githubusercontent.com", "api.frankfurter.dev", "www.python.org"):
        report["rede"][host] = check_dns(host)
    try:
        status, body = fetch(SOURCES["programas_publicos"])
        programs = parse_programs(body.decode("utf-8", errors="replace")) if status == 200 else []
        report["oportunidades"] = programs
        report["diretorio"] = {"ok": status == 200, "http": status, "itens": len(programs),
                               "fonte": SOURCES["programas_publicos"]}
    except Exception as exc:
        report["diretorio"] = {"ok": False, "erro": f"{type(exc).__name__}: {exc}"}
    try:
        status, body = fetch(SOURCES["conversao_usd_brl"])
        data = json.loads(body.decode("utf-8"))
        rate = data.get("rates", {}).get("BRL")
        report["cambio"] = ({"ok": True, "USD_BRL": rate, "data": data.get("date"),
                             "fonte": SOURCES["conversao_usd_brl"]}
                            if status == 200 and isinstance(rate, (int, float)) and rate > 0
                            else {"ok": False, "erro": "Taxa BRL inválida na resposta."})
    except Exception as exc:
        report["cambio"] = {"ok": False, "erro": f"{type(exc).__name__}: {exc}"}
    try:
        status, _ = fetch(SOURCES["teste_https"])
        report["https"] = {"ok": 200 <= status < 500, "http": status}
    except Exception as exc:
        report["https"] = {"ok": False, "erro": f"{type(exc).__name__}: {exc}"}
    dns_ok = sum(1 for result in report["rede"].values() if result.get("ok"))
    https_ok = bool(report.get("https", {}).get("ok"))
    directory_ok = bool(report.get("diretorio", {}).get("ok"))
    fx_ok = bool(report.get("cambio", {}).get("ok"))
    report["resumo"] = {
        "dns_ok": dns_ok, "dns_total": len(report["rede"]),
        "https_ok": https_ok, "catalogo_publico_ok": directory_ok,
        "cambio_ok": fx_ok,
        "conectividade_externa_confirmada": https_ok and (directory_ok or fx_ok),
        "oportunidades_listadas": len(report["oportunidades"]),
        "ganhos_confirmados": 0,
        "aviso": "Programas listados são oportunidades, não prova de vulnerabilidade nem garantia de pagamento. Respeite escopo e regras.",
    }
    return report

def main() -> int:
    parser = argparse.ArgumentParser(description="GÊNESE: fontes públicas e recompensas autorizadas")
    parser.add_argument("--loop", type=int, default=0, help="repetir a cada N segundos (mínimo 60)")
    parser.add_argument("--json", action="store_true", help="imprimir JSON")
    args = parser.parse_args()
    if args.loop and args.loop < 60:
        parser.error("--loop precisa ser 60 segundos ou mais")
    while True:
        report = run_once()
        if args.json:
            print(json.dumps(report, ensure_ascii=False, indent=2))
        else:
            print("GÊNESE AUTÔNOMO |", report["timestamp_utc"])
            for host, result in report["rede"].items():
                print(f"DNS {'OK' if result['ok'] else 'FALHOU'} | {host} | {result.get('ips', result.get('error'))}")
            print("HTTPS:", report.get("https"))
            print("Diretório público:", report.get("diretorio"))
            print("Câmbio USD/BRL:", report.get("cambio"))
            print("Oportunidades listadas:", len(report["oportunidades"]))
            print("Ganhos confirmados nesta execução: R$ 0,00")
            print("Transferência executada: não")
        if not args.loop:
            return 0 if report["resumo"]["conectividade_externa_confirmada"] else 2
        time.sleep(args.loop)

if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except KeyboardInterrupt:
        print("GÊNESE encerrado pelo usuário.", file=sys.stderr)
        raise SystemExit(130)
