# GÊNESE

Motor de descoberta de oportunidades públicas de receita legítima, com priorização cripto/Web3, relatórios auditáveis e registro de evidências. O sistema identifica pistas e organiza a investigação; não afirma que encontrou dinheiro nem garante ganhos.

## Descoberta autônoma

O `motor_receita.py` reúne um diretório de programas de bug bounty e issues públicas do GitHub que mencionam recompensa/valor. Deduplica links, prioriza sinais relacionados a cripto/Web3 e salva um relatório JSON. Uma menção a recompensa é apenas uma pista: confira a fonte oficial, regras, escopo, elegibilidade e se a oferta continua ativa.

```bash
python motor_receita.py
python motor_receita.py --json
python motor_receita.py --output relatorio.json --json
```

O relatório padrão é salvo como `genese_receita.json`.

## Diagnóstico e priorização

Requisitos: Python 3.10+ e `curl`.

```bash
python genese_autonomo.py --json
python priorizador_recompensas.py > oportunidades.json
python -m unittest discover -s tests -v
```

O diagnóstico verifica DNS/HTTPS, lê um catálogo público limitado e consulta a cotação USD/BRL. O priorizador organiza programas por correspondência textual com termos de cripto/Web3. Nenhuma dessas operações comprova uma falha, direito a recompensa ou pagamento.

## Binance: cotação pública (somente leitura)

O arquivo `binance_public.py` consulta a API pública Spot sem chave de API e sem entrar em conta privada:

```bash
python binance_public.py --symbol BTCUSDT
python binance_public.py --symbol ETHUSDT
python -m unittest -v test_binance_public
```

A cotação pública não é saldo, receita, lucro garantido nem transferência. Esta integração não acessa saldo privado, não negocia e não deposita/saca fundos.

## Livro de recompensas auditável

O arquivo `registro_recompensas.py` registra oportunidades e acompanha os estados `encontrada`, `aprovada` e `paga`. É um livro contábil local, não uma consulta bancária independente.

```bash
python registro_recompensas.py adicionar --titulo "Programa público" --url https://example.org/security
python registro_recompensas.py resumo
```

Só marque uma recompensa como aprovada/paga quando houver evidência oficial correspondente.

## Segurança e limites

- O GÊNESE não explora sistemas, não testa alvos automaticamente, não acessa contas alheias e não retira fundos.
- Testes de segurança só podem ocorrer em ativos expressamente autorizados e dentro das regras publicadas.
- Nenhuma senha, seed phrase, chave privada ou API key privada da Binance é necessária.
- O programa não cria dinheiro do nada. Receita confirmada permanece zero até existir evidência confiável de recebimento.
- Não há pagamento, Pix, depósito ou saque automático. A carteira interna continua em modo contábil até existir integração legítima, segura e testada com um provedor.
- A lista pública é limitada e pode conter resultados desatualizados ou não elegíveis. Confirme sempre no site oficial.