# GÊNESE PAY — histórico consolidado e especificação integrada

Este documento consolida as decisões do projeto desde a criação do repositório e evita tratar protótipos, oportunidades ou testes locais como receita real.

## Repositório e estado atual

- Repositório: https://github.com/lexo4k/Genese
- Branch base que contém a aplicação atual: `Lexo/NutriFit`
- Branch de consolidação desta documentação: `genese-integrado`
- A aplicação existente é principalmente Python, com dashboard web local e interface PWA. O repositório também contém módulos de diagnóstico, ledger de evidências, consulta de APIs somente leitura e runtime para iniciar um minerador externo configurado pelo operador.
- A branch atual não é um APK Android nativo. A interface PWA instalável não instala Python nem um motor de mineração no Android.

## Linha do tempo das decisões

### 1. GÊNESE inicial: encontrar oportunidades legítimas

Em 16/10/2026, o objetivo inicial era pesquisar pequenas quantias reais e oportunidades públicas na internet, verificar se eram reais e registrar somente o que pudesse ser comprovado. Foram discutidos scanners de programas públicos de recompensa, conversão de moeda, verificação de conectividade e testes de parser.

Regras que permanecem:
- Encontrar uma oportunidade não equivale a receber dinheiro.
- Valores máximos anunciados por programas não são saldo disponível nem promessa de ganho.
- Recompensas só podem ser reconhecidas depois da confirmação do emissor/provedor.
- Não explorar contas de terceiros, não retirar dinheiro de terceiros e não fazer testes fora do escopo autorizado.
- O ledger deve manter evidências como não verificadas até haver confirmação independente.

### 2. Destino financeiro: Mercado Pago foi substituído

O projeto começou com a ideia de acumular oportunidades legítimas para recebimento no Mercado Pago. Em seguida, o usuário rejeitou o fluxo de cobrar clientes via Pix, QR Code ou código copia-e-cola. O destino mencionado passou a ser Binance.

Regras atuais:
- Não implementar um sistema cujo “ganho” venha de cobrar o próprio usuário, fabricar saldo ou simular depósitos.
- A consulta à Binance deve ser real e de leitura, usando credenciais mantidas no ambiente e com permissões mínimas.
- Configurar um endereço de depósito não movimenta fundos nem prova um depósito.
- Uma integração de saque só pode ser considerada implementada quando houver suporte oficial, autenticação adequada, confirmação de rede/endereço, teste seguro e comprovante verificável. Não há saque automático comprovado no código atual.

### 3. GÊNESE PAY: Android + web, sem saldos fictícios

Em 18/10/2026, o projeto foi definido como GÊNESE PAY, com fontes legítimas de receita combinadas, destino Binance e suporte Android/web. O usuário exigiu testes antes de afirmar que algo funciona.

O projeto evoluiu para:
- dashboard web local;
- diagnósticos reais de rede e TLS;
- registro de evidências financeiras não verificadas;
- consulta somente leitura à API da NiceHash;
- consulta somente leitura de saldos e depósitos Binance, quando credenciais são configuradas;
- runtime opcional que inicia um executável de mineração externo, já instalado e compatível com o equipamento;
- PWA para instalação como atalho de navegador.

Esses componentes não criam receita. Uma conexão TLS, um processo ativo, uma linha de log ou uma share observada não provam pagamento. A confirmação precisa vir da pool/provedor e, para depósito, da conta de destino.

### 4. Ramo de mineração e endereço Bitcoin

Em 19/10/2026, o usuário voltou a pedir mineração real e informou como endereço Bitcoin de destino:
`bc1qnfzu8ydmz3ka0pfv4amq99epy8mcdawj4eqwup`

O usuário pediu para usar um motor de mineração e enviar diretamente a esse endereço, sem depender de um endereço/conta NiceHash. Isso não pode ser garantido só pelo painel: o protocolo de mineração e o serviço/pool determinam como o trabalho é enviado e como as recompensas são pagas. Um endereço de carteira não faz a pool pagar diretamente nele se o serviço exigir conta/worker ou tiver regras próprias.

A documentação atual do repositório diz que o runtime apenas inicia um minerador externo configurado, não baixa nem instala mineradores, e não realiza saques. O dispositivo Moto G35 não é um ASIC Bitcoin e mineração SHA-256 por CPU em telefone não é economicamente viável. Não declarar lucro com base em hashrate estimado ou logs.

