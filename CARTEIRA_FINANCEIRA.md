# GÊNESE Wallet MVP

Esta branch adiciona uma primeira aplicação web de carteira com autenticação, saldo contábil interno e extrato.

## Estado real nesta versão

- Cadastro e login por e-mail/senha, com hash PBKDF2.
- Sessões com token aleatório e expiração.
- Banco SQLite, saldo calculado a partir de lançamentos em centavos.
- Extrato das últimas 100 movimentações.
- Interface web responsiva em português.
- Endpoint de saúde e testes automatizados no GitHub Actions.
- Checkout Pix do comerciante suporta sandbox e modo de produção explicitamente configurado; sem credenciais válidas, permanece desabilitado.

**Não é uma conta bancária nem uma carteira custodial. Não recebe, guarda nem envia dinheiro real.** Não há endpoint público para adicionar saldo manualmente. Nenhum saldo pode ser tratado como fundos reais sem confirmação do provedor e conciliação com os fundos correspondentes.

## Executar localmente

Requisitos: Python 3.10+; nenhuma dependência externa.

```bash
python -m unittest discover -s tests -v
python wallet_api.py
```

Abra `http://127.0.0.1:8080` no navegador. O banco de dados `genese_wallet.sqlite3` será criado no diretório do projeto. Para testes, use uma senha exclusiva com pelo menos 12 caracteres.

Para mudar host/porta/caminho do banco:

```bash
GENESE_HOST=127.0.0.1 PORT=8080 GENESE_DB_PATH=/caminho/seguro/genese.sqlite3 python wallet_api.py
```

O servidor padrão só escuta em localhost. Não exponha diretamente à internet. Antes de qualquer produção, é necessário HTTPS, proteção contra força bruta, recuperação de conta, política de privacidade, monitoramento, gestão de segredos, revisão de segurança e implantação apropriada.

## Rotas

- `GET /`: interface web.
- `GET /health`: informa o modo efetivo (`merchant-checkout-sandbox`, `merchant-checkout-production` ou `ledger-only`), se o checkout está habilitado e mantém `real_money_enabled=false` porque a carteira interna não é custodial.
- `POST /api/register`: `{"email":"voce@example.com","password":"senha-com-12-ou-mais"}`.
- `POST /api/login`: retorna token Bearer de sessão.
- `GET /api/me`, `GET /api/wallet`, `GET /api/transactions`, `GET /api/pix/charges` e `GET /api/pix/charges/{id}`: exigem `Authorization: Bearer <token>`.
- `POST /api/logout`: revoga a sessão.
- `POST /api/pix/charge`: cria uma cobrança Pix para a conta comerciante conectada em sandbox ou produção, conforme `MP_MODE`. Corpo: `{"amount_cents":100,"payer_email":"pagador@example.com","description":"Cobrança"}`.
- `POST /api/webhooks/mercadopago`: recebe eventos de ordem e valida `x-signature`, `x-request-id`, `MP_WEBHOOK_SECRET` e `data.id` antes de consultar o provedor.
- `POST /api/pix/transfer`: permanece HTTP 503; este produto de checkout não implementa transferência ou saque.

## Mercado Pago: sandbox e produção

O adaptador usa a API oficial de ordens do Mercado Pago. A documentação oficial descreve o endpoint `/v1/orders`, a resposta com QR/código Pix, o uso de `X-Idempotency-Key` e testes com credenciais de teste. Veja [Pix em Orders API](https://www.mercadopago.com.br/developers/pt/docs/checkout-api-orders/payment-integration/websites/pix) e [compra de teste Pix](https://www.mercadopago.com.br/developers/pt/docs/checkout-api-orders/integration-test/pix).

Configure somente no ambiente do servidor:
```bash
MP_MODE=sandbox
MP_ACCESS_TOKEN=<token-de-teste>
MP_WEBHOOK_SECRET=<segredo-webhook-do-app-de-teste>
```
Nunca coloque essas variáveis no frontend, no código versionado ou em mensagens públicas. O adaptador aceita apenas `MP_MODE=sandbox` ou `MP_MODE=production`. Sem credenciais correspondentes válidas, a criação de cobranças retorna erro. A CI valida o código, mas não confirma transações reais com o Mercado Pago.

O webhook precisa de uma URL pública HTTPS configurada no painel de desenvolvedor para o evento de ordens. A assinatura é validada conforme o [guia oficial de webhooks](https://www.mercadopago.com.br/developers/pt/docs/subscriptions/additional-content/your-integrations/notifications/webhooks). A aplicação também consulta a ordem diretamente antes de atualizar o status.

**Limites importantes:** este fluxo cria cobranças para a conta comerciante conectada, que pode movimentar dinheiro real quando configurado em produção. Não é uma conta bancária nem carteira custodial, não credita o saldo pessoal da aplicação e não envia Pix para terceiros. O estado do pagamento deve ser conciliado com a conta comerciante. Produção exige autorização do titular elegível, credenciais de produção configuradas fora do GitHub, revisão de segurança e confirmação dos requisitos legais/regulatórios. Uma chave Pix sozinha não autoriza consultar saldos ou transferir dinheiro. O GitHub guarda código, não dinheiro.

## GÊNESE: oportunidades

Os scripts existentes continuam limitados a consultar fontes públicas e programas de recompensa autorizados. Listar um programa não significa que exista dinheiro disponível nem garante receita. Não há mineração de saldo, exploração automática, retirada de fundos de terceiros ou transferência de recompensas para Pix nesta versão.
