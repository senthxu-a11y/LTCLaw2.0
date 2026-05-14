# H8 Legacy UI Route Test Matrix

## Goal

Confirm legacy surfaces are hidden, redirected, or explicitly labelled, and that the final smoke matrix covers the architecture boundary.

## Source Focus

- Console routes and navigation.
- Knowledge Base and Doc Library pages.
- SVN pages and redirect rules.
- Advanced/Admin Panel.
- Backend legacy KB/retrieval/SVN routes.
- Narrow backend and frontend helper tests.

## Checklist

- [ ] Knowledge Base is hidden from the main formal flow or clearly labelled legacy.
- [ ] Doc Library is not presented as formal RAG input.
- [ ] `/knowledge-base` is not the main formal knowledge entry.
- [ ] `/svn-sync` redirects or shows frozen legacy behavior.
- [ ] `/game/advanced/svn` redirects or shows frozen legacy behavior.
- [ ] Advanced page presents Admin Panel/local management, not SVN runtime control.
- [ ] Project settings wording treats old SVN fields as local project root/legacy compatibility.
- [ ] SVN watcher does not start.
- [ ] SVN monitoring start/stop/status return disabled/frozen state.
- [ ] SVN sync route does not run update/sync/revert/commit.
- [ ] Legacy retrieval is debug/migration-only.
- [ ] Permission tests cover planner/viewer/admin/source_writer boundaries.
- [ ] RAG tests cover map gate, focus refs, ignored/deprecated, and no KB fallback.
- [ ] Release tests cover strict/bootstrap/build/publish separation.
- [ ] Workbench Suggest tests cover validation and evidence refs.
- [ ] Source-write tests cover gate, allowlist, audit, and no auto rebuild.
- [ ] Model Router tests cover structured failure and model type routing.
- [ ] SVN freeze tests cover routes and service start.
- [ ] Citation deep-link smoke remains intact.

## Tests To Prefer

- Backend focused test suite for P0/P1 architecture boundaries.
- Frontend helper tests for admin panel, evidence display, and map review helpers.
- Console typecheck if current repository state permits it.

## Pass Standard

Legacy routes cannot mislead users into treating old KB/retrieval/SVN runtime as formal architecture.
