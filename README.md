# GÊNESE PAY

Motor de descoberta de oportunidades públicas de receita legítima, com priorização cripto/Web3, relatórios auditáveis e um painel web local. O sistema identifica pistas e organiza a investigação; não afirma que encontrou dinheiro nem garante ganhos.

## Painel web GÊNESE PAY

Requisitos: Python 3.10+ e conexão à internet para consultar fontes públicas.

```bash
python genese_pay_web.py
```

Abra `http://127.0.0.1:8765` no mesmo dispositivo em que o servidor estiver rodando. O painel adapta-se a telas de celular e computador. O botão **Buscar oportunidades reais** consulta o motor público existente e atualiza `genese_receita.json`.

Endpoints locais:
- `GET /api/status`: estado do painel. Receita confirmada fica em zero e Binance aparece desconectada até haver integração privada real.
- `GET /api/opportunities`: último relatório salvo.
- `POST /api/refresh`: atualiza o relatório consultando fontes públicas.

Por segurança, o servidor escuta somente em localhost. Não exponha a internet pública nem encaminhe portas: ainda não há autenticação de usuário, HTTPS, banco de dados multiusuário nem gestão de segredos. Para usar o painel no Android, o Python precisa estar rodando no próprio aparelho; o painel não é um APK instalável ainda.

## Descoberta autônoma

O `motor_receita.py` reúne um diretório de programas de bug bounty e issues públicas do GitHub que mencionam recompensa/valor. Deduplica links, prioriza sinais relacionados a cripto/Web3 e salva um relatório JSON. Uma menção a recompensa é apenas uma pista: confira a fonte oficial, regras, escopo, elegibilidade e se a oferta continua ativa.

```bash
python motor_receita.py
python motor_receita.py --json
python motor_receita.py --output relatorio.json --json
```

O relatório padrão é salvo em `genese_receita.json`.

## Diagnóstico e priorização

```bash
python genese_autonomo.py --json
python priorizador_recompensas.py > oportunidades.json
python -m unittest discover -s tests -v
python -m unittest -v test_binance_public
```

O diagnóstico verifica DNS/HTTPS, lê um catálogo público limitado e consulta a cotação USD/BRL. O priorizador organiza programas por correspondência textual com termos de cripto/Web3. Nenhuma dessas operações comprova uma falha, direito a recompensa ou pagamento.

## Binance: estado atual

O arquivo `binance_public.py` consulta a API pública Spot sem chave de API e sem entrar em conta privada:

```bash
python binance_public.py --symbol BTCUSDT
python binance_public.py --symbol ETHUSDT
```

A cotação pública não é saldo, receita, lucro garantido nem transferência. **O GÊNESE PAY ainda não consulta saldo privado, não negocia, não deposita e não saca fundos.** Não coloque API keys, senhas, seed phrases ou chaves privadas em código, issues ou navegador.

## Binance: consulta privada somente leitura (opcional)

O arquivo `binance_account_readonly.py` faz uma consulta assinada ao endpoint Spot de conta, usando somente uma chave criada com permissão de leitura. Ele não possui rotas para ordens, depósitos, saques ou transferências e não deve ser tratado como mecanismo de geração de renda.

Configure as variáveis no ambiente do seu próprio dispositivo/servidor, sem colocá-las no código, no GitHub, no navegador ou em mensagens:

```bash
export BINANCE_API_KEY="sua_chave_de_leitura"
export BINANCE_API_SECRET="seu_segredo"
python binance_account_readonly.py
```

No Windows PowerShell, use `$env:BINANCE_API_KEY` e `$env:BINANCE_API_SECRET`. Crie a chave na Binance com a menor permissão necessária, sem habilitar saque nem trading; se a plataforma permitir, restrinja por IP. Nunca compartilhe os valores dessas variáveis. Se não tiver certeza das permissões, não configure a chave.

O retorno mostra apenas ativos Spot com saldo livre ou bloqueado e declara explicitamente que isso não é receita do GÊNESE. A integração é um utilitário separado: o painel ainda não consulta essa conta automaticamente. Os testes usam respostas simuladas e verificam assinatura/validação, não fazem login real nem confirmam um saldo real.

Teste local:

```bash
python -m unittest discover -s tests -v
python -m py_compile binance_account_readonly.py
```

## Livro de recompensas auditável

O arquivo `registro_recompensas.py` registra oportunidades e acompanha estados como `encontrada`, `aprovada` e `paga`. É um livro contábil local, não uma consulta bancária independente. Só marque uma recompensa como aprovada/paga quando houver evidência oficial correspondente.

## Ofertas de recompensa com aceite, entrega e pagamento rastreáveis

O arquivo `contratos_recompensa.py` implementa um fluxo local de estados para ofertas de trabalho: rascunho → aceite explícito do pagador → evidência de fundos informada → entrega → aprovação/rejeição → pagamento informado → confirmação externa registrada.

