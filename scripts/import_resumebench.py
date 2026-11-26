"""Authenticated, pinned import; does not accept terms or bypass the publisher gate."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import sys
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_io import LOCAL, RESUME_SOURCE, REVISION, write_staged
from urllib.request import Request, urlopen
from dotenv import load_dotenv

if __name__ == "__main__":
    load_dotenv()
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--approve-reviewed", action="store_true",
                        help="Activate ONLY after manually checking all staged text for PII.")
    args = parser.parse_args()
    if args.approve_reviewed:
        path = LOCAL / "resumebench.json"
        (LOCAL / "review.sha256").write_text(hashlib.sha256(path.read_bytes()).hexdigest())
        print("Activated locally reviewed records; files remain ignored by Git.")
    else:
        token = os.getenv("HF_TOKEN", "").strip()
        request = Request(f"{RESUME_SOURCE}/resolve/{REVISION}/test.jsonl",
                          headers={"Authorization": f"Bearer {token}"} if token else {})
        try:
            with urlopen(request, timeout=60) as response:
                raw = response.read(20_000_001)
            if len(raw) > 20_000_000:
                raise ValueError("Dataset exceeds the import size limit.")
            records = [json.loads(line) for line in raw.decode().splitlines() if line.strip()]
            path = write_staged(records)
            print(f"Staged minimized text at {path}. Review every record locally before --approve-reviewed.")
        except Exception as exc:
            print(f"Import failed ({type(exc).__name__}): {exc}. No dataset activated.", file=sys.stderr)
            sys.exit(1)
