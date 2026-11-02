# TelaViva

Central gratuita de descoberta de entretenimento para navegador, Android via PWA e uso em navegadores de TV.

## O que está implementado
- Interface responsiva para celular, computador e telas grandes.
- Catálogo de descoberta separado em filmes, séries, esportes e ao vivo.
- Pesquisa em português e filtros por categoria.
- Favoritos salvos localmente no navegador.
- Atalhos para Pluto TV, Plex e YouTube.
- Instalação PWA quando o navegador oferece suporte.
- Cache do aplicativo para abrir a interface sem conexão depois da primeira visita.
- Navegação por teclado e setas, útil em teclados e controles remotos compatíveis.
- Indicador de conectividade e mensagens acessíveis.
- Verificação automática de sintaxe e estrutura pelo GitHub Actions.

## Abrir
Hospede os arquivos em qualquer hospedagem estática HTTPS. Para testar localmente:

```bash
python -m http.server 8080
```

Abra `http://localhost:8080`. O service worker exige HTTPS, exceto em localhost.

## Serviços e direitos
TelaViva é um diretório/central de descoberta. Não hospeda, grava, desbloqueia ou retransmite filmes, séries, canais ou partidas. Os cartões são atalhos para serviços externos, não garantem que um título ou evento esteja disponível. Cada plataforma controla catálogo, região, publicidade, login e direitos de transmissão. Só devem ser adicionadas fontes oficiais ou licenciadas.

## Android e Android TV
No Android, instale pelo aviso do navegador ou pelo menu “Instalar aplicativo/Adicionar à tela inicial”. Em Android TV, abra a URL em um navegador compatível. A navegação por setas/Enter funciona quando o navegador da TV envia eventos de teclado. Esta entrega ainda não é um APK nativo nem um app publicado na Play Store.

## Publicação
O workflow em `.github/workflows/quality.yml` verifica os arquivos a cada push e pull request. O workflow `pages.yml` publica no GitHub Pages quando a opção Pages estiver habilitada para o repositório com origem GitHub Actions.

## Limites desta versão
- Não há player próprio nem feed de programação ao vivo.
- Não há API de catálogo integrada porque os serviços precisam autorizar acesso e incorporação.
- Favoritos ficam neste navegador/dispositivo e não sincronizam entre aparelhos.
- A interface funciona offline, mas os vídeos e serviços externos precisam de internet.
