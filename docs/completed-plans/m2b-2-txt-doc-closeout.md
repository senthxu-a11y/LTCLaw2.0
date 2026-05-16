# M2B-2 TXT Document Closeout

- Scope: add rule-only TXT document discovery and deterministic paragraph-based indexing.
- Document discovery now marks configured .txt files as cold-start available.
- TXT document parsing uses the first non-empty line as title and chunks by paragraph/title blocks.
- Candidate, release, and RAG now accept doc:CharacterGrowth through the same map-governed document path.
- Validation target: focused TXT document tests plus existing M1 regression and smoke remain required.
