# TelaViva

Aplicação web progressiva (PWA) com experiência de navegação inspirada em serviços de streaming.

## Recursos implementados
- Navegação por início, filmes, séries, esportes, ao vivo, minha lista e disponíveis para assistir.
- Busca por título, descrição, palavras-chave e fonte.
- Ordenação alfabética e recomendada.
- Identificação visual de conteúdo reproduzível versus prévias demonstrativas.
- Detalhes de título, favoritos e perfis locais separados por perfil.
- Player oficial do YouTube para Big Buck Bunny, Sintel, Tears of Steel e episódios 2 e 3 de Caminandes, com tela cheia, tratamento de falhas e link alternativo para abrir a fonte.
- Retomada de reprodução via YouTube IFrame API, com salvamento periódico do ponto assistido.
- Retomada de progresso preparada para fontes HTML5 próprias autorizadas.
- PWA instalável em navegadores compatíveis e cache offline da interface.

## Catálogo e direitos
Big Buck Bunny é um filme aberto da Blender Foundation, sob licença Creative Commons Attribution 3.0, reproduzido pelo player oficial incorporado do YouTube. Atribuição: © 2008 Blender Foundation / www.bigbuckbunny.org.
Os demais cartões são prévias demonstrativas e não representam filmes, séries ou eventos disponíveis para reprodução. Pluto TV e Plex são links externos, não integrações de reprodução dentro deste app. O projeto não extrai streams de serviços terceiros.
Para adicionar títulos reais, cada item precisa de arquivo de mídia/URL fornecido pelo titular ou uma integração oficial autorizada. Metadados e pôsteres não concedem direitos de exibição. Respeitar DRM, autenticação, georrestrições, atribuição e termos de cada provedor.

## Integrações oficiais e configuração

O backend Vercel inclui endpoints server-side para:
- `/api/search?q=...`: pesquisa de filmes e séries no TMDB, com conteúdo adulto excluído. Retorna apenas metadados e imagens; não fornece arquivos de vídeo nem direitos de reprodução.
- `/api/availability?id=...&type=movie|tv`: consulta ofertas no Brasil pela JustWatch Partner API e só funciona com token de parceiro.
- `/api/integrations`: informa quais credenciais e fontes estão realmente configuradas.

Configure no painel do projeto Vercel, em Environment Variables, sem publicar os valores no Git:
- `TMDB_READ_ACCESS_TOKEN`: token de leitura do TMDB. Para uso comercial, é necessária autorização/licença comercial do TMDB. A chave de desenvolvedor gratuita não deve ser presumida como licença comercial.
- `JUSTWATCH_PARTNER_TOKEN`: token emitido após contrato com a JustWatch.

A API do Prime Video é destinada atualmente a parceiros gerenciados. A integração de reprodução direta do Plex depende de identificação, credenciais, acordo e requisitos técnicos fornecidos pelo próprio Plex. Esses serviços permanecem corretamente marcados como pendentes até que o acesso seja concedido. Não há reprodução direta de Netflix, Disney+, Prime Video, Plex ou Pluto TV neste projeto sem integração autorizada do respectivo provedor.

Atribuição TMDB obrigatória quando a integração estiver ativa: “This product uses the TMDB API but is not endorsed or certified by TMDB.” Consulte os termos e requisitos de marca do TMDB antes de ativar uso comercial.

## Limitações atuais
- Perfis, favoritos e progresso são locais ao navegador/dispositivo; não existe login nem sincronização na nuvem.
- A incorporação do YouTube pode estar sujeita a restrições do titular, disponibilidade regional e políticas da plataforma. A retomada depende de a API oficial carregar e permitir a reprodução.
- Ainda não há contas na nuvem, sincronização de perfis, recomendações algorítmicas, controle parental, CDN próprio, DRM próprio ou painel administrativo.
- É uma PWA, não um APK nativo nem um app Android TV publicado.

## Desenvolvimento local
Execute `python -m http.server 8080` e abra `http://localhost:8080`. Service worker requer HTTPS, exceto localhost.

## Próximas etapas de produção
1. Contratar/obter licenças e definir provedores de conteúdo com permissão de reprodução.
2. Criar backend de contas, perfis, catálogo editorial e sincronização.
3. Configurar credenciais TMDB/JustWatch autorizadas no Vercel e validar os contratos/termos comerciais.
4. Implementar reprodução adaptativa, legendas, múltiplas faixas de áudio, DRM e CDN conforme contratos.
5. Criar apps nativos Android/Android TV, testes em aparelhos e publicação nas lojas.

Nunca publicar credenciais, tokens privados ou URLs secretas de mídia no repositório.
