"""MatchMind AI — Stitch presentation, existing Python intelligence pipeline."""
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
from time import perf_counter
from uuid import uuid4
from dotenv import load_dotenv
import streamlit as st
from parser import parse_pdf, ResumeError
from matcher import CandidateIndex, requirement_evidence
from dataset_io import load_real_dataset, load_occupations, occupation_requirements
from reports import build_report
from ui_theme import apply_theme, badge, empty_state, label, section_title, stat
from deployment import AGENT_BUDGET, AccessDenied, authorized, indexing_slot, public_mode

load_dotenv()
ROOT = Path(__file__).parent
PAGES = ["Overview", "Candidate Matching", "Semantic Search", "AI Assistant", "Candidate Intelligence", "Data & Evaluation"]
ICONS = ["dashboard", "group_add", "manage_search", "forum", "person_search", "database"]
st.set_page_config(page_title="MatchMind AI", page_icon="🧠", layout="wide", initial_sidebar_state="expanded")


def setting(name, default=""):
    value = os.getenv(name)
    if value:
        return value
    try:
        return str(st.secrets.get(name, default))
    except FileNotFoundError:
        return default


def navigate(page):
    st.session_state.page = page


def activity(message):
    events = st.session_state.setdefault("activity", [])
    events.insert(0, {"message": message, "time": datetime.now(timezone.utc).strftime("%H:%M:%S UTC")})
    del events[12:]


def clear_results():
    for item in ("messages", "results", "retrieval_query", "tool_calls", "gap_result", "evaluation", "retrieval_ms"):
        st.session_state.pop(item, None)


def candidate_name(cid):
    return index.resumes[cid].filename


key = setting("OPENAI_API_KEY").strip()
is_public = public_mode(setting("MATCHMIND_PUBLIC", "true"))
access_secret = setting("MATCHMIND_AGENT_ACCESS_CODE")
generation = st.session_state.get("generation", 0)
page = st.session_state.setdefault("page", "Overview")
with st.sidebar:
    logo_col, brand_col = st.columns([.18, .82], gap="small")
    with logo_col:
        st.markdown('<span class="brand-mark">⌘</span>', unsafe_allow_html=True)
    with brand_col:
        st.title("MatchMind AI")
        st.caption("Local workspace")
    for name, icon in zip(PAGES, ICONS):
        st.button(name, icon=f":material/{icon}:", key=f"nav_{PAGES.index(name)}",
                  type="primary" if page == name else "secondary", width="stretch",
                  on_click=navigate, args=(name,))
    st.markdown('<div class="sidebar-rule"></div><div class="workspace-label">Candidate workspace</div>', unsafe_allow_html=True)
    source_mode = st.radio("Candidate source", ["Uploaded resumes", "Real-world dataset"], key=f"source_{generation}")
    use_dataset = source_mode == "Real-world dataset"
    demo = st.checkbox("Use synthetic sample resumes", key=f"demo_{generation}", disabled=use_dataset)
    if key:
        st.success("Assistant configured")
    else:
        st.warning("Search mode · no OpenAI key")
    unlocked = not is_public
    if key and is_public:
        if len(access_secret) < 24:
            st.caption("Public assistant locked. The owner must configure a private access code of at least 24 characters.")
        else:
            supplied = st.text_input("Recruiter assistant access code", type="password", key="agent_access_code")
            unlocked = authorized(access_secret, supplied)
            st.caption("Assistant unlocked" if unlocked else "Local search is public. Ask the project owner for assistant access.")
    consent = st.checkbox("Allow sending resume evidence and questions to OpenAI", disabled=not bool(key), key="consent")
    st.caption("One assistant · three callable tools. A nonempty key does not verify API access. SDK tracing is disabled.")
    dark = st.toggle("Dark appearance", key="dark_appearance")
    if st.button("Clear workspace", icon=":material/restart_alt:", width="stretch"):
        st.session_state.clear()
        st.session_state.generation = generation + 1
        st.rerun()

apply_theme(dark)
enabled = bool(key and consent and unlocked)
dataset_resumes, dataset_metadata, dataset_error = [], None, ""
if use_dataset:
    try:
        dataset_resumes, dataset_metadata = load_real_dataset()
        with st.sidebar:
            st.caption(f"{len(dataset_resumes)} real records · CC BY 4.0")
    except (ValueError, OSError, KeyError, TypeError) as exc:
        dataset_error = str(exc)
        with st.sidebar:
            st.warning(dataset_error)
            st.caption("0 real records available. Upload PDFs to continue. No synthetic fallback.")
