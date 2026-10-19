#!/usr/bin/env python3
"""Gera status do GÊNESE PAY sem confundir código/testes com receita real."""
import json
import os
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def build_report(root=ROOT, env=None):
    root = Path(root)
    env = dict(os.environ if env is None else env)
    files = {
        "api_wallet": "wallet_api.py",
        "painel_web": "genese_pay_web.py",
        "motor_oportunidades": "motor_receita.py",
        "consulta_binance_readonly": "binance_account_readonly.py",
        "produto_digital_rascunho": "produto_inicial/kit-controle-financeiro-autonomos.md",
    }
    present = {key: (root / path).is_file() for key, path in files.items()}
    ci = env.get("GITHUB_ACTIONS") == "true"
    tests_ok = ci and env.get("GENESE_CI_TESTS_PASSED") == "true"
    health_ok = ci and env.get("GENESE_CI_HEALTH_PASSED") == "true"
    run_id = env.get("GITHUB_RUN_ID", "")
    repo = env.get("GITHUB_REPOSITORY", "")
    run_url = f"https://github.com/{repo}/actions/runs/{run_id}" if ci and repo and run_id else None
    stages = [
        {"id":"codigo_base","nome":"Arquivos centrais presentes","status":"concluida" if all(present[k] for k in ("api_wallet","painel_web","motor_oportunidades")) else "pendente","evidencia":{k:present[k] for k in ("api_wallet","painel_web","motor_oportunidades")},"limite":"Presença de arquivos não prova integração."},
        {"id":"testes","nome":"Testes automatizados no CI","status":"concluida" if tests_ok else "pendente","evidencia":{"workflow":run_url,"passaram":tests_ok},"limite":"Válido apenas para este commit."},
        {"id":"api_health","nome":"Inicialização e health check da API","status":"concluida" if health_ok else "pendente","evidencia":{"workflow":run_url,"health_check_passou":health_ok},"limite":"Teste no runner, não hospedagem pública."},
        {"id":"painel_testes","nome":"Testes do painel web e das respostas de estado","status":"concluida" if tests_ok else "pendente","evidencia":{"workflow":run_url,"suite_unittest_passou":tests_ok},"limite":"Testes de painel/rotas não comprovam implantação pública nem conexão privada."},
        {"id":"binance_codigo","nome":"Utilitário Binance somente leitura presente","status":"concluida" if present["consulta_binance_readonly"] else "pendente","evidencia":{"arquivo_presente":present["consulta_binance_readonly"]},"limite":"Não prova conexão, saldo nem receita."},
        {"id":"integracao","nome":"Painel, API, motor e Binance integrados","status":"pendente","evidencia":{"teste_ponta_a_ponta":False},"limite":"Exige teste integrado com resultado observável."},
        {"id":"hospedagem","nome":"Hospedagem pública segura e HTTPS","status":"pendente","evidencia":{"url_publica_verificada":False,"https_verificado":False},"limite":"O painel atual é local."},
        {"id":"receita","nome":"Receita real confirmada","status":"pendente","evidencia":{"venda_verificada":False,"receita_confirmada_brl":0},"limite":"Rascunhos e oportunidades não são receita."},
        {"id":"binance_deposito","nome":"Depósito real confirmado e conciliado","status":"pendente","evidencia":{"consulta_privada_executada":False,"deposito_confirmado":False},"limite":"Nenhum depósito foi comprovado."},
        {"id":"android","nome":"APK Android construído e testado em dispositivo","status":"pendente","evidencia":{"apk_verificado":False,"teste_dispositivo":False},"limite":"Painel web não é APK."},
    ]
    return {
        "produto":"GÊNESE PAY","schema_version":1,
        "gerado_em":datetime.now(timezone.utc).isoformat(),
        "commit":env.get("GITHUB_SHA"),"workflow_run_url":run_url,
        "resumo":{"etapas_concluidas_com_evidencia":sum(x["status"]=="concluida" for x in stages),"etapas_total":len(stages),"receita_confirmada_brl":0},
        "arquivos":present,"etapas":stages,
    }


def write_report(root=ROOT, env=None):
    root = Path(root)
    report = build_report(root, env)
    out = root / "evidencias"
    out.mkdir(parents=True, exist_ok=True)
    (out / "status_etapas.json").write_text(json.dumps(report, ensure_ascii=False, indent=2)+"\n", encoding="utf-8")
    lines = ["# GÊNESE PAY — status baseado em evidências", "", f"- Commit: {report['commit'] or 'não informado'}", f"- CI: {report['workflow_run_url'] or 'sem execução CI nesta chamada'}", f"- Etapas concluídas com evidência: {report['resumo']['etapas_concluidas_com_evidencia']}/{report['resumo']['etapas_total']}", "- Receita confirmada: R$ 0,00", "", "> Testes verdes não provam hospedagem, venda ou depósito.", "", "| Etapa | Estado | Limite |", "|---|---|---|"]
    for s in report["etapas"]:
        lines.append(f"| {s['nome']} | {s['status'].upper()} | {s['limite']} |")
    (out / "STATUS_ETAPAS.md").write_text("\n".join(lines)+"\n", encoding="utf-8")
    return report


if __name__ == "__main__":
    print(json.dumps(write_report(), ensure_ascii=False, indent=2))
