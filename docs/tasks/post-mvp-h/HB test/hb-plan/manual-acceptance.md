# Manual Acceptance

Manual checks are not a substitute for P0 tests, but they verify the user-facing architecture closure.

## Flow 1: Admin Knowledge Chain

- [ ] Use admin agent to open Admin Panel.
- [ ] Confirm current release / previous release / formal map / RAG status are visible.
- [ ] Trigger candidate-from-source.
- [ ] Inspect diff review.
- [ ] Save Formal Map.
- [ ] Build Release and confirm current release does not change.
- [ ] Publish Current and confirm current release updates.
- [ ] Run formal RAG query and confirm citations come from release artifacts.

## Flow 2: Planner Workbench

- [ ] Use planner agent to open Workbench.
- [ ] Generate AI suggestion.
- [ ] Confirm `formal_context_status` is visible.
- [ ] Confirm Draft Overlay is marked non-formal.
- [ ] Attempt source-write and confirm 403.
- [ ] Switch to source_writer agent.
- [ ] Write back `update_cell`.
- [ ] Confirm SVN Update warning appears before write.
- [ ] Confirm audit is generated after write.
- [ ] Confirm current release is unchanged.

## Flow 3: Legacy KB

- [ ] Open Legacy Knowledge Base.
- [ ] Confirm page states it does not participate in formal Release / RAG / Chat / Workbench Suggest.
- [ ] Run RAG query.
- [ ] Confirm citation source is not KB.
- [ ] Build Release and confirm KB is not read.

## Receipt Requirements

Report browser/environment used, exact agent roles used, screenshots if available, and any manual-only residual risk.
