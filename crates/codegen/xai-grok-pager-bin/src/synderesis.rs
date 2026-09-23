// Modified by Synderesis, 2026-09-20: product bootstrap, isolated state and API routing.
use anyhow::{Result, bail};
use std::path::PathBuf;

pub fn configure() -> Result<()> {
    let home = std::env::var_os("SYNDERESIS_CODE_HOME")
        .map(PathBuf::from)
        .or_else(|| {
            // Native Windows shells normally expose USERPROFILE, not HOME.
            let user_home = if cfg!(windows) {
                std::env::var_os("USERPROFILE").or_else(|| std::env::var_os("HOME"))
            } else {
                std::env::var_os("HOME")
            };
            user_home.map(|p| PathBuf::from(p).join(".synderesis-code"))
        })
        .ok_or_else(|| anyhow::anyhow!("Set SYNDERESIS_CODE_HOME to your private state directory"))?;
    let mut key = std::env::var("SYNDERESIS_API_KEY").unwrap_or_default();
    let args: Vec<String> = std::env::args().skip(1).collect();
    if args.iter().any(|a| a == "--reauth" || a == "--reauthenticate") {
        bail!("Use synderesis-code login to sign in through the Synderesis website");
    }
    if args.first().is_some_and(|a| matches!(a.as_str(), "setup" | "share" | "trace")) {
        bail!("This upstream cloud command is not part of Synderesis Code");
    }
    let information_only = args.iter().any(|a| matches!(a.as_str(), "--help" | "-h" | "--version" | "-v" | "-V" | "version" | "doctor" | "help"));
    if args.first().is_some_and(|a| a == "logout") {
        crate::synderesis_auth::logout()?;
        std::process::exit(0);
    }
    if args.first().is_some_and(|a| a == "login") {
        crate::synderesis_auth::login()?;
        std::process::exit(0);
    }
    if key.trim().is_empty() { key = crate::synderesis_auth::saved_key().unwrap_or_default(); }
    if !information_only && key.trim().is_empty() { key = crate::synderesis_auth::login()?; }
    if key.chars().any(char::is_whitespace) {
        bail!("SYNDERESIS_API_KEY must not contain whitespace");
    }
    let base_url = "https://www.synderesis.eu/v1/code".to_owned();
    #[cfg(feature = "synderesis-test-endpoint")]
    let base_url = {
        let value = std::env::var("SYNDERESIS_CODE_TEST_BASE_URL").unwrap_or(base_url);
        let url = reqwest::Url::parse(&value)?;
        if url.scheme() != "http" || url.host_str() != Some("127.0.0.1") {
            bail!("Test builds require an explicit loopback test endpoint");
        }
        value
    };
    xai_grok_login::synderesis::configure((!key.is_empty()).then(|| key.clone()));
    xai_grok_shell::agent::config::configure_synderesis_model(base_url.clone());
    let config = serde_json::json!({
        "cli": {"auto_update": false},
        "telemetry": {"enabled": false, "otel_enabled": false},
        "relay": {"enabled": false},
        "compat": {"claude": {"mcps": false, "hooks": false}, "cursor": {"mcps": false, "hooks": false}},
        "models": {"default": "synderesis-code", "allowed_models": ["synderesis-code"],
            "web_search": "synderesis-code", "session_summary": "synderesis-code", "image_description": "synderesis-code", "prompt_suggestion": "synderesis-code"}
    });
    // Runs at the very beginning of main, before threads or the async runtime exist.
    unsafe {
        for (name, _) in std::env::vars_os() {
            if name.to_str().is_some_and(|n| n.starts_with("GROK_") || n.starts_with("XAI_") || n.starts_with("OTEL_")) {
                std::env::remove_var(name);
            }
        }
        std::env::set_var("GROK_HOME", home);
        // Internal upstream auth resolver expects this name. The value is a Synderesis
        // customer key, not an xAI key; all built-in inference uses the Synderesis endpoint.
        std::env::set_var("SYNDERESIS_API_KEY", &key);
        std::env::set_var("XAI_API_KEY", key);
        std::env::set_var("GROK_CONFIG", config.to_string());
        std::env::set_var("GROK_MODELS_BASE_URL", &base_url);
        std::env::set_var("GROK_MODELS_LIST_URL", format!("{base_url}/models"));
        for (name, value) in [
            ("GROK_DISABLE_AUTOUPDATER", "1"), ("DISABLE_ERROR_REPORTING", "1"), ("DISABLE_TELEMETRY", "1"),
            ("GROK_TELEMETRY_ENABLED", "0"), ("GROK_TELEMETRY_TRACE_UPLOAD", "0"),
            ("GROK_CLAUDE_MCPS_ENABLED", "0"), ("GROK_CURSOR_MCPS_ENABLED", "0"),
            ("GROK_CLAUDE_HOOKS_ENABLED", "0"), ("GROK_CURSOR_HOOKS_ENABLED", "0"),
            ("GROK_RELAY_SYNC_ENABLED", "0"), ("OTEL_TRACES_EXPORTER", "none")
        ] { std::env::set_var(name, value); }
    }
    Ok(())
}
