package com.genese.pay;

import android.app.Activity;
import android.content.Intent;
import android.graphics.Color;
import android.net.Uri;
import android.os.Bundle;
import android.view.ViewGroup;
import android.webkit.WebChromeClient;
import android.webkit.WebResourceRequest;
import android.webkit.WebSettings;
import android.webkit.WebView;
import android.webkit.WebViewClient;
import android.widget.FrameLayout;
import android.widget.TextView;
import java.net.URI;

public final class MainActivity extends Activity {
    private WebView webView;
    private String trustedHost;

    @Override protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        String baseUrl = BuildConfig.GENESE_BASE_URL;
        if (baseUrl == null || baseUrl.trim().isEmpty()) { showSetupNotice(); return; }
        try {
            URI uri = URI.create(baseUrl);
            if (!"https".equalsIgnoreCase(uri.getScheme()) || uri.getHost() == null || uri.getUserInfo() != null) { showSetupNotice(); return; }
            trustedHost = uri.getHost().toLowerCase();
        } catch (RuntimeException ex) { showSetupNotice(); return; }

        webView = new WebView(this);
        webView.setBackgroundColor(Color.rgb(16, 24, 39));
        WebSettings settings = webView.getSettings();
        settings.setJavaScriptEnabled(true);
        settings.setDomStorageEnabled(true);
        settings.setAllowFileAccess(false);
        settings.setAllowContentAccess(false);
        settings.setMixedContentMode(WebSettings.MIXED_CONTENT_NEVER_ALLOW);
        settings.setJavaScriptCanOpenWindowsAutomatically(false);
        settings.setSupportMultipleWindows(false);
        settings.setSafeBrowsingEnabled(true);
        webView.setWebChromeClient(new WebChromeClient());
        webView.setWebViewClient(new WebViewClient() {
            @Override public boolean shouldOverrideUrlLoading(WebView view, WebResourceRequest request) {
                Uri target = request.getUrl();
                String scheme = target.getScheme();
                String host = target.getHost();
                if ("https".equalsIgnoreCase(scheme) && host != null && host.equalsIgnoreCase(trustedHost)) return false;
                if ("https".equalsIgnoreCase(scheme) || "mailto".equalsIgnoreCase(scheme)) {
                    try { startActivity(new Intent(Intent.ACTION_VIEW, target)); } catch (Exception ignored) { }
                }
                return true;
            }
        });
        setContentView(webView, new ViewGroup.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        webView.loadUrl(baseUrl);
    }

    private void showSetupNotice() {
        FrameLayout root = new FrameLayout(this);
        root.setBackgroundColor(Color.rgb(11, 17, 32));
        TextView notice = new TextView(this);
        notice.setTextColor(Color.rgb(238, 244, 255));
        notice.setTextSize(18);
        notice.setPadding(40, 48, 40, 48);
        notice.setText("GÊNESE PAY\n\nO aplicativo Android foi compilado, mas o serviço HTTPS ainda não foi configurado.\n\nPara a versão de produção, publique a API com HTTPS e gere a versão assinada apontando para o domínio oficial. Nenhum saldo ou recebimento é simulado.");
        root.addView(notice, new FrameLayout.LayoutParams(ViewGroup.LayoutParams.MATCH_PARENT, ViewGroup.LayoutParams.MATCH_PARENT));
        setContentView(root);
    }

    @Override public void onBackPressed() {
        if (webView != null && webView.canGoBack()) webView.goBack(); else super.onBackPressed();
    }
    @Override protected void onDestroy() {
        if (webView != null) { webView.destroy(); webView = null; }
        super.onDestroy();
    }
}
