#!/usr/bin/env python3
"""GÊNESE PAY: buscador de oportunidades públicas, sem mineração ou saldos fictícios.

Executar: python genese_receita.py
A interface e a API usam apenas páginas públicas de diretórios. O coletor não
submete trabalhos, não testa sistemas, não faz pagamentos e não estima ganhos
sem evidência explícita na página de origem.
"""
from __future__ import annotations

import hashlib
import json
import os
import re
import sqlite3
import threading
from datetime import datetime, timezone
from html.parser import HTMLParser
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urljoin, urlparse, urldefrag
from urllib.request import Request, urlopen
from urllib.parse import parse_qs
from mercadopago_webhook import verify_and_fetch
from binance_readonly import read_account_and_deposits, BinanceAPIError

HOST = os.getenv("GENESE_HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", os.getenv("GENESE_PORT", "8766")))
DB = Path(os.getenv("GENESE_RECEITA_DB", "genese_receita.sqlite3"))
SOURCES = [
    {"name": "Intigriti: programas públicos", "url": "https://www.intigriti.com/researchers/bug-bounty-programs"},
    {"name": "Bugcrowd: programas públicos", "url": "https://www.bugcrowd.com/bug-bounty-list/"},
]
SEARCH = {"running": False, "progress": 0, "message": "Pronto para buscar", "results": [], "updated_at": None, "error": None}
LOCK = threading.RLock()


def db_init():
    with sqlite3.connect(DB) as c:
        c.execute("""CREATE TABLE IF NOT EXISTS opportunities (
            url TEXT PRIMARY KEY, title TEXT NOT NULL, source TEXT NOT NULL,
            summary TEXT NOT NULL, estimate_amount REAL, estimate_currency TEXT,
            estimate_basis TEXT, found_at TEXT NOT NULL)""")
        c.execute("""CREATE TABLE IF NOT EXISTS payments (
            provider TEXT NOT NULL, transaction_id TEXT NOT NULL, currency TEXT NOT NULL,
            amount REAL NOT NULL CHECK(amount > 0), status TEXT NOT NULL,
            verified_at TEXT, PRIMARY KEY(provider, transaction_id))""")
        c.commit()


class Anchors(HTMLParser):
    def __init__(self, base):
        super().__init__(convert_charrefs=True)
        self.base, self.href, self.text, self.items = base, None, [], []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            href = dict(attrs).get("href")
            if href:
                self.href, self.text = urljoin(self.base, href), []

    def handle_data(self, data):
        if self.href is not None:
            self.text.append(data.strip())

    def handle_endtag(self, tag):
        if tag == "a" and self.href is not None:
            title = re.sub(r"\s+", " ", " ".join(x for x in self.text if x)).strip()
            u = urldefrag(self.href)[0]
            p = urlparse(u)
            if title and p.scheme == "https" and p.netloc and len(title) >= 4:
                self.items.append((title[:180], u))
            self.href, self.text = None, []


def fetch_page(url):
    req = Request(url, headers={"User-Agent": "GenesePayPublicOpportunityIndexer/1.0 (+public-directory-indexing)", "Accept": "text/html"})
    with urlopen(req, timeout=12) as response:
        if response.status != 200:
            raise RuntimeError(f"HTTP {response.status}")
        content_type = response.headers.get("Content-Type", "")
        if "html" not in content_type.lower():
            raise RuntimeError("A fonte não retornou HTML")
        return response.read(2_000_000).decode("utf-8", "replace")