try:
    occupational_data = load_occupations()
    occupation_error = ""
except (OSError, ValueError, KeyError) as exc:
    occupational_data, occupation_error = None, f"Occupational data could not load ({type(exc).__name__})."

DESCRIPTIONS = {
    "Overview": ("Recruitment Intelligence Overview", "Monitor your candidate pool, active requirements, and evidence-based research."),
    "Candidate Matching": ("Candidate Matching", "Ingest PDF resumes, define job requirements, and retrieve candidates with supporting evidence."),
    "Semantic Search": ("Semantic Search", "Search documented experience by meaning. Trace every result back to its source."),
    "AI Assistant": ("AI Recruitment Assistant", "Evidence-backed comparisons, skill-gap reasoning, and tailored interview questions."),
    "Candidate Intelligence": ("Candidate Intelligence", "Inspect documented experience and review evidence against the current requirements."),
    "Data & Evaluation": ("Data & Evaluation", "Manage source provenance, inspect the vector index, and evaluate reviewed retrieval judgments."),
}
left, right = st.columns([2.5, 1.4], vertical_alignment="center")
with left:
    st.header(DESCRIPTIONS[page][0])
    st.caption(DESCRIPTIONS[page][1])
with right:
    a, b = st.columns(2)
    a.button("Search", icon=":material/search:", on_click=navigate, args=("Semantic Search",), width="stretch")
    b.button("Upload resumes", icon=":material/upload_file:", type="primary", on_click=navigate, args=("Candidate Matching",), width="stretch")
st.markdown('<div class="page-rule"></div>', unsafe_allow_html=True)
stats_slot = st.empty() if page == "Overview" else None

# Shared widgets stay mounted on every route, preserving uploaded bytes and
# widget identity across navigation without reloading the embedding model.
with st.expander("Resume batch & job input", expanded=page == "Candidate Matching"):
    upload_col, job_col = st.columns(2, gap="large")
    with upload_col:
        section_title("Resume batch", f"Text-based PDFs · up to {5 if is_public else 20} files · 10 MB and 30 pages each")
        if is_public:
            st.caption("Public demo: 20 MB upload total and 60,000 extracted characters per batch. Use anonymized, authorized documents.")
        uploads = st.file_uploader("Upload PDF resumes", type=["pdf"], accept_multiple_files=True,
            key=f"uploads_{generation}", disabled=use_dataset)
        if use_dataset:
            st.caption("Using reviewed dataset records. Switch to Uploaded resumes for PDF input.")
        if demo and not use_dataset:
            st.caption("Synthetic fixtures enabled explicitly. All sample records are fictional.")
    with job_col:
        section_title("Job description", "Set the role requirements for retrieval and the assistant")
        default_jd = (ROOT / "samples" / "job_description.txt").read_text(encoding="utf-8") if demo and not use_dataset else ""
        if default_jd and not st.session_state.get("job_description", "").strip():
            st.session_state.job_description = default_jd
        st.session_state.setdefault("job_description", default_jd)
        jd = st.text_area("Job description", height=180, max_chars=20000, key="job_description",
                          placeholder="Describe the skills, responsibilities, and experience you want to explore…")
    with st.expander("Use real O*NET occupational requirements"):
        if occupational_data:
            occupation = st.selectbox("Occupation", occupational_data["occupations"],
                format_func=lambda o: f"{o['code']} · {o['title']}", key="occupation")
            def use_occupation():
                selected = st.session_state.occupation
                st.session_state.job_description = occupation_requirements(selected)[:20000]
                st.session_state.occupation_reference = f"O*NET 31.0 · {selected['code']} · {selected['title']}"
            st.button("Use occupational requirements", on_click=use_occupation)
            st.caption(occupational_data["attribution"])
            st.markdown("[Official database](https://www.onetcenter.org/database.html) · [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/)")
        else:
            st.warning(occupation_error or "O*NET data is not installed. Run python scripts/download_onet.py.")

sources = [(f.name, f.getvalue()) for f in uploads or []] if not use_dataset else []
if demo and not use_dataset:
    sources += [(p.name, p.read_bytes()) for p in sorted((ROOT / "samples").glob("*.pdf"))]
fingerprint = hashlib.sha256(source_mode.encode() + b"".join(name.encode() + hashlib.sha256(data).digest() for name, data in sources)
    + "".join(r.candidate_id for r in dataset_resumes).encode()).hexdigest()
