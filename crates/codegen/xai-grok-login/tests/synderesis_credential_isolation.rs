// Modified by Synderesis, 2026-10-12: verify the product credential cannot leave on upstream media/auth paths.
use std::sync::Arc;
use wiremock::MockServer;
use xai_grok_login::config::GrokComConfig;
use xai_grok_login::manager::Login;
use xai_grok_login::side_call_bearer::SharedAuthKeyProvider;
use xai_grok_login::{AuthError, AuthManager, AuthMode, GrokAuth};
use xai_grok_tools::implementations::grok_build::image_gen::{ImageGenClient, ImageGenConfig};
use xai_grok_tools::types::ApiKeyProvider;
use xai_grok_tools::types::api_key_provider::SideCallBearerError;

#[tokio::test]
async fn product_auth_stays_on_its_route_and_never_reaches_upstream_media() {
    xai_grok_login::synderesis::configure(Some("synthetic-product-key".into()));
    let dir = tempfile::tempdir().unwrap();
    let server = MockServer::start().await;
    let manager = Arc::new(AuthManager::new_with_proxy_base_url(
        dir.path(),
        GrokComConfig::default(),
        server.uri(),
    ));
    manager.hot_swap(GrokAuth {
        key: "synthetic-cached-upstream-key".into(),
        auth_mode: AuthMode::ApiKey,
        ..Default::default()
    });
    manager.set_process_static_api_key(Some("synthetic-static-upstream-key".into()));
    assert_eq!(
        xai_grok_login::auth_method::read_xai_api_key_env().unwrap(),
        "synthetic-product-key"
    );
    assert!(manager.current().is_none());
    assert!(manager.current_wire_valid().is_none());
    assert!(manager.current_or_expired().is_none());
    assert_eq!(manager.login_changes().snapshot().login, Login::SignedOut);
    assert!(matches!(manager.auth().await, Err(AuthError::NotLoggedIn)));
    assert!(manager.static_api_key_for_export().is_none());
    assert!(matches!(
        manager.side_call_bearer(),
        Err(SideCallBearerError::ForeignSession)
    ));
    assert!(matches!(
        manager.side_call_bearer_async().await,
        Err(SideCallBearerError::ForeignSession)
    ));
    let provider = Arc::new(SharedAuthKeyProvider(manager));
    assert!(provider.current_api_key().is_none());
    assert!(provider.current_api_key_async().await.is_none());
    let client = ImageGenClient::new(
        &ImageGenConfig::Enabled {
            api_key: None,
            base_url: server.uri(),
            extra_headers: indexmap::IndexMap::new(),
            image_gen_enabled: true,
            image_edit_enabled: true,
            model_override: None,
            edit_model_override: None,
            tier_restricted: false,
        },
        Some(provider),
    )
    .unwrap();
    assert!(client.generate("a cat", "auto").await.is_err());
    assert!(
        server.received_requests().await.unwrap().is_empty(),
        "no HTTP request may carry the product credential to an upstream image service"
    );
}