def clean_opportunities():
    found = {}
    with LOCK:
        SEARCH.update(running=True, progress=0, message="Iniciando busca nas fontes públicas…", error=None, results=[])
    for index, source in enumerate(SOURCES):
        with LOCK:
            SEARCH.update(progress=int(index / len(SOURCES) * 85), message=f"Consultando: {source['name']}")
        try:
            parser = Anchors(source["url"])
            parser.feed(fetch_page(source["url"]))
            for title, url in parser.items:
                # Keep only likely program-detail links; never treat a directory itself as a payout.
                lower = (title + " " + url).lower()
                if not any(k in lower for k in ("program", "bounty", "challenge", "intigriti", "bugcrowd", "disclosure")):
                    continue
                if url in {s["url"] for s in SOURCES}:
                    continue
                if url not in found:
                    found[url] = {
                        "id": hashlib.sha256(url.encode()).hexdigest()[:16],
                        "title": title, "url": url, "source": source["name"],
                        "summary": "Oportunidade pública localizada em diretório. Leia as regras e confirme elegibilidade, escopo e remuneração na página oficial.",
                        "estimated_reward": None,
                        "estimate_label": "Sem estimativa confiável; o diretório não comprova pagamento.",
                        "payment_status": "Não recebido / não verificado",
                        "next_step": "Abrir a página oficial e ler requisitos, regras, idade mínima e política de remuneração."
                    }
        except Exception as exc:
            with LOCK:
                SEARCH["error"] = (SEARCH.get("error") or []) + [{"source": source["name"], "error": f"{type(exc).__name__}: {exc}"}]
    timestamp = datetime.now(timezone.utc).isoformat(timespec="seconds")
    with sqlite3.connect(DB) as c:
        for row in found.values():
            c.execute("""INSERT INTO opportunities(url,title,source,summary,found_at)
                VALUES(?,?,?,?,?) ON CONFLICT(url) DO UPDATE SET title=excluded.title,
                source=excluded.source, summary=excluded.summary""",
                (row["url"], row["title"], row["source"], row["summary"], timestamp))
        c.commit()
        # Include previously indexed records as well as new results.
        rows = c.execute("SELECT url,title,source,summary,estimate_amount,estimate_currency,estimate_basis FROM opportunities ORDER BY title COLLATE NOCASE").fetchall()
    results = []
    for url, title, source, summary, amount, currency, basis in rows:
        results.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:16], "title": title, "url": url,
            "source": source, "summary": summary, "estimated_reward": None if amount is None else {"amount": amount, "currency": currency, "basis": basis, "label": "ESTIMATIVA, NÃO É RECEITA"},
            "estimate_label": basis or "Sem estimativa confiável; não inferir valores.", "payment_status": "Não recebido / não verificado",
            "next_step": "Conferir regras oficiais, requisitos e elegibilidade antes de participar."
        })
    with LOCK:
        SEARCH.update(running=False, progress=100, message=f"Busca concluída: {len(results)} links únicos no catálogo.", results=results, updated_at=timestamp)
    return public_state()


def _load_saved_opportunities():
    """Restore indexed links after a process restart; never count them as income."""
    db_init()
    with sqlite3.connect(DB) as c:
        rows = c.execute(
            "SELECT url,title,source,summary,estimate_amount,estimate_currency,estimate_basis "
            "FROM opportunities ORDER BY title COLLATE NOCASE"
        ).fetchall()
    restored = []
    for url, title, source, summary, amount, currency, basis in rows:
        restored.append({
            "id": hashlib.sha256(url.encode()).hexdigest()[:16],
            "title": title, "url": url, "source": source, "summary": summary,
            "estimated_reward": None if amount is None else {
                "amount": amount, "currency": currency, "basis": basis,
                "label": "ESTIMATIVA, NÃO É RECEITA"
            },
            "estimate_label": basis or "Sem estimativa confiável; não inferir valores.",
            "payment_status": "Não recebido / não verificado",
            "next_step": "Conferir regras oficiais, requisitos e elegibilidade antes de participar."
        })
    return restored


def public_state():
    # A web service can restart; restore its saved catalogue rather than showing
    # a misleading empty list until another network search is run.
    with LOCK:
        if not SEARCH["results"] and not SEARCH["running"]:
            try:
                SEARCH["results"] = _load_saved_opportunities()
                if SEARCH["results"] and not SEARCH["updated_at"]:
                    SEARCH["message"] = "Catálogo restaurado do banco local; execute uma nova busca para atualizar."
            except sqlite3.Error as exc:
                SEARCH["error"] = [{"source": "banco local", "error": str(exc)}]
        return {**SEARCH, "results": list(SEARCH["results"]), "error": SEARCH["error"]}


def start_search():
    with LOCK:
        if SEARCH["running"]:
            return {"ok": True, "already_running": True, **public_state()}
        SEARCH.update(running=True, progress=1, message="Preparando busca…", error=None)
    def run():
        try:
            clean_opportunities()
        except Exception as exc:
            with LOCK:
                SEARCH.update(running=False, message="A busca falhou; nenhum ganho foi contabilizado.", error=str(exc))
    threading.Thread(target=run, daemon=True).start()
    return {"ok": True, "started": True, **public_state()}


