# External data provenance and access audit

Verified 23 November 2026. No personal resume data is distributed in this repository.

**24 November follow-up:** a bounded search checked four alternative datasets, including two directly downloadable Hugging Face sources. None satisfied the combined genuine-original-resume, license/provenance, and unauthenticated-access requirements. No replacement records were imported. See the [alternative dataset audit](ALTERNATIVE_DATASET_AUDIT.md) for exact access results and rejection reasons; the upload workflow is preserved.

## Resume dataset investigation

**Preferred source:** [Careerflow/ResumeBench on Hugging Face](https://huggingface.co/datasets/Careerflow/ResumeBench), formerly ResumeExtractBench. Metadata revision inspected: `db07f5ad52c061784f5728a4ded1e356e4b59278`. The publisher card declares **CC BY 4.0** and describes 300 documents: 138 real-world anonymized, 9 handwritten, 153 synthetic. It lists 20 documents in the public test split, with source labels distinguishing `real-anonymized` records. These are publisher statements, not an independent audit of employment claims or consent. Older cached cards describe a different 30-document release; the importer pins the inspected current revision, rather than relying on those outdated counts.

The hosting page requires acceptance of conditions and account-information sharing. An unauthenticated request to:

`https://huggingface.co/datasets/Careerflow/ResumeBench/resolve/db07f5ad52c061784f5728a4ded1e356e4b59278/test.jsonl`

returned **HTTP 401**, stating that access is restricted and authentication is required. **Downloaded resume records: 0. Indexed real-world records: 0.** The repository exposes a local authenticated importer but contains no copied benchmark resumes. No gated conditions were accepted on the user's behalf.

CC BY 4.0 permits reuse and adaptation with attribution and indication of changes, subject to its terms. It does not itself supply privacy, publicity, or third-party rights. Publisher access conditions must also be reviewed by the account holder. MatchMind does not claim to have independently verified those rights for inaccessible records. Before any import, verify your permitted use on the publisher page and obtain access. The pipeline admits only publisher-labeled `real-anonymized` entries and retains source-record references and the declared license.

**Not integrated:** [opensporks/resumes](https://huggingface.co/datasets/opensporks/resumes), a mirror of [Snehaan Bhawal's Kaggle resume dataset](https://www.kaggle.com/datasets/snehaanbhawal/resume-dataset). Its card declares CC0-1.0 but explicitly describes scraped LiveCareer resume examples and leaves personal/sensitive-data documentation unspecified. This audit could not establish original resume authenticity, consent, or the uploader's authority over underlying third-party content. A mirror's license label alone was insufficient verification for this project's requirements. No records from it were imported.

**Not integrated:** [capitaletech/anonymization-resumes-dataset](https://huggingface.co/datasets/capitaletech/anonymization-resumes-dataset) has an empty dataset card and includes a generated-resume split. Its licensing/provenance was not adequate for this task.

## O*NET occupational requirements — installed

Source: [official O*NET 31.0 Database](https://www.onetcenter.org/database.html).
License: [O*NET Database license](https://www.onetcenter.org/license_db.html), [CC BY 4.0](https://creativecommons.org/licenses/by/4.0/).

Includes adapted O*NET® 31.0 Database information from the U.S. Department of Labor, Employment and Training Administration (USDOL/ETA), used under CC BY 4.0. MatchMind selected and reformatted fields. USDOL/ETA has not approved, endorsed, or tested these modifications. O*NET® is a trademark of USDOL/ETA.

`onet_occupations.json` contains **1,016 occupations**, derived from:

| Official file | Source rows | Fields retained |
| --- | ---: | --- |
| occupation_data.csv | 1,016 | SOC code, title, description |
| software_skills.csv | 31,821 | Workplace Example, grouped by SOC code and deduplicated |
| task_statements.csv | 18,838 | Task, grouped by SOC code and deduplicated |

Exact download URLs, download UTC timestamp, SHA-256 checksums, byte counts, row counts, version, and changes are in the JSON manifest. Fields are grouped, not generated. No minimum skill rating or other arbitrary relevance threshold is used. The UI composes an editable occupational requirements reference from these fields. This is not an actual employer job advertisement, a resume dataset, or ground truth for recruitment suitability.

Regenerate using `python scripts/download_onet.py`. This requires internet access but no account. Download failures do not overwrite the existing processed file. No sensitive worker-level attributes or individual records are imported from O*NET.

## Private local data

`data/private/` is ignored by Git and must never be published. The importer stages minimized structured source extracts there. It drops identity fields, employer/institution names, dates, profiles, interests, and custom sections; removes known identity strings, URLs, contacts, and explicit sensitive-field lines; deduplicates; and reports actual counts. It retains skills, professional experience descriptions, degree fields, and project descriptions. Free text can still contain residual PII or sensitive proxies. Every staged record needs local human privacy review before activation. Any re-import or file edit invalidates the SHA-256 review marker.

Original PDF pagination is unavailable in structured extracts. For dataset candidates, `p.1` denotes the structured extract; source provenance explicitly says so. Reports and the inspection tool expose the original record reference. This avoids claiming that reconstructed content is an original PDF page. All retained professional statements come from source fields, with explicit redactions; none are generated by an LLM.
