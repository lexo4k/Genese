#!/usr/bin/env python3
"""GÊNESE PAY: gera um kit digital e um dossiê preparatório de abertura.

Não envia formulários a órgãos públicos, não constitui empresa, não publica ofertas,
não cobra compradores e não declara vendas. Gera arquivos locais para revisão humana.
"""
from __future__ import annotations

import argparse
import csv
import json
import re
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def slugify(text: str) -> str:
    text = text.strip().lower()
    text = re.sub(r"[^a-z0-9]+", "-", text)
    return text.strip("-")[:64] or "produto-digital"


def validate_text(value: str, field: str, max_len: int = 5000) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field} é obrigatório.")
    value = value.strip()
    if len(value) > max_len:
        raise ValueError(f"{field} excede {max_len} caracteres.")
    return value


def make_digital_product(title: str, audience: str, problem: str, content: str,
                         price_brl: float, out_dir: Path) -> dict[str, Any]:
    title = validate_text(title, "title", 120)
    audience = validate_text(audience, "audience", 300)
    problem = validate_text(problem, "problem", 500)
    content = validate_text(content, "content", 30000)
    if isinstance(price_brl, bool) or not isinstance(price_brl, (int, float)) or price_brl < 0:
        raise ValueError("price_brl precisa ser um número maior ou igual a zero.")
    out_dir.mkdir(parents=True, exist_ok=True)
    slug = slugify(title)
    created = datetime.now(timezone.utc).isoformat(timespec="seconds")
    product_path = out_dir / f"{slug}-produto.md"
    sales_path = out_dir / f"{slug}-pagina-vendas.md"
    offer_path = out_dir / f"{slug}-oferta.json"
    product_text = f"""# {title}

**Para quem:** {audience}

**Problema que ajuda a resolver:** {problem}

## Material

{content}

## Limites e uso responsável

Este material é educativo e deve ser revisado antes da publicação. Não prometa resultados
que não foram demonstrados. Corrija informações imprecisas e respeite direitos autorais.
"""
    sales_text = f"""# {title}

Um material digital para **{audience}**.

## O que você recebe

- Um arquivo digital com o conteúdo descrito abaixo.
- Orientações práticas para trabalhar no problema: {problem}

## Descrição do material

{content[:1200]}

## Preço proposto

R$ {price_brl:.2f}

## Antes de publicar

- Revise o conteúdo e confirme que tem direito de comercializá-lo.
- Informe claramente formato, entrega, suporte, política de reembolso e dados do vendedor.
- Configure uma plataforma de venda e pagamento apropriada.
- Não publique promessas de resultados garantidos.
- Esta página é um rascunho. Nenhuma oferta foi publicada e nenhuma venda foi realizada.
"""
    offer = {
        "schema_version": 1,
        "title": title,
        "slug": slug,
        "audience": audience,
        "problem": problem,
        "proposed_price_brl": round(float(price_brl), 2),
        "currency": "BRL",
        "status": "draft_not_published",
        "sales": 0,
        "confirmed_received": 0,
        "created_at": created,
        "files": [product_path.name, sales_path.name],
        "limitations": [
            "Oferta não publicada automaticamente.",
            "Vendas e pagamentos não são presumidos.",
            "Preço é apenas uma proposta e não garantia de demanda.",
        ],
    }
    product_path.write_text(product_text, encoding="utf-8")
    sales_path.write_text(sales_text, encoding="utf-8")
    offer_path.write_text(json.dumps(offer, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "draft_created", "offer": offer, "files": [str(product_path), str(sales_path), str(offer_path)]}


def make_business_readiness_packet(trade_name: str, activity: str, state: str,
                                   out_dir: Path) -> dict[str, Any]:
    trade_name = validate_text(trade_name, "trade_name", 200)
    activity = validate_text(activity, "activity", 500)
    state = validate_text(state, "state", 100)
    out_dir.mkdir(parents=True, exist_ok=True)
    packet = {
        "schema_version": 1,
        "trade_name_proposed": trade_name,
        "activity_description": activity,
        "state_or_federal_unit": state,
        "status": "preparation_only_not_registered",
        "created_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "steps": [
            {"step": 1, "task": "Verificar viabilidade do nome, atividade e endereço na REDESIM", "status": "not_done"},
            {"step": 2, "task": "Definir natureza jurídica, CNAEs e regime tributário com responsável adulto/profissional quando necessário", "status": "not_done"},
            {"step": 3, "task": "Preparar e revisar o ato constitutivo e documentos exigidos", "status": "not_done"},
            {"step": 4, "task": "Protocolar e assinar pelos responsáveis autorizados no órgão competente", "status": "not_done"},
            {"step": 5, "task": "Aguardar aprovação e conferir o CNPJ no canal oficial da Receita Federal", "status": "not_done"},
            {"step": 6, "task": "Obter licenças estaduais/municipais aplicáveis", "status": "not_done"},
        ],
        "official_links": [
            "https://www.gov.br/empresas-e-negocios/pt-br/redesim/abrir-cnpj/",
            "https://www.gov.br/pt-br/servicos/inscrever-no-cnpj",
        ],
        "limitations": [
            "Este dossiê não é registro oficial nem comprovante de CNPJ.",
            "O sistema não assina, não envia nem aprova formulários em nome de ninguém.",
            "A abertura depende de requisitos legais, autoridade competente e assinaturas válidas.",
        ],
    }
    path = out_dir / "dossie_abertura_empresa.json"
    path.write_text(json.dumps(packet, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": packet["status"], "file": str(path), "packet": packet}


def main() -> int:
    parser = argparse.ArgumentParser(description="Gera kit de produto digital ou dossiê preparatório empresarial")
    sub = parser.add_subparsers(dest="command", required=True)
    product = sub.add_parser("produto")
    product.add_argument("--titulo", required=True)
    product.add_argument("--publico", required=True)
    product.add_argument("--problema", required=True)
    product.add_argument("--conteudo", required=True, help="Conteúdo original que será incluído no produto")
    product.add_argument("--preco", type=float, required=True)
    product.add_argument("--saida", type=Path, default=Path("saida_genese"))
    business = sub.add_parser("empresa")
    business.add_argument("--nome-proposto", required=True)
    business.add_argument("--atividade", required=True)
    business.add_argument("--estado", required=True)
    business.add_argument("--saida", type=Path, default=Path("saida_genese"))
    args = parser.parse_args()
    if args.command == "produto":
        result = make_digital_product(args.titulo, args.publico, args.problema, args.conteudo, args.preco, args.saida)
    else:
        result = make_business_readiness_packet(args.nome_proposto, args.atividade, args.estado, args.saida)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
