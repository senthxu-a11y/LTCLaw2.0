# M2B-3 DOCX Document Closeout

- Scope: add rule-only DOCX document discovery and minimal paragraph-only parsing.
- Document discovery now marks configured .docx files as cold-start available.
- DOCX parsing reads only body paragraphs, uses the first readable paragraph as title, and ignores tables, images, comments, revisions, and embedded objects.
- Candidate, release, and RAG now accept doc:EconomyLoop through the same map-governed document path.
- Validation target: focused DOCX document tests plus existing M1 regression and smoke remain required.
