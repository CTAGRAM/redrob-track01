# Redrob Track-01 — Intelligent Candidate Ranking

A fast, deterministic, fully-auditable system that ranks the **top-100 candidates** from a 100,000-profile pool for the released *Senior AI Engineer* job description.

> **Reproduce the submission (single command):**
> ```bash
> python rank.py --candidates ./candidates.jsonl --out ./submission.csv
> ```
> Runs in **~18 seconds on CPU**, **no network**, **no GPU**, **zero third-party dependencies** (Python 3.9+ standard library only). Output passes the official `validate_submission.py`.

---

## Why this approach

The job description states the trap outright: *"the right answer is NOT to find candidates whose skills section contains the most AI keywords."* Our analysis of the pool confirms it — **every skill appears ~12,000 times**, assigned near-uniformly at random, so keyword counting is pure noise.

So the engine **reads what a candidate actually built** — the free-text descriptions in their career history — and scores that against the JD's real requirements:

- **Role match** — genuine ML/AI/Data-Scientist/Search/Applied-Scientist roles.
- **Shipped-system evidence** — did they build a **ranking / search / recommendation / retrieval** system? (the decisive signal)
- **Vector-search & evaluation** — embeddings/vector-DB experience and ranking-eval literacy (NDCG/MRR/MAP).
- **Domain** — NLP/IR (rewarded) vs CV/speech/robotics-only (penalized).
- **Experience** — the 5–9-year band, sweet spot 6–8.
- **Product vs services** — entire-career-at-services is a JD-stated negative.
- **Corroboration** — Redrob skill assessments back up claimed skills.

Then two **bounded modifiers** apply — **availability** (recency, recruiter response, open-to-work) and **location** (Pune/Noida/metros preferred; willing-to-relocate neutralizes) — as gentle adjustments, never the primary ranker. Finally a **consistency gate** removes internally-impossible "honeypot" profiles (e.g. more months in a role than the calendar allows) so they can never reach the shortlist.

This is the **"shipper over researcher"** philosophy the JD asks for: a system that has thought about the latency–quality tradeoff and scales to a 200K production pool, not one that calls an LLM per candidate.

## What's in here

```
rank.py                 # entrypoint — produces submission.csv
src/
  config.py             # tunable weights, frozen reference date, score range
  io_load.py            # memory-safe streaming JSONL reader
  jd.py                 # the JD encoded as lexicons + evidence scorer
  features.py           # deterministic feature extraction
  honeypot.py           # internal-consistency detector + hard gate
  behavior.py           # bounded availability + location modifiers
  scorer.py             # rubric scoring, tier estimate, positives/concerns
  reasoning.py          # fact-grounded, varied, rank-consistent justifications
sandbox/app.py          # interactive Streamlit demo (the sandbox)
tests/test_pipeline.py  # format validity, honeypot gate, determinism
docs/METHODOLOGY.md     # full write-up
Dockerfile  Makefile  requirements*.txt  submission_metadata.yaml
```

## Run it

```bash
# 1. Produce the submission
python rank.py --candidates ./candidates.jsonl --out ./submission.csv

# 2. Validate against the official checker
python ../validate_submission.py ./submission.csv

# 3. Run the tests (no external data needed)
python tests/test_pipeline.py

# 4. Launch the interactive demo
pip install -r requirements-sandbox.txt
streamlit run sandbox/app.py
```

Or via Docker (matches the Stage-3 sandbox exactly, network disabled):

```bash
docker build -t redrob-ranker .
docker run --rm --network none -v "$PWD/..":/data redrob-ranker \
  python rank.py --candidates /data/candidates.jsonl --out /data/submission.csv
```

## Guarantees (how we avoid disqualification)

| Constraint | This system |
|---|---|
| ≤5 min, CPU-only | ~18 s on CPU for 100K |
| ≤16 GB RAM | streams the file; tiny footprint |
| No network / no hosted LLM at ranking | none — pure standard library |
| 0 honeypots in top-100 | hard consistency gate; verified each run (exits non-zero otherwise) |
| Deterministic / reproducible | frozen reference date, stable sort, no randomness — byte-identical output |
| Valid format | passes the official `validate_submission.py` |

See `docs/METHODOLOGY.md` for the full design rationale and the data analysis behind it.
