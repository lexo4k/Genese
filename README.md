# TelaViva

Central gratuita de entretenimento para navegador, Android (PWA) e futura versão Android TV.

## Estado atual
Esta primeira versão é uma PWA responsiva com catálogo demonstrativo, pesquisa, filtros, favoritos locais e diretório de serviços oficiais gratuitos. Ela **não hospeda nem retransmite** filmes, séries ou partidas. Cada conteúdo real precisa de uma fonte oficial/licenciada antes de ser publicado.

## Executar localmente
Abra `index.html` em um servidor estático. Exemplo:

```bash
python -m http.server 8080
```

Acesse `http://localhost:8080`.

## Próximas etapas
- Integrar catálogos/APIs autorizadas e feeds oficiais.
- Validar disponibilidade regional e direitos de cada transmissão.
- Criar player somente para fontes que autorizem incorporação.
- Empacotar para Android e adaptar navegação por controle remoto para Android TV.
- Adicionar testes automatizados e pipeline de build.

## Gratuito
Sem assinatura ou cobrança. Custos de hospedagem e eventuais anúncios só devem ser adicionados com transparência.