if st.session_state.get("source_fingerprint") != fingerprint:
    st.session_state.pop("index", None)
    clear_results()
    st.session_state.source_fingerprint = fingerprint
if st.session_state.get("active_jd") != jd:
    clear_results()
    st.session_state.active_jd = jd
build_col, status_col = st.columns([1, 2], vertical_alignment="center")
build = build_col.button("Build candidate index", icon=":material/bolt:", type="primary",
    disabled=not (sources or dataset_resumes), width="stretch")
if "index" in st.session_state:
    status_col.caption("Index ready · reused across navigation and search. Rebuild only when documents change.")
else:
    status_col.caption(f"{len(sources) + len(dataset_resumes)} documents available · build the index to begin")
if build:
    max_documents = 5 if is_public else 20
    if len(sources) + len(dataset_resumes) > max_documents:
        st.error(f"This workspace accepts at most {max_documents} resumes per index.")
    elif is_public and sum(len(data) for _, data in sources) > 20 * 1024 * 1024:
        st.error("Public demo batches must total at most 20 MB.")
    elif len(sources) > 20:
        st.error("Please upload at most 20 resumes.")
    else:
        resumes = list(dataset_resumes)
        for name, data in sources:
            try:
                resume = parse_pdf(data, name)
                resumes.append(resume)
                for warning in resume.warnings:
                    st.warning(f"{name}: {warning}")
            except ResumeError as exc:
                st.error(f"{name}: {exc}")
        if resumes:
            try:
                if is_public and sum(len(r.text) for r in resumes) > 60_000:
                    raise ValueError("Public demo text limit is 60,000 characters per batch.")
                with st.status("Building the candidate index…", expanded=True) as status:
                    st.write("Loading cached MiniLM weights and encoding resume passages.")
                    started = perf_counter()
                    with indexing_slot():
                        new_index = CandidateIndex(resumes)
                    st.session_state.index = new_index
                    st.session_state.index_ms = (perf_counter() - started) * 1000
                    clear_results()
                    status.update(label=f"Index ready · {len(new_index.resumes)} candidates · {len(new_index.chunks)} evidence chunks", state="complete", expanded=False)
                activity(f"Indexed {len(new_index.resumes)} resumes into {len(new_index.chunks)} evidence chunks")
                st.success("Index ready. Duplicate documents are deduplicated by content.")
            except Exception as exc:
                st.session_state.pop("index", None)
                clear_results()
                st.error(str(exc) if isinstance(exc, (ValueError, AccessDenied)) else f"Index could not load ({type(exc).__name__}). Check dependencies, network access and the model cache; then retry.")
index = st.session_state.get("index")


def require_index():
    if index is None:
        empty_state("Your candidate workspace starts here", "Upload authorized resumes in the batch input above and build the index. An external dataset is not required.", "upload_file")
        return False
    return True


def render_search():
    section_title("Candidate retrieval", "Dynamic passage cosine similarity. Scores measure retrieval, never hiring suitability.")
    search_col, count_col = st.columns([3, 1], vertical_alignment="bottom")
    with search_col:
        query = st.text_input("Semantic search", placeholder="Python and machine learning projects", key="search_query")
    with count_col:
        top_k = st.slider("Candidates to retrieve", 1, max(2, min(50, len(index.resumes))), min(5, len(index.resumes)), key="top_k")
    if st.button("Search candidates", icon=":material/manage_search:", type="primary", disabled=not (query.strip() or jd.strip())):
        try:
            with st.spinner("Retrieving resume evidence…"):
                started = perf_counter()
                st.session_state.results = index.search(query.strip() or jd, top_k)
                st.session_state.retrieval_ms = (perf_counter() - started) * 1000
                st.session_state.retrieval_query = query.strip() or jd
                activity(f"Retrieved {len(st.session_state.results)} candidates using semantic search")
            st.rerun()
        except Exception as exc:
            st.session_state.pop("results", None)
            st.error(str(exc) if isinstance(exc, ValueError) else f"Search failed ({type(exc).__name__}). Please retry.")
    current = st.session_state.get("results", [])
    if current:
        st.caption(f"Last executed query: {st.session_state.get('retrieval_query', '')}")
        st.caption(f"{len(current)} candidates · {st.session_state.get('retrieval_ms', 0):.0f} ms measured retrieval time")
        st.dataframe([{"Rank": i, "Document": r["filename"], "Candidate ID": r["candidate_id"],
                       "Retrieval similarity (cosine)": round(r["similarity"], 4)} for i, r in enumerate(current, 1)], hide_index=True, width="stretch")
        for row in current:
            with st.container(border=True, key=f"panel_result_{row['candidate_id']}"):
                identity, score = st.columns([3, 1])
                with identity:
                    st.markdown(f'<div class="candidate-head"><div class="candidate-avatar">{label(row["candidate_id"][:2].upper())}</div>'
                        f'<div><h3>{label(row["filename"])}</h3><p>{label(row["candidate_id"])}</p></div></div>', unsafe_allow_html=True)
                with score:
                    st.markdown(f'<div class="candidate-score">{row["similarity"]:.4f}</div><div class="score-caption">Retrieval cosine</div>', unsafe_allow_html=True)
                st.markdown(f'<div class="evidence">{label(row["text"])}</div>', unsafe_allow_html=True)
                st.caption(f"Supporting resume evidence · {row['citation']}")
                def open_profile(cid=row["candidate_id"]):
                    st.session_state.profile_candidate = cid
                    navigate("Candidate Intelligence")
                st.button("Open intelligence profile", key=f"profile_{row['candidate_id']}", on_click=open_profile)
    else:
        empty_state("Find the evidence behind the experience", "Search a skill, project, or responsibility—or leave the query empty to search the current job description.")


