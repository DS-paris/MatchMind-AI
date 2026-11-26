# Validation record

## Alternative dataset audit — 24 November 2026

- Bounded investigation of four alternatives completed; details in `data/ALTERNATIVE_DATASET_AUDIT.md`. ResumeBench was not retried.
- Direct unauthenticated range requests for datasetmaster JSONL and TechWolf CSV each returned **HTTP 206** and 1,024 bytes. Access was verified, but authenticity/provenance requirements were not met: the former mixes real/synthetic records without a documented trustworthy source discriminator; the latter's primary paper documents GPT-3.5 rewriting of experience text.
- MikePfunk28 metadata reports gated access; OpenResume's official Zenodo record is restricted. No account terms accepted, no access requests submitted, and no gates bypassed.
- Replacement records imported/indexed: **0**. No raw candidate text persisted. No code was changed to accept an unverified source, and the existing PDF upload workflow is preserved.
- Full existing suite: **41 passed in 32.48 seconds** on the unchanged application code. Source access checks and tests required reviewed elevated network/tool permissions.
- Retrieval with imported alternative records and real-world quality evaluation: **not performed**, because no suitable replacement was verified. Existing fixture tests must not be interpreted as such an evaluation.

## Real-world dataset integration update — 23 November 2026

- Full suite: **41 passed in 7.44 seconds**. Includes all existing tests, both sidebar status regression paths, source switching/invalidation, gated-dataset unavailable behavior, O*NET requirements selection, source-specific ingestion, privacy minimization, synthetic exclusion, deduplication, review-marker integrity, pinned revision validation, FAISS indexing of ingested contract fixtures, official O*NET manifest validation, and evaluation-metric calculation/rejection tests.
- `python scripts/smoke_server.py`: **passed** after the integration; temporary server stopped.
- `python scripts/smoke_retrieval.py`: **passed** with actual MiniLM/FAISS and existing explicitly synthetic fixtures. Aurora 0.6326, Cedar 0.3524, Brook 0.1047. This is a regression check, not real-world evaluation.
- `python -m pip check`: no broken requirements. Source compilation passed.
- O*NET official downloads/preprocessing: **passed**. 1,016 occupations; 31,821 software-skill source rows; 18,838 task source rows. The manifest in `data/onet_occupations.json` records exact URLs, SHA-256 hashes, byte/row counts, date, version, transformations and attribution.
- ResumeBench public metadata: accessible; inspected pinned revision `db07f5ad52c061784f5728a4ded1e356e4b59278`, publisher license CC BY 4.0. Actual `test.jsonl` request: **HTTP 401**, restricted access/authentication required. Real resumes downloaded/indexed: **0**. The authenticated importer is implemented and tested with contract fixtures; its successful live import path could not be validated without publisher-granted access. No access gate was bypassed.
- **No real-world retrieval evaluation performed.** There are no verified downloaded real records or human-reviewed job–resume pairs. The evaluation runner is implemented but no real-world metrics are claimed. See `evaluation/README.md` for the labeling protocol and exact limitation.
- Live OpenAI generation and browser visual inspection remain unverified. AppTest exercised UI behavior using injected test encoders; real MiniLM ran separately in the smoke test. No dependencies were added for this update.
- The working directory is not a Git repository, so `git status` could not run. Ignore rules are supplied, including `data/private/`, tokens and private evaluation output; no personal resume dataset was downloaded or included.

# MatchMind validation record

## Public-deployment preparation — 25 November 2026

Architecture remains one Streamlit/Python process with the existing six screens and local MiniLM/FAISS pipeline. No app, repository, image or secret was published. Git and Docker were not on PATH; repository-history inspection and a local Docker build could not be performed. A pre-change source/config backup is `.cache/backups/before_deployment_prep.zip`.

Deployment changes include Linux CPU-only Torch selection, Python 3.12 Docker/CI targets, pinned primary runtime libraries, separate development requirements, shared/single-flight CPU model loading, embedding batches of 16, a 2,000-chunk bound and one-at-a-time index builds. Public batches are limited to five documents, 20 MB total and 60,000 extracted characters. Default public AI access fails closed without a 24+ character private access code, even with a key; consent is also required. Persistent single-host quotas and concurrency checks are enforced before generation. SDK output/context bounds were added; tracing remains disabled. These are single-host request controls, not a certified billing limit or distributed access-control system.

The final full suite passed **56 tests in 40.52 seconds**. Dependency consistency and Python compilation passed. A temporary Streamlit HTTP health check passed and stopped its own server. Coverage includes wrong/correct public access codes and quota enforcement before the mocked provider, concurrent atomic/global quotas, cooldowns, counter persistence, access defaults, release exclusions and chunk rejection before model loading. Original semantic/PDF/tool/UI coverage remains; existing mocked assistant UI tests explicitly select trusted local mode and isolated counter files.

Real MiniLM/FAISS profiling passed on Windows / Python 3.14.7: three synthetic sample PDFs, three vectors, 384 dimensions, **709.9 MiB peak process working set**, 37.24 seconds elapsed including imports/model loading. Query `Python machine learning semantic search embeddings FAISS` returned Aurora 0.6326, Cedar 0.3524 and Brook 0.1047. These are measured retrieval cosines, not real-world relevance evaluation results. The profiler includes Streamlit and agent SDK imports but is not a full multi-session browser/host load test. The first probe passed its retrieval assertions but failed to read memory because a Windows ctypes function lacked argument types; the signature was corrected and the rerun completed successfully. Raw profile: ignored `.cache/deployment-profile.json`.

