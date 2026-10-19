# GÊNESE PAY: preparação de empresa e produto digital

## Gerar um kit de produto digital

O script gera um arquivo de conteúdo, uma página de vendas em rascunho e metadados de oferta. Use apenas conteúdo original ou material que você tem direito de comercializar.

```bash
python preparar_negocio.py produto --titulo "Guia de organização financeira" --publico "iniciantes" --problema "organizar despesas pessoais" --conteudo "Liste despesas fixas e variáveis, depois compare com a renda." --preco 9.90
```

Os arquivos são gravados na pasta `saida_genese`. O produto e a página precisam ser revisados e publicados por uma pessoa. O script não cria uma loja, não processa pagamento e mantém vendas e recebimentos em zero até uma integração real confirmar eventos de pagamento.

## Preparar dossiê de abertura de empresa

```bash
python preparar_negocio.py empresa --nome-proposto "Nome a consultar" --atividade "atividade pretendida" --estado "RS"
```

O script gera `saida_genese/dossie_abertura_empresa.json` com etapas e links oficiais. Ele não protocola nem registra empresa automaticamente. A abertura no Brasil exige verificações de viabilidade, dados corretos, documentação e assinaturas dos responsáveis nos sistemas oficiais. Consulte a REDESIM: https://www.gov.br/empresas-e-negocios/pt-br/redesim/abrir-cnpj/

## Verificar confirmações reais

Use `verificador_confirmacoes_reais.py` para consulta externa de CNPJ e histórico de depósitos Binance. Para a Binance, use somente uma API key de leitura, configurada em variáveis de ambiente e sem permissões de saque ou negociação. Um depósito confirmado não prova sozinho que o GÊNESE PAY o gerou.

## Limites importantes

- Não inventa CPF/CNPJ, assinaturas, saldo, clientes, vendas ou comprovantes.
- Não há garantia de que o produto será vendido ou gere receita.
- Não faz cadastro nem submissão oficial sem a ação e autorização dos responsáveis.
- Não coloque dados pessoais, chaves API ou segredos em arquivos versionados.
