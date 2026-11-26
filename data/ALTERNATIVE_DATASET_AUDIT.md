# Alternative resume dataset audit — 24 November 2026

## Outcome

No suitable replacement was verified among the four alternatives checked in this bounded search. **Imported records: 0. Indexed replacement records: 0.** No candidate text was persisted, no original source evidence was fabricated, and no real-world retrieval metrics were produced. PDF uploads, the existing MiniLM/FAISS pipeline, O*NET references, and the optional explicitly synthetic fixtures remain available.

ResumeBench was not retried. Its previously observed HTTP 401 remains the documented blocker. This audit does not claim that no suitable dataset exists anywhere; the sources below did not satisfy the combined authenticity, licensing, and access requirements.

## Sources checked

| Source | License/access evidence | Authenticity evidence and decision |
| --- | --- | --- |
| [datasetmaster/resumes](https://huggingface.co/datasets/datasetmaster/resumes) | Publisher metadata and card declare MIT; `gated: false`. A direct unauthenticated range GET of the pinned `master_resumes.jsonl` returned HTTP **206**, with 1,024 initial bytes received. | Card explicitly says the dataset merges submitted real CVs with Faker-generated synthetic resumes. Its documented record schema does not establish a reliable source-level real/synthetic discriminator or traceability to original submissions. Do not guess which records are genuine from style or content. **Rejected: a genuine-only subset could not be verified.** |
| [TechWolf/anonymous-working-histories](https://huggingface.co/datasets/TechWolf/anonymous-working-histories) | Publisher card declares CC BY 4.0; `gated: false`. A direct unauthenticated range GET of pinned `test.csv` returned HTTP **206**, with 1,024 initial bytes received. | The authors' paper documents derivation from Kaggle/LiveCareer resumes, then **GPT-3.5 rewriting** of the experience sections before structured extraction (§3.1, page 3). These are real-resume-derived career histories, not untouched original resume text. They omit education/projects/skills sections and do not resolve the underlying third-party rights questions already noted for the scraped source. **Rejected for this request: cannot present rewritten text as original, non-LLM-generated resume evidence.** |
| [MikePfunk28/resume-training-dataset](https://huggingface.co/datasets/MikePfunk28/resume-training-dataset) | Card/API declare MIT, but current metadata reports `gated: auto`, and the page requires agreeing to access conditions. No gated file download attempted. | Card describes curated resume examples and feedback conversations; it does not sufficiently establish a genuine-only resume subset with original-document traceability. **Rejected: gated and insufficient authenticity evidence.** |
| [OpenResume on Zenodo](https://zenodo.org/records/14726170) | Official record is labeled **Restricted**. No access request submitted and no restricted file download attempted. | Research project describes both anonymized real-derived and synthetic data. **Not integrated: required direct public access is unavailable.** |

License labels are recorded as publisher declarations, not as independent proof of all underlying copyright or privacy rights. No permissions were inferred from unauthenticated download access alone. Mixed/synthetic data was not silently substituted into the real-world source selector.

## Reproducible access references

No credentials were used in these checks. Metadata was fetched once for the three Hugging Face candidates; no gated authentication attempts or repeated inaccessible-source retries were performed.

- datasetmaster revision: `3a53af8a0ac0eb7a6a0d83aca29d6e3fc103c446`
- [Pinned file](https://huggingface.co/datasets/datasetmaster/resumes/resolve/3a53af8a0ac0eb7a6a0d83aca29d6e3fc103c446/master_resumes.jsonl)
- TechWolf revision: `300f78901132de9c388e8b4101d84d148f9ba65a`
- [Pinned file](https://huggingface.co/datasets/TechWolf/anonymous-working-histories/resolve/300f78901132de9c388e8b4101d84d148f9ba65a/test.csv)
- MikePfunk28 metadata revision: `bd167fcb1dc281707c8ca7a2d4aa822f63650d74`
- [TechWolf primary paper, §3.1](https://ceur-ws.org/Vol-3490/RecSysHR2023-paper_1.pdf)

The TechWolf card's `pretty_name` says “Synthetic ESCO skill sentences,” while its title/body describe anonymous career histories. The paper provides the more specific construction account, including LLM rewriting; the ambiguous metadata was not used as evidence that the records were original resumes.

## Application behavior and verification

No importer, source-selector, matching, agent, or privacy code was changed for an unverified replacement. The existing real-dataset source remains unavailable unless an authorized, locally reviewed ResumeBench import is activated. Uploads remain the usable path for real documents you are authorized to process. No resume subset was downloaded for retention, indexed, or made visible in the UI during this audit.

Consequently, semantic retrieval **with imported replacement records could not be tested**. This limitation is distinct from the existing MiniLM/FAISS engineering tests and synthetic smoke checks. No new dataset-quality or hiring-quality result is claimed.
