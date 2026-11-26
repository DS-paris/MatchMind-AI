"""Build a reviewed allowlist-only source ZIP. Never uploads or runs git add."""
from hashlib import sha256
import json
from pathlib import Path
import re
from zipfile import ZipFile, ZIP_DEFLATED

ROOT = Path(__file__).resolve().parents[1]
ROOT_FILES = "app.py agent.py matcher.py parser.py privacy.py dataset_io.py reports.py ui_theme.py deployment.py requirements.txt requirements-dev.txt README.md DEPLOYMENT.md VALIDATION.md UI_REDESIGN.md .gitignore .dockerignore Dockerfile .env.example".split()
SECRET = re.compile(rb"(?:sk-(?:proj-)?[A-Za-z0-9_-]{24,}|hf_[A-Za-z0-9]{24,}|-----BEGIN (?:RSA |OPENSSH |EC )?PRIVATE KEY-----)")


def release_files(root=ROOT):
    files = [root / name for name in ROOT_FILES]
    files += [root / name for name in (
        ".streamlit/config.toml", ".streamlit/secrets.example.toml", ".github/workflows/ci.yml",
        "data/onet_occupations.json", "data/README.md", "data/ALTERNATIVE_DATASET_AUDIT.md",
        "evaluation/README.md", "samples/job_description.txt",
        "samples/candidate_aurora.pdf", "samples/candidate_brook.pdf", "samples/candidate_cedar.pdf")]
    for folder in ("scripts", "tests"):
        files.extend(sorted((root / folder).glob("*.py")))
    files.extend(sorted((root / "static").glob("*.css")))
    files.extend(p for p in sorted((root / "static/fonts").glob("*"))
                 if p.suffix in {".css", ".ttf", ".woff2"} or p.name.endswith("-LICENSE.txt"))
    return sorted(set(files))


def prepare(root=ROOT):
    files = release_files(root)
    records = []
    for path in files:
        if not path.is_file() or path.is_symlink() or not path.resolve().is_relative_to(root.resolve()):
            raise ValueError(f"Missing or unsafe release file: {path.name}")
        data = path.read_bytes()
        if SECRET.search(data):
            raise ValueError(f"Possible secret detected in {path.relative_to(root)}; release aborted.")
        records.append({"path": path.relative_to(root).as_posix(), "bytes": len(data),
                        "sha256": sha256(data).hexdigest()})
    output = root / ".cache" / "release"
    output.mkdir(parents=True, exist_ok=True)
    archive = output / "MatchMind-deploy.zip"
    with ZipFile(archive, "w", ZIP_DEFLATED) as bundle:
        for record, path in zip(records, files):
            bundle.write(path, record["path"])
    (output / "manifest.json").write_text(json.dumps(records, indent=2), encoding="utf-8")
    print(f"Prepared {len(records)} allowlisted files, {archive.stat().st_size} ZIP bytes.")
    print(archive)
    print("Not published. Review the manifest and content before creating a repository.")
    return archive


if __name__ == "__main__":
    prepare()
