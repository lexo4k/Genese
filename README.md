# GÊNESE

Monitor de fontes públicas para listar programas de recompensa de segurança, priorizar os que parecem relacionados a cripto/Web3 e produzir relatórios auditáveis.

## Fluxo atual

1. Diagnostica DNS e HTTPS para fontes públicas configuradas.
2. Lê um catálogo público de programas que declaram oferecer recompensas.
3. Prioriza registros por correspondência textual com termos de cripto/Web3.
4. Gera um relatório JSON com links oficiais, escopo publicado e próximos passos.
5. Registra explicitamente que receitas, saldos e pagamentos permanecem não confirmados.
6. Mantém a carteira em modo contábil/sandbox, sem afirmar que há dinheiro real disponível.

## Executar

Requisitos: Python 3.10+ e `curl`.

```bash
python genese_autonomo.py --json
python priorizador_recompensas.py > oportunidades.json
python -m unittest discover -s tests -v
python -m unittest test_registro_recompensas -v
```

O fluxo GitHub Actions compila o código e executa os testes. O relatório produzido localmente é `genese_oportunidades.json`. O livro de recompensas usa `recompensas_registro.json` (ou o caminho indicado por `--db`).

## Binance: cotação pública (somente leitura)

O arquivo `binance_public.py` consulta a API pública Spot sem chave de API e sem entrar em conta privada. Para consultar o preço atual retornado pela Binance:

```bash
python binance_public.py --symbol BTCUSDT
python binance_public.py --symbol ETHUSDT
python -m unittest -v test_binance_public
```

A resposta contém campos explícitos indicando que cotação não é saldo, receita, lucro garantido nem transferência. Esta integração não acessa saldo privado, não negocia e não deposita/saca fundos.

## Livro de recompensas auditável

O arquivo `registro_recompensas.py` registra oportunidades e acompanha os estados `encontrada`, `aprovada` e `paga`. Ele não acessa banco, corretora ou carteira e não envia transações.

```bash
# Registrar uma oportunidade pública
python registro_recompensas.py adicionar --titulo "Programa público" --url https://example.org/security

# Registrar aprovação oficial (substitua o ID e a evidência pelos dados reais)
python registro_recompensas.py aprovar --id 1 --valor 25 --moeda BRL --evidencia-url https://example.org/approval

# Só depois de receber, registrar evidência oficial do pagamento
python registro_recompensas.py pagar --id 1 --evidencia-url https://example.org/payment
python registro_recompensas.py resumo
```

O total do resumo é um registro informado pelo operador, não uma consulta bancária independente. O programa exige URLs HTTPS e estados coerentes, mas não consegue provar sozinho que uma página é autêntica ou que o dinheiro entrou na conta.

## Limites importantes

- O catálogo é uma fonte pública limitada, não uma varredura de toda a internet.
- Correspondência por palavra-chave não prova que exista uma falha, dinheiro disponível, elegibilidade ou pagamento por Pix.
- Qualquer teste técnico deve ser feito somente em ativos explicitamente autorizados e dentro do escopo e das regras publicadas.
- Não há exploração automática, acesso a contas, retirada de fundos, mineração ou pagamento automático.
- A carteira interna é apenas um livro contábil. Cobrança de teste e webhook não equivalem a saldo bancário nem habilitam saques.
- Um pagamento real exige um direito legítimo ao recebimento, confirmação do pagador/provedor e conciliação.

O projeto pode organizar oportunidades legítimas e evidências, mas não pode garantir renda nem fabricar dinheiro a partir de dados públicos.