def stripe_account_status():
    """Read-only Stripe diagnostics. Never creates charges or initiates payouts."""
    secret = os.getenv("STRIPE_SECRET_KEY", "").strip()
    if not secret:
        return {
            "ok": True, "configured": False, "account_verified": False,
            "payouts_enabled": False, "balance": None,
            "status": "not_configured",
            "note": "Configure STRIPE_SECRET_KEY as a secret in Render after completing Stripe onboarding."
        }, 200
    import base64
    import urllib.error
    import urllib.request

    def stripe_get(path):
        req = Request(
            "https://api.stripe.com/v1/" + path,
            headers={"Authorization": "Bearer " + secret, "Accept": "application/json"},
            method="GET",
        )
        try:
            with urlopen(req, timeout=12) as response:
                return json.loads(response.read(1_000_000).decode("utf-8"))
        except urllib.error.HTTPError as exc:
            detail = exc.read(2000).decode("utf-8", "replace")
            raise RuntimeError("Stripe API HTTP " + str(exc.code) + ": " + detail)

    try:
        account = stripe_get("account")
        balance = stripe_get("balance")
        available = [
            {"amount_minor": item.get("amount", 0), "currency": item.get("currency", "").upper()}
            for item in balance.get("available", [])
        ]
        pending = [
            {"amount_minor": item.get("amount", 0), "currency": item.get("currency", "").upper()}
            for item in balance.get("pending", [])
        ]
        settings = account.get("settings") or {}
        payout_settings = settings.get("payouts") or {}
        schedule = payout_settings.get("schedule") or {}
        enabled = bool(account.get("payouts_enabled"))
        details = bool(account.get("details_submitted"))
        charges = bool(account.get("charges_enabled"))
        return {
            "ok": True, "configured": True, "account_id": account.get("id"),
            "country": account.get("country"), "currency": account.get("default_currency"),
            "details_submitted": details, "charges_enabled": charges,
            "payouts_enabled": enabled,
            "payout_schedule": {"interval": schedule.get("interval"), "delay_days": schedule.get("delay_days")},
            "available_balance": available, "pending_balance": pending,
            "status": "ready_for_payouts" if enabled else "onboarding_or_payouts_incomplete",
            "note": "Somente leitura. A API não cria receita nem inicia repasses. Confirme a conta bancária e a programação de repasses no Dashboard da Stripe."
        }, 200
    except (OSError, ValueError, RuntimeError) as exc:
        return {
            "ok": False, "configured": True, "status": "provider_error",
            "payouts_enabled": False, "error": str(exc),
            "note": "Nenhum repasse foi iniciado."
        }, 502


def payment_summary():
    db_init()
    with sqlite3.connect(DB) as c:
        pending = c.execute("SELECT COUNT(*) FROM payments WHERE status!='CONFIRMED'").fetchone()[0]
        rows = c.execute("SELECT provider,transaction_id,currency,amount,status,verified_at FROM payments WHERE status='CONFIRMED' ORDER BY verified_at DESC").fetchall()
    return {"confirmed_total_by_currency": _totals(rows), "confirmed_payments": [
        {"provider": r[0], "transaction_id": r[1], "currency": r[2], "amount": r[3], "status": r[4], "verified_at": r[5]} for r in rows],
        "pending_count": pending, "note": "Só pagamentos aprovados e consultados na API oficial do Mercado Pago podem ser confirmados. Sem confirmação real, receita confirmada = zero."}


def _totals(rows):
    totals = {}
    for r in rows:
        totals[r[2]] = round(totals.get(r[2], 0) + float(r[3]), 8)
    return totals




