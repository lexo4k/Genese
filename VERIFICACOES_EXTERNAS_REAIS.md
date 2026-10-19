# Verificações externas reais do GÊNESE PAY

## Consultar situação cadastral de CNPJ

```bash
python verificador_confirmacoes_reais.py cnpj 11.222.333/0001-81
```

O exemplo de CNPJ acima é apenas ilustrativo e pode falhar no dígito verificador. Use o CNPJ real da empresa que você tem autorização para consultar. A ferramenta consulta a BrasilAPI, um espelho de dados públicos cadastrais. Se retornar situação ativa, isso é uma confirmação preliminar externa, não substitui o comprovante oficial da Receita Federal nem registra empresa nova.

## Verificar depósitos efetivamente creditados na Binance

Crie uma chave API Binance com **somente permissões de leitura**. Não habilite trading ou saques. Configure os segredos no ambiente do dispositivo/servidor, nunca no código, em commit, issue ou mensagem:

```bash
export BINANCE_API_KEY='sua_chave_de_leitura'
export BINANCE_API_SECRET='seu_segredo'
python verificador_confirmacoes_reais.py binance-deposits
python verificador_confirmacoes_reais.py binance-deposits --coin USDT
```

A integração usa o histórico privado de depósitos Spot. Só o status Binance `1` é tratado como depósito creditado com sucesso. Estados pendentes, bloqueados ou outros não contam. A ferramenta é somente leitura e não envia nem movimenta fundos.

## O que isso confirma e o que não confirma

- **CNPJ encontrado e ativo:** consulta externa ao espelho cadastral; confirme a prova jurídica no canal oficial.
- **Depósito Binance status 1:** a API da Binance retornou um depósito creditado.
- **Receita do GÊNESE PAY:** não é inferida só porque há um depósito. Para classificá-lo como receita do projeto, também é preciso vincular o depósito a um contrato, recompensa ou venda legítima identificável.
- **Empresa nova:** o código não registra uma empresa. O registro deve ocorrer nos órgãos competentes e requer dados e autorizações legítimos.
- **Testes automatizados:** usam payloads de teste e não afirmam que um CNPJ ou depósito real foi consultado.

Execute os testes com `python -m unittest tests.test_verificador_confirmacoes_reais -v` ou pela suíte do repositório.
