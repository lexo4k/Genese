# TelaViva

Experiência de streaming em formato de catálogo, com interface cinematográfica, perfis locais, Minha lista, detalhes, progresso preparado e player HTML5.

## Implementado
- Interface inspirada em plataformas de streaming, destaque e catálogo em cartões.
- Categorias: filmes, séries, esportes e ao vivo.
- Pesquisa, detalhes, favoritos e perfis locais.
- Seção Continuar assistindo preparada para progresso de players autorizados.
- Player com incorporação oficial do YouTube para o filme aberto Big Buck Bunny (Blender Foundation), além de player HTML5 para fontes próprias autorizadas.
- PWA instalável em navegadores compatíveis e cache offline da interface.

## Direitos e reprodução
O catálogo inclui Big Buck Bunny, filme aberto da Blender Foundation sob Creative Commons Attribution 3.0, reproduzido pelo player oficial incorporado do YouTube. Atribuição: © 2008 Blender Foundation / www.bigbuckbunny.org. Os demais cartões continuam demonstrativos. O player não extrai streams de serviços terceiros. Para ativar reprodução real, cada item precisa de uma URL de mídia fornecida pelo titular/licenciante, ou integração oficial autorizada com permissões e termos do provedor. DRM, autenticação e georrestrições devem ser respeitados. Pluto TV e Plex são links externos, não prova de autorização para incorporar seus players. O vídeo Big Buck Bunny usa incorporação padrão do YouTube e respeita a disponibilidade definida pelo titular.

## Perfis e dados
Perfis, lista e progresso ficam no armazenamento local do navegador/dispositivo. Não há login, sincronização em nuvem ou backend nesta entrega.

## Executar localmente
`python -m http.server 8080` e abrir http://localhost:8080. Service worker exige HTTPS, exceto localhost.

## Android / Android TV
Instalação PWA em navegadores compatíveis. Ainda não é APK nativo nem app publicado na Play Store/Android TV.

## Próxima etapa de produção
1. Obter licenças e selecionar APIs/players oficiais que autorizem distribuição/embeds.
2. Ingerir metadados e artes por API com chave guardada no backend. TMDB fornece metadados, não direitos de reprodução.
3. Criar backend de contas, perfis, sincronização, catálogo editorial e histórico.
4. Integrar provedores de vídeo, CDN, autenticação e DRM conforme contratos.
5. Testar em dispositivos reais e publicar APK/Android TV após implementação nativa.

Nunca publicar streams, chaves privadas ou credenciais no repositório.
