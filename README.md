# Synderesis Code

A Catholic coding assistant for your terminal, an Apache-2.0 fork of Grok Build. It can inspect a project, edit files, run commands with local permission controls, and work through multi-step coding tasks.

**Alpha release.** Requires an active Synderesis subscription and prepaid credit.

## Sign in

Run `synderesis-code login`. Your browser opens the normal Synderesis account website, where you sign in and approve the device. A one-use PKCE exchange connects the CLI; its account key is saved in your operating system's credential store. You do not need a separate model-provider account.

Then run `synderesis-code` in your project, or `synderesis-code -p "Explain this project"` for a single terminal response. Use `--help` for local permissions and sandbox options. State is kept in `~/.synderesis-code` (override with `SYNDERESIS_CODE_HOME`). In unattended environments, inject `SYNDERESIS_API_KEY` at runtime using your secret manager. Never put a real key in a plaintext `.env` file.

`synderesis-code logout` removes this device's locally saved key. Revoke the device key from [your account](https://www.synderesis.eu/account/) to invalidate all copies. Website sign-out does not revoke CLI access.

## Catholic conduct

Synderesis applies its Catholic system policy on the server and reviews each proposed answer and tool action before releasing it to the CLI. Requests to facilitate wrongdoing are refused with a permissible alternative. Ordinary service is available regardless of the user's identity or beliefs. Local instructions cannot replace the server policy. This is a fallible AI system; local permission prompts and human review remain necessary.

## Service and billing

The CLI connects to the Synderesis API. The underlying models may change without requiring a CLI update. Upstream credentials stay on the server. A paid Synderesis subscription and prepaid credit are required. Generation and the separate action review are both charged at provider inference cost divided by 0.70, converted to EUR at the configured published exchange-rate snapshot. This is a 30% gross margin, not a 30% markup. Cached input is priced separately; long-context rates apply when applicable. The server reserves a conservative maximum before dispatch and settles actual usage atomically.

Output is delivered after action review, so the initial response may take longer than an unreviewed live stream. This initial release supports text conversations and local function tools. It does not expose provider-hosted tools, image input or server-stored conversations. EU-only inference has not been verified.

## Build

Use the repository's pinned Rust toolchain and install `dotslash` for the upstream build tools, then:

```sh
cargo build -p xai-grok-pager-bin --release --locked
./target/release/synderesis-code --version
```

Do not enable `synderesis-test-endpoint` in distributed builds. That feature exists solely for loopback integration tests. Normal builds use the canonical Synderesis API.

The present binary package targets Apple Silicon macOS. It is not notarized. Other operating systems require building from source and have not yet been verified.

## Attribution

Synderesis is an independent company. This project is not affiliated with or endorsed by xAI, Vercel, or the Catholic Church. Original Grok Build copyright, Apache-2.0 licensing and third-party notices are retained in `LICENSE` and `THIRD-PARTY-NOTICES`. Modified source files carry change notices. Upstream source revision: `4247f661689354b831191f11eeeac8424993fe3d`.
