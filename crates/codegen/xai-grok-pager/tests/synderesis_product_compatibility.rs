// Modified by Synderesis, 2026-10-12: retain auth, theme, sandbox and settings compatibility.
#[test]
fn product_advertises_its_auth_and_preserves_saved_preferences() {
    use xai_grok_shell::agent::auth_method::{AuthMethodsBuildInputs, build_auth_methods};
    xai_grok_login::synderesis::configure(Some("synthetic-product-key".into()));
    let methods = build_auth_methods(AuthMethodsBuildInputs {
        has_external_api_key: true,
        has_cached_token: true,
        has_enterprise_oidc: true,
        enterprise_oidc_issuer: Some("https://wrong.invalid"),
        login_label: Some("Wrong provider"),
        has_auth_provider_command: true,
        preferred_method: None,
    });
    assert_eq!(methods.methods.len(), 2);
    assert!(
        methods
            .methods
            .iter()
            .all(|m| m.name().contains("Synderesis"))
    );
    let (label, method, _) = xai_grok_pager::acp::find_interactive_login_method(&methods.methods);
    assert_eq!(label.as_deref(), Some("Synderesis"));
    assert_eq!(method.unwrap().0.as_ref(), "synderesis.login");
    // The product sandbox environment choice survives bootstrap's upstream-env cleanup.
    unsafe {
        std::env::set_var("SYNDERESIS_CODE_SANDBOX", "none");
    }
    use clap::Parser;
    let args = xai_grok_pager::app::PagerArgs::try_parse_from(["synderesis-code"]).unwrap();
    assert_eq!(args.sandbox.as_deref(), Some("none"));
    let settings = xai_grok_pager::settings::defs::default_settings();
    for hidden in [
        "coding_data_sharing",
        "voice_keybind_enabled",
        "voice_capture_mode",
        "voice_stt_language",
    ] {
        assert!(
            !settings.iter().any(|setting| setting.key == hidden),
            "unsupported upstream setting {hidden} is visible"
        );
    }
    use xai_grok_pager::theme::ThemeKind;
    for (old, current) in [
        ("groknight", "synderesis-night"),
        ("grok-night", "synderesis-night"),
        ("grokday", "synderesis-day"),
        ("grok-day", "synderesis-day"),
    ] {
        assert_eq!(ThemeKind::from_name(old), ThemeKind::from_name(current));
        assert_eq!(ThemeKind::from_name(old).unwrap().display_name(), current);
    }
}
