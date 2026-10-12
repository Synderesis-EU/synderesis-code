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

Grok inference remains on the server, behind `synderesis-code`; customers do not
need an xAI credential. Always verify the latest released Grok model and current
gateway catalogues before releasing. Prefer Neon when it offers that current
model and branch access has been verified; otherwise use Vercel. On 2026-10-12,
the newest model is Grok 4.7 (`spacexai/grok-4.7` on Vercel), while Neon's public
catalogue offers only Grok 4.6. Do not restore an older upstream default or assume
a version-specific `-latest` alias advances across Grok generations.

The API repository's `python -m scripts.check_code_model_catalogue` verifies the
newest model by release date, provider token limits and committed cached/long
context pricing. It fails when a newer Grok appears, pricing changes, or Neon
adds the current model. Update and verify generation, action review and credit
settlement together; never automatically route to a new model using stale rates.
Provider selection stays separate from native source and installer versions.

Before distributing a native build, run the login/account-switch/logout,
HTTP/file-tool roundtrip, catalogue-outage and terminal layout checks. Compile
the distributable without `synderesis-test-endpoint`; loopback test executables
are verification tools only. Test the binary extracted from the final archive.
Include checksums, build provenance and the existing license/third-party notices.
