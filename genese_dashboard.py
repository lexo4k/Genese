"""Local-only GÊNESE PAY dashboard.

Binds to loopback only. It exposes read-only status and NiceHash telemetry,
never secrets, and never initiates mining, purchases, withdrawals, or transfers.
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import urlparse

from genese_pay_core import income_summary, load_mining_config, probe_pool
from nicehash_readonly import credentials_from_env, collect_read_only_status
from genese_miner_runtime import start_miner, stop_miner, status as miner_status
from binance_readonly import BinanceAPIError, read_account_and_deposits

HOST = "127.0.0.1"
PORT = int(os.environ.get("GENESE_DASHBOARD_PORT", "8765"))

PAGE = """<!doctype html>
<html lang="pt-BR">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<meta name="color-scheme" content="dark">
<link rel="manifest" href="/manifest.webmanifest">
<link rel="icon" href="/icon.svg" type="image/svg+xml">
<meta name="theme-color" content="#0b1020">
<title>GÊNESE PAY</title>
<style>
:root{font-family:system-ui,-apple-system,Segoe UI,sans-serif;color:#edf2ff;background:#0b1020}
*{box-sizing:border-box}body{margin:0;padding:24px;max-width:1000px;margin-inline:auto}
header{display:flex;align-items:center;justify-content:space-between;gap:12px;flex-wrap:wrap}
h1{margin:0;font-size:clamp(1.7rem,5vw,2.5rem);letter-spacing:.04em}
.sub{color:#9eabc9;margin-top:6px}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(220px,1fr));gap:14px;margin-top:22px}
.card{background:#151d33;border:1px solid #2b3653;border-radius:16px;padding:18px;min-width:0}
.card h2{font-size:1rem;color:#aab8da;margin:0 0 12px}.value{font-size:1.25rem;font-weight:700;overflow-wrap:anywhere}
.small{font-size:.9rem;color:#aab8da;line-height:1.5;overflow-wrap:anywhere}
button{background:#b8f36b;color:#17220b;border:0;border-radius:10px;padding:12px 16px;font-weight:750;font-size:1rem}
button:focus-visible{outline:3px solid white;outline-offset:3px}.status{display:inline-block;border-radius:99px;padding:4px 9px;background:#283653;font-size:.82rem}
ul{padding-left:18px}.foot{margin-top:20px;color:#9eabc9;font-size:.88rem}
#raw{white-space:pre-wrap;overflow-wrap:anywhere;max-height:380px;overflow:auto;font-size:.82rem}
</style>
</head>
<body>
<header><div><h1>GÊNESE PAY</h1><div class="sub">Painel local de conectividade e evidências financeiras</div></div><button id="refresh">Atualizar dados</button></header>
<div class="grid">
<section class="card"><h2>Conexão com o endpoint NiceHash</h2><div class="value" id="pool">Carregando…</div><p class="small" id="pooldetail">Teste TLS real. Isso não comprova mineração.</p></section>
<section class="card"><h2>Processo de mineração real</h2><div class="value" id="minerstate">Não iniciado</div><p class="small" id="minerdetail">Inicia um executável de mineração instalado e configurado neste servidor.</p><button id="startminer">Iniciar minerador</button> <button id="stopminer" style="background:#f0a6a6">Parar</button></section>
<section class="card"><h2>Receita confirmada</h2><div class="value">Não disponível</div><p class="small">Nenhum valor estimado ou alegado será tratado como dinheiro recebido.</p></section>
<section class="card"><h2>Destino Binance</h2><div class="value" id="binance">Não verificado</div><p class="small">Configurar um endereço não comprova depósito. Nenhuma transferência é executada.</p></section>
<section class="card"><h2>Verificação real Binance</h2><div class="value" id="binanceapi">Aguardando consulta</div><p class="small" id="binanceap_detail">Consulta real somente leitura de saldos e depósitos. Configure chaves locais sem permissão de saque.</p><button id="fetchbinance">Verificar saldo e depósitos</button><pre id="binanceoutput"></pre></section><section class="card"><h2>API privada NiceHash</h2><div class="value" id="api">Aguardando consulta</div><p class="small" id="apidetail">Consulta somente leitura. Credenciais ficam no ambiente local.</p><button id="fetchapi">Consultar API privada</button></section>
<section class="card"><h2>Integridade do painel</h2><div class="value">Somente leitura</div><p class="small">Sem compra de hashpower, saque, transferência ou saldo fictício.</p></section>
</div>
<section class="card" style="margin-top:14px"><h2>Saída real do minerador</h2><pre id="mineroutput">Nenhum processo iniciado.</pre></section>
<section class="card" style="margin-top:14px"><h2>Resposta técnica</h2><pre id="raw">Aguardando…</pre></section>
<p class="foot">Executado em localhost. Não exponha este painel publicamente nem compartilhe dados privados da conta.</p>
<script>
const $=id=>document.getElementById(id);
async function refresh(){
 $('refresh').disabled=true;
 try{
  const r=await fetch('/api/status',{cache:'no-store'}); const d=await r.json();
  $('pool').textContent=d.pool_probe.connected?'TLS conectado':'Sem conexão';
  $('pooldetail').textContent=d.pool_probe.connected?'Certificado TLS validado; mineração continua não confirmada.':(d.pool_probe.error||'Falha de conexão');
  $('binance').textContent=d.config.binance_destination_configured?'Endereço configurado, depósito não verificado':'Não configurado';
  $('raw').textContent=JSON.stringify(d,null,2);
 }catch(e){$('raw').textContent='Falha ao consultar painel: '+e}
 finally{$('refresh').disabled=false}
}
async function refreshMiner(){
 try{const r=await fetch('/api/miner',{cache:'no-store'});const d=await r.json();
  $('minerstate').textContent=d.running?'Processo ativo (PID '+d.pid+')':(d.configured?'Pronto para iniciar':'Minerador não configurado');
  $('minerdetail').textContent='Shares aceitas observadas: '+d.accepted_shares_observed+'; rejeitadas: '+d.rejected_shares_observed+'. Receita e depósito Binance não confirmados.';
  $('mineroutput').textContent=(d.recent_output||[]).join('\n')||d.last_error_line||d.note;
 }catch(e){$('minerstate').textContent='Indisponível';$('minerdetail').textContent=String(e)}
}
async function minerAction(action){
 $('startminer').disabled=true;$('stopminer').disabled=true;
 try{const r=await fetch('/api/miner/'+action,{method:'POST',cache:'no-store'});const d=await r.json();$('raw').textContent=JSON.stringify(d,null,2);if(!r.ok)throw new Error(d.error||'Falha ao executar');}
 catch(e){$('raw').textContent='Falha ao '+action+': '+e}
 finally{$('startminer').disabled=false;$('stopminer').disabled=false;await refreshMiner()}
}
async function fetchApi(){
 $('fetchapi').disabled=true; $('api').textContent='Consultando…';
 try{
  const r=await fetch('/api/nicehash',{cache:'no-store'}); const d=await r.json();
  $('api').textContent=d.mode==='read_only'?(d.all_requests_succeeded?'API respondeu':'Resposta parcial/erro'):(d.status||'Erro');
  $('apidetail').textContent=d.note||d.error||'Nenhum dado de saldo foi confirmado pelo painel.';
  $('raw').textContent=JSON.stringify(d,null,2);
 }catch(e){$('api').textContent='Falha';$('apidetail').textContent=String(e)}
 finally{$('fetchapi').disabled=false}
}
async function fetchBinance(){
 $('fetchbinance').disabled=true; $('binanceapi').textContent='Consultando Binance…';
 try{const r=await fetch('/api/binance',{cache:'no-store'});const d=await r.json();
  if(!r.ok) throw new Error(d.error||d.note||'Falha na consulta');
  $('binanceapi').textContent=d.status==='provider_confirmed_read_only'?'Dados reais recebidos':'Credenciais ausentes';
  $('binanceap_detail').textContent=d.note||d.status;
  $('binanceoutput').textContent=JSON.stringify({account_balances:d.account_balances,recent_deposits:d.recent_deposits},null,2);
 }catch(e){$('binanceapi').textContent='Não verificado';$('binanceap_detail').textContent=String(e)}
 finally{$('fetchbinance').disabled=false}
}
$('refresh').addEventListener('click',refresh); $('fetchapi').addEventListener('click',fetchApi); $('fetchbinance').addEventListener('click',fetchBinance);
$('startminer').addEventListener('click',()=>minerAction('start')); $('stopminer').addEventListener('click',()=>minerAction('stop')); refresh(); refreshMiner();
if ('serviceWorker' in navigator) navigator.serviceWorker.register('/service-worker.js').catch(()=>{});
</script>
</body></html>"""


class Handler(BaseHTTPRequestHandler):
    server_version = "GenesePayLocal/1.0"

    def _json(self, payload: dict, status: int = 200) -> None:
        body = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Cache-Control", "no-store")
        self.send_header("X-Content-Type-Options", "nosniff")
        self.end_headers()
        self.wfile.write(body)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        static_files = {"/manifest.webmanifest": ("manifest.webmanifest", "application/manifest+json; charset=utf-8"), "/service-worker.js": ("service-worker.js", "text/javascript; charset=utf-8"), "/icon.svg": ("icon.svg", "image/svg+xml")}
        if path in static_files:
            filename, content_type = static_files[path]
            try:
                with open(filename, "rb") as asset:
                    body = asset.read()
            except OSError:
                self._json({"ok": False, "error": "static_asset_missing"}, 500)
                return
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-cache")
            self.send_header("X-Content-Type-Options", "nosniff")
            if path == "/service-worker.js":
                self.send_header("Service-Worker-Allowed", "/")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/":
            body = PAGE.encode("utf-8")
            self.send_response(200)
            self.send_header("Content-Type", "text/html; charset=utf-8")
            self.send_header("Content-Length", str(len(body)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.end_headers()
            self.wfile.write(body)
            return
        if path == "/api/status":
            try:
                config = load_mining_config()
                self._json({
                    "service": "GENESE PAY",
                    "mode": "local_read_only",
                    "config": {
                        "pool_host": config.pool_host,
                        "pool_port": config.pool_port,
                        "worker_configured": bool(config.worker),
                        "binance_destination_configured": bool(config.payout_address and config.payout_network),
                        "binance_network": config.payout_network or None,
                    },
                    "pool_probe": probe_pool(config, timeout=3.0),
                    "income": income_summary(),
                    "mining_active": False,
                    "binance_transfer_executed": False,
                })
            except (OSError, ValueError) as exc:
                self._json({"ok": False, "error": str(exc)}, 500)
            return
        if path == "/api/miner":
            self._json(miner_status())
            return
        if path == "/api/binance":
            try:
                self._json(read_account_and_deposits(timeout=8.0))
            except (ValueError, BinanceAPIError) as exc:
                self._json({"ok": False, "status": "verification_failed", "error": str(exc)}, 502)
            return
        if path == "/api/nicehash":
            try:
                creds = credentials_from_env()
                if creds is None:
                    self._json({
                        "ok": False,
                        "status": "credentials_missing",
                        "required_environment": ["NICEHASH_API_KEY", "NICEHASH_API_SECRET", "NICEHASH_ORGANIZATION_ID"],
                        "note": "Nenhuma chamada privada foi feita; configure credenciais localmente.",
                    }, 503)
                    return
                self._json(collect_read_only_status(creds, timeout=5.0))
            except ValueError as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        self._json({"ok": False, "error": "not_found"}, 404)

    def do_POST(self) -> None:
        origin = self.headers.get("Origin")
        if origin and origin != "http://127.0.0.1:" + str(PORT):
            self._json({"ok": False, "error": "cross_origin_request_rejected"}, 403)
            return
        path = urlparse(self.path).path
        if path == "/api/miner/start":
            try:
                self._json(start_miner())
            except (OSError, ValueError, RuntimeError) as exc:
                self._json({"ok": False, "error": str(exc)}, 400)
            return
        if path == "/api/miner/stop":
            self._json(stop_miner())
            return
        self._json({"ok": False, "error": "not_found"}, 404)

    def log_message(self, fmt: str, *args: object) -> None:
        # Keep local logs free of request query strings and private provider data.
        print("GENESE dashboard: " + fmt % args)


def main() -> None:
    server = ThreadingHTTPServer((HOST, PORT), Handler)
    print(f"GÊNESE PAY local dashboard: http://{HOST}:{PORT}")
    print("Local-only server. Press Ctrl+C to stop.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
