# Synderesis Code implementation status

Last verified: 2026-09-21.

Synderesis Code is an Apache-2.0 fork of Grok Build, revision 4247f661689354b831191f11eeeac8424993fe3d. Original licensing and third-party notices are retained.

The CLI uses the Synderesis API and website PKCE sign-in. Device credentials remain in the OS credential store; local state lives in ~/.synderesis-code. Upstream telemetry, updater and relay are disabled. External client plugins and MCP servers require explicit selection.

The backend provides /v1/code/models and /v1/code/responses, fixed Catholic policy, independent action review, and atomic prepaid credit/usage settlement. Generation and review are priced at provider inference cost divided by 0.70. Model selection is an operational implementation detail and is not specified in this documentation.

Validation: 72 focused backend tests, 19 website tests, an optimized release build, the compiled CLI protocol fixture and production website-to-CLI sign-in pass. The alpha macOS binary is not notarized. Do not distribute a build with the synderesis-test-endpoint feature.
