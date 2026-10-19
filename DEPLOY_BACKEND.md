# GÊNESE PAY: implantação do backend

## Estado real e limites
O backend atual funciona em modo `ledger-only`: cadastro, login e carteira contábil de saldo inicial zero. Não representa saldo bancário, não gera dinheiro, não envia saques e não recebe fundos na Binance. O checkout Pix antigo está bloqueado com HTTP 410. Não trate o serviço como pronto para dinheiro real.

## Hospedar com HTTPS no Render
1. Abra https://dashboard.render.com/ e conecte o repositório `lexo4k/Genese`.
2. Crie um **Blueprint** a partir do repositório e selecione a branch `feature/carteira-financeira-mvp`.
3. O Blueprint usa `render.yaml`, cria o serviço Docker `genese-pay-api` e um disco persistente de 1 GB em `/data`. Revise o plano e eventuais custos antes de confirmar.
4. Aguarde o deploy. Copie a URL HTTPS que o próprio Render mostrar; não invente nem digite um domínio presumido.
5. Abra `https://URL-REAL-DO-RENDER/health`. Confirme `ok=true`, `mode=ledger-only`, `real_money_enabled=false` e `pix_enabled=false`. Se falhar, consulte os logs do serviço e corrija antes de seguir.
6. Em GitHub > Settings > Secrets and variables > Actions, crie `GENESE_BASE_URL` com a URL HTTPS real, sem barra final e sem credenciais: https://github.com/lexo4k/Genese/settings/secrets/actions
7. A URL só passa a ser considerada verificada depois de testar a resposta pública real e confirmar que o APK usa essa URL.

**Limite de acesso:** não tenho acesso autenticado ao painel Render desta sessão, então não consigo provisionar o serviço ou obter uma URL real em seu nome. O Blueprint e a configuração já estão no repositório, prontos para importação; criar o serviço requer uma ação autenticada no painel.

## Assinar APK Android de produção
Em https://github.com/lexo4k/Genese/settings/secrets/actions, configure os quatro secrets abaixo usando uma keystore de lançamento que você controla:
- `ANDROID_KEYSTORE_BASE64`: conteúdo Base64 da keystore de release.
- `ANDROID_KEYSTORE_PASSWORD`: senha da keystore.
- `ANDROID_KEY_ALIAS`: alias da chave.
- `ANDROID_KEY_PASSWORD`: senha da chave.

Não coloque a keystore, senhas ou chaves no código, em issues ou em mensagens. Não gere uma keystore descartável para fingir continuidade: se perder a chave, futuras atualizações do mesmo app podem não instalar sobre a versão anterior. Depois de configurar os secrets, execute o workflow **GENESE PAY Android APK and signed release gate** e confirme que o job **Build signed production APK when secrets are configured** e a verificação de assinatura terminam em sucesso. O APK debug não é um APK de produção assinado.

## Validar credenciais Binance sem movimentar dinheiro
O script `scripts/binance_readonly_check.py` testa somente a autenticação de leitura do endpoint Spot `GET /api/v3/account`. Não cria ordens, depósitos, transferências ou saques e não imprime saldos nem a URL assinada.

1. Na Binance, crie uma API key com permissões **somente leitura**. Não habilite saque; use restrição de IP sempre que possível.
2. Configure localmente `BINANCE_API_KEY` e `BINANCE_API_SECRET` como variáveis de ambiente privadas. Nunca faça commit delas. Não as adicione ao Render enquanto o backend não tiver uma necessidade comprovada para isso.
3. Execute `python scripts/binance_readonly_check.py` num ambiente com acesso HTTPS à Binance. `PASS` confirma apenas que a chave autenticou uma consulta de leitura naquele momento.
4. Se a chave não estiver disponível, a validação real permanece pendente. Testes unitários de assinatura não provam que uma conta Binance real foi autenticada.

Não existe forma legítima de criar dinheiro do nada. Para receber receita real, o projeto precisa primeiro de uma fonte de rendimento legítima, um processo comprovável de liquidação e, para criptoativos, ativo/rede/endereço de depósito verificados na própria Binance. Este MVP ainda não implementa esses fluxos. Não use endereço presumido e não habilite saques automáticos.

## Validação feita no CI
O CI verifica sintaxe, testes unitários, imagem Docker, endpoint de saúde, cadastro/login/sessão e carteira inicial zerada, além de confirmar que checkout está bloqueado. Isso não substitui implantação externa, teste em aparelho Android, auditoria de segurança ou confirmação de depósito real.

## Antes de usar dados ou fundos reais
Faça revisão independente de segurança, rate limiting, recuperação de conta, revogação/expiração de sessão, backups e teste de restauração, monitoramento, política de privacidade e avaliação jurídica/regulatória aplicável. Não marque o produto como pronto para dinheiro real apenas porque `/health` responde HTTP 200.
