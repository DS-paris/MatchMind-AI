"""Real MiniLM + FAISS sample smoke test with OS-measured peak RSS; no LLM."""
import json
from pathlib import Path
import sys
from time import perf_counter
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))


def peak_mib():
    if sys.platform == "win32":
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [("cb", wintypes.DWORD), ("PageFaultCount", wintypes.DWORD)] + [
                (name, ctypes.c_size_t) for name in ("PeakWorkingSetSize", "WorkingSetSize",
                "QuotaPeakPagedPoolUsage", "QuotaPagedPoolUsage", "QuotaPeakNonPagedPoolUsage",
                "QuotaNonPagedPoolUsage", "PagefileUsage", "PeakPagefileUsage")]
        handle = ctypes.windll.kernel32.GetCurrentProcess
        handle.restype = wintypes.HANDLE
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        read_memory = ctypes.windll.psapi.GetProcessMemoryInfo
        read_memory.argtypes = [wintypes.HANDLE, ctypes.POINTER(Counters), wintypes.DWORD]
        read_memory.restype = wintypes.BOOL
        if not read_memory(handle(), ctypes.byref(counters), counters.cb):
            raise OSError("Could not read process memory counters")
        return counters.PeakWorkingSetSize / 1024**2
    import resource
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return peak / (1024**2 if sys.platform == "darwin" else 1024)


def main():
    started = perf_counter()
    import streamlit  # Include the actual UI and SDK import footprint.
    import agent
    from matcher import CandidateIndex
    from parser import parse_pdf
    root = Path(__file__).resolve().parents[1]
    resumes = [parse_pdf(p.read_bytes(), p.name) for p in sorted((root / "samples").glob("*.pdf"))]
    index = CandidateIndex(resumes)
    rows = index.search("Python machine learning semantic search embeddings FAISS", 3)
    assert len(rows) == 3 and rows[0]["filename"] == "candidate_aurora.pdf"
    assert index.index.ntotal == len(index.chunks) and index.index.d == 384
    result = {"platform": sys.platform, "python": sys.version.split()[0], "records": len(index.resumes),
        "vectors": index.index.ntotal, "dimensions": index.index.d, "peak_rss_mib": round(peak_mib(), 1),
        "elapsed_seconds": round(perf_counter() - started, 2),
        "results": [{"document": r["filename"], "cosine": round(r["similarity"], 4)} for r in rows],
        "scope": "Single process, three synthetic fixtures. Not a concurrent-load or hosted-memory guarantee."}
    output = root / ".cache" / "deployment-profile.json"
    output.parent.mkdir(exist_ok=True)
    output.write_text(json.dumps(result, indent=2), encoding="utf-8")
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
