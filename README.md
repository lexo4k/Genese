# GÊNESE PAY

Projeto em evolução para monitoramento real, contabilização auditável e preparação de integrações. O repositório ainda não é um minerador completo nem um aplicativo Android/web pronto.

## Núcleo adicionado

- `genese_pay_core.py`: configuração explícita de pool, verificação real de handshake TLS com o endpoint configurado e livro local de receitas comprovadas.
- O teste de conexão de pool **não** significa que há mineração ativa. O módulo não submete shares nem inventa hashrate.
- A receita só entra no livro com provedor, moeda, valor positivo, referência externa de transação e URL HTTPS de evidência. Referências duplicadas são recusadas.
- O total é separado por moeda. Não mistura BTC com BRL nem transforma oportunidade em dinheiro recebido.
- O campo de destino Binance é apenas configuração de endereço/rede; o projeto **não** executa saques nem confirma saldo na Binance.

## Configuração do núcleo

Variáveis opcionais:
- `GENESE_POOL_HOST` (padrão: `nhmp-ssl.eu.nicehash.com`)
- `GENESE_POOL_PORT` (padrão: `443`)
- `GENESE_WORKER` (nome do worker)
- `BINANCE_DEPOSIT_ADDRESS` e `BINANCE_DEPOSIT_NETWORK` (devem ser informados juntos; confirme que moeda e rede são compatíveis no serviço de destino antes de usar)

O banco SQLite local é `genese_pay.sqlite3` por padrão; use `GENESE_LEDGER_DB` para escolher outro caminho. Não coloque chaves de API, senhas ou frases-semente no repositório.

## Testar

Requisitos: Python 3.10+ e `curl`.

```bash
python -m py_compile genese_autonomo.py priorizador_recompensas.py genese_pay_core.py
python -m unittest discover -s tests -v
python genese_autonomo.py --json
python priorizador_recompensas.py > oportunidades.json
```

GitHub Actions executa os testes e guarda relatórios. Aprovação dos testes valida o código testado, não prova rentabilidade, mineração ativa, saldo externo nem pagamento.

## O que ainda falta para o objetivo final

A execução real de mineração requer um mecanismo de mineração compatível com hardware suportado e configuração de pool/worker; o núcleo atual apenas verifica conectividade. Também faltam uma integração autenticada com dados oficiais de ganhos do provedor, interface Android/web e fluxo de depósito verificado. Nenhuma transferência automática para Binance foi implementada.
