# Proposta de apoio: GÊNESE PAY

## Resumo

O GÊNESE PAY é um projeto em desenvolvimento para organizar oportunidades legítimas de receita, registrar ofertas de trabalho e manter estados auditáveis entre proposta, aceite, entrega, aprovação e confirmação de pagamento. O objetivo é evitar saldos fictícios e separar oportunidades de dinheiro efetivamente recebido.

Repositório: https://github.com/lexo4k/Genese

## Problema

Projetos pessoais e pequenos desenvolvedores precisam de uma forma simples de acompanhar trabalhos remunerados sem tratar uma oportunidade encontrada na internet como receita garantida. O GÊNESE PAY busca tornar cada etapa rastreável e reduzir afirmações de pagamento sem evidência.

## O que já existe no protótipo

- Painel web local responsivo para visualizar oportunidades.
- Descoberta de fontes públicas e geração de fichas para análise.
- Fluxo local de ofertas com aceite, entrega, revisão e evidências de pagamento.
- Utilitário separado de consulta privada somente leitura da conta Spot da Binance, ainda sem integração automática com o painel.
- Testes automatizados para partes do fluxo, executados em GitHub Actions em commits anteriores.

Estes itens não significam que o sistema já possui um pagador contratado, que uma oferta esteja financiada, nem que um crédito real tenha sido recebido. As integrações reais ainda precisam ser concluídas e verificadas.

## Plano de trabalho proposto

### Etapa 1: segurança e qualidade
- Revisar e testar os módulos existentes.
- Melhorar validação de dados, logs e documentação.
- Não armazenar chaves privadas nem credenciais no repositório.
- Manter o painel local até existir autenticação e implantação segura.

### Etapa 2: integração de uma fonte legítima
- Selecionar uma plataforma ou organização que publique tarefas ou recompensas com termos claros.
- Confirmar as regras de elegibilidade e autorização antes de qualquer trabalho.
- Integrar somente interfaces oficiais documentadas, se disponíveis.
- Não automatizar submissões que violem regras da plataforma.

### Etapa 3: confirmação independente de pagamentos
- Separar proposta, aprovação, pagamento iniciado e pagamento recebido.
- Validar eventos por API oficial ou outra evidência independente confiável.
- Integrar a consulta Binance em modo somente leitura e testar com autorização do titular.
- Não habilitar negociação ou saque automático nesta etapa.

### Etapa 4: documentação e demonstração
- Publicar instruções de instalação e execução.
- Demonstrar testes reproduzíveis com dados claramente marcados como teste.
- Publicar limitações conhecidas e resultados reais sem expor dados pessoais.

## Uso pretendido de eventual apoio

Qualquer apoio aprovado seria usado para desenvolvimento, testes, documentação, infraestrutura indispensável e revisão de segurança. O orçamento, a moeda, o cronograma e os critérios finais de entrega devem ser definidos de acordo com as regras do programa financiador antes de enviar uma candidatura.

## Como avaliar o projeto

- Testes reproduzíveis passam no CI.
- Nenhum saldo de teste aparece como receita recebida.
- Nenhuma chave ou segredo é versionado.
- A integração usa documentação oficial e respeita autorização e termos.
- Um pagamento só é marcado como recebido após confirmação independente.
- O estado de crédito na Binance é demonstrado separadamente de uma recompensa aprovada.

## Transparência e limitações

Este documento é uma proposta técnica, não um pedido já submetido, uma concessão aprovada, um contrato com financiador ou promessa de rendimento. Não existe garantia de aprovação nem de pagamento. O repositório precisa passar por revisão, cumprir os critérios de cada programa e ter uma candidatura enviada pelo responsável elegível. Se o programa exigir maioridade, verificação de identidade ou responsável legal, essas condições devem ser cumpridas; não devem ser contornadas.

## Contato e próximos passos

A candidatura deve ser submetida pelo titular do projeto por meio do canal oficial do programa escolhido. Não publicar chaves API, documentos pessoais, endereço residencial ou dados bancários em issues ou arquivos públicos.
