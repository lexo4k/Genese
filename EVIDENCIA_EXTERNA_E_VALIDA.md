# Evidência externa e válida no GÊNESE PAY

Atualizado: 2026-10-18. Este documento distingue fontes públicas reais de prova de receita. Links abaixo são fontes externas identificadas; consulte novamente as páginas antes de tomar decisões. Este documento não é comprovante de registro empresarial, venda, saldo ou pagamento.

## 1. Produto digital

O repositório contém um produto inicial, uma página de vendas em rascunho, um CSV vazio e metadados da oferta:
- `produto_inicial/kit-controle-financeiro-autonomos.md`
- `produto_inicial/pagina-vendas-kit-controle-financeiro.md`
- `produto_inicial/modelo-movimentacoes-financeiras.csv`
- `produto_inicial/oferta-kit-controle-financeiro.json`

**Evidência que existe agora:** os arquivos estão versionados no GitHub e podem ser inspecionados publicamente.
**Evidência que não existe:** publicação em uma loja, pedido de cliente, venda, recebimento ou depósito. O arquivo da oferta deve permanecer com vendas e recebimentos confirmados em zero até existir confirmação independente.

## 2. Registro empresarial

Fonte oficial brasileira: https://www.gov.br/empresas-e-negocios/pt-br/redesim/abrir-cnpj/

A página oficial explica o fluxo de abertura. O GÊNESE pode preparar um dossiê, mas não pode emitir um CNPJ, assinar declarações em nome de responsáveis ou registrar uma empresa por conta própria. A evidência válida de registro é o comprovante oficial emitido após o processo real, não o dossiê local.

Para consultar uma empresa já existente, o verificador usa uma fonte pública de terceiros e declara essa limitação. Confirme dados jurídicos relevantes diretamente nos canais oficiais da Receita Federal/REDESIM.

## 3. Binance

Documentação oficial do endpoint de histórico de depósitos: https://developers.binance.com/docs/wallet/capital/deposite-history

O módulo `verificador_confirmacoes_reais.py` pode consultar esse histórico com credenciais privadas configuradas no ambiente do titular e permissão somente de leitura. Ele não envia, saca, negocia nem transfere fundos.

**Evidência que só pode ser criada com acesso autorizado do titular:** resposta real da Binance com um depósito concluído. Não inclua chaves API, segredos, códigos 2FA ou frases de recuperação no GitHub, em arquivos públicos ou no chat. Crie uma chave com permissão mínima de leitura e desative saque e trading.

Um depósito na Binance, isoladamente, não prova que o dinheiro veio de uma venda do GÊNESE. Para atribuir receita, é necessário conciliar a transação com uma venda ou remuneração legítima e a confirmação do respectivo pagador.

## 4. Como classificar a evidência

- `draft`: conteúdo preparado, ainda não publicado.
- `external_source_seen`: uma fonte pública foi consultada, mas isso não comprova pagamento.
- `payment_pending`: existe uma transação alegada, ainda sem confirmação independente.
- `payment_confirmed`: existe comprovante externo confiável e a transação foi conciliada com sua origem.
- `business_registered`: existe comprovante oficial de registro válido.

Não promova automaticamente um estado para outro com base em texto livre, captura de tela sem validação, saldo digitado manualmente ou resultado de teste simulado.

## Limite honesto

Nenhum programa pode fabricar evidência externa verdadeira. A evidência precisa vir do órgão público, da plataforma de venda/pagador ou da Binance. O GÊNESE pode coletar e validar essas respostas quando houver acesso autorizado; não pode garantir que uma venda ocorra, que um órgão aprove um registro ou que a Binance tenha fundos.