def run_question(question):
    try:
        # Enforced at execution, as well as through disabled UI controls.
        if not enabled:
            raise AccessDenied("Unlock the assistant and consent to provider sharing first.")
        from agent import ask_agent
        messages = st.session_state.setdefault("messages", [])
        with st.status("Assistant running · waiting for model-selected tools…", expanded=True) as status:
            st.caption("Only completed SDK tool calls appear in the trace. No simulated activity is shown.")
            session_id = st.session_state.setdefault("budget_session", uuid4().hex)
            with AGENT_BUDGET.request(session_id):
                answer, calls = ask_agent(index, question, jd, key, setting("OPENAI_MODEL", "gpt-4.1-mini"), messages,
                    retrieval_context={"query": st.session_state.get("retrieval_query", ""), "results": st.session_state.get("results", [])})
            status.update(label=f"Assistant completed · {len(calls)} tool calls recorded", state="complete", expanded=False)
        messages.extend([{"role": "user", "content": question}, {"role": "assistant", "content": answer}])
        st.session_state.tool_calls = calls
        activity(f"Assistant completed an evidence review with {len(calls)} recorded tool calls")
        st.rerun()
    except AccessDenied as exc:
        st.warning(str(exc))
    except Exception as exc:
        st.error(f"Assistant request failed ({type(exc).__name__}). Check key, model access, quota and connection. Local search remains available.")


def render_assistant(compact=False):
    section_title("Recruiter assistant" if compact else "Evidence-backed conversation", "One OpenAI agent with search, inspection, and skill-evidence tools")
    if not enabled:
        st.info("The assistant requires a server-side OpenAI key, sharing consent and, in public mode, a private access code. Semantic search works without these.")
    messages = st.session_state.setdefault("messages", [])
    for message in messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
    if not compact:
        a, b = st.columns([2, 1], vertical_alignment="bottom")
        candidate = a.selectbox("Interview candidate", list(index.resumes), format_func=candidate_name, key="interview_candidate")
        if b.button("Generate evidence-based interview questions", disabled=not enabled or not jd.strip(), width="stretch"):
            run_question(f"Generate 6 interview questions for candidate {candidate}, based on the job requirements and documented experience. Cite evidence and label verification questions.")
        if st.button("Compare top two candidates", disabled=not enabled or len(st.session_state.get("results", [])) < 2):
            ids = [r["candidate_id"] for r in st.session_state.results[:2]]
            run_question(f"Compare candidates {ids[0]} and {ids[1]} using resume evidence against the job description. Inspect both. Do not recommend a hiring decision.")
    question = st.chat_input("Ask about uploaded candidate evidence…", disabled=not enabled, max_chars=5000, key="assistant_prompt")
    if question:
        run_question(question)
    calls = st.session_state.get("tool_calls", [])
    if calls:
        with st.expander("Agent tool execution trace", expanded=not compact):
            for i, call in enumerate(calls, 1):
                st.markdown(f"**{i}. {call['tool']}** · recorded SDK result")
                st.json(call["result"])
    elif not compact:
        st.caption("No tool calls recorded. Try: Compare the top two candidates using resume evidence.")