## Componentes já presentes no repositório

- `genese_dashboard.py`: dashboard web local; deve permanecer limitado a localhost, salvo futura implementação explícita de autenticação e proteção de rede.
- `genese_pay_core.py`: verificação TLS da pool e ledger de evidências não verificadas.
- `genese_autonomo.py`: diagnóstico de rede e consulta a fontes públicas de oportunidades.
- `priorizador_recompensas.py`: organização/priorização de programas públicos de recompensa.
- `nicehash_readonly.py`: consulta de endpoints NiceHash explicitamente permitidos em modo somente leitura.
- `binance_readonly.py` (quando presente na branch usada): consulta de dados da Binance em modo somente leitura.
- `genese_miner_runtime.py`: inicia/supervisiona um minerador externo já instalado e registra sinais observados em sua saída.
- `manifest.webmanifest`, `service-worker.js` e `icon.svg`: instalação PWA da interface.
- `tests/`: testes automatizados de parser, ledger e regras de evidência.
- `.github/workflows/`: verificações automatizadas de código, quando habilitadas na branch.

## Critérios obrigatórios para chamar uma função de “real e funcionando”

1. **Execução:** o processo inicia e termina corretamente, sem valores simulados.
2. **Rede:** DNS, conexão TCP e TLS são testados separadamente; falha de rede é exibida como falha, nunca como sucesso.
3. **Mineração:** minerador compatível com hardware e algoritmo corretos, pool/worker autorizados, conexão confirmada e shares aceitas pela pool.
4. **Receita:** valor de recompensa confirmado pela fonte oficial; logs, estimativas e tetos de bounty não contam.
5. **Pagamento:** transação confirmada pelo provedor ou blockchain e rede corretas.
6. **Depósito:** saldo/depósito conferido na conta de destino ou por confirmação on-chain, sem inferir sucesso apenas de um endereço configurado.
7. **Segredos:** API keys e segredos não entram no Git, logs, screenshots ou pacote público. Para consulta, usar permissões somente leitura.
8. **Testes:** testes unitários e de integração executados; testes que dependem da rede externa devem ser identificados separadamente dos testes locais.
9. **Android:** distinguir PWA, backend Python, minerador externo e APK nativo. Não chamar PWA de APK.
10. **Segurança:** nenhum acesso a contas alheias, exploração não autorizada, retirada de fundos de terceiros ou mineração sem autorização.

## Bloqueios conhecidos que não podem ser ocultados

- Não existe prova no estado atual de shares aceitas por uma pool para esta sessão.
- Não existe comprovante de recompensa criada pelo GÊNESE.
- Não existe comprovante de saque automático da NiceHash para Binance ou para o endereço BTC informado.
- A consulta somente leitura não é um motor de pagamento.
- O runtime depende de um executável externo compatível, instalado e configurado pelo operador.
- O teste de conectividade externa precisa ser executado numa rede em que o dispositivo/servidor tenha acesso à Internet. Uma falha de DNS/egress no ambiente de execução não pode ser corrigida apenas por alterar o código.
- Não há APK Android nativo comprovado nesta branch.

## Próxima ordem de execução

1. Consolidar código e testes de todas as branches de GÊNESE sem sobrescrever versões conflitantes de forma cega.
2. Executar a suíte local e corrigir todos os erros reproduzíveis.
3. Fazer verificações reais de conectividade a partir do dispositivo/servidor que executará o app.
4. Validar o caminho de mineração apenas com hardware, minerador, conta/worker e serviço autorizados e compatíveis.
5. Verificar a forma de pagamento suportada pelo provedor antes de configurar destino; não prometer pagamento direto à carteira se a pool não o suportar.
6. Manter a Binance como destino de acompanhamento/recebimento quando houver um fluxo oficial compatível, sem implementar transferência financeira fictícia.
7. Gerar artefato Android apenas após escolher e testar a arquitetura nativa; PWA e APK devem ser rotulados corretamente.

## Estado financeiro inicial

- Receita confirmada atribuível ao GÊNESE: **0** até existir prova oficial verificável.
- Shares aceitas confirmadas nesta consolidação: **nenhuma evidência fornecida**.
- Saque/depósito automatizado confirmado: **não**.
- Nenhum saldo fictício deve ser exibido.
