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
```

O fluxo GitHub Actions compila o código e executa os testes. O relatório produzido localmente é `genese_oportunidades.json`.

## Limites importantes

- O catálogo é uma fonte pública limitada, não uma varredura de toda a internet.
- Correspondência por palavra-chave não prova que exista uma falha, dinheiro disponível, elegibilidade ou pagamento por Pix.
- Qualquer teste técnico deve ser feito somente em ativos explicitamente autorizados e dentro do escopo e das regras publicadas.
- Não há exploração automática, acesso a contas, retirada de fundos, mineração ou pagamento automático.
- A carteira interna é apenas um livro contábil. Cobrança de teste e webhook não equivalem a saldo bancário nem habilitam saques.
- Um pagamento real exige um direito legítimo ao recebimento, confirmação do pagador/provedor e conciliação.

O projeto pode organizar oportunidades legítimas e evidências, mas não pode garantir renda nem fabricar dinheiro a partir de dados públicos.
