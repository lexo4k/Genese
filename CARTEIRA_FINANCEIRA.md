# GÊNESE Wallet MVP

Esta branch adiciona uma primeira aplicação web de carteira com autenticação, saldo contábil interno e extrato.

## Estado real nesta versão

- Cadastro e login por e-mail/senha, com hash PBKDF2.
- Sessões com token aleatório e expiração.
- Banco SQLite, saldo calculado a partir de lançamentos em centavos.
- Extrato das últimas 100 movimentações.
- Interface web responsiva em português.
- Endpoint de saúde e testes automatizados no GitHub Actions.
- Endpoints Pix respondem HTTP 503 intencionalmente enquanto nenhum provedor financeiro está configurado.

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
- `GET /health`: estado do serviço; declara explicitamente que Pix está desativado.
- `POST /api/register`: `{"email":"voce@example.com","password":"senha-com-12-ou-mais"}`.
- `POST /api/login`: retorna token Bearer de sessão.
- `GET /api/me`, `GET /api/wallet`, `GET /api/transactions`: exigem `Authorization: Bearer <token>`.
- `POST /api/logout`: revoga a sessão.
- `POST /api/pix/charge` e `POST /api/pix/transfer`: HTTP 503 até integração real ser construída e validada.

## Para ativar Pix real

1. Selecionar um provedor que ofereça API Pix adequada ao modelo de negócio e concluir cadastro/contrato.
2. Usar ambiente sandbox, documentação oficial e credenciais armazenadas em secrets do ambiente de servidor.
3. Implementar criação de cobrança, consulta de status, webhooks com validação de assinatura, idempotência, conciliação e trilha de auditoria.
4. Implementar transferências somente com autorização do titular, autenticação forte, limites, confirmação e controles antifraude.
5. Fazer testes de integração e revisão de segurança. Confirmar requisitos regulatórios e jurídicos aplicáveis no Brasil antes de oferecer carteira ou custódia ao público.

Uma chave Pix sozinha não autoriza o sistema a consultar saldos ou iniciar transferências. Não coloque senha bancária, chave privada ou token financeiro no repositório GitHub. O GitHub guarda código; não guarda o dinheiro.

## GÊNESE: oportunidades

Os scripts existentes continuam limitados a consultar fontes públicas e programas de recompensa autorizados. Listar um programa não significa que exista dinheiro disponível nem garante receita. Não há mineração de saldo, exploração automática, retirada de fundos de terceiros ou transferência de recompensas para Pix nesta versão.
