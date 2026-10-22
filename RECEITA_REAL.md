# Caminho de receita real do GÊNESE PAY

## Fonte inicial escolhida: patrocínio de software aberto

O GÊNESE PAY pode procurar apoio financeiro recorrente para manter e melhorar o projeto. O caminho sugerido é o GitHub Sponsors, sujeito a aprovação e às regras oficiais do programa. Para participantes com menos de 18 anos, as regras do GitHub exigem cumprir a lei de idade aplicável e que o processador consiga verificar as informações do responsável legal.

- Perfil de referência: https://github.com/sponsors/lexo4k
- Termos oficiais: https://github.com/github/docs/blob/main/content/site-policy/github-terms/github-sponsors-additional-terms.md
- A existência do link não comprova que o perfil está habilitado, que há patrocinadores ou que existe saldo a receber.
- Nenhum patrocinador, valor ou recebimento é presumido pelo GÊNESE PAY.
- A cobrança e o repasse seguem o fluxo oficial do GitHub e do processador de pagamentos. O app não cria cobranças, não captura cartões e não recebe notificações financeiras automaticamente.
- O fluxo de patrocínio não paga diretamente para a Binance por meio deste repositório. Qualquer movimentação posterior depende dos meios de pagamento oficialmente oferecidos, titularidade, elegibilidade e verificações aplicáveis. Não contornar limites de idade ou verificações.

## O que o aplicativo já faz

1. Coleta catálogos públicos de vagas e programas de recompensa para revisão.
2. Gera relatórios de oportunidades, sem enviar candidaturas automaticamente.
3. Mantém registros manuais de recebimentos sem apresentá-los como verificados.
4. Consulta saldos e depósitos Binance em modo somente leitura quando o backend está configurado com credenciais próprias e restritas a leitura.
5. Mantém os ganhos confirmados como zero até haver evidência real. Um registro manual não é prova de pagamento.

## Próxima integração necessária

A confirmação automática de patrocínios só deve ser implementada depois que o perfil for aprovado e houver uma fonte oficial de eventos/relatórios de pagamento acessível com autorização. Então, integrar apenas dados de recebimento verificados, com proteção de segredos e testes. Não usar chaves com permissão de saque para confirmar depósitos.

## Teste de aceitação

- [ ] Perfil de patrocínio aprovado e requisitos legais verificados.
- [ ] Primeiro patrocínio real aparece no painel oficial do provedor.
- [ ] Valor líquido, moeda, data e estado de repasse são confirmados no relatório oficial.
- [ ] O app registra o recebimento como verificado somente quando existe evidência confiável.
- [ ] Qualquer transferência posterior é tratada separadamente e nunca simulada como concluída.
\n## Decisão de integridade financeira\n\nOs controles de depósito e transferência simulados foram removidos da interface principal para não confundir testes com receita. O painel não apresenta saldo fictício como dinheiro disponível.\n