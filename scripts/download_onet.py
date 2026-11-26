"""Download official CC BY 4.0 occupational data; preserve checksums and source rows."""
import csv
from datetime import datetime, timezone
import hashlib
import io
import json
from pathlib import Path
import sys
from urllib.request import urlopen
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dataset_io import ROOT, ONET_ATTRIBUTION

BASE = "https://www.onetcenter.org/dl_files/database/db_31_0_csv/"


def build_occupations(tables):
    occupations = {r["O*NET-SOC Code"]: {"code": r["O*NET-SOC Code"],
                    "title": r["Title"], "description": r["Description"], "skills": [], "tasks": []}
                   for r in tables["occupation_data.csv"]}
    for table, field, target in [("software_skills.csv", "Workplace Example", "skills"),
                                 ("task_statements.csv", "Task", "tasks")]:
        for row in tables[table]:
            occupation = occupations.get(row["O*NET-SOC Code"])
            if occupation and row[field] not in occupation[target]:
                occupation[target].append(row[field])
    return list(occupations.values())


if __name__ == "__main__":
    tables, sources = {}, []
    for filename in ("occupation_data.csv", "software_skills.csv", "task_statements.csv"):
        with urlopen(BASE + filename, timeout=60) as response:
            raw = response.read(30_000_001)
        if len(raw) > 30_000_000:
            raise ValueError("O*NET file exceeds size limit")
        rows = list(csv.DictReader(io.StringIO(raw.decode("utf-8-sig"))))
        tables[filename] = rows
        sources.append({"url": BASE + filename, "sha256": hashlib.sha256(raw).hexdigest(),
                        "bytes": len(raw), "rows": len(rows)})
    payload = {"version": "31.0", "license": "CC BY 4.0",
        "license_url": "https://creativecommons.org/licenses/by/4.0/",
        "attribution": ONET_ATTRIBUTION, "downloaded_utc": datetime.now(timezone.utc).isoformat(),
        "sources": sources, "changes": "Selected titles, descriptions, unique software examples and tasks; grouped by SOC code. No generated text or rating thresholds.",
        "occupations": build_occupations(tables)}
    folder = ROOT / "data"
    folder.mkdir(exist_ok=True)
    (folder / "onet_occupations.json").write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"occupations": len(payload["occupations"]), "sources": sources}, indent=2))
