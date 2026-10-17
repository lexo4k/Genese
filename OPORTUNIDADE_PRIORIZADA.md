# Oportunidade priorizada: programa público da Immunefi

Data da revisão: 2026-10-16

## Por que foi selecionado
A página oficial do programa da Immunefi publica um escopo de segurança, informa recompensa máxima de até US$ 50.000 e exige prova de conceito. Isso é apenas o teto anunciado, não uma promessa de pagamento.

Fontes oficiais:
- Programa e escopo: https://immunefi.com/bug-bounty/immunefi/scope/
- Informações e pagamentos: https://immunefi.com/bug-bounty/immunefi/information/
- Regras gerais: https://immunefi.com/rules/

## Regras essenciais antes de qualquer teste
- Ler a página de escopo e confirmar que o ativo e o impacto estão explicitamente cobertos.
- Não testar contratos na mainnet nem em testnets públicas; as regras gerais proíbem esses testes para este programa. Qualquer validação técnica deve ficar em ambiente local/fork autorizado e sem causar dano.
- Não fazer varredura automatizada que gere tráfego significativo.
- Não acessar dados, contas ou fundos de outras pessoas; não retirar, alterar ou transferir ativos.
- Não enviar relatório automático gerado apenas por scanner. É necessário demonstrar um impacto real e reproduzível, conforme as regras.
- Não publicar detalhes de falha não corrigida.
- O programa informa exigência de KYC para pagamentos; não envie documentos ou dados pessoais ao GÊNESE. Confira elegibilidade e requisitos oficiais com um responsável legal antes de qualquer cadastro ou submissão.

## Pagamento
A página do programa informa pagamento de recompensas em USDC na rede Ethereum, não por Pix. Não há conversão nem transferência automática para Pix implementada. Um pagamento só existe se o programa validar e aceitar um relatório elegível. O valor máximo anunciado não representa saldo disponível nem ganho garantido.

## Estado do GÊNESE
- Programa priorizado para revisão humana: Immunefi.
- Falha válida encontrada: não.
- Relatório enviado/aprovado: não.
- Recompensa confirmada: US$ 0.
- Pagamento automático/Pix: não implementado.

## Próximo passo seguro
Revisar o escopo oficial e, se houver uma ideia concreta, reproduzi-la apenas num laboratório local autorizado. Não executar testes em sistemas reais sem autorização expressa e específica.
