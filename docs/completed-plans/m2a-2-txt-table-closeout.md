# M2A-2 TXT Table Closeout

- Scope: add rule-only TXT table discovery and indexing for tab-separated table files.
- Discovery now marks configured .txt table files as cold-start available.
- TXT parser now ignores # and // comment lines, uses the first non-comment row as header, and keeps tab-separated data rows.
- Cold-start candidate path now accepts table:EnemyConfig from TXT input without changing document or script behavior.
- Validation target: focused TXT table tests plus M1 regression and smoke remain required.
