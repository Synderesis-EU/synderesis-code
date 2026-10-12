# Synderesis Code implementation status

Current verification: 2026-10-13 (package checks in progress).

The previous published release was verified on 2026-09-21.

Synderesis Code is an Apache-2.0 fork of Grok Build, revision 4247f661689354b831191f11eeeac8424993fe3d. Original licensing and third-party notices are retained.

The CLI uses the Synderesis API and website PKCE sign-in. Device credentials remain in the OS credential store; local state lives in ~/.synderesis-code. Upstream telemetry, updater and relay are disabled. External client plugins and MCP servers require explicit selection.

The backend provides /v1/code/models and /v1/code/responses, fixed Catholic policy, independent action review, and atomic prepaid credit/usage settlement. Generation and review are priced at 1.5 times provider inference cost. Model selection is an operational implementation detail and is not specified in this documentation.

Validation: 72 focused backend tests, 19 website tests, an optimized release build, the compiled CLI protocol fixture and production website-to-CLI sign-in pass. The alpha macOS binary is not notarized. Do not distribute a build with the synderesis-test-endpoint feature.

## Upstream refresh in progress — 2026-10-12

The isolated update incorporates public Grok Build 1.0.45 commit 2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8 using the earlier upstream baseline as the three-way merge base. Existing product account, policy, tool, branding and permission changes are retained. Product endpoint defaults moved with upstream into xai-grok-config; Synderesis still owns their destination. The compiled model and API catalogue now agree on 500,000 context tokens and 32,768 default output tokens. Information-only startup avoids reading the OS credential store. See UPSTREAM.md for the required latest-Grok and Neon/Vercel selection checks.

The dependency and source check passed; native executable and package verification are still in progress. Public installers are unchanged.

Current evidence: 44 regression checks pass against production API source
7f9239a2c9b96c655d6052a7585617ca54029faf. The existing Neon GLM 5.3 Flash
route passed a live native file-tool request; no backend/model deployment was
performed. Credential isolation and logout checks pass, including a real image
client that emits no HTTP request with a customer credential. The 37 theme and
24 settings checks pass, and product auth/theme/sandbox compatibility passes.
The prior CLI's synthetic saved session resumes in 1.0.45 after its original
file is removed. Loopback tool, unavailable-catalogue, login/account-switch/logout
and native /login checks pass at 70x22, 100x32 and 160x40. These are isolated
fixtures; the final optimized binaries and Drive readbacks are still pending.
