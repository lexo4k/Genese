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

## Livro de recompensas auditável

O arquivo `registro_recompensas.py` registra oportunidades e acompanha estados como `encontrada`, `aprovada` e `paga`. É um livro contábil local, não uma consulta bancária independente. Só marque uma recompensa como aprovada/paga quando houver evidência oficial correspondente.

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
