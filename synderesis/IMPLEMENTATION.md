# Synderesis Code implementation status

Last verified: 2026-09-21. Local alpha candidate; not published or deployed.

Upstream: xai-org/grok-build, Apache-2.0, revision 4247f661689354b831191f11eeeac8424993fe3d. License and third-party notices retained. The Rust binary is named synderesis-code and uses the Synderesis terminal wordmark and palette. Website PKCE login stores the device key in the OS credential store; separate state lives in ~/.synderesis-code. Upstream telemetry, updater and relay are disabled.

The deployment candidate is isolated at the separate backend release worktree on current production base 46d67208435a7eb8c0d5ec6eb03d4be1fda2ede4. It preserves newer desktop pairing and gateway fields. Routes /v1/code/models and /v1/code/responses implement text/function Responses conversion, fixed Catholic policy, independent no-tool action review, and atomic prepaid credit/usage settlement. Migration 0015 is not applied in production. SYNDERESIS_CODE_ENABLED defaults off.

Upstream: Vercel AI Gateway spacexai/grok-4.6, with the existing gateway key or project OIDC. User funded the gateway; live synthetic tool invocation, tool-result continuation, ordinary action review and credential-theft rejection now pass. No new provider credential is needed. Generation plus review cost / 0.70 gives a 30% inference gross margin. Gateway rates are $2/M input, $0.50/M cached input, $6/M output, doubled from 200001 input tokens. The deployment document records the ECB 2026-09-18 EUR/USD snapshot. EU-only inference is not verified.

Validation: 72 focused backend/protocol/auth/billing tests pass, including temporary real PostgreSQL transactions. Compiled CLI/HTTP fixture exposed a missing Responses output_tokens_details field; it is fixed and regression-covered. Real interactive website login against the new deployed API remains a release gate. The local alpha is not notarized.

Publication requires the user's exact-preview approval under AGENTS.md. Never deploy the unrelated dirty main checkout or distribute a build with the synderesis-test-endpoint feature.
