# Real-world retrieval evaluation status

**Not performed:** verified real resume records could not be downloaded (ResumeBench HTTP 401). No real-world relevance metrics or manually reviewed pairs are claimed. Existing synthetic smoke-test scores and deterministic unit-test metrics are engineering checks, not real-world evaluations.

Once permitted real records are available and privacy-reviewed, create a small local JSON array under `data/private/judgments.json`. Review each job/query against **all candidates in the evaluation corpus**, assign relevant candidate IDs based on documented experience, and record your identity/role and evidence notes. Include at least several diverse queries, positive and negative pairs, and ambiguous cases. Freeze labels before viewing retrieval scores. Use actual requirements, e.g. a selected O*NET reference with its SOC code noted; do not represent an occupational reference as an employer posting.

Each item must have these fields (this is a schema, not a labeled example):

- `query`: original job requirements or occupational reference text
- `relevant_candidate_ids`: nonempty array of reviewed candidate IDs from the exact corpus
- `reviewer`: human reviewer identifier
- `evidence_notes`: source citations and rationale for relevant/nonrelevant judgments

Run `python scripts/evaluate_retrieval.py data/private/judgments.json --k 3`.
The runner uses real MiniLM embeddings, the existing FAISS pipeline, and reports mean recall@k and MRR@k over submitted labels, rankings, corpus IDs, source revision and judgment-file checksum. It rejects missing review metadata and unknown candidate IDs. Queries with no relevant candidates are outside these metrics; assess those separately rather than supplying invented positives. The code cannot verify that a reviewer truly performed the review.

Results are written to ignored `evaluation/local_results.json`; they include private source evidence. Do not commit them. Share only appropriately reviewed aggregate metrics with dataset revision, sample size, annotation protocol and limitations. A tiny subjective set cannot establish overall quality, hiring suitability, or fairness.
