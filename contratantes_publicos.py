#!/usr/bin/env python3
"""Coleta vagas públicas legítimas para revisão humana; nunca se candidata sozinho.

Os feeds são catálogos, não ofertas garantidas. Idade mínima, país, requisitos,
contrato e pagamento devem ser confirmados no anúncio oficial. Nenhum dado pessoal
é enviado a contratantes por este módulo.
"""
from __future__ import annotations

import json
import os
import sys
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen

SOURCES = {
    "Arbeitnow": "https://www.arbeitnow.com/api/job-board-api",
    "Remotive": "https://remotive.com/api/remote-jobs?limit=100",
}
KEYWORDS = (
    "junior", "entry level", "intern", "internship", "trainee", "apprentice",
    "developer", "software", "web", "frontend", "backend", "python", "qa",
    "tester", "support", "customer service", "design", "content", "writer",
    "data entry", "virtual assistant", "translation", "video editor",
)
REMOTE_HINTS = ("remote", "worldwide", "anywhere", "brasil", "brazil", "latin america")


def _get_json(url: str, timeout: int) -> dict:
    request = Request(
        url,
        headers={"User-Agent": "GenesePay-opportunity-collector/1.0", "Accept": "application/json"},
    )
    with urlopen(request, timeout=timeout) as response:
        if response.status != 200:
            raise RuntimeError(f"Fonte respondeu HTTP {response.status}: {url}")
        payload = json.loads(response.read().decode("utf-8", errors="replace"))
    if not isinstance(payload, dict):
        raise ValueError(f"Formato inesperado no feed: {url}")
    return payload


def fetch_jobs(timeout: int = 15) -> tuple[list[dict], dict[str, str]]:
    all_rows: list[dict] = []
    source_status: dict[str, str] = {}
    for source_name, url in SOURCES.items():
        try:
            payload = _get_json(url, timeout)
            rows = payload.get("data") or payload.get("jobs") or []
            if not isinstance(rows, list):
                raise ValueError("lista de vagas ausente")
            for row in rows:
                if isinstance(row, dict):
                    normalized = dict(row)
                    normalized["_fonte_catalogo"] = source_name
                    all_rows.append(normalized)
            source_status[source_name] = f"ok: {len(rows)} anúncios lidos"
        except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError, OSError) as exc:
            source_status[source_name] = f"falhou: {type(exc).__name__}: {exc}"
    if not source_status or not any(value.startswith("ok:") for value in source_status.values()):
        raise RuntimeError("Nenhum catálogo público respondeu: " + "; ".join(source_status.values()))
    return all_rows, source_status


def normalize_job(raw: dict) -> dict | None:
    title = str(raw.get("title") or raw.get("position") or "").strip()
    company = str(raw.get("company_name") or raw.get("company") or "").strip()
    url = str(raw.get("url") or raw.get("apply_url") or "").strip()
    if not title or not company or not url.startswith("https://"):
        return None

    tags = raw.get("tags") or []
    if not isinstance(tags, list):
        tags = []
    location = str(
        raw.get("location") or raw.get("candidate_required_location") or ""
    ).strip()
    searchable = " ".join([
        title, company, str(raw.get("description") or ""),
        location, " ".join(map(str, tags)),
    ]).lower()
    relevance = sum(1 for word in KEYWORDS if word in searchable)
    if relevance == 0:
        return None

    remote_flag = raw.get("remote") is True or str(raw.get("remote", "")).lower() == "true"
    remote = remote_flag or any(hint in location.lower() for hint in REMOTE_HINTS)
    draft = (
        f"Olá, equipe de {company}. Tenho interesse na oportunidade de {title}.\n\n"
        "Minhas habilidades relevantes: [preencher com habilidades reais].\n"
        "Projetos ou portfólio: [inserir links próprios, se houver].\n"
        "Disponibilidade/localização: [preencher].\n\n"
        "Posso compartilhar mais detalhes e confirmar o escopo, os critérios de seleção, "
        "a remuneração e a forma de contratação. Obrigado."
    )
    return {
        "fonte_catalogo": raw.get("_fonte_catalogo", "não informada"),
        "titulo": title,
        "contratante": company,
        "local": location or "não informado",
        "remoto_indicado": remote,
        "tags": [str(tag) for tag in tags[:20]],
        "url_oficial": url,
        "publicado_em": raw.get("created_at") or raw.get("publication_date"),
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


def build_report(rows: list[dict], source_status: dict[str, str] | None = None) -> dict:
    jobs = [job for raw in rows if isinstance(raw, dict) if (job := normalize_job(raw))]
    jobs.sort(key=lambda job: (-job["relevancia"], job["contratante"].lower(), job["titulo"].lower()))
    return {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "fontes": source_status or {},
        "anuncios_publicos_lidos": len(rows),
        "anuncios_relevantes": len(jobs),
        "anuncios": jobs[:150],
        "candidaturas_enviadas": 0,
        "contratacoes_confirmadas": 0,
        "ganhos_confirmados": 0,
        "saldo_confirmado": None,
        "pagamento_automatico": False,
        "transferencia_binance_automatica": False,
        "limites": [
            "Vaga pública não é oferta garantida nem prova de que a empresa contratará.",
            "As fontes são limitadas e podem concentrar-se em Europa ou trabalho remoto internacional.",
            "Idade, país, requisitos, contrato, remuneração e pagamento precisam ser confirmados no anúncio oficial.",
            "O rascunho é genérico e exige revisão; nenhuma candidatura ou mensagem é enviada automaticamente.",
            "Nenhum dado pessoal ou credencial é coletado ou transmitido.",
            "Só considerar trabalho permitido pela legislação local e pelas regras da plataforma.",
        ],
    }


def main() -> int:
    try:
        rows, source_status = fetch_jobs(timeout=int(os.getenv("GENESE_TIMEOUT", "15")))
        report = build_report(rows, source_status)
        output = json.dumps(report, ensure_ascii=False, indent=2)
        print(output)
        with open("genese_contratantes.json", "w", encoding="utf-8") as handle:
            handle.write(output + "\n")
        return 0
    except (HTTPError, URLError, TimeoutError, ValueError, RuntimeError, OSError) as exc:
        print(json.dumps({
            "erro": f"{type(exc).__name__}: {exc}",
            "anuncios_publicos_lidos": 0,
            "candidaturas_enviadas": 0,
            "ganhos_confirmados": 0,
            "pagamento_automatico": False,
        }, ensure_ascii=False, indent=2), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
