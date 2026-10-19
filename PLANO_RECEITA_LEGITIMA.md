# Mecanismo de receita legítima do GÊNESE

## Objetivo
Transformar oportunidades públicas e autorizadas em recompensas reais, sem inventar saldo, acessar contas alheias ou executar testes fora do escopo permitido.

## Fluxo verificável
1. **Descobrir:** catalogar programas públicos de recompensas e oportunidades de trabalho, guardando a URL oficial, as regras e a data da consulta.
2. **Verificar elegibilidade:** conferir idade mínima, país aceito, requisitos de cadastro, escopo permitido e regras de pagamento. Não contornar restrições; se houver requisito de maioridade, interromper e pedir orientação a um responsável.
3. **Trabalhar dentro da autorização:** em programas de segurança, limitar-se estritamente ao escopo e aos métodos expressamente autorizados. O GÊNESE deve apenas organizar oportunidades e evidências, não explorar sistemas automaticamente.
4. **Submeter:** registrar o identificador da submissão, a data e a confirmação oficial de recebimento. Uma submissão ainda não é receita.
5. **Aguardar decisão:** registrar separadamente os estados enviada, em análise, aprovada, rejeitada e paga.
6. **Confirmar pagamento:** só marcar como paga quando houver confirmação verificável do pagador e comprovante legítimo. Guardar URL/identificador de referência e data, sem armazenar senhas, códigos de autenticação ou chaves privadas.
7. **Conciliar:** registrar valor, moeda, taxas e identificador da transação. O saldo confirmado é a soma dos pagamentos efetivamente recebidos, menos taxas e saídas comprovadas.
8. **Auditar:** manter histórico de alterações; não apagar rejeições nem converter cotações, pontos internos ou recompensas pendentes em dinheiro recebido.

## Regra de saldo
- **Cotação de mercado:** referência informativa; não é saldo.
- **Pontos internos:** unidade de pontuação do app; não é dinheiro e não promete resgate.
- **Recompensa pendente/aprovada:** não é saldo disponível até o pagamento efetivo.
- **Dinheiro/cripto recebido:** contabilizar somente após confirmação independente da transação.

## Limites da integração
A API pública da Binance fornece cotações de mercado, não deposita fundos nem gera receita. O GÊNESE não deve solicitar nem armazenar credenciais de conta, chaves privadas ou códigos de autenticação. Não implementar negociação, depósitos ou saques automáticos. Qualquer serviço financeiro deve respeitar as regras oficiais de elegibilidade, identidade e jurisdição; não contornar controles de idade ou verificação.

## Próxima implementação técnica
- importar e deduplicar programas a partir de fontes oficiais;
- apresentar URL, regras, elegibilidade e última verificação;
- criar um registo por oportunidade e submissão;
- distinguir visualmente estimativa, pendente, aprovada e paga;
- permitir conciliação manual com comprovante, mantendo trilha de auditoria;
- testar que nenhuma recompensa não paga entra no total recebido.

## Critério de sucesso
O sistema só pode declarar receita quando existir um pagamento real verificável. Encontrar uma oportunidade, executar uma consulta pública, obter uma cotação ou criar pontos no aplicativo não gera, por si só, dinheiro.
