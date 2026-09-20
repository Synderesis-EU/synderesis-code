// Synderesis Code: website PKCE login with loopback callback and OS credential storage.
use anyhow::{Context, Result, bail};
use base64::{Engine as _, engine::general_purpose::URL_SAFE_NO_PAD};
use sha2::{Digest, Sha256};
use std::io::{Read, Write};
use std::net::TcpListener;
use std::time::{Duration, Instant};

const ORIGIN: &str = "https://www.synderesis.eu";
fn credential() -> Result<keyring::Entry> {
    Ok(keyring::Entry::new("eu.synderesis.code", "account")?)
}
pub fn saved_key() -> Option<String> { credential().ok()?.get_password().ok() }
pub fn logout() -> Result<()> {
    match credential()?.delete_credential() {
        Ok(()) | Err(keyring::Error::NoEntry) => {},
        Err(_) => bail!("Could not remove the saved credential from your OS credential store"),
    }
    println!("Signed out of Synderesis Code on this device. Revoke its key at {ORIGIN}/account/ to invalidate other copies.");
    Ok(())
}

pub fn login() -> Result<String> {
    // Initialize the credential entry; secure storage is confirmed when saving the key.
    let entry = credential()?;
    let listener = TcpListener::bind("127.0.0.1:0")?;
    listener.set_nonblocking(true)?;
    let address = listener.local_addr()?;
    let redirect = format!("http://{address}/synderesis-code/callback");
    let verifier = URL_SAFE_NO_PAD.encode(rand::random::<[u8; 48]>());
    let state = URL_SAFE_NO_PAD.encode(rand::random::<[u8; 32]>());
    let challenge = URL_SAFE_NO_PAD.encode(Sha256::digest(verifier.as_bytes()));
    let mut url = reqwest::Url::parse(&format!("{ORIGIN}/account/"))?;
    url.query_pairs_mut().extend_pairs([
        ("extension_connect", "1"), ("client", "synderesis-code"),
        ("state", &state), ("code_challenge", &challenge),
        ("code_challenge_method", "S256"), ("redirect_uri", &redirect),
    ]);
    println!("Sign in to Synderesis and approve Synderesis Code in your browser.\n{url}");
    #[cfg(target_os = "macos")]
    let _ = std::process::Command::new("/usr/bin/open").args(["-a", "Safari", url.as_str()]).status();
    #[cfg(not(target_os = "macos"))]
    let _ = webbrowser::open(url.as_str());
    let deadline = Instant::now() + Duration::from_secs(300);
    loop {
        if Instant::now() > deadline { bail!("Sign-in expired. Run synderesis-code login again."); }
        let (mut socket, _) = match listener.accept() {
            Ok(value) => value,
            Err(e) if e.kind() == std::io::ErrorKind::WouldBlock => { std::thread::sleep(Duration::from_millis(100)); continue; },
            Err(e) => return Err(e.into()),
        };
        socket.set_read_timeout(Some(Duration::from_secs(2)))?;
        let mut raw = [0u8; 8192];
        let count = match socket.read(&mut raw) { Ok(n) => n, Err(_) => continue };
        let request = String::from_utf8_lossy(&raw[..count]);
        let Some(target) = request.lines().next().and_then(|l| l.strip_prefix("GET ")).and_then(|l| l.strip_suffix(" HTTP/1.1")) else { continue; };
        let callback = match reqwest::Url::parse(&format!("http://{address}{target}")) { Ok(u) => u, Err(_) => continue };
        let pairs: Vec<_> = callback.query_pairs().collect();
        let states: Vec<_> = pairs.iter().filter(|(k,_)| k=="state").collect();
        let codes: Vec<_> = pairs.iter().filter(|(k,_)| k=="code").collect();
        if callback.path() != "/synderesis-code/callback" || states.len()!=1 || codes.len()!=1
            || states[0].1 != state || codes[0].1.len()>256 || codes[0].1.is_empty() {
            let _ = socket.write_all(b"HTTP/1.1 400 Bad Request\r\nConnection: close\r\nContent-Length: 0\r\n\r\n");
            continue;
        }
        let client = reqwest::blocking::Client::builder().redirect(reqwest::redirect::Policy::none()).timeout(Duration::from_secs(30)).build()?;
        let response = client.post(format!("{ORIGIN}/v1/auth/device/exchange")).json(&serde_json::json!({
            "code": codes[0].1, "state": state, "code_verifier": verifier, "redirect_uri": redirect
        })).send().context("Could not reach Synderesis sign-in")?;
        if !response.status().is_success() { bail!("Synderesis could not connect this device (HTTP {}). Check your account and active-key limit.", response.status()); }
        let result: serde_json::Value = response.json().context("Invalid sign-in response")?;
        let key = result.get("api_key").and_then(|v| v.as_str()).filter(|s| s.starts_with("sk_live_") && s.len()<512).context("Sign-in returned no valid device credential")?.to_owned();
        entry.set_password(&key).map_err(|_| anyhow::anyhow!("Could not save your credential securely. Revoke the newly issued key in Account and enable your OS credential store before signing in again."))?;
        let body = "Synderesis Code is connected. You can close this tab and return to your terminal.";
        let _ = write!(socket, "HTTP/1.1 200 OK\r\nContent-Type: text/plain; charset=utf-8\r\nCache-Control: no-store\r\nContent-Security-Policy: default-src 'none'\r\nConnection: close\r\nContent-Length: {}\r\n\r\n{}", body.len(), body);
        println!("Signed in to Synderesis Code.");
        return Ok(key);
    }
}
