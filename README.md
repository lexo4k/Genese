# GÊNESE

Monitor de fontes públicas para descobrir programas de recompensa de segurança e priorizar os que parecem relacionados a cripto/Web3.

## O que faz
- Testa DNS, HTTPS e acesso às fontes públicas.
- Consulta um catálogo público de programas de bug bounty.
- Prioriza programas com termos como Bitcoin, wallet, blockchain, Web3 e DeFi.
- Gera relatórios JSON para revisar as oportunidades.

## O que não faz
- Não procura nem toma fundos de carteiras ou contas de terceiros.
- Não explora vulnerabilidades, não contorna autenticação e não faz varredura ativa de alvos.
- Não promete rendimento nem afirma que um programa contém fundos perdidos.
- Não submete relatórios nem movimenta pagamentos automaticamente.

Uma recompensa só pode surgir de um programa autorizado, com teste dentro do escopo, falha válida, relatório aceito e aprovação do programa.

## Executar
Requisitos: Python 3.10+ e `curl`.

```bash
python genese_autonomo.py --json
python priorizador_recompensas.py > oportunidades.json
python -m unittest discover -s tests -v
```

O fluxo GitHub Actions executa testes e guarda os relatórios como artefatos.
