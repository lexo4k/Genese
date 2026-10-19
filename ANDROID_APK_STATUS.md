# GÊNESE PAY Android APK

## O que esta etapa entrega

- Projeto Android nativo em Java com WebView restrita ao domínio HTTPS configurado.
- Bloqueio de tráfego HTTP sem TLS, conteúdo misto, acesso a arquivos locais e navegação interna para outros domínios.
- Workflow GitHub Actions que compila um APK debug, verifica que o arquivo existe e publica o artefato por 30 dias.
- Nenhum saldo fictício, chave privada, seed phrase ou segredo Binance dentro do APK.

## Como obter o APK de teste

1. Abra a aba Actions do repositório.
2. Selecione GENESE PAY Android APK e abra uma execução concluída com sucesso.
3. Baixe o artefato `genese-pay-android-debug-apk` na seção Artifacts.
4. O APK debug serve para teste, não para distribuição como versão de produção.

## Bloqueios de produção

O build debug é uma prova de compilação, não comprova que o serviço financeiro está implantado. O APK abre uma tela de configuração se `GENESE_BASE_URL` não estiver definida.

Para uma versão utilizável, é necessário:
- publicar `wallet_api.py` em um serviço HTTPS público, com banco persistente e configuração segura;
- executar testes de ponta a ponta no backend implantado;
- configurar `GENESE_BASE_URL` com o domínio HTTPS do serviço;
- configurar os segredos de assinatura Android `ANDROID_KEYSTORE_BASE64`, `ANDROID_KEYSTORE_PASSWORD`, `ANDROID_KEY_ALIAS` e `ANDROID_KEY_PASSWORD`;
- gerar e validar um APK release assinado e testar em dispositivo físico;
- revisar privacidade, autenticação, proteção de dados, políticas de distribuição e integrações financeiras.

**Estado honesto:** o projeto Android e o pipeline de APK de teste foram adicionados. A versão de produção ainda não pode ser declarada pronta enquanto não houver endpoint HTTPS, assinatura de release, testes no dispositivo e validação das integrações reais. O app não gera dinheiro por si só e não realiza depósitos ou transferências Binance.
