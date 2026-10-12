#[test]
fn logout_cannot_fall_back_to_the_startup_environment_key() {
    keyring::set_default_credential_builder(keyring::mock::default_credential_builder());
    unsafe {
        std::env::set_var("XAI_API_KEY", "synthetic-stale-key");
    }
    xai_grok_login::synderesis::configure(Some("synthetic-current-key".into()));
    assert_eq!(
        xai_grok_login::auth_method::read_xai_api_key_env().unwrap(),
        "synthetic-current-key"
    );
    xai_grok_login::synderesis::logout().unwrap();
    assert!(xai_grok_login::auth_method::read_xai_api_key_env().is_err());
    assert!(xai_grok_login::synderesis::current_key().is_none());
}
