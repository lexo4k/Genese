#!/usr/bin/env python3
"""GÊNESE PAY: cria um kit digital original inicial, pronto para revisão e venda.

Não publica ofertas, não processa pagamentos e não promete renda. Vendas e créditos
só podem ser confirmados por fontes externas verificáveis.
"""
from __future__ import annotations

import csv
import json
from datetime import datetime, timezone
from pathlib import Path


def gerar_kit_inicial(destino: Path) -> dict:
    destino.mkdir(parents=True, exist_ok=True)
    agora = datetime.now(timezone.utc).isoformat(timespec="seconds")
    guia = """# Kit de Controle Financeiro para Autônomos

## Objetivo
Organizar entradas, despesas e dinheiro reservado usando registros simples. Material educativo; não é aconselhamento contábil ou tributário.

## Rotina semanal de 15 minutos
1. Registre cada venda recebida com data, descrição e valor realmente recebido.
2. Registre cada despesa paga, guardando o comprovante.
3. Separe movimentações pessoais das profissionais sempre que possível.
4. Compare o total recebido com as despesas pagas. Não confunda venda prometida com dinheiro recebido.
5. Anote impostos ou obrigações a confirmar com profissional habilitado.
6. Guarde cópias de segurança e nunca inclua senhas, chaves privadas ou dados completos de cartões na planilha.

## Indicadores
- Entradas recebidas: soma dos recebimentos confirmados.
- Despesas pagas: soma dos pagamentos efetuados.
- Resultado de caixa do período: entradas recebidas menos despesas pagas.
- Valores pendentes: acompanhe à parte, sem somá-los ao dinheiro disponível.

## Revisão mensal
- Confira os registros contra extratos e recibos.
- Corrija duplicidades.
- Exporte uma cópia.
- Defina uma meta realista para o próximo mês.
- Consulte um contador sobre obrigações aplicáveis ao seu caso.

## Modelo de registro
Use o arquivo CSV incluído. Preencha uma linha por movimentação. O arquivo começa vazio de propósito: não contém receitas ou saldos fictícios.
"""
    pagina = """# Kit de Controle Financeiro para Autônomos

**Organize recebimentos e despesas em uma rotina simples.**

Este kit digital inclui:
- Guia prático de organização financeira semanal e mensal.
- Planilha CSV para registrar entradas e despesas.
- Indicadores simples para conferir o caixa.
- Orientações para distinguir valores pendentes de dinheiro realmente recebido.

**Público:** profissionais autônomos e pequenos prestadores de serviço.
**Preço sugerido para teste:** R$ 9,90, sujeito à validação de demanda.

## Transparência
Este material é educativo e não substitui orientação contábil. O comprador deve revisar se o formato atende às suas necessidades.

## Antes de publicar
1. Revise o conteúdo e faça uma cópia de teste da planilha.
2. Escolha uma plataforma de venda que aceite seu cadastro e sua faixa etária/legal.
3. Configure preço, entrega digital, suporte e política de reembolso.
4. Publique somente após conferir os termos da plataforma e as regras aplicáveis.
5. Divulgue sem spam, sem avaliações falsas e sem prometer resultados financeiros.

**Status atual:** rascunho não publicado. Nenhuma venda ou receita foi confirmada.
"""
    guide_path = destino / "kit-controle-financeiro-autonomos.md"
    sales_path = destino / "pagina-vendas-kit-controle-financeiro.md"
    csv_path = destino / "modelo-movimentacoes-financeiras.csv"
    offer_path = destino / "oferta-kit-controle-financeiro.json"
    guide_path.write_text(guia, encoding="utf-8")
    sales_path.write_text(pagina, encoding="utf-8")
    with csv_path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.writer(f)
        writer.writerow(["data", "tipo", "descricao", "categoria", "valor_brl", "status", "comprovante_ref", "observacoes"])
    oferta = {
        "schema_version": 1,
        "title": "Kit de Controle Financeiro para Autônomos",
        "price_suggestion_brl": 9.90,
        "currency": "BRL",
        "status": "draft_not_published",
        "sales": 0,
        "confirmed_received_brl": 0.0,
        "created_at": agora,
        "files": [guide_path.name, sales_path.name, csv_path.name],
        "next_steps": [
            "Revisar o conteúdo e testar o CSV",
            "Escolher plataforma de venda compatível e concluir cadastro autorizado",
            "Publicar a oferta manualmente ou por integração oficial autorizada",
            "Vincular cada pedido a uma confirmação de pagamento externa",
            "Verificar separadamente depósitos reais na Binance por API somente leitura"
        ],
        "limitations": [
            "O kit é gerado localmente e não é publicado automaticamente.",
            "Não há compradores, vendas ou pagamentos presumidos.",
            "O preço sugerido não garante demanda nem renda."
        ]
    }
    offer_path.write_text(json.dumps(oferta, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return {"status": "draft_created", "files": [str(guide_path), str(sales_path), str(csv_path), str(offer_path)], "offer": oferta}


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--saida", type=Path, default=Path("saida_genese"))
    args = parser.parse_args()
    print(json.dumps(gerar_kit_inicial(args.saida), ensure_ascii=False, indent=2))