The allowlisted release bundle was created with 65 files (about 1.65 MB compressed), and ZIP inventory assertions confirmed excluded secret/private/archive/CSV/Word/cache paths were absent. It is not published. The release is regenerated after final documentation updates; `.cache/release/manifest.json` contains actual source hashes for review.

Linux installation, Docker build, free-host RAM fit, actual hosted native uploads/downloads, concurrent traffic and live provider-generated answers are pending manual/CI verification. There is no configured OpenAI key and no live-LLM claim. GitHub Actions is supplied to run Linux/Python 3.12 tests, real MiniLM/FAISS profiling and a 4 GB container check after the user approves publication. No measured production metrics or real dataset records are fabricated.

The allowlist release script excludes credentials, private data, archives, CSV exports, model caches and the historical Word report; it checks common credential patterns before packaging. This is narrower than uploading the workspace, but still requires human source/content review and cannot prove absence of every secret or PII. See `DEPLOYMENT.md` for exact publication/secrets steps and final hosted acceptance checks.

## Stitch redesign verification — 24 November 2026

- Final complete suite: **49 passed in 61.78 seconds**, after the final presentation-only contrast adjustments. All original 41 tests remain unchanged. Added integration coverage for six-screen navigation, retained index/results, candidate profiles and phrase evidence, mocked assistant wiring/errors/interviews, current-corpus evaluation, HTML escaping, failed rebuilds and actual PDF upload bytes. Test doubles are explicitly used for unit embeddings and live-provider boundaries.
- Dependency check, Python compilation and HTTP Streamlit smoke test passed.
- Browser compared supplied Stitch HTML with the redesigned app. Actual MiniLM/FAISS indexing completed with three explicitly synthetic sample PDFs, three chunks, 384 dimensions. Actual query `Python machine learning semantic search embeddings FAISS` returned Aurora 0.6326, Cedar 0.3524, Brook 0.1047 with cited source evidence. One warmed retrieval measured 88 ms; no benchmark claim is made.
- Verified navigation retained the live index/results; candidate profile source text, requirement-comparison controls, actual dataset/index statistics and disabled no-key assistant actions rendered correctly. Inspected light/dark modes and corrected/rechecked status/input contrast. No raw Python expressions or DeltaGenerator output appeared in inspected screens.
- Native browser file-picker automation expired and a second button attempt did not expose a usable picker. Native file selection/download completion remain manual checks; the actual PDF-byte parser/build/search integration passes.
- Live model-selected OpenAI tool calls, final answers and citation quality remain unverified without a valid key/quota/consent. Existing SDK tool handlers are tested; mocked chat tests are not live LLM tests. External resume corpus remains unavailable; no imported real records or evaluation metrics are fabricated.
- Screenshot: `.cache/stitch_verification/semantic-search.jpg`. Original source backup: `.cache/backups/before_stitch_redesign.zip`. Business modules and original tests were checked against that backup and remained unchanged. No new runtime dependencies. Temporary preview/reference servers were stopped.

The historical original MVP record below describes the earlier build; its statement that browser inspection was not performed is superseded by the redesign verification above.

Executed on Windows with Python 3.14.7, 23 November 2026.

## Passed

- Dependency installation in `.venv`; `python -m pip check`: no broken requirements.
- `python -m pytest -q`: **26 passed** (8.51 seconds).
- Tests cover PDF extraction/citations, invalid/empty/encrypted PDFs, size limits, cosine ranking, normalization, deduplication, query validation, sensitive-field filtering, all three real SDK tool invocation handlers, missing keys, runner wiring with a mocked LLM boundary, report references, and Streamlit no-key/demo/search/clear flows.
- `python scripts/smoke_server.py`: Streamlit HTTP health check passed; temporary server stopped.
- Three supplied synthetic PDFs generated and successfully parsed with extractable text.
- Python source compilation passed.

The unit suite injects a deterministic embedding test double and mocks the LLM runner boundary where appropriate. Passing these tests does not imply a live OpenAI response was tested.

## Integration verification

- Real MiniLM download/embedding retrieval: **passed** using the actual `all-MiniLM-L6-v2` weights, generated sample PDFs, normalized embeddings, and FAISS. For `Python machine learning semantic search embeddings FAISS`, the results were Aurora **0.6326**, Cedar **0.3524**, Brook **0.1047**. These are measured cosine retrieval similarities, not hardcoded values or suitability scores. The script asserted all three candidates were returned, scores were in range, and the semantic-search project was retrieved first.
- Live OpenAI generation: **not tested**. A valid key, available model, quota and consent are needed. Verify autonomous tool selection, follow-up questions, comparisons, skill-gap wording, and interview questions against source pages.
- Browser visual inspection and deployment: **not performed**. AppTest exercised UI behavior; HTTP smoke verified server startup. Review layout in a browser and verify download behavior before recording a portfolio demo.

## Environment notes

Sandbox restrictions blocked package/model network access and localhost sockets. Dependency installation, the complete SDK/UI test suite, and HTTP health check were run with reviewed elevated tool permissions. The initial incomplete-install attempts and test-harness compatibility errors were corrected before the passing run.

Installed key versions: Streamlit 1.67.0, openai-agents 0.25.0, sentence-transformers 5.7.0, faiss-cpu 1.16.0, PyMuPDF 1.28.2, NumPy 2.5.5, PyTorch 2.15.0, pytest 9.2.0.

The first scientific-stack import took several minutes in this environment before the model download began. Periodic diagnostic traces showed progress through SciPy/scikit-learn imports, then Hugging Face downloading; the final integration check exited successfully. The weights are now cached under `.cache/models/`. Windows emitted a nonfatal symlink-cache warning; caching and retrieval still completed.