if page == "Overview":
    with stats_slot.container():
        cols = st.columns(4)
        top_rows = st.session_state.get("results", [])[:5]
        with cols[0]:
            stat("Indexed resumes", len(index.resumes) if index else 0, f"{len(index.chunks) if index else 0} evidence chunks embedded", "description")
        with cols[1]:
            stat("Active job requirements", 1 if jd.strip() else 0, "Current editable role in this session", "work_outline")
        with cols[2]:
            stat("Mean retrieved similarity", f"{sum(r['similarity'] for r in top_rows)/len(top_rows):.4f}" if top_rows else "—", "Cosine · last search, up to 5 results", "analytics")
        with cols[3]:
            stat("Agent availability", "Configured" if enabled else "Search only", "1 assistant · 3 tools · API access unverified", "memory")
    st.write("")
    main, side = st.columns([2, 1], gap="large")
    with main:
        with st.container(border=True, key="panel_requirements"):
            section_title("Active job requirements", "The role currently used for candidate discovery")
            if jd.strip():
                st.text(jd[:700] + ("…" if len(jd) > 700 else ""))
                st.caption(st.session_state.get("occupation_reference", "User-supplied requirements"))
            else:
                st.caption("No role added yet. Enter a job description in the batch input above.")
        with st.container(border=True, key="panel_activity"):
            section_title("Recent activity", "Actual events from this session")
            for event in st.session_state.get("activity", [])[:4]:
                st.markdown(f'<div class="activity-row">{label(event["message"])}<span>{label(event["time"])}</span></div>', unsafe_allow_html=True)
            if not st.session_state.get("activity"):
                st.caption("Activity appears after indexing, retrieval, and assistant requests.")
    with side:
        with st.container(border=True, key="panel_services"):
            section_title("Intelligence services")
            for title, detail in [("Semantic retriever", "MiniLM + FAISS · ready" if index else "Awaiting candidate index"),
                                  ("Recruiter assistant", "Configured · not yet validated" if enabled else "API key and consent required"),
                                  ("Occupational reference", f"{len(occupational_data['occupations'])} O*NET occupations" if occupational_data else "Not installed")]:
                st.markdown(f'<div class="status-row"><strong>{label(title)}</strong><span>{label(detail)}</span></div>', unsafe_allow_html=True)
        with st.container(border=True, key="panel_actions"):
            section_title("Quick actions")
            st.button("Batch index PDF resumes", on_click=navigate, args=("Candidate Matching",), width="stretch")
            st.button("Compare candidate evidence", on_click=navigate, args=("AI Assistant",), width="stretch")
    if index:
        render_search()
        render_assistant(compact=True)
    else:
        require_index()
elif page in ("Candidate Matching", "Semantic Search"):
    if require_index():
        render_search()
elif page == "AI Assistant":
    if require_index():
        render_assistant()
elif page == "Candidate Intelligence":
    if require_index():
        ids = list(index.resumes)
        if st.session_state.get("profile_candidate") not in ids:
            st.session_state.profile_candidate = ids[0]
        cid = st.selectbox("Candidate profile", ids, format_func=candidate_name, key="profile_candidate")
        resume = index.resumes[cid]
        st.subheader(resume.filename)
        badge(f"{cid} · {len(resume.pages)} source pages")
        st.caption(resume.provenance)
        overview_tab, gap_tab = st.tabs(["Documented experience & projects", "Job requirement comparison"])
        with overview_tab:
            for evidence in resume.evidence():
                with st.container(border=True, key=f"panel_source_{evidence['page']}"):
                    st.caption(evidence["citation"])
                    st.text(evidence["text"])
        with gap_tab:
            st.caption("Exact-phrase evidence hints, not a skills classifier. Missing phrases require review; absence does not establish inability.")
            if st.button("Review requirement evidence", disabled=not jd.strip()):
                st.session_state.gap_result = {"candidate": cid, "jd": jd, "evidence": requirement_evidence(resume, jd)}
            gap_result = st.session_state.get("gap_result", {})
            if gap_result.get("candidate") == cid and gap_result.get("jd") == jd:
                for requirement in gap_result["evidence"]["requirements"]:
                    with st.container(border=True):
                        st.text(requirement["requirement"])
                        matches = requirement["exact_phrase_evidence"]
                        if matches:
                            for evidence in matches:
                                st.caption(evidence["citation"])
                                st.text(evidence["text"])
                        else:
                            st.caption("Exact phrase not explicitly evidenced; inspect the source or ask the assistant.")
        st.button("Ask AI assistant", on_click=navigate, args=("AI Assistant",))
