# GÊNESE PAY: implantação do backend

## O que este pacote faz
- Empacota a API Python existente em Docker.
- Configura o servidor para escutar em `0.0.0.0`, necessário para o serviço web receber tráfego externo.
- Usa armazenamento persistente em `/data` para o SQLite e uma verificação de saúde em `/health`.
- Inclui um Blueprint Render (`render.yaml`) para provisionamento assistido.

## Implantação
1. Entre em https://dashboard.render.com/ e conecte o repositório `lexo4k/Genese`.
2. Crie um Blueprint usando este repositório e selecione a branch `fix/deployable-backend-binance`.
3. Revise o serviço e o disco persistente antes de confirmar. O disco configurado requer um plano Render compatível e pode gerar cobrança.
4. Aguarde o deploy e teste `https://SEU-DOMINIO/health`. Não use um domínio inventado.
5. Configure o secret GitHub `GENESE_BASE_URL` com a URL HTTPS real do serviço, sem credenciais embutidas.
6. Configure a assinatura Android em GitHub Actions secrets. Nunca grave senhas, keystore, API keys ou seed phrases no repositório.
7. Execute novamente o workflow Android e confirme que o artefato de release aparece, a assinatura é verificada e o APK aponta para o domínio implantado.

## Limites financeiros importantes
O backend atual é um ledger contábil, não uma instituição financeira nem uma carteira custodiada. As rotas de checkout antigas usam Mercado Pago e não são a fonte de receita nem o destino de recebimento deste projeto. Não configure credenciais Mercado Pago para tentar transformar esse ledger em saldo sacável. Transferências e depósitos Binance ainda não estão implementados nem verificados.

Uma carteira Binance recebe fundos reais quando um pagador legítimo envia criptoativos para um endereço de depósito correto, na rede correta, e a transação é confirmada. O software não pode criar dinheiro do nada. Não use endereços ou chaves inventados. Uma integração automática futura exige escolher ativo/rede, endereço oficial da conta e API keys com permissões mínimas, guardadas apenas no servidor. Nunca habilite saques com uma chave API de leitura.

## Persistência e segurança
- O disco é persistente; faça backup e teste recuperação antes de usar dados reais.
- O servidor HTTP interno depende do HTTPS fornecido pelo host. Não exponha a porta diretamente à internet sem TLS.
- Esta configuração é um ponto de partida de implantação, não uma auditoria de segurança ou certificação financeira.
- Antes de armazenar dados reais, adicione rate limiting, política de senha/recuperação, expiração e revogação de sessões, migrações/backup, monitoramento e revisão de segurança.
- Não marque a aplicação como pronta para dinheiro real apenas porque `/health` responde 200.
