#!/usr/bin/env python3
"""GÊNESE PAY: painel local para oportunidades e estado financeiro honesto.

Por segurança, escuta em localhost por padrão. Não pede credenciais Binance,
não consulta saldo privado e não executa transferências. Valores confirmados
permanecem zero até uma integração verificável ser implementada.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

ROOT = Path(__file__).resolve().parent
REPORT = ROOT / "genese_receita.json"

HTML = r"""<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="theme-color" content="#101827"><title>GÊNESE PAY</title>
<style>
:root{color-scheme:dark;--bg:#0b1120;--panel:#141e30;--line:#2a3850;--text:#eef4ff;--muted:#9eacc3;--accent:#70e1b3;--warn:#ffcc75}
*{box-sizing:border-box}body{margin:0;background:linear-gradient(150deg,#101a2d,var(--bg) 60%);color:var(--text);font:16px system-ui,-apple-system,Segoe UI,sans-serif}
main{max-width:1080px;margin:auto;padding:24px 16px 48px}.top{display:flex;justify-content:space-between;align-items:center;gap:12px;flex-wrap:wrap}
.brand{display:flex;align-items:center;gap:12px}.logo{display:grid;place-items:center;width:48px;height:48px;border-radius:15px;background:var(--accent);color:#082219;font-weight:900;font-size:24px}
h1{font-size:clamp(24px,4vw,36px);margin:0}p{color:var(--muted);line-height:1.5}.sub{margin:4px 0 20px}.grid{display:grid;grid-template-columns:repeat(3,minmax(0,1fr));gap:14px;margin:20px 0}
.card{background:var(--panel);border:1px solid var(--line);border-radius:18px;padding:18px;min-width:0}.label{color:var(--muted);font-size:14px}.value{font-size:clamp(24px,4vw,34px);font-weight:750;margin:9px 0}.tag{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:5px 9px;font-size:12px;color:var(--warn)}
.actions{display:flex;gap:10px;flex-wrap:wrap;margin:16px 0}button{border:0;border-radius:12px;padding:12px 16px;font-weight:700;background:var(--accent);color:#082219;cursor:pointer}button.secondary{background:#25334a;color:var(--text);border:1px solid var(--line)}button:disabled{opacity:.55;cursor:wait}
section{margin-top:20px}.section-head{display:flex;justify-content:space-between;gap:10px;align-items:center;flex-wrap:wrap}h2{font-size:20px}.list{display:grid;gap:10px}.op{background:#111b2b;border:1px solid var(--line);border-radius:14px;padding:14px}.op a{color:var(--accent);overflow-wrap:anywhere}.op h3{margin:0 0 7px;font-size:16px}.meta{font-size:13px;color:var(--muted)}.notice{border-left:3px solid var(--warn);padding:10px 13px;background:#211d18;border-radius:6px;color:#f8e7c9}
footer{margin-top:28px;color:var(--muted);font-size:13px}@media(max-width:720px){.grid{grid-template-columns:1fr}.value{font-size:28px}.card{padding:16px}}
</style></head><body><main>
<header class="top"><div class="brand"><div class="logo">G</div><div><h1>GÊNESE PAY</h1><div class="label">Central de oportunidades e finanças</div></div></div><span class="tag" id="systemState">INTEGRAÇÃO FINANCEIRA PENDENTE</span></header>
<p class="sub">Painel transparente. Oportunidades não são ganhos, e saldo só conta após confirmação externa.</p>
<div class="notice">A Binance ainda não está conectada. Não informe chave privada, seed phrase ou senha neste painel. Nenhuma transferência é habilitada.</div>
<div class="grid">
<div class="card"><div class="label">Receita confirmada</div><div class="value" id="income">R$ 0,00</div><span class="tag">Sem recebimentos comprovados</span></div>
<div class="card"><div class="label">Saldo Binance</div><div class="value" id="balance">Não conectado</div><span class="meta">Consulta privada não implementada</span></div>
<div class="card"><div class="label">Oportunidades encontradas</div><div class="value" id="count">—</div><span class="meta" id="updated">Ainda não atualizado</span></div>
</div>
<div class="actions"><button id="refresh">Buscar oportunidades reais</button><button class="secondary" id="reload">Atualizar painel</button></div>
<section><div class="section-head"><h2>Fontes de receita para avaliar</h2><span class="meta" id="sourceState">Sem consulta nesta sessão</span></div>
<div id="opportunities" class="list"><div class="card">Toque em “Buscar oportunidades reais” para consultar fontes públicas. O sistema não participa automaticamente nem promete pagamento.</div></div></section>
<section class="card"><h2>O que falta para pagamentos reais</h2><ol>
<li>Selecionar uma fonte que pague por um trabalho ou serviço efetivamente realizado.</li>
<li>Confirmar elegibilidade, regras, valor e método de pagamento no provedor oficial.</li>
<li>Adicionar backend protegido e integração de conta com permissões mínimas, sem expor segredos no navegador.</li>
<li>Validar um recebimento real e conciliar o histórico antes de habilitar qualquer saque.</li>
</ol><p>Estado atual: descoberta pública implementada no motor existente; conexão privada da Binance, processamento de receitas e transferências ainda não implementados.</p></section>
<footer>GÊNESE PAY · painel local · sem saldo fictício · dados públicos podem estar desatualizados.</footer>
</main><script>
const $=id=>document.getElementById(id);
function money(v){return new Intl.NumberFormat('pt-BR',{style:'currency',currency:'BRL'}).format(Number(v)||0)}
async function load(){try{const r=await fetch('/api/status');if(!r.ok)throw Error('HTTP '+r.status);const d=await r.json();$('income').textContent=money(d.receita_confirmada_brl);$('balance').textContent=d.binance_conectada?'Conectado':'Não conectado';$('count').textContent=d.oportunidades_encontradas;$('updated').textContent=d.atualizado_em?'Atualizado: '+d.atualizado_em:'Nenhum relatório ainda';}catch(e){$('sourceState').textContent='Erro: '+e.message}}
function safeLink(url){try{const u=new URL(url);return u.protocol==='https:'?u.href:null}catch{return null}}
function render(d){const root=$('opportunities');root.replaceChildren();const rows=Array.isArray(d.oportunidades)?d.oportunidades:[];if(!rows.length){root.textContent='Nenhuma oportunidade disponível. Tente novamente mais tarde.';return}
for(const item of rows.slice(0,60)){const card=document.createElement('article');card.className='op';const h=document.createElement('h3');h.textContent=item.titulo||'Oportunidade sem título';card.append(h);const p=document.createElement('p');p.textContent=(item.fonte||'Fonte pública')+' · '+(item.status||'não verificado')+' · '+(item.relevancia_cripto?'sinal cripto/Web3':'outra categoria');card.append(p);const desc=document.createElement('p');desc.textContent=item.acao||item.sinal_de_recompensa||'Confira as condições no site oficial.';card.append(desc);const link=safeLink(item.url);if(link){const a=document.createElement('a');a.href=link;a.target='_blank';a.rel='noopener noreferrer';a.textContent='Abrir fonte oficial';card.append(a)}root.append(card)}}
$('refresh').addEventListener('click',async()=>{const b=$('refresh');b.disabled=true;b.textContent='Consultando fontes…';$('sourceState').textContent='Consulta em andamento';try{const r=await fetch('/api/refresh',{method:'POST'});const d=await r.json();if(!r.ok)throw Error(d.error||'Falha na consulta');render(d);$('sourceState').textContent='Consulta concluída: '+(d.fontes_consultadas||[]).filter(x=>x.ok).length+' fontes OK';await load()}catch(e){$('sourceState').textContent='Consulta falhou: '+e.message}finally{b.disabled=false;b.textContent='Buscar oportunidades reais'}});
$('reload').addEventListener('click',load);load();
</script></body></html>"""


def read_report() -> dict[str, Any]:
    try:
        data = json.loads(REPORT.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except (OSError, json.JSONDecodeError):
        return {}


def status_payload() -> dict[str, Any]:
    report = read_report()
    summary = report.get("resumo", {})
    return {
        "produto": "GENESE PAY",
        "receita_confirmada_brl": 0.0,
        "saldo_binance": None,
        "binance_conectada": False,
        "transferencias_habilitadas": False,
        "oportunidades_encontradas": int(summary.get("candidatas_encontradas", 0) or 0),
        "atualizado_em": report.get("timestamp_utc"),
        "estado": "integracao_financeira_pendente",
        "aviso": "Nenhuma receita ou transferência foi confirmada.",
    }


class Handler(BaseHTTPRequestHandler):
    server_version = "GeneSePayLocal/0.1"

    def _send(self, status: int, payload: bytes, content_type: str) -> None:
        self.send_response(status)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(payload)))
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Cache-Control", "no-store")
        self.end_headers()
        self.wfile.write(payload)

    def _json(self, status: int, data: dict[str, Any]) -> None:
        self._send(status, json.dumps(data, ensure_ascii=False).encode("utf-8"), "application/json; charset=utf-8")

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self._send(200, HTML.encode("utf-8"), "text/html; charset=utf-8")
        elif path == "/api/status":
            self._json(200, status_payload())
        elif path == "/api/opportunities":
            self._json(200, read_report())
        else:
            self._json(404, {"error": "not_found"})

    def do_POST(self) -> None:
        if urlparse(self.path).path != "/api/refresh":
            self._json(404, {"error": "not_found"})
            return
        # Avoid unbounded request bodies; refresh accepts no client-provided data.
        try:
            length = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            length = -1
        if length < 0 or length > 1024:
            self._json(400, {"error": "invalid_request"})
            return
        try:
            from motor_receita import collect_opportunities
            report = collect_opportunities()
            REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            self._json(200, report)
        except Exception as exc:
            self._json(502, {"error": "source_query_failed", "detail": f"{type(exc).__name__}: {exc}"})

    def log_message(self, fmt: str, *args: Any) -> None:
        # Keep terminal output concise; do not log request payloads or secrets.
        print("%s - %s" % (self.address_string(), fmt % args))


def main() -> None:
    host = os.environ.get("GENESE_PAY_HOST", "127.0.0.1")
    port = int(os.environ.get("PORT", "8765"))
    if host not in {"127.0.0.1", "localhost", "::1"}:
        raise SystemExit("Por segurança, o painel só pode escutar em localhost até existir autenticação e HTTPS.")
    server = ThreadingHTTPServer((host, port), Handler)
    print(f"GÊNESE PAY disponível em http://{host}:{port}")
    print("Modo seguro: sem Binance privada, sem saldo inventado e sem transferências.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
