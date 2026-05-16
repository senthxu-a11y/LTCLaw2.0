# M2B-1 Markdown Document Source Closeout

- Scope: add rule-only Markdown document source discovery, canonical facts generation, candidate doc refs, release doc grounding, and RAG citation path.
- Added project-local docs source config and discovery API.
- Cold-start now builds canonical doc facts from Markdown when docs source is configured.
- Release doc artifact now carries deterministic summary and chunks from canonical doc facts.
- RAG grounding now reads doc chunks from current release and can cite doc:BattleSystem.
- Validation target: focused Markdown lane tests plus existing M1 cold-start regression and smoke remain required.
