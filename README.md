# Synderesis Code

A Catholic coding assistant for your terminal, an Apache-2.0 fork of Grok Build. It can inspect a project, edit files, run commands with local permission controls, and work through multi-step coding tasks. This source incorporates upstream Grok Build 1.0.45 while retaining Synderesis sign-in, policies, local state, branding and permission controls.

**Alpha release.** Requires an active Synderesis subscription and prepaid credit.

The dated Grok Build 1.0.45 preview is installed from the supplied package; see `INSTALL.txt`. The public installers below still provide the previous published release.

## Install

Apple Silicon macOS:

```sh
curl -fsSL https://www.synderesis.eu/cli/install.sh | bash
```

Windows x64 or ARM64 (through x64 emulation), in Command Prompt:

```cmd
curl.exe -fsSL https://www.synderesis.eu/cli/install.cmd -o "%TEMP%\synderesis-install.cmd" && call "%TEMP%\synderesis-install.cmd"
```

Or in PowerShell:

```powershell
irm https://www.synderesis.eu/cli/install.ps1 | iex
```

The installers download a native executable and verify the release checksum. Python and Rust are not required. Installation uses your own account, without administrator access. The shell installer prints a PATH command if needed; the Windows installer adds its directory to your user PATH. The Command Prompt launcher also makes the command available in the current window. You can also download the packages and source from [GitHub Releases](https://github.com/Synderesis-EU/synderesis-code/releases).

## Sign in

Run `synderesis-code login`, or `/login` inside an open CLI session. Both commands use the same Synderesis sign-in flow. Your browser opens the normal Synderesis account website, where you sign in and return automatically to the CLI. A one-use PKCE exchange connects the CLI; its account key is saved in your operating system's credential store. You do not need a separate model-provider account.

Then run `synderesis-code` in your project, or `synderesis-code -p "Explain this project"` for a single terminal response. Use `--help` for local permissions and sandbox options. State is kept in `~/.synderesis-code` (override with `SYNDERESIS_CODE_HOME`). In unattended environments, inject `SYNDERESIS_API_KEY` at runtime using your secret manager. Never put a real key in a plaintext `.env` file.

On Windows, these commands run directly in Command Prompt as well as PowerShell. No WSL or separate shell is required. Run `cd` to your project directory, then `synderesis-code` to open the interactive terminal interface. Rerun the installer above to update an existing installation.

`synderesis-code logout` removes this device's locally saved key. Revoke the device key from [your account](https://www.synderesis.eu/account/) to invalidate all copies. Website sign-out does not revoke CLI access.

## Catholic conduct

Synderesis applies its Catholic system policy on the server and reviews each proposed answer and tool action before releasing it to the CLI. Requests to facilitate wrongdoing are refused with a permissible alternative. Ordinary service is available regardless of the user's identity or beliefs. Local instructions cannot replace the server policy. This is a fallible AI system; local permission prompts and human review remain necessary.

## Service and billing

The CLI connects to the Synderesis API. The underlying models may change without requiring a CLI update. Upstream credentials stay on the server. A paid Synderesis subscription and prepaid credit are required. The current route uses Neon GLM 5.3 Flash. Generation and the separate action review are both charged at 1.5 times provider inference cost, converted to EUR at the configured published exchange-rate snapshot. Cached input is priced separately; pricing evidence follows the actual server route. The server reserves a conservative maximum before dispatch and settles actual usage atomically.

Output is delivered after action review, so the initial response may take longer than an unreviewed live stream. This initial release supports text conversations and local function tools. It does not expose provider-hosted tools, image input or server-stored conversations. EU-only inference has not been verified.

The conversation context window is 500,000 tokens, shared by input and output. The CLI requests up to 32,768 output tokens per turn by default; the current API clamps larger explicit output caps to GLM's 131,000-token output limit, subject to the combined context limit. Automatic compaction leaves room for the next response and action review. The context counter measures conversation size, not your prepaid credit balance.

## Build

Use the repository's pinned Rust toolchain. On macOS or Linux, install `dotslash` for the upstream build tools, then:

```sh
cargo build -p xai-grok-pager-bin --release --locked
./target/release/synderesis-code --version
```

On Windows, install Protocol Buffers compiler 29.3 and set `PROTOC` to its executable, then build the native target:

```powershell
$env:PROTOC = 'C:\path\to\protoc.exe'
cargo build -p xai-grok-pager-bin --release --locked --target x86_64-pc-windows-msvc
```

Do not enable `synderesis-test-endpoint` in distributed builds. That feature exists solely for loopback integration tests. Normal builds use the canonical Synderesis API.

Native packages target Apple Silicon macOS and Windows x64; Windows ARM64 runs the x64 package under emulation. Both are unsigned; the macOS binary is not notarized. Other operating systems require building from source and have not yet been verified. Windows builds use the portability fixes recorded in the package's `BUILD-COMMIT.txt` and the matching Windows source archive.

## Attribution

Synderesis is an independent company. This project is not affiliated with or endorsed by xAI, Vercel, or the Catholic Church. Original Grok Build copyright, Apache-2.0 licensing and third-party notices are retained in `LICENSE` and `THIRD-PARTY-NOTICES`. Modified source files carry change notices. Upstream source revision: `2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8` (Grok Build 1.0.45); internal source revision is recorded separately in `SOURCE_REV`.
