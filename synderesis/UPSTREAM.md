# Upstream and Grok model maintenance

The 2026-10-12 update incorporates Grok Build 1.0.45 from public commit
`2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8`. The previous baseline was
`4247f661689354b831191f11eeeac8424993fe3d` (1.0.38). `SOURCE_REV` separately
records the internal monorepo revision supplied by upstream.

Preserve the fork's changes when updating: Synderesis website PKCE login,
OS credential storage and account switching, private state, canonical API
endpoint, server conduct policy and action review, local permission controls,
disabled upstream telemetry/updater/relay, explicit external plugin selection,
branding, welcome artwork and width-aware loader, and Windows portability.
Use a three-way update against the recorded upstream baseline in an isolated
checkout. Never replace the entire fork with an upstream snapshot.

Inference remains on the server, behind `synderesis-code`; customers do not
need a model-provider credential. The owner confirmed on 2026-10-12 that the
current Neon GLM 5.3 Flash route should continue if verified working. Updating
the native Grok Build source must not reset that server route to upstream's
baked-in Grok defaults.

For a future requested Grok route, verify the latest released Grok and live
provider catalogues, including pricing and capabilities. Prefer Neon when it
offers that current model with verified branch access; otherwise use Vercel.
The 2026-10-12 catalogues list Grok 4.7 on Vercel and only Grok 4.6 on Neon.
Choose by release date rather than numeric version: Grok 4.20 predates 4.7.
Never assume a version-specific `-latest` alias advances across generations,
and never automatically route to a new model using stale billing rates.

Before distributing a native build, run the login/account-switch/logout,
HTTP/file-tool roundtrip, catalogue-outage and terminal layout checks. Compile
the distributable without `synderesis-test-endpoint`; loopback test executables
are verification tools only. Test the binary extracted from the final archive.
Include checksums, build provenance and the existing license/third-party notices.
