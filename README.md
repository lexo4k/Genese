# GÊNESE PAY

Projeto em evolução para monitoramento de conectividade, registro de evidências e preparação de integrações. O repositório ainda não é um minerador completo nem um aplicativo Android/web pronto.

## Núcleo adicionado

- `genese_pay_core.py`: configuração explícita de pool e verificação real de handshake TLS com o endpoint configurado.
- `genese_dashboard.py`: painel web local responsivo, preso a `127.0.0.1`, com status de conectividade, consulta privada opcional e indicadores que separam estimativas de valores confirmados.\n- `nicehash_readonly.py`: cliente autenticado **somente de leitura** para consultar dados do provedor NiceHash (rigs, não pagos e contas), usando variáveis de ambiente. Não tem endpoints de compra, saque ou alteração financeira.
- `tests/test_nicehash_readonly.py`: valida a assinatura HMAC e bloqueia rotas fora da lista de leitura.
- O teste de conexão de pool **não** significa que há mineração ativa. O módulo não submete shares nem inventa hashrate.
- O livro local aceita declarações com provedor, moeda, valor positivo, referência e URL HTTPS, mas as mantém como **NÃO VERIFICADAS**. Uma URL e um identificador não provam que a transação existe.
- Os valores declarados nunca são chamados de receita confirmada e o saldo externo fica desconhecido até existir validação direta e autenticada no provedor.
- Referências duplicadas são recusadas. Totais ficam separados por moeda.
- O campo de destino Binance é apenas configuração de endereço/rede; o projeto **não** executa saques nem confirma saldo na Binance.

## Configuração do núcleo

Variáveis opcionais:
- `GENESE_POOL_HOST` (padrão: `nhmp-ssl.eu.nicehash.com`)
- `GENESE_POOL_PORT` (padrão: `443`)
- `GENESE_WORKER` (nome do worker)
- `BINANCE_DEPOSIT_ADDRESS` e `BINANCE_DEPOSIT_NETWORK` (devem ser informados juntos; a configuração não valida endereço nem compatibilidade de rede)

O banco SQLite local é `genese_pay.sqlite3` por padrão; use `GENESE_LEDGER_DB` para escolher outro caminho. Não coloque chaves de API, senhas ou frases-semente no repositório.

## Testar

Requisitos: Python 3.10+ e `curl`.

```bash
python -m py_compile genese_autonomo.py priorizador_recompensas.py genese_pay_core.py nicehash_readonly.py genese_dashboard.py
python -m unittest discover -s tests -v
python genese_autonomo.py --json
python priorizador_recompensas.py > oportunidades.json\npython genese_dashboard.py
```

GitHub Actions executa os testes e guarda relatórios. Aprovação dos testes valida o código testado, não prova rentabilidade, mineração ativa, saldo externo nem pagamento.

Abra `http://127.0.0.1:8765` no mesmo dispositivo em que o servidor estiver rodando para acessar o painel. Ele fica disponível somente localmente por segurança. A API privada NiceHash exige credenciais autorizadas definidas no ambiente local; sem elas, nenhuma consulta privada é feita.\n\n## O que ainda falta para o objetivo final

A execução real de mineração requer um mecanismo de mineração compatível com hardware suportado e configuração de pool/worker; o núcleo atual apenas verifica conectividade. Falta validar a integração de leitura com credenciais reais autorizadas do provedor, interpretar os campos reais de ganhos, interface Android/web e fluxo de depósito verificado. Nenhuma transferência automática para Binance foi implementada.