PAGE = r"""<!doctype html><html lang="pt-BR"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1"><meta name="theme-color" content="#0b1020"><title>GÊNESE PAY</title>
<style>
:root{color-scheme:dark;font-family:system-ui,Segoe UI,sans-serif;background:#0b1020;color:#edf2ff}*{box-sizing:border-box}body{max-width:1000px;margin:auto;padding:20px}header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}.brand{font-size:clamp(1.8rem,5vw,2.8rem);font-weight:850;letter-spacing:.04em}.muted{color:#aab8d6;line-height:1.5}.panel{background:#151d33;border:1px solid #2b3653;border-radius:18px;padding:18px;margin:16px 0}.hero{text-align:center;padding:clamp(22px,5vw,48px)}.mainbtn{width:100%;max-width:620px;min-height:86px;border:0;border-radius:18px;background:linear-gradient(100deg,#b8f36b,#8ce4b0);color:#13200b;font-size:clamp(1.1rem,4vw,1.65rem);font-weight:900;letter-spacing:.02em;cursor:pointer;box-shadow:0 8px 30px #8ce4b02a}.mainbtn:disabled{opacity:.65;cursor:wait}button:focus-visible,a:focus-visible{outline:3px solid white;outline-offset:3px}.stats{display:grid;grid-template-columns:repeat(auto-fit,minmax(180px,1fr));gap:12px}.stat{background:#0e162a;border-radius:12px;padding:14px}.num{font-size:1.5rem;font-weight:800}.track{height:10px;background:#293550;border-radius:99px;overflow:hidden;margin:16px 0 8px}.bar{height:100%;width:0;background:#b8f36b;transition:width .3s}.row{display:flex;justify-content:space-between;gap:12px;align-items:center;flex-wrap:wrap}.result{padding:14px 0;border-top:1px solid #2b3653}.result h3{margin:0 0 8px;font-size:1.05rem}.result a{color:#b8f36b;overflow-wrap:anywhere}.tag{font-size:.8rem;color:#ffe0a3}.foot{font-size:.85rem;color:#8e9bb8}pre{white-space:pre-wrap;overflow-wrap:anywhere}
</style></head><body>
<header><div><div class="brand">GÊNESE PAY</div><div class="muted">Painel financeiro: recebimentos comprovados, integrações e repasses</div></div><span class="tag">SEM MINERAÇÃO · SEM SALDO FALSO</span></header>
<section class="panel hero"><button id="refreshFinance" class="mainbtn">ATUALIZAR STATUS FINANCEIRO</button><p id="message" class="muted">Consultando pagamentos confirmados, configuração e estado das integrações. Oportunidades não são dinheiro recebido.</p><div class="track" role="progressbar" aria-label="Progresso da busca" aria-valuemin="0" aria-valuemax="100" aria-valuenow="0"><div class="bar" id="bar"></div></div><div class="row muted"><span id="progress">0% concluído</span><span id="updated">Ainda não pesquisado</span></div></section>
<div class="stats"><section class="panel stat"><div class="muted">Links únicos encontrados</div><div class="num" id="count">0</div></section><section class="panel stat"><div class="muted">Receita confirmada</div><div class="num" id="total">R$ 0,00</div><div class="foot">Mostra apenas eventos de pagamento verificados.</div></section><section class="panel stat"><div class="muted">Pagamentos confirmados</div><div class="num" id="payments">0</div></section></div>
<section class="panel"><h2>Oportunidades públicas</h2><button id="connect" type="button">Buscar oportunidades públicas</button><p class="muted">Links deduplicados por URL canônica. Estimativas só aparecem quando uma fonte fornece valor identificável. Nenhuma estimativa é contabilizada como receita.</p><div id="results" class="muted">Nenhuma busca executada ainda.</div></section>
<section class="panel"><h2>Binance: saldo e depósitos verificados</h2><p class="muted">Consulta privada protegida por token do proprietário. Configure GENESE_OWNER_TOKEN e as credenciais Binance somente de leitura no Render. O token não fica salvo no navegador.</p><label for="ownerToken">Token privado do proprietário</label><input id="ownerToken" type="password" autocomplete="current-password" placeholder="Token configurado no Render" style="display:block;width:100%;padding:12px;margin:8px 0;background:#0e162a;color:#edf2ff;border:1px solid #2b3653;border-radius:8px"><div id="binanceState" class="muted">Consulta protegida, aguardando token.</div><button id="refreshBinance" type="button">Consultar Binance</button></section>
<section class="panel"><h2>Histórico de recebimentos verificados</h2><p class="muted">Só aparecem transações que a API oficial confirmou. Esta lista não cria recebimentos nem representa oportunidades como saldo.</p><div id="paymentnote" class="muted">Carregando estado dos pagamentos…</div><div id="paymentHistory" class="muted">Consultando transações confirmadas…</div></section><section class="panel"><h2>Repasses para sua carteira</h2><div id="payoutState" class="muted">Verificando integração de repasses…</div><p class="muted">Nenhum repasse será marcado como concluído sem confirmação do provedor. A versão atual não executa transferências automáticas.</p></section><section class="panel"><h2>Stripe: conta e saldo</h2><p class="muted">Consulta somente leitura da conta Stripe vinculada ao segredo do servidor. Não mostra dados bancários completos nem inicia repasses.</p><div id="stripeState" class="muted">Consultando Stripe…</div><button id="refreshStripe" type="button">Verificar Stripe</button></section>
<section class="panel"><h2>Diagnóstico de recebimento real</h2><p class="muted">Este painel verifica a configuração do servidor. Não mostra dinheiro estimado como saldo e não considera a integração pronta sem uma fonte pagadora e um caminho de repasse comprovados.</p><div id="revenueState" class="muted" role="status" aria-live="polite">Verificando configuração…</div><button id="refreshRevenue" type="button">Atualizar diagnóstico</button></section>
<p class="foot">Fontes consultadas: diretórios públicos oficiais. A busca não testa ativos, não envia relatórios, não contorna regras e não garante elegibilidade ou recompensa. Respeite as regras e a idade mínima de cada oportunidade.</p>
<script>
const $=id=>document.getElementById(id);
function render(d){$('message').textContent=d.message||'Busca finalizada';$('bar').style.width=(d.progress||0)+'%';$('progress').textContent=(d.progress||0)+'% concluído';document.querySelector('[role=progressbar]').setAttribute('aria-valuenow',d.progress||0);$('count').textContent=(d.results||[]).length;$('updated').textContent=d.updated_at?'Atualizado '+new Date(d.updated_at).toLocaleString():'Aguardando';$('connect').disabled=!!d.running;$('connect').textContent=d.running?'BUSCANDO…':'Buscar oportunidades públicas';$('results').replaceChildren();if(!d.results||!d.results.length){$('results').textContent=d.error?'A busca encontrou erros. Confira a resposta técnica abaixo.':'Nenhum link listado ainda.';return}for(const r of d.results){const article=document.createElement('article');article.className='result';const h=document.createElement('h3');h.textContent=r.title;const a=document.createElement('a');a.href=r.url;a.target='_blank';a.rel='noopener noreferrer';a.textContent='Abrir fonte oficial ↗';const p=document.createElement('p');p.className='muted';p.textContent=r.summary;const s=document.createElement('p');s.className='tag';s.textContent=r.estimate_label||'Sem estimativa confiável';const status=document.createElement('p');status.className='muted';status.textContent='Pagamento: '+r.payment_status;article.append(h,a,p,s,status);$('results').append(article)}}
async function status(){try{const r=await fetch('/api/status',{cache:'no-store'});const d=await r.json();render(d);const p=await fetch('/api/payments',{cache:'no-store'});const pd=await p.json();const currencies=Object.entries(pd.confirmed_total_by_currency||{});$('total').textContent=currencies.length?currencies.map(([c,v])=>c+' '+v.toLocaleString()).join(' · '):'R$ 0,00';$('payments').textContent=(pd.confirmed_payments||[]).length;$('paymentnote').textContent=pd.note;$('paymentHistory').replaceChildren();const confirmed=pd.confirmed_payments||[];if(!confirmed.length){$('paymentHistory').textContent='Nenhum recebimento confirmado registrado. Isso não significa que exista dinheiro pendente: não há transação confirmada para mostrar.'}else{for(const item of confirmed){const row=document.createElement('p');row.className='result';row.textContent=[item.provider,item.currency+' '+Number(item.amount).toLocaleString(),item.status,item.verified_at||''].filter(Boolean).join(' · ');$('paymentHistory').append(row)}}$('payoutState').textContent='Não configurado: o servidor não envia dinheiro para Pix nem executa repasses externos.'}catch(e){$('message').textContent='Não foi possível consultar a API: '+e}}
$('connect').addEventListener('click',async()=>{try{const r=await fetch('/api/search',{method:'POST'});const d=await r.json();render(d);const poll=setInterval(async()=>{try{const q=await fetch('/api/status',{cache:'no-store'});const v=await q.json();render(v);if(!v.running)clearInterval(poll)}catch(e){clearInterval(poll);$('message').textContent='Busca interrompida: '+e}},800)}catch(e){$('message').textContent='Falha ao iniciar busca: '+e}});
async function binanceStatus(){const target=$('binanceState');const token=$('ownerToken').value.trim();if(!token){target.textContent='Informe o token privado configurado no Render. Nenhuma consulta privada foi feita.';return}try{const r=await fetch('/api/binance',{cache:'no-store',headers:{'Authorization':'Bearer '+token}});const d=await r.json();target.replaceChildren();const p=document.createElement('pre');p.textContent=JSON.stringify(d,null,2);target.append(p)}catch(e){target.textContent='Consulta indisponível: '+e}}
$('refreshBinance').addEventListener('click',binanceStatus);
async function revenueStatus(){const target=$('revenueState');target.textContent='Verificando configuração do servidor…';try{const r=await fetch('/api/receita',{cache:'no-store'});const d=await r.json();target.replaceChildren();const heading=document.createElement('p');heading.textContent=d.revenue_source_connected&&d.automatic_payout_enabled?'Fonte e repasse configurados. Ainda é necessário confirmar transação real.':'NÃO PRONTO PARA RECEBER RENDIMENTOS AUTOMATICAMENTE';target.append(heading);for(const item of (d.checks||[])){const row=document.createElement('p');row.className='muted';row.textContent=(item.ok?'✓ ':'✗ ')+item.label+': '+item.detail;target.append(row)}if(!r.ok)throw new Error('HTTP '+r.status)}catch(e){target.textContent='Diagnóstico indisponível: '+e.message+'. Nenhuma receita ou transferência foi confirmada.'}}
async function stripeStatus(){const target=$('stripeState');target.textContent='Consultando estado da conta Stripe…';try{const r=await fetch('/api/stripe/status',{cache:'no-store'});const d=await r.json();target.replaceChildren();const heading=document.createElement('p');heading.textContent=d.configured?(d.payouts_enabled?'Stripe conectada; repasses habilitados no provedor.':'Chave encontrada, mas repasses ainda não estão habilitados.'):'Stripe ainda não está conectada ao servidor.';target.append(heading);for(const [label,value] of [['Estado',d.status],['País',d.country],['Moeda padrão',d.currency],['Detalhes enviados',d.details_submitted],['Cobranças habilitadas',d.charges_enabled],['Repasses habilitados',d.payouts_enabled],['Programação',d.payout_schedule&&d.payout_schedule.interval]]){if(value!==undefined&&value!==null){const row=document.createElement('p');row.className='muted';row.textContent=label+': '+String(value);target.append(row)}}if(d.available_balance){const row=document.createElement('p');row.className='muted';row.textContent='Saldo disponível (unidades mínimas): '+d.available_balance.map(x=>x.currency+' '+x.amount_minor).join(' · ');target.append(row)}if(d.pending_balance){const row=document.createElement('p');row.className='muted';row.textContent='Saldo pendente (unidades mínimas): '+d.pending_balance.map(x=>x.currency+' '+x.amount_minor).join(' · ');target.append(row)}const note=document.createElement('p');note.className='muted';note.textContent=d.note||d.error||'';target.append(note)}catch(e){target.textContent='Consulta Stripe indisponível: '+e.message+'. Nenhum repasse foi iniciado.'}}\n$('refreshStripe').addEventListener('click',stripeStatus);\n$('refreshRevenue').addEventListener('click',revenueStatus);
$('refreshFinance').addEventListener('click',async()=>{await status();await revenueStatus();await binanceStatus();await stripeStatus();});
status();binanceStatus();revenueStatus();stripeStatus();
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def send_json(self, obj, code=200):
        body = json.dumps(obj, ensure_ascii=False).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            body = PAGE.encode()
            self.send_response(200); self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body))); self.send_header("Cache-Control", "no-store")
            self.end_headers(); self.wfile.write(body); return
        if path == "/api/status":
            self.send_json(public_state()); return
        if path == "/api/payments":
            self.send_json(payment_summary()); return
        if path == "/api/receita":
            stripe_key = bool(os.getenv("STRIPE_SECRET_KEY"))
            mp_token = bool(os.getenv("MERCADOPAGO_ACCESS_TOKEN"))
            mp_secret = bool(os.getenv("MERCADOPAGO_WEBHOOK_SECRET") or os.getenv("GENESE_PAYMENT_WEBHOOK_SECRET"))
            self.send_json({"ok": True, "revenue_source_connected": False, "automatic_payout_enabled": False, "checks": [
                {"key": "revenue_source", "ok": False, "label": "Fonte de receita", "detail": "Nenhuma fonte pagadora está conectada; o catálogo de oportunidades apenas lista links públicos."},
                {"key": "mp_access_token", "ok": mp_token, "label": "Token do Mercado Pago", "detail": "Configurado no servidor." if mp_token else "Falta configurar MERCADOPAGO_ACCESS_TOKEN no Render."},
                {"key": "mp_webhook_secret", "ok": mp_secret, "label": "Assinatura do webhook", "detail": "Configurada no servidor." if mp_secret else "Falta configurar MERCADOPAGO_WEBHOOK_SECRET no Render."},
                {"key": "stripe_key", "ok": stripe_key, "label": "Chave Stripe", "detail": "Segredo configurado; consulte /api/stripe/status para verificar a conta." if stripe_key else "Falta configurar STRIPE_SECRET_KEY como segredo no Render."},
                {"key": "automatic_payout", "ok": False, "label": "Repasse automático", "detail": "Não é iniciado por este servidor. O estado da conta Stripe é somente leitura; programe repasses no Dashboard da Stripe."}
            ]}); return
        if path == "/api/stripe/status":
            result, code = stripe_account_status()
            self.send_json(result, code); return
        if path == "/api/binance":
            owner_token = os.getenv("GENESE_OWNER_TOKEN", "")
            supplied = self.headers.get("Authorization", "")
            if not owner_token or not supplied.startswith("Bearer ") or not __import__("hmac").compare_digest(supplied[7:], owner_token):
                self.send_json({"ok": False, "status": "owner_auth_required", "note": "Configure GENESE_OWNER_TOKEN no Render e envie o token no painel. Nenhum dado privado foi consultado."}, 401)
                return
            try:
                self.send_json(read_account_and_deposits())
            except (BinanceAPIError, ValueError) as exc:
                self.send_json({"ok": False, "status": "provider_error", "error": str(exc), "withdrawals_enabled_by_this_app": False}, 502)
            return
        if path == "/health":
            self.send_json({"ok": True, "service": "genese-pay", "app": "GÊNESE PAY", "health": "ok", "revenue_source_connected": False, "automatic_payout_enabled": False, "real_money_enabled": False, "wallet_transfers_enabled": False}); return
        self.send_json({"ok": False, "error": "not_found"}, 404)

    def do_POST(self):
        if urlparse(self.path).path == "/api/search":
            self.send_json(start_search()); return
        parsed = urlparse(self.path)
        if parsed.path == "/api/webhooks/mercadopago":
            length = min(int(self.headers.get("Content-Length", "0")), 65536)
            body = self.rfile.read(length)
            try:
                payload = json.loads(body.decode("utf-8"))
                data_id = str(payload.get("data", {}).get("id", "") or parse_qs(parsed.query).get("data.id", [""])[0])
                if str(payload.get("type", "")).lower() not in ("payment", "payments") or not data_id:
                    self.send_json({"ok": True, "ignored": True})
                    return
                result = verify_and_fetch(self.headers.get("X-Signature", ""), self.headers.get("X-Request-Id", ""), data_id)
                if result.get("confirmed"):
                    db_init()
                    with sqlite3.connect(DB) as c:
                        c.execute("INSERT INTO payments(provider,transaction_id,currency,amount,status,verified_at) VALUES(?,?,?,?,?,?) ON CONFLICT(provider,transaction_id) DO NOTHING", ("mercadopago", result["transaction_id"], result["currency"], result["amount"], "CONFIRMED", datetime.now(timezone.utc).isoformat(timespec="seconds")))
                        c.commit()
                self.send_json(result)
            except (ValueError, json.JSONDecodeError, OSError) as exc:
                self.send_json({"ok": False, "error": str(exc)}, 400)
            return
        self.send_json({"ok": False, "error": "not_found"}, 404)

    def log_message(self, fmt, *args):
        print("GENESE receita: " + fmt % args)


def main():
    db_init()
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"GÊNESE PAY: http://{HOST}:{PORT}")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
