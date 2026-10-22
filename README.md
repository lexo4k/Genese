# GÊNESE PAY

O GÊNESE PAY agora pode iniciar e supervisionar um **minerador externo real já instalado** no computador/servidor onde o painel é executado. O programa não simula hashrate, não fabrica saldo e não declara pagamento sem confirmação do provedor.

## Execução real do minerador

O runtime em `genese_miner_runtime.py` inicia o executável configurado usando subprocesso sem shell, acompanha a saída real do processo, conta linhas que indicam shares aceitas/rejeitadas e permite encerrar o processo pelo painel.

É necessário ter equipamento compatível e um minerador legítimo instalado no mesmo computador/servidor. **Um Moto G35 não se transforma em ASIC nem passa a minerar Bitcoin de forma economicamente viável por instalar este painel.** O código não baixa executáveis, não instala mineradores por conta própria e não compra poder computacional.

Configure no ambiente do computador/servidor:

- `GENESE_MINER_EXECUTABLE`: caminho absoluto para o executável do minerador instalado, ou nome disponível no PATH.
- `GENESE_MINER_ARGS_JSON`: lista JSON de argumentos exigidos pelo minerador instalado. Os argumentos devem apontar para sua pool e credenciais/worker autorizados. Exemplo apenas de formato: `["--help"]`. Esse exemplo só mostra o formato e não inicia mineração útil.

Não coloque chaves, senhas ou frases-semente no repositório. Use apenas credenciais que você controla e confira o endereço e a rede de pagamento diretamente no provedor antes de minerar.

## Iniciar e parar

1. Instale e configure um minerador compatível com seu equipamento e algoritmo, seguindo a documentação oficial do fabricante/provedor.
2. Defina as duas variáveis acima no ambiente do processo que vai executar o painel.
3. Inicie o painel com `python genese_dashboard.py`.
4. Abra `http://127.0.0.1:8765` no mesmo computador/servidor e use **Iniciar minerador** ou **Parar**.
5. A saída exibida vem do processo externo. Contagens de shares não equivalem a lucro, saldo nem depósito na Binance.

O painel permanece preso a `127.0.0.1` por segurança. Não o exponha diretamente à internet.

## NiceHash e Binance

- `nicehash_readonly.py` consulta dados da NiceHash por API autenticada somente de leitura.
- `genese_pay_core.py` faz verificação TLS da pool e mantém declarações financeiras não verificadas separadas de receita confirmada.
- A configuração de endereço Binance **não** realiza transferência. Este repositório ainda não executa saque na NiceHash nem comprova depósito na Binance.
- O código não explora contas alheias, não retira fundos de terceiros e não cria dinheiro do nada.

## Demais módulos

- `genese_dashboard.py`: interface web local com controles do processo de mineração.
- `genese_autonomo.py` e `priorizador_recompensas.py`: diagnóstico de conectividade e organização de programas públicos de recompensa; encontrar um programa não garante recompensa.
- `.github/workflows/genese.yml`: verificação automática de sintaxe e integridade do código. Essa automação não representa mineração ou pagamento.


## Interface instalável no celular

A interface agora inclui manifesto PWA, ícone SVG e service worker para instalação como atalho de app em navegadores compatíveis. Os arquivos são servidos pelo próprio painel local. O cache é limitado à interface estática; as rotas `/api/` nunca são servidas do cache offline, para evitar exibir dados antigos como se fossem atuais.

**Limite importante:** instalar a interface não instala Python nem um minerador no Android. Para que os controles funcionem, o backend Python precisa estar em execução no mesmo dispositivo e o minerador externo precisa estar instalado e configurado. Este repositório ainda não contém APK Android nativo, não executa mineração por conta própria e não confirma pagamentos/depósitos Binance. O painel continua vinculado a `127.0.0.1` e rejeita POSTs de origens web diferentes.

## Verificação de saldo e depósitos Binance (somente leitura)

O painel possui uma rota `/api/binance` que consulta a API privada real da Binance para obter saldos Spot e os 20 depósitos recentes. Configure `BINANCE_API_KEY` e `BINANCE_API_SECRET` no ambiente do processo. Use uma chave API com permissões de leitura somente, sem saque e sem trading. Nunca publique as chaves nem as coloque no GitHub.

A integração assina requisições com HMAC-SHA256 e mostra os valores retornados pela Binance. Sem credenciais válidas, o painel informa que não verificou. A função **não** minera, não cria receita, não movimenta fundos e não faz saque. A confirmação de saldo/deposito real não prova que o GÊNESE PAY gerou esse dinheiro.


## Busca pública de oportunidades e confirmação de pagamentos

A nova interface está em `genese_receita.py`. Ela apresenta o botão **CONECTAR E GERAR RECEITA**, acompanha o progresso, consulta diretórios públicos oficiais, remove URLs duplicadas e separa oportunidades de pagamentos recebidos.

### Executar localmente

```bash
python genese_receita.py
```

Abra `http://127.0.0.1:8766`. Requer Python 3.10+ e acesso à internet. Não instala dependências externas.

### Limites financeiros importantes

- Um link de oportunidade não é receita e não significa elegibilidade ou pagamento garantido.
- Não há mineração, criação de faturas para simular receita, nem saldos inventados.
- O catálogo não estima recompensa quando não há um valor confiável explícito na fonte.
- O total de pagamentos começa em zero e só aceita eventos normalizados `payment.settled` com assinatura HMAC válida.
- Para ativar o endpoint de webhook, configure `GENESE_PAYMENT_WEBHOOK_SECRET` no ambiente do servidor e configure o provedor para enviar o evento normalizado com o cabeçalho `X-Genese-Signature: sha256=<HMAC-SHA256 do corpo bruto>`. O provedor precisa autenticar a liquidação real; não exponha esse endpoint sem HTTPS, proteção contra repetição e validação específica do provedor em produção.
- O webhook é uma interface de integração genérica, não uma integração Mercado Pago pronta. O adaptador oficial do provedor ainda precisa mapear e validar eventos reais.

A pesquisa limita-se a diretórios públicos e não faz varredura ativa, testes de segurança, submissões ou transações. Leia os termos, a elegibilidade e a idade mínima de cada oportunidade.
