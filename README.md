# GÊNESE PAY

O GÊNESE PAY agora pode iniciar e supervisionar um **minerador externo real já instalado** no computador/servidor onde o painel é executado. O programa não simula hashrate, não fabrica saldo e não declara pagamento sem confirmação do provedor.

## Execução real do minerador

O runtime em `genese_miner_runtime.py` inicia o executável configurado usando subprocesso sem shell, acompanha a saída real do processo, conta linhas que indicam shares aceitas/rejeitadas e permite encerrar o processo pelo painel.

É necessário ter equipamento compatível e um minerador legítimo instalado no mesmo computador/servidor. **Um Moto G35 não se transforma em ASIC nem passa a minerar Bitcoin de forma economicamente viável por instalar este painel.** O código não baixa executáveis, não instala mineradores por conta própria e não compra poder computacional.

Configure no ambiente do computador/servidor:

- `GENESE_MINER_EXECUTABLE`: caminho absoluto para o executável do minerador instalado, ou nome disponível no PATH.
- `GENESE_MINER_ARGS_JSON`: lista JSON de argumentos exigidos pelo minerador instalado. Os argumentos devem apontar para sua pool e credenciais/worker autorizados. Exemplo apenas de formato: `["--help"]`. Esse exemplo só mostra o formato e não inicia mineração útil.

Não coloque chaves, senhas ou frases-semente no repositório. Use apenas credenciais que você controla e confira o endereço e a rede de pagamento diretamente no provedor antes de minerar.

## Iniciar e parar

1. Instale e configure um minerador compatível com seu equipamento e algoritmo, seguindo a documentação oficial do fabricante/provedor.
2. Defina as duas variáveis acima no ambiente do processo que vai executar o painel.
3. Inicie o painel com `python genese_dashboard.py`.
4. Abra `http://127.0.0.1:8765` no mesmo computador/servidor e use **Iniciar minerador** ou **Parar**.
5. A saída exibida vem do processo externo. Contagens de shares não equivalem a lucro, saldo nem depósito na Binance.

O painel permanece preso a `127.0.0.1` por segurança. Não o exponha diretamente à internet.

## NiceHash e Binance

- `nicehash_readonly.py` consulta dados da NiceHash por API autenticada somente de leitura.
- `genese_pay_core.py` faz verificação TLS da pool e mantém declarações financeiras não verificadas separadas de receita confirmada.
- A configuração de endereço Binance **não** realiza transferência. Este repositório ainda não executa saque na NiceHash nem comprova depósito na Binance.
- O código não explora contas alheias, não retira fundos de terceiros e não cria dinheiro do nada.

## Demais módulos

- `genese_dashboard.py`: interface web local com controles do processo de mineração.
- `genese_autonomo.py` e `priorizador_recompensas.py`: diagnóstico de conectividade e organização de programas públicos de recompensa; encontrar um programa não garante recompensa.
- `.github/workflows/genese.yml`: verificação automática de sintaxe e integridade do código. Essa automação não representa mineração ou pagamento.

