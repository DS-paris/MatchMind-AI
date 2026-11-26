# Deploy MatchMind AI

Prepared 25 November 2026. Nothing has been published, no repository has been created, and no public URL is claimed. Publication needs your approval and your hosting account. Follow the steps below when ready.

## Platform decision

**Try Streamlit Community Cloud first:** it hosts this exact Python/Streamlit architecture, supplies HTTPS and secret storage, and has a free service. No FastAPI, Node build or separate backend is needed. Use **Python 3.12**. Its resource allowance is limited and can change; fitting this model is a deployment acceptance check, not a promise. CPU-only Torch, lazy/shared MiniLM loading, batch size 16 and public corpus limits reduce the footprint. If it is killed by the host, use the Docker fallback with at least 4 GB RAM; start with one replica and check measured memory before inviting traffic.

**Hugging Face Docker Spaces is the memory-friendly alternative:** the documented CPU Basic allocation is 2 vCPU / 16 GB, without hourly hardware charges, but current documentation says creating new compute Spaces requires a paid plan. Do not assume it is free for a new account. Verify your account's entitlement/pricing before accepting any charge. A Docker-capable host with 4–8 GB RAM is another option; no paid service has been ordered here.

Official references checked: [Streamlit Community Cloud](https://docs.streamlit.io/deploy/streamlit-community-cloud), [resource limits](https://docs.streamlit.io/knowledge-base/deploy/resource-limits), [secrets](https://docs.streamlit.io/deploy/streamlit-community-cloud/deploy-your-app/secrets-management), [HF hardware/access](https://huggingface.co/docs/hub/en/spaces-overview), [Docker Spaces](https://huggingface.co/docs/hub/en/spaces-sdks-docker), [CPU PyTorch wheels](https://download.pytorch.org/whl/cpu/torch/).

## 1. Prepare a clean source directory locally

The current workspace contains raw archives and a dataset export. **Do not upload the entire directory** or run a blind `git add .` there. The packager uses an explicit source allowlist, checks symlinks and common credential patterns, and includes only the three known synthetic PDFs and occupational reference JSON. It is not a certified secret/PII scanner: review its manifest and the source before publication.

From this project's root in PowerShell:

```powershell
.\.venv\Scripts\python scripts\prepare_release.py
Expand-Archive -LiteralPath .cache\release\MatchMind-deploy.zip -DestinationPath ..\MatchMind-public
Set-Location ..\MatchMind-public
```

Choose a new, empty destination. Review `.cache/release/manifest.json` in the original workspace. The generated ZIP and manifest stay ignored locally. Raw archives, CSVs, private resumes, model weights, evaluation judgments, `.env`, real `secrets.toml` and the historical Word audit are excluded. Only `data/onet_occupations.json` and source/license documentation are public dataset assets.

Git and Docker were not available on PATH in the preparation environment. If you use Git CLI, install it from [git-scm.com](https://git-scm.com/downloads), reopen the terminal, and run the following **in the clean extracted directory only**, after deciding to publish:

```powershell
git init -b main
git add .
git status --short
git diff --cached --stat
git diff --cached
git commit -m "Prepare MatchMind AI portfolio deployment"
```

Review filenames and diffs locally; do not paste real credentials into chat. A `.gitignore` does not remove secrets already committed. If a key was ever committed, revoke/rotate it and clean repository history before publishing.

## 2. Create the GitHub repository (manual publication step)

1. Sign into GitHub and choose **New repository**. Name it `matchmind-ai`. Choose public only after reviewing the release; a private repository can also be connected to Streamlit with the relevant GitHub permissions.
2. Do not initialize another README if using the Git commands above.
3. Copy GitHub's actual HTTPS repository URL, then run:

```powershell
git remote add origin https://github.com/YOUR_USERNAME/matchmind-ai.git
git push -u origin main
```

Replace `YOUR_USERNAME`. These commands publish code; they have **not** been executed. Alternatively upload the extracted, reviewed source through GitHub's UI, including `.streamlit`, `.github` and `.gitignore`.

4. Inspect the repository online. Verify no `.env`, private data, raw ZIP/CSV, secrets or model cache appears. In **Actions**, let `Validate deployment` run. It installs on Linux/Python 3.12, runs tests, profiles the real model and builds/tests Docker; it never publishes an image or invokes OpenAI. These Linux jobs are configured but have not yet run on GitHub. Resolve any failure before claiming deployment readiness. The profile artifact reports actual peak memory, not a prefilled benchmark.

## 3. Deploy the free-first Streamlit app

1. Sign into [Streamlit Community Cloud](https://share.streamlit.io) using your GitHub account. Review the requested repository permissions.
2. Select **Create app**, the reviewed repository, branch `main`, and entrypoint **`app.py`**.
3. Choose an available `*.streamlit.app` subdomain. Select **Python 3.12** under advanced settings.
4. Begin with no OpenAI key. Set this in the deployment secret editor (not GitHub source):

```toml
MATCHMIND_PUBLIC = "true"
```

5. Deploy when you approve publication. Wait for dependency installation and first MiniLM download. No gated model or HF token is needed for `all-MiniLM-L6-v2`. The first load can be slow; restarts/hibernation can cause another cold start. Do not disable CORS or XSRF protection to work around deployment errors.
6. Run the acceptance checks below, inspect server resource logs, and copy the **actual live HTTPS URL** into your internship application only after those pass. No live URL exists from this preparation alone.

Community Cloud reads `requirements.txt` and `.streamlit/config.toml`. CPU Torch is explicitly selected for Linux; pytest is separate in `requirements-dev.txt`. Top-level runtime versions are pinned except dotenv, but transitive dependencies are not a fully hashed lock. The Linux CI/build must verify their combined compatibility. No OS package file is needed for the declared binary-wheel stack.

Local final checks: **56 tests passed in 40.52 seconds**, dependency consistency and server health passed, and real MiniLM/FAISS retrieval measured **709.9 MiB peak process memory** on Windows / Python 3.14.7 for three synthetic fixtures. The 37.24-second run includes imports/model loading. This is a small local workload, not Linux host usage, a concurrent-load benchmark or a guarantee that the free tier fits. The actual public deployment remains untested until you complete these steps.

## 4. Enable invited AI access safely (optional)

Search, uploads, profiles, lexical gap review, O*NET and report generation work without an OpenAI key or an external resume corpus. The existing SDK agent needs a paid API key/model quota for generated answers, comparisons and interview questions.

1. Create a separate project-scoped OpenAI API key, with the minimum permissions needed for Responses API generation. Configure provider project limits/alerts and a low funded balance appropriate to your demo. Provider budget alerts may be soft limits; do not assume they enforce a hard dollar cutoff.
2. Generate a random access code locally. For example:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

3. In Streamlit's **server-side secret settings**, add the real values manually:

```toml
MATCHMIND_PUBLIC = "true"
OPENAI_API_KEY = "REPLACE_PRIVATELY"
OPENAI_MODEL = "gpt-4.1-mini"
MATCHMIND_AGENT_ACCESS_CODE = "REPLACE_WITH_RANDOM_32_PLUS_CHARACTER_CODE"
```

The model must be available to your API project. Share the access code privately with invited interviewers, never in the public README or URL. Do not expose the OpenAI key to reviewers. Leave the key absent if you want search-only access. `MATCHMIND_PUBLIC=false` is exclusively for trusted local use; never set it on the hosted app.

Controls in `deployment.py`, `app.py` and `agent.py`:

- Public AI requires a server secret at least 24 characters long, constant-time access-code checking and explicit sharing consent. It is checked again at execution, not just through button state.
- One active assistant request per server process; 30 attempts per rolling 24 hours globally, five per session/hour, 15 seconds between a session's attempts. Failed attempts consume allowance. SQLite stores only random session IDs and timestamps under ignored `.cache/`.
- Clearing a workspace/new browser can reset the session identity, but cannot bypass the host-wide allowance. Rotating/recreating the access code does not itself reset persisted counts. Restarting with the same disk retains counts; redeploy/ephemeral-disk loss resets them. Multiple replicas with separate disks would each have their own allowance. This is for **one replica**, not a distributed billing control.
- SDK maximum eight turns, 1,200 output tokens per model turn, 120-second outer timeout, 60-second client timeout and one retry. Initial context is capped at 100,000 characters. Tool-returned evidence can still be large. These controls bound requests, not exact dollar cost or total provider input tokens.
- Public indexing accepts at most five documents, 20 MB total upload bytes, 60,000 extracted characters; each PDF keeps existing 10 MB / 30-page bounds. All indexes cap at 2,000 chunks. One index build at a time, CPU inference, shared model cache. Multiple active sessions still consume additional memory; this is a low-traffic portfolio demo, not a hardened anonymous hiring service.

To stop all paid use immediately, remove/revoke the server key. Do not log provider payloads, resumes or secret values. SDK tracing remains disabled. Do not add private data to `static/`, because that directory is intentionally served publicly for fonts/CSS.

## 5. Acceptance checks before sharing the URL

1. Open the URL in an incognito session. Verify all six pages and light/dark modes. Without a key or with a wrong access code, AI actions must remain disabled while search works.
2. Enable the explicitly synthetic examples, build the index, and search `Python machine learning semantic search embeddings FAISS`. Check three returned candidates, page citations, and dynamic cosine scores. Do not describe those scores as hiring probabilities or real-world evaluation metrics.
3. Clear the workspace and upload an authorized anonymized text PDF. Build/search, inspect its source, review requirement evidence and download the Markdown report. Try an empty/scanned/corrupt PDF and verify a readable error. Native hosted file selection/download needs manual verification.
4. Navigate away and back; verify the index remains and user data never appears in another browser session. Start a second browser session to check workspace isolation. The model is shared; candidate indexes are not.
5. If AI is configured, enter the private code and consent; ask a skill question, compare two actual results, and generate interview questions. Inspect actual SDK tool traces and source citations. Missing provider access/quota must show a recoverable error. Verify the cooldown and limits. No live provider run was performed during preparation because no key was configured.
6. Check app logs for out-of-memory kills. Use the Linux CI memory profile as guidance, then test actual hosted indexing and several concurrent sessions. This environment's Windows measurement is not the host's RAM usage. If the host kills the process, use the larger Docker host instead of claiming success based only on its HTTP health endpoint.
7. Only after these checks pass, use the assigned URL on your application. Preserve a short screen recording in case a free host sleeps during an interview.

## Docker fallback

The Dockerfile builds on Python 3.12 / Debian Bookworm as a nonroot user, installs CPU Torch, warms the public model during build, and serves Streamlit on port 8501. It uses a restrictive `.dockerignore`; no key is copied into the image. At least 4 GB RAM is a conservative starting point, subject to Linux profiling and concurrency checks.

After installing Docker and reviewing the source:

```powershell
docker build -t matchmind-ai .
docker run --rm --memory=4g matchmind-ai python scripts/profile_deployment.py
docker run --rm -p 8501:8501 matchmind-ai
```

For AI, inject credentials through your hosting secret manager at runtime. For a local container, `--env-file .env` can be used with a local ignored file; never pass literal keys in command history or use Docker build arguments for secrets. A local HTTP URL is not a public deployment. A generic Docker host must route HTTPS and WebSockets to port 8501 and run one replica. The Docker image was not built locally because Docker is unavailable here.

For an entitled Hugging Face account, create a **Docker Space**, upload the reviewed source, and prepend this metadata to that Space's README:

```yaml
---
title: MatchMind AI
sdk: docker
app_port: 8501
---
```

Set environment secrets in the Space's Settings, not README or Dockerfile. Choose hardware only after checking charges. Record the assigned `*.hf.space` URL and perform the same acceptance checks.

## Updating later

Edit/test in your working project, rerun `scripts/prepare_release.py`, review changed allowlisted files and copy them into the clean Git repository. Commit/push only when you intend to publish an update. Community Cloud rebuilds dependencies when requirements change. Do not copy private caches, resumes or historical archives into the release. Backups remain local at `.cache/backups/before_deployment_prep.zip` and `.cache/backups/before_stitch_redesign.zip`.
