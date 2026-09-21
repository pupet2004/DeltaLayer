# Project

## Goal

Build a verifiable financial query and analysis system on top of an agentic data platform, with deterministic data access, evidence provenance, verification, and bounded report/chart/export output.

## Current Architecture

- Deterministic structured-data and SQL paths provide facts and calculations.
- Evidence and provenance remain explicit at the acquisition and verification boundaries.
- The v0.6-E path binds reports and charts to verified claims and preserves deterministic History replay.
- A separate v0.7 native Input -> Action -> Output runtime provides direct model-to-tool interaction with bounded execution.

## Current Stage

The v0.7 native-runtime and local-search baseline is committed at `29a17ed`,
anchored by `archive/v07-minimal-agent-runtime`. The new atomic `read_web_page`
tool is committed at `8bbc6a3` and passes 85 focused/old Research regression cases and standalone live
extraction. Independent SearXNG settings now retain Google CSE and 360search,
with 6-second engine budgets. Final search validation was 35/35 nonempty and
unchanged Qicetai standalone search was 5/5. Local DNS still returns synthetic
`198.18.0.0/15` mapping. Independent A/AAAA DoH validation now enables safe
hostname reads while preserving literal/private and redirect rejection.
All 183 focused/regression tests pass, including the original 85 unchanged.
The fresh-process real DeepSeek search/read/answer chain passed under Fake-IP.
The URL-safety fix, security tests, and acceptance documentation are committed
at `e15bb23` (`fix(v0.7): support safe webpage reads behind fake-ip proxies`).

## Recently Completed

- v0.6-E offline claim verification and report binding were recorded with explicit acceptance blockers.
- v0.7 native runtime consolidation was committed.
- The canonical development-directory boundary was documented.
- A local-first SearXNG HTTP provider adapter and independent deployment
  configuration were added to the existing WebResearchService.
- The independent native Windows SearXNG deployment is now installed and
  running at `http://127.0.0.1:8888`; JSON search and the v0.7 DeepSeek
  external-research smoke passed with the API Pool disabled.
- Added the atomic page reader using SafeFetcher and Trafilatura; 85 focused
  and regression cases pass. No agent loop, system prompt, or client changes.
- Live DeepSeek independently chose the reader after searches and continued
  searching after its structured URL rejection. Full records remain outside
  Git in the local Qicetai logs directory.
- After the local network change, unchanged current-source reading succeeded
  for example.com and the previously blocked Sina article (2771 characters).
- A fresh-process real DeepSeek retest made eight searches, received no URLs,
  and reported the limitation without calling the reader or inventing sources.
- A subsequent SearXNG reliability task changed only the independent search
  settings, removing failing/rate-limited default engines and Sogou's repeated
  parser failures. Final A-E queries were each 5/5 nonempty.
- The latest real DeepSeek retest made eight successful searches and chose
  two page reads autonomously; both reads were blocked by synthetic DNS.
- A subsequent Fake-IP fix added independent public DNS verification only at
  the URL safety boundary. Real DeepSeek then searched twice, autonomously
  read 10,353 characters from a returned government publication, and answered.
  No runtime, prompt, tool schema, VPN, or SearXNG settings changed.

## Known Constraints

- Current source, tests, Git history, and the actual workspace are authoritative over summaries or old task notes.
- History replay must reuse saved results rather than rerun model/tool/verification work.
- Report, Chart, and Export must not invent analysis outside verified evidence and claims.
- Provider failure, incomplete fixtures, and unverified integration paths must remain explicit.
- Hostname reads now require successful independent A/AAAA DNS verification;
  DoH failures fail closed. Literal Fake-IP addresses remain blocked.
- Original-hostname fetching preserves proxy routing but does not pin the
  ultimate socket address. It trusts VPN/proxy forwarding and does not claim
  protection against every connection-time DNS race or a malicious proxy.
- Google CSE can still rate-limit under sustained traffic; 360search kept the
  final tests nonempty. Strict news-only filtering is not available in the
  two-general-engine profile: SearXNG falls back to general search for NEWS.
- Historical all-empty searches reported upstream timeouts; the exact prior
  VPN/network cause cannot be proven from available records.
- API restart was blocked by execution policy during the latest observation;
  current-source tests and existing-process live results must be distinguished.

## Open Areas

- Harden and validate the native runtime boundary and recovery behavior.
- Complete provider, browser, data, and export integration checks where fixtures and credentials permit.
- Restart the resident API onto the reader changes when execution permits;
  the successful current-source acceptance used a fresh Python process.