Esse fluxo **não cria uma empresa pagadora nem força uma entidade a pagar**. O pagador precisa aceitar os termos; a evidência de financiamento deve vir de uma fonte legítima (por exemplo, um serviço de escrow/marketplace real ou confirmação do pagador). Nesta versão, as URLs e referências são registradas, mas não verificadas automaticamente por banco, custodiante ou API. Por isso os estados deixam claro quando a confirmação externa ainda está pendente.

O módulo é um protótipo local de workflow, não um serviço jurídico de escrow nem um processador de pagamentos. Não aceite tarefas sem conferir identidade do pagador, termos, escopo, critérios, prazo, impostos, política de disputa e disponibilidade real dos fundos.

Criar rascunho de oferta a partir de um arquivo JSON:

```bash
python contratos_recompensa.py new --json oferta.json
python contratos_recompensa.py list
```

Campos de exemplo para `oferta.json`:

```json
{
  "pagador": "Nome da empresa ou cliente",
  "contato_pagador": "contato oficial",
  "termos_url": "https://example.org/terms",
  "trabalho": "Descrição específica do trabalho",
  "criterios_aceitacao": "Como o resultado será avaliado",
  "valor": 100,
  "moeda": "BRL",
  "prazo_utc": "2026-12-31T23:59:59Z",
  "pagamento_metodo": "Método de pagamento acordado"
}
```

As funções de aceite, entrega, avaliação e pagamento podem ser usadas por uma futura API autenticada. Ainda não há endpoint web, login, assinatura digital, verificação automática de fundos ou confirmação direta da Binance para esse fluxo.

## Prioridades de desenvolvimento

1. **Fonte de receita concreta:** escolher um provedor ou marketplace com remuneração explícita e regras verificáveis; o motor de oportunidades, sozinho, não gera receita.
2. **Backend seguro:** autenticação, HTTPS, banco de dados, auditoria e gestão de segredos antes de hospedar publicamente.
3. **Binance somente leitura:** integração privada opcional com permissão mínima para consultar saldo; manter saques desativados e nunca solicitar permissão de saque desnecessária.
4. **Recebimentos verificáveis:** integrar um provedor que confirme pagamentos por API/webhook assinado e conciliar cada evento para evitar duplicação.
5. **Transferências controladas:** só depois de receita efetiva, teste em ambiente apropriado, limites, validação de endereço/rede e confirmação explícita do titular.
6. **Aplicativo Android:** transformar o painel em PWA/APK depois que o backend estiver seguro e acessível; o arquivo atual é um painel web local, não um APK.

## Segurança e limites

- O GÊNESE não explora sistemas, não testa alvos automaticamente, não acessa contas alheias e não retira fundos.
- Testes de segurança só podem ocorrer em ativos expressamente autorizados e dentro das regras publicadas.
- O programa não cria dinheiro do nada. Receita confirmada permanece zero até existir evidência confiável de recebimento.
- Não há pagamento, depósito ou saque automático. Não confunda oportunidades listadas, cotação de mercado ou saldo manual com dinheiro recebido.
- A lista pública é limitada e pode conter resultados desatualizados ou não elegíveis. Confirme sempre no site oficial.


## Kit inicial de produto digital (novo)

O arquivo motor_receita_inicial.py gera automaticamente um primeiro produto original simples: um guia de controle financeiro para autônomos, uma página de vendas em rascunho, um CSV vazio para registros reais e metadados da oferta.

```bash
python motor_receita_inicial.py --saida saida_genese
python -m unittest discover -s tests -v
```

O kit começa com vendas e recebimentos confirmados em zero. Isso automatiza a preparação do produto, não a conquista de clientes nem o recebimento de dinheiro. Para transformar em receita real, é necessário revisar o material, usar uma plataforma de venda compatível, publicar a oferta e confirmar cada pagamento por fonte externa. O valor de R$ 9,90 é apenas uma hipótese inicial de preço, não uma previsão de vendas.

## Etapas externas que ainda dependem de dados reais

1. **Empresa:** o gerador preparar_negocio.py empresa prepara um dossiê, mas não registra empresa. A abertura deve ser feita nos canais oficiais e com os responsáveis autorizados: https://www.gov.br/empresas-e-negocios/pt-br/redesim/abrir-cnpj/
2. **CNPJ existente:** verificador_confirmacoes_reais.py cnpj NUMERO consulta uma fonte pública de terceiros. Para verificar uma empresa específica, use um CNPJ válido e autorizado e confira o comprovante oficial. Não use exemplos fictícios como prova.
3. **Binance:** verificador_confirmacoes_reais.py binance-deposits exige variáveis de API configuradas no próprio ambiente, com permissão somente de leitura. Nunca envie chave ou segredo pelo chat, commit, issue ou arquivo público. A consulta não transfere fundos e não prova, sozinha, que um depósito veio de uma venda do GÊNESE.
