# Stitch redesign integration

## Design source and technology decision

Source supplied by the user: `stitch_matchmind_ai_recruitment_intelligence.zip` (the project did not contain a file literally named `stitch-ui.zip`). All six `code.html` exports were extracted safely to `.cache/stitch_reference/` and inspected. They are static HTML using a Tailwind CDN/config, Google Fonts and Material Symbols; no React source, bundled JavaScript application, screenshots, raster artwork or separate assets were included in the ZIP. The export's links target illustrative paths and are not a working application.

Streamlit was retained to preserve Python integration, upload/session behavior, the embedding cache and one-command deployment. Native widgets supply the actual actions; HTML/CSS is used only for presentation and escaped evidence cards. External source text is escaped before any custom HTML insertion. There is no new REST API, Node build, React app or separate backend process.

## Design system retained

- Light surfaces `#F5FAFF`, `#EAF5FF`, white cards; teal primary `#00626E`; text `#0F1D26`; outlined 8/12px components; export dark tokens available through the sidebar toggle.
- Wix Madefor Display headings, Instrument Sans body, Spline Sans Mono IDs/scores, and Material Symbols icons. Font files and OFL/Apache notices are local. The download helper preserves the actual format/weight returned by the provider rather than disguising TTF as WOFF2.
- Left navigation, overview statistic cards, two-column role/service layout, batch ingestion panel, evidence cards, candidate profile, chat/tool trace and source/evaluation tables.
- Short surface/hover transitions, reduced-motion support, visible focus states, responsive stacking and explicit empty/disabled/error states.

## Screen mapping

| Export screen | Connected implementation |
| --- | --- |
| Overview dashboard | Actual indexed count/chunks, current single job description, mean of up to five last retrieved scores, honest assistant availability, session activity and working navigation actions |
| Candidate matching | Existing PDF parser and source selection, job input, O*NET requirements, MiniLM/FAISS index building, dynamic retrieval table and cited evidence cards |
| Semantic search | Same CandidateIndex search pipeline; raw cosine scores and a link from every result to its source profile |
| AI recruitment assistant | Existing ask_agent and actual SDK tool loop; prompt input, comparison using current result IDs, interview generation, recorded tool outputs; disabled without key/consent |
| Candidate intelligence | Actual document filename/ID, source provenance/page evidence, exact-phrase requirement review, navigation to the assistant |
| Data and evaluation | Actual sources/counts/license notices, O*NET manifest, read-only runtime configuration, human-label upload and existing evaluate() applied to the current index, downloadable measured results |

The exported design's fabricated profiles/experience, percentages, three-agent health/latency, pgvector/HNSW labels, alternate OpenAI embedding models, benchmark metrics and shortlist actions do not match the current backend. These were replaced with real values, omitted, or shown as unavailable. The live application has one OpenAI assistant with three tools and a MiniLM/FAISS index. It does not implement hybrid O*NET candidate scoring or infer skills/experience for profile decorations.

## Preserved functionality and session behavior

Core business modules, agent tool definitions and evaluation logic are unchanged byte-for-byte from the pre-redesign backup. All original tests are unchanged. Shared upload/JD/O*NET widgets remain mounted across routes; navigating does not remove upload bytes or rebuild the model/index. Source changes invalidate the index and dependent outputs. JD changes invalidate outputs but retain the candidate vectors. A failed rebuild clears a stale index; search errors clear stale results. Clear workspace resets session references and widget generations.

The frontend evaluation screen now invokes the already existing `scripts.evaluate_retrieval.evaluate()` against whichever authorized corpus is indexed. This preserves its reviewer/notes/ID checks, supports uploaded resumes, and requires no external dataset. It does not certify that labels were actually human-reviewed. No private judgments/results are automatically written to public assets.

## Backup and file changes

Original source, scripts, configuration and tests are preserved in `.cache/backups/before_stitch_redesign.zip`. No keys, uploaded resumes, model weights or private dataset records were included in that backup. To roll back, first stop Streamlit, extract the backup to a separate folder and restore its tracked project files. New presentation files can remain unused. Do not overwrite active private data when restoring.

Modified:

