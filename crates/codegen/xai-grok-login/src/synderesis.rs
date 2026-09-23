// Synderesis Code: website PKCE login with loopback callback and OS credential storage.
use anyhow::{Context, Result, bail};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use sha2::{Digest, Sha256};
use std::sync::{OnceLock, RwLock};
use std::time::Duration;
use tokio::io::{AsyncReadExt, AsyncWriteExt};
use tokio::net::TcpListener;
use tokio::time::{Instant, timeout};

static PRODUCT_KEY: OnceLock<RwLock<Option<String>>> = OnceLock::new();

/// Installed once by the product bootstrap; never mutate process environment in the TUI.
pub fn configure(key: Option<String>) {
    #[cfg(feature = "synderesis-test-endpoint")]
    if std::env::var_os("SYNDERESIS_CODE_TEST_AUTH_ORIGIN").is_some() {
        // Isolated fixture binary only: never touch the operator's credential store.
        keyring::set_default_credential_builder(keyring::mock::default_credential_builder());
    }
    assert!(
        PRODUCT_KEY.set(RwLock::new(key)).is_ok(),
        "product auth configured once"
    );
}
pub fn enabled() -> bool {
    PRODUCT_KEY.get().is_some()
}
pub fn current_key() -> Option<String> {
    PRODUCT_KEY
        .get()
        .and_then(|key| key.read().expect("product credential lock").clone())
}
fn publish_key(key: Option<String>) {
    if let Some(current) = PRODUCT_KEY.get() {
        *current.write().expect("product credential lock") = key;
    }
}

const ORIGIN: &str = "https://www.synderesis.eu";
fn origin() -> Result<String> {
    #[cfg(feature = "synderesis-test-endpoint")]
    if let Ok(value) = std::env::var("SYNDERESIS_CODE_TEST_AUTH_ORIGIN") {
        let url = reqwest::Url::parse(&value)?;
        if url.scheme() != "http"
            || url.host_str() != Some("127.0.0.1")
            || url.path() != "/"
            || url.query().is_some()
            || url.fragment().is_some()
            || !url.username().is_empty()
            || url.password().is_some()
        {
            bail!("Test authentication requires a loopback origin");
        }
        return Ok(value.trim_end_matches('/').to_owned());
    }
    Ok(ORIGIN.to_owned())
}
fn open_browser(url: &str) {
    #[cfg(feature = "synderesis-test-endpoint")]
    if std::env::var_os("SYNDERESIS_CODE_TEST_AUTH_ORIGIN").is_some() {
        return;
    }
    #[cfg(target_os = "macos")]
    let _ = std::process::Command::new("/usr/bin/open")
        .args(["-a", "Safari", url])
        .status();
    #[cfg(not(target_os = "macos"))]
    let _ = webbrowser::open(url);
}
fn credential() -> Result<keyring::Entry> {
    Ok(keyring::Entry::new("eu.synderesis.code", "account")?)
}
pub fn saved_key() -> Option<String> {
    credential().ok()?.get_password().ok()
}
pub fn logout() -> Result<()> {
    match credential()?.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => {}
        Err(_) => bail!("Could not remove the saved credential from your OS credential store"),
    }
    publish_key(None);
    Ok(())
}

