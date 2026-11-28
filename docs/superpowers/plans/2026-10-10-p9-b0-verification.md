# P9-B0 verification plan

Goal: verify existing backend on exact main SHA and publish evidence-only Draft PR.
Baseline: bce395a8c102491f4cf9ac26106b7263d08ad515.
Files: docs/qa/p9-b0-release-readiness.md, reviewer handoff guide, sanitized evidence.
Constraints: no production/frontend/migration/frozen edits; no human labels; no Stage 2; no merge.

- [x] Read PR16 audit and PR18 remediation; verify GitHub main and CI.
- [x] Create own worktree and audit/p9-b0-release-readiness branch.
- [x] Start own PostgreSQL17 with empty data directory, dedicated DB, loopback port and UTC.
- [x] Run six required files; save log/JUnit and independently inspect counts.
- [x] Run justified Matching scoring, Invitation lifecycle/concurrency, Assessment and FSP controls.
- [x] Verify frozen package read-only; on mismatch preserve files and diagnose canonical bytes.
- [x] Prepare blinded handoff; human status awaits actual reviewers; Stage 2 remains unstarted.
- [x] Write 12-section report and evidence; separate historical, CI and new local results.
- [ ] Recheck baseline, scope, diff; commit exact documentation paths; push and create Draft PR.
- [ ] Verify Draft/unmerged status and stop for Sava review.

Review focus: candidate input coherence; four consent/FSP combinations; scalar/relation response coherence;
pre-ACCEPTED contact and ownership gates; locale/newline prerequisites and unpublished banks.
Execution: agent performs audit inline; no broad rescan or duplicated full suite.

Snapshot: technical checks completed before publication. Final two publication steps are confirmed by the actual GitHub Draft PR receipt and final reply, not premarked before the commit.
