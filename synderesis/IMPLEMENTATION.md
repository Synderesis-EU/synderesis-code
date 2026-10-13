# Synderesis Code implementation status

Current verification: 2026-10-13.

The previous published release was verified on 2026-09-21. The dated preview incorporates Grok Build 1.0.45 from public upstream commit `2bdd1d6a6369de0e8c68132ea4539e9abd9e14a8`, rechecked on 2026-10-13. The previous upstream baseline was `4247f661689354b831191f11eeeac8424993fe3d` (1.0.38). Original licensing and third-party notices are retained; `SOURCE_REV` separately records upstream's internal monorepo revision.

The CLI uses the Synderesis API and website PKCE sign-in. Device credentials remain in the OS credential store; local state lives in ~/.synderesis-code. Upstream telemetry, updater and relay are disabled. External client plugins and MCP servers require explicit selection.

The backend provides /v1/code/models and /v1/code/responses, fixed Catholic policy, independent action review, and atomic prepaid credit/usage settlement. Generation and review are priced at 1.5 times provider inference cost. The verified route remains Neon GLM 5.3 Flash. No backend or model deployment was performed. See UPSTREAM.md for future model-maintenance and Neon/Vercel selection checks.

Previous release validation: 72 focused backend tests, 19 website tests, an optimized release build, the compiled CLI protocol fixture and production website-to-CLI sign-in passed on 2026-09-21.

## Verified upstream refresh

The isolated three-way update retains existing account, policy, tool, branding, permission and session behavior. Product endpoint defaults moved with upstream into xai-grok-config; Synderesis still owns their destination. The compiled model and API catalogue agree on 500,000 context tokens and 32,768 default output tokens. Information-only startup avoids reading the OS credential store. Saved theme aliases, product authentication labels, credential isolation, SYNDERESIS_CODE_SANDBOX, privacy/feedback routes, welcome artwork and the responsive working indicator are preserved.

The optimized Apple Silicon executable passed live file reading, code editing and execution against GLM. It also reused the saved OS credential without an environment key or a new login. The final extracted Mac executable matches the live-tested binary hash. A synthetic session saved by the previous 1.0.38 CLI resumes in 1.0.45 after its original file is removed.

Windows cold-start verification exposed upstream's unbounded PowerShell/WMI hardware-ID query blocking initialization under ARM emulation. The Windows-only repair reuses existing cached identifiers and otherwise generates and atomically caches UUIDv4. It passed fresh-state production startup without seeding an identifier or extending the timeout. Existing cached UUIDv5 identities are preserved. Non-Windows identity behavior is unchanged.

The exact Windows runtime passed model/file-tool calls, unavailable-catalogue startup, PKCE wrong-state rejection and cancellation, saved sign-in reuse, logout, account switching, menu/Quit and literal /login at 160x40, 100x32 and 70x22. Both Windows x64 and real Windows ARM also passed an interactive prompt → HTTP model request → actual file read → rendered answer → Quit. These coding and authentication checks use isolated synthetic fixtures; the normal executable's canonical production HTTPS route and startup were checked separately without customer credentials.

Windows evidence: [production build](https://github.com/Synderesis-EU/synderesis-code/actions/runs/38366862752), [protocol and login](https://github.com/Synderesis-EU/synderesis-code/actions/runs/38370199534), [full x64 and ARM verification](https://github.com/Synderesis-EU/synderesis-code/actions/runs/38372500693). All passed.

Additional checks: 44 regressions pass against production API source `7f9239a2c9b96c655d6052a7585617ca54029faf`; the model-catalogue fallback check, two credential-isolation checks, 37 theme tests, 24 settings tests, 69 welcome-layout tests and nine identifier-cache/permission regressions pass. The original API working files match the saved owner baseline.

## Packages

The dated preview packages are in the existing [team Drive folder](https://drive.google.com/drive/folders/1mZGAqiyR07ItDC7G7jZiX4IqWGcAe8TJ). Use their INSTALL.txt; public installers still provide the previous published release. Both packages are unsigned alpha builds; macOS is not notarized.

Mac executable source: `e9c8975af8d75595c9f6376e5b0b161b5eec3c47`.
Windows executable source: `1c7ccb765c592b9fccf1e71905a4ea8738fb9cde`.
The branch source archive includes the Windows-only repair and final verification tooling/documentation. Each package contains the build revision, upstream revision, license, third-party notices and internal checksums; the separate checksum sheet covers the final archives. The Windows handoff ZIP retains the exact CI production executable. Do not distribute a build with the synderesis-test-endpoint feature.
