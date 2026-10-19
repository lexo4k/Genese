# GÊNESE PAY: como conectar um pagador real

## Regra principal

O software não cria dinheiro nem obriga uma organização externa a pagar. Um pagador só é real para o GÊNESE PAY quando existe uma fonte identificável, termos válidos, um compromisso aceito e evidência verificável do pagamento. Uma URL, um valor digitado ou um comprovante enviado por alguém não provam, isoladamente, que há fundos disponíveis.

## Estados que não podem ser confundidos

1. **Fonte descoberta**: existe uma página pública ou oportunidade. Receita confirmada: R$ 0.
2. **Oferta recebida**: existe uma proposta com termos e valor, ainda não aceita. Receita confirmada: R$ 0.
3. **Oferta aceita**: o pagador aceitou expressamente os termos. Isso, sozinho, não prova que reservou fundos. Receita recebida: R$ 0.
4. **Fundos verificados**: um provedor confiável confirma uma reserva ou depósito real, quando esse recurso está disponível. Uma referência digitada pelo usuário não é verificação.
5. **Trabalho aprovado**: o pagador ou plataforma confirmou que os critérios foram atendidos. Ainda não significa que o pagamento chegou.
6. **Pagamento confirmado**: uma fonte independente e confiável confirma a transação recebida. Somente então o ledger pode contabilizar receita recebida.
7. **Crédito Binance confirmado**: a integração oficial de leitura confirma o ativo e o valor efetivamente creditados na conta. Esse estado é separado de uma recompensa aprovada ou de uma transferência apenas solicitada.

## Fontes legítimas que podem ser integradas

- Trabalho contratado com preço, escopo, aceite e pagamento definidos.
- Recompensas ou subsídios de programas oficiais cujas regras permitam a participação e cujo pagamento tenha sido aprovado.
- Receita de um produto ou serviço próprio, caso existam clientes e uma plataforma de pagamento contratada.
- Patrocínios ou doações voluntárias com condições claras.

Nenhuma dessas fontes garante renda. Cada uma depende de elegibilidade, demanda, aprovação e regras do provedor.

## Critérios mínimos para declarar um pagador conectado

- Identidade e domínio oficial da organização verificados.
- Termos e critérios de remuneração publicados ou contratualmente aceitos.
- Elegibilidade confirmada antes de iniciar qualquer trabalho.
- Método de pagamento e países aceitos confirmados nas regras oficiais.
- Evidência independente de aprovação e pagamento.
- Integração de recebimento testada sem expor chaves privadas.
- Para Binance, consulta oficial de leitura confirmando o crédito; uma carteira configurada ou endereço salvo não é saldo.

## Segurança

- Nunca testar sistemas sem autorização expressa e escopo definido.
- Nunca usar credenciais de terceiros, explorar contas alheias ou retirar valores sem autorização.
- Nunca inserir chaves, senhas, documentos ou códigos de autenticação em issues, commits, logs ou conversas.
- Não iniciar trabalho pago com base apenas em uma promessa, screenshot ou comprovante não verificado.
- Não apresentar dados de teste como dinheiro real.

## Situação atual do projeto

O fluxo de contratos e o utilitário Binance de leitura são protótipos. O fluxo de contratos registra evidências fornecidas, mas não verifica automaticamente saldo bancário, escrow ou identidade do pagador. O utilitário Binance é somente leitura e ainda exige teste real autorizado. Portanto, o projeto não possui, por causa desses módulos, um pagador contratado nem receita confirmada.

## Próxima integração técnica

Antes de ativar pagamentos automáticos, escolher uma fonte legítima específica e implementar seu fluxo oficial, com autenticação segura, verificação independente de eventos e testes. Não declarar a integração pronta até que os testes passem e um pagamento real autorizado seja confirmado.
