// Both terminal login and interactive /login use the same Synderesis PKCE flow.
pub use xai_grok_login::synderesis::saved_key;
pub fn login() -> anyhow::Result<String> {
    let key = tokio::runtime::Builder::new_current_thread()
        .enable_all()
        .build()?
        .block_on(xai_grok_login::synderesis::login(None))?;
    println!("Signed in to Synderesis Code.");
    Ok(key)
}
pub fn logout() -> anyhow::Result<()> {
    xai_grok_login::synderesis::logout()?;
    println!("Signed out of Synderesis Code on this device.");
    Ok(())
}