elif page == "Data & Evaluation":
    section_title("Dataset management & licensing", "Actual sources available to this workspace")
    st.dataframe([
        {"Dataset": "Current resume workspace", "License / permissions": "User-authorized uploads" if not use_dataset else "CC BY 4.0 · reviewed ResumeBench", "Records": len(index.resumes) if index else 0, "State": "Indexed" if index else "Not indexed"},
        {"Dataset": "O*NET 31.0 occupational references", "License / permissions": "CC BY 4.0 · USDOL/ETA", "Records": len(occupational_data["occupations"]) if occupational_data else 0, "State": "Available" if occupational_data else "Not installed"},
        {"Dataset": "Reviewed external resumes", "License / permissions": "Publisher conditions and local privacy review", "Records": len(dataset_resumes), "State": "Available" if dataset_resumes else "Unavailable / not loaded"}], hide_index=True, width="stretch")
    st.markdown("[ResumeBench source](https://huggingface.co/datasets/Careerflow/ResumeBench)")
    st.caption(dataset_error or "The real-dataset selector only loads locally privacy-reviewed records. No verified public replacement corpus has been imported.")
    if dataset_metadata:
        st.json(dataset_metadata)
    if occupational_data:
        with st.expander("O*NET attribution and preprocessing manifest"):
            st.json({k: v for k, v in occupational_data.items() if k != "occupations"})
    section_title("System configuration", "Actual runtime values; no unsupported model switches")
    st.json({"embedding_model": "sentence-transformers/all-MiniLM-L6-v2", "index": "FAISS IndexFlatIP",
             "vectors": index.index.ntotal if index else 0, "dimensions": index.index.d if index else None,
             "chunk_words": 100, "chunk_stride_words": 75, "similarity": "normalized inner product / cosine",
             "agent_model": setting("OPENAI_MODEL", "gpt-4.1-mini"), "agent_tracing": "disabled"})
    section_title("Reviewed retrieval evaluation", "Supply human relevance judgments for the current corpus. No benchmark values are prefilled.")
    judgments_file = st.file_uploader("Reviewed judgments JSON", type=["json"], key="judgments")
    eval_k = st.number_input("Evaluation k", min_value=1, max_value=50, value=3, step=1)
    if st.button("Run reviewed evaluation", disabled=index is None or judgments_file is None):
        try:
            if judgments_file.size > 1_000_000:
                raise ValueError("Judgments file must be under 1 MB.")
            from scripts.evaluate_retrieval import evaluate
            with st.spinner("Evaluating labeled retrieval queries…"):
                evaluation = evaluate(index, json.loads(judgments_file.getvalue()), int(eval_k))
            st.session_state.evaluation = evaluation
            activity(f"Evaluated {evaluation['queries']} human-labeled queries at k={int(eval_k)}")
        except Exception as exc:
            st.session_state.pop("evaluation", None)
            st.error(str(exc) if isinstance(exc, ValueError) else f"Evaluation failed ({type(exc).__name__}). Check JSON schema and candidate IDs.")
    if st.session_state.get("evaluation"):
        evaluation = st.session_state.evaluation
        a, b, c = st.columns(3)
        a.metric("Reviewed queries", evaluation["queries"])
        b.metric(f"Recall@{evaluation['k']}", f"{evaluation['mean_recall_at_k']:.4f}")
        c.metric(f"MRR@{evaluation['k']}", f"{evaluation['mrr_at_k']:.4f}")
        st.caption("Measured on supplied labels only. Reviewer metadata cannot prove review occurred. No hiring suitability or fairness conclusion follows.")
        st.download_button("Download evaluation results", json.dumps(evaluation, indent=2), file_name="matchmind-evaluation.json", mime="application/json")
    else:
        st.caption("No evaluation results. Required fields: query, relevant_candidate_ids, reviewer, evidence_notes.")

if index:
    st.download_button("Download Markdown research report", build_report(index, st.session_state.get("results", []), jd,
        st.session_state.get("messages", []), st.session_state.get("retrieval_query", ""), st.session_state.get("occupation_reference", "")),
        file_name="matchmind-report.md", mime="text/markdown", icon=":material/download:")
st.markdown('<div class="footer-note">MatchMind AI · Retrieval similarity is not hiring suitability. Review source evidence; all hiring decisions remain with people.</div>', unsafe_allow_html=True)
