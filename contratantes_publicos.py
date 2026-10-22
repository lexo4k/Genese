#!/usr/bin/env python3
"""Coleta vagas públicas legítimas para revisão humana; nunca se candidata sozinho.

O catálogo não garante contratação, remuneração, elegibilidade nem saque. O usuário
deve conferir idade mínima, país, requisitos, contrato e método de pagamento no site
oficial. Nenhum dado pessoal é enviado a contratantes por este módulo.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCE_URL = "https://www.arbeitnow.com/api/job-board-api"
KEYWORDS = (
    "junior", "entry level", "intern", "internship", "trainee", "apprentice",
    "developer", "software", "web", "frontend", "backend", "python", "qa",
    "tester", "support", "customer service", "design", "content", "writer",
    "data entry", "virtual assistant", "translation", "video editor",
)
REMOTE_HINTS = ("remote", "worldwide", "anywhere", "brasil", "brazil", "latin america")


def fetch_jobs(timeout: int = 15) -> list[dict]:
    request = Request(
        SOURCE_URL,
        headers={"User-Agent": "GenesePay-opportunity-collector/1.0", "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Fonte de vagas respondeu HTTP {response.status}")
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    rows = payload.get("data", [])
    if not isinstance(rows, list):
        raise ValueError("Formato inesperado no catálogo público de vagas")
    return rows


def normalize_job(raw: dict) -> dict | None:
    title = str(raw.get("title") or "").strip()
    company = str(raw.get("company_name") or raw.get("company") or "").strip()
    url = str(raw.get("url") or "").strip()
    if not title or not company or not url.startswith("https://"):
        return None

    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    searchable = " ".join([
        title, company, str(raw.get("description") or ""),
        str(raw.get("location") or ""), " ".join(map(str, tags)),
    ]).lower()
    relevance = sum(1 for word in KEYWORDS if word in searchable)
    if relevance == 0:
        return None

    location = str(raw.get("location") or "").strip()
    remote = bool(raw.get("remote")) or any(hint in location.lower() for hint in REMOTE_HINTS)
    draft = (
        f"Olá, equipe de {company}. Tenho interesse na oportunidade de {title}.\n\n"
        "Minhas habilidades relevantes: [preencher com habilidades reais].\n"
        "Projetos ou portfólio: [inserir links próprios, se houver].\n"
        "Disponibilidade/localização: [preencher].\n\n"
        "Posso compartilhar mais detalhes e confirmar o escopo, os critérios de seleção, "
        "a remuneração e a forma de contratação. Obrigado."
    )
    return {
        "titulo": title,
        "contratante": company,
        "local": location or "não informado",
        "remoto_indicado": remote,
        "tags": [str(tag) for tag in tags[:20]],
        "url_oficial": url,
        "publicado_em": raw.get("created_at"),
        "salario_informado": raw.get("salary") or None,
        "relevancia": relevance,
        "idade_minima": "não verificada; conferir no anúncio oficial",
        "elegibilidade_no_brasil": "não verificada",
        "contrato_e_pagamento": "não verificados; confirmar antes de começar",
        "status_candidatura": "não enviada",
        "rascunho_candidatura": draft,
        "proximo_passo": (
            "Abrir o anúncio oficial; confirmar empresa, idade mínima, país aceito, "
            "escopo, remuneração, contrato e forma/prazo de pagamento. "
            "Revisar o rascunho e só enviar se elegível e autorizado."
        ),
    }


def build_report(rows: list[dict]) -> dict:
    jobs = [job for raw in rows if isinstance(raw, dict) if (job := normalize_job(raw))]
    jobs.sort(key=lambda job: (-job["relevancia"], job["contratante"].lower(), job["titulo"].lower()))
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fonte": SOURCE_URL,
        "vagas_publicas_lidas": len(rows),
        "anuncios_relevantes": len(jobs),
        "anuncios": jobs[:100],
        "candidaturas_enviadas": 0,
        "contratacoes_confirmadas": 0,
        "ganhos_confirmados": 0,
        "saldo_confirmado": None,
        "pagamento_automatico": False,
        "transferencia_binance_automatica": False,
        "limites": [
            "Vaga pública não é oferta garantida nem prova de que a empresa contratará.",
            "Idade, país, requisitos, contrato, remuneração e pagamento precisam ser confirmados no anúncio oficial.",
            "O rascunho é genérico e exige revisão; nenhuma candidatura ou mensagem é enviada automaticamente.",
            "Nenhum dado pessoal ou credencial é coletado ou transmitido.",
            "Só considerar trabalho permitido pela legislação local e pelas regras da plataforma.",
        ],
    }


def main() -> int:
    try:
        rows = fetch_jobs(timeout=int(os.getenv("GENESE_TIMEOUT", "15")))
        report = build_report(rows)
        output = json.dumps(report, ensure_ascii=False, indent=2)
        print(output)
        with open("genese_contratantes.json", "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
        return 0
    except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({
            "erro": f"{type(exc).__name__}: {exc}",
            "vagas_publicas_lidas": 0,
            "candidaturas_enviadas": 0,
            "ganhos_confirmados": 0,
            "pagamento_automatico": False,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