- `app.py`: six-screen controller and integration, persistent inputs, evidence/profile/chat/evaluation interactions, actual session status/activity.
- `.streamlit/config.toml`: supplied light palette and trusted local static serving; dark appearance uses supplied dark tokens in CSS.
- `README.md`: architecture, exact launch/setup commands, screen workflow and validation limitations.
- `VALIDATION.md`: final redesign execution record.

Added:

- `ui_theme.py`: escaped presentation helpers and design token injection.
- `static/stitch.css`: responsive Stitch theme, focus/disabled/loading/animation styling and dark tokens.
- `static/fonts/fonts.css`, typeface/icon font files and license notices: self-hosted fonts referenced by the supplied design.
- `scripts/fetch_ui_fonts.py`: optional maintenance fetcher for the exact font families and their licenses.
- `tests/test_stitch_ui.py`: new integration/regression coverage without changing original tests.
- `UI_REDESIGN.md`: this design mapping, implementation/verification record and limitations.

Unchanged business modules: `agent.py`, `matcher.py`, `parser.py`, `privacy.py`, `dataset_io.py`, `reports.py`, `scripts/evaluate_retrieval.py`, and the original test files. No new runtime dependencies were added.

## Verification status

The final full suite passed with **49 tests in 61.78 seconds**, including the final contrast adjustments. Existing 41 tests were preserved. New coverage includes all six routes, index reuse, profile/gap evidence, real retrieval context passed to a mocked assistant, interview routing, assistant error handling, evaluation against the active index, HTML escaping, stale-index invalidation and actual PDF fixture bytes through the upload/build/search path. Dependency consistency, Python compilation and the HTTP server smoke check also passed.

Actual browser verification compared the supplied overview HTML with the running app at `http://127.0.0.1:8502`. It found and corrected typography weights/formats, local font loading, crowded navigation/branding, action contrast, card positions and surfaces. The browser file-chooser automation expired; a second upload-button attempt exposed no usable picker. Therefore native browser PDF file selection is **not claimed as passed**. The standard Streamlit uploader remains, and an integration test feeds actual PDF fixture bytes through the same parser/build/search path. The explicit sample option is used separately for real-model browser verification.

Real-model browser verification completed: three explicitly synthetic sample PDFs produced three evidence vectors with 384 dimensions. The query `Python machine learning semantic search embeddings FAISS` returned Aurora 0.6326, Cedar 0.3524 and Brook 0.1047. The UI measured 88 ms for that warmed search; this single measurement is not a performance benchmark or relevance evaluation. Navigation retained the index/results. Candidate profiles displayed source pages, requirement comparison controls were present, the assistant correctly disabled chat/comparison/interview actions without a key, and Data & Evaluation showed the actual index, 1016 O*NET occupations and zero imported external resumes. No debug expressions or DeltaGenerator representations were observed in these inspected screens.

Light and dark appearance were visually inspected. Two dark-mode contrast issues in status messages and text inputs were corrected and rechecked. The saved light-theme result screenshot is `.cache/stitch_verification/semantic-search.jpg`. Temporary verification servers were stopped; the user's existing application server was not deliberately stopped. The standard launch command is unchanged. Automated test results do not constitute a live LLM or production deployment test.

## Remaining limitations

- A live OpenAI key/model/quota is still required to verify model-chosen tool calls, final answers and citation quality. UI tests use explicit doubles; they are not live AI results. Actual tool traces appear only after the existing agent returns, not token-by-token streaming.
- The real-world resume corpus remains unavailable without a reviewed local import. Uploads are a complete independent workflow; O*NET is occupational reference data, not a candidate corpus.
- Existing PDF/OCR, exact-phrase gap, heuristic privacy and raw-source export/provider-sharing limits remain. Use authorized, pre-anonymized documents; no automated hiring decisions are made.
- Streamlit widgets differ from the static Tailwind mock in browser-native upload controls, selection menus, dataframe rendering, route mechanics and chat placement. The design's unsupported switches/actions and fake data were not reproduced as functional product capabilities.
- Appearance uses CSS around Streamlit components. Future major Streamlit markup changes may require a visual regression pass. No pixel-diff percentage or unperformed responsiveness/production-deployment test is claimed.