pub async fn login(
    url_tx: Option<tokio::sync::oneshot::Sender<crate::AuthUrlInfo>>,
) -> Result<String> {
    // Initialize the credential entry; secure storage is confirmed when saving the key.
    let origin = origin()?;
    let entry = credential()?;
    let listener = TcpListener::bind("127.0.0.1:0").await?;
    let address = listener.local_addr()?;
    let redirect = format!("http://{address}/synderesis-code/callback");
    let verifier = URL_SAFE_NO_PAD.encode(rand::random::<[u8; 48]>());
    let state = URL_SAFE_NO_PAD.encode(rand::random::<[u8; 32]>());
    let challenge = URL_SAFE_NO_PAD.encode(Sha256::digest(verifier.as_bytes()));
    let mut url = reqwest::Url::parse(&format!("{origin}/account/"))?;
    url.query_pairs_mut().extend_pairs([
        ("extension_connect", "1"),
        ("client", "synderesis-code"),
        ("state", &state),
        ("code_challenge", &challenge),
        ("code_challenge_method", "S256"),
        ("redirect_uri", &redirect),
    ]);
    if let Some(tx) = url_tx {
        let _ = tx.send(crate::AuthUrlInfo {
            url: url.to_string(),
            mode: crate::AuthUrlMode::Command,
        });
    } else {
        eprintln!("Sign in to Synderesis and approve Synderesis Code in your browser.\n{url}");
    }
    open_browser(url.as_str());
    let deadline = Instant::now() + Duration::from_secs(300);
    loop {
        if Instant::now() > deadline {
            bail!("Sign-in expired. Run synderesis-code login again.");
        }
        let (mut socket, _) = tokio::time::timeout_at(deadline, listener.accept())
            .await
            .context("Sign-in expired. Run /login again.")??;
        let mut raw = [0u8; 8192];
        let count = match timeout(Duration::from_secs(2), socket.read(&mut raw)).await {
            Ok(Ok(n)) => n,
            _ => continue,
        };
        let request = String::from_utf8_lossy(&raw[..count]);
        let Some(target) = request
            .lines()
            .next()
            .and_then(|l| l.strip_prefix("GET "))
            .and_then(|l| l.strip_suffix(" HTTP/1.1"))
        else {
            continue;
        };
        let callback = match reqwest::Url::parse(&format!("http://{address}{target}")) {
            Ok(u) => u,
            Err(_) => continue,
        };
        let pairs: Vec<_> = callback.query_pairs().collect();
        let states: Vec<_> = pairs.iter().filter(|(k, _)| k == "state").collect();
        let codes: Vec<_> = pairs.iter().filter(|(k, _)| k == "code").collect();
        if callback.path() != "/synderesis-code/callback"
            || states.len() != 1
            || codes.len() != 1
            || states[0].1 != state
            || codes[0].1.len() > 256
            || codes[0].1.is_empty()
        {
            let _ = socket
                .write_all(
                    b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n",
                )
                .await;
            continue;
        }
        let client = reqwest::Client::builder()
            .redirect(reqwest::redirect::Policy::none())
            .timeout(Duration::from_secs(30))
            .build()?;
        let response = client.post(format!("{origin}/v1/auth/device/exchange")).json(&serde_json::json!({
            "code": codes[0].1, "state": state, "code_verifier": verifier, "redirect_uri": redirect
        })).send().await.context("Could not reach Synderesis sign-in")?;
        if !response.status().is_success() {
            bail!(
                "Synderesis could not connect this device (HTTP {}). Check your account and active-key limit.",
                response.status()
            );
        }
        let result: serde_json::Value =
            response.json().await.context("Invalid sign-in response")?;
        let key = result
            .get("api_key")
            .and_then(|v| v.as_str())
            .filter(|s| {
                s.starts_with("sk_live_") && s.len() < 512 && !s.chars().any(char::is_whitespace)
            })
            .context("Sign-in returned no valid device credential")?
            .to_owned();
        entry.set_password(&key).map_err(|_| anyhow::anyhow!("Could not save your credential securely. Revoke the newly issued key in Account and enable your OS credential store before signing in again."))?;
        let body =
            "Synderesis Code is connected. You can close this tab and return to your terminal.";
        publish_key(Some(key.clone()));
        let reply = format!(
            "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nCache-Control: no-store\r\nContent-Security-Policy: default-src 'none'\r\nConnection: close\r\nContent-Length: {}\r\n\r\n{}",
            body.len(),
            body
        );
        // No await after secure storage/publication: cancellation cannot report failure after committing login.
        let _ = socket.try_write(reply.as_bytes());
        return Ok(key);
    }
}
