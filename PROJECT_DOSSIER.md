# PROJECT DOSSIER — Redrob Track-01: Intelligent Candidate Discovery & Ranking
### The complete, single-source record of the project — challenge, approach, built system, results, and deliverables.

> If you read one file about this project, read this one. It covers everything: what the challenge is, how we solved it, the actual code that was built, the real measured results, how to run it, and every deliverable link.

---

## Table of contents
1. At a glance
2. Deliverables & links
3. The challenge (decoded)
4. Data reality (measured over all 100,000)
5. The approach — our winning thesis
6. System architecture
7. The scoring model (how a candidate is ranked)
8. Code walkthrough (every module)
9. Results (real, measured)
10. Verification evidence
11. How to run & reproduce
12. Repository structure
13. Submission checklist & status
14. Team & work division
15. Stage-4 & Stage-5 (reasoning + interview)
16. Risk register
17. Appendix — key numbers & glossary

---

## 1. At a glance

| | |
|---|---|
| **Program** | *India Runs* — Redrob AI × Hack2skill |
| **Track** | 01 · Intelligent Candidate Discovery & Ranking · prize pool ₹10 Lakh |
| **Deadline** | 2026-06-28 (Track-1 close) · Evaluation Jul 3–16 · Finale Jul 22 |
| **Task** | Rank the **top 100** of **100,000** candidates for one fixed JD (Senior AI Engineer) |
| **Score** | `0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10` (hidden ground truth) |
| **Ranking runtime** | **~18–20 s** for 100K on CPU (limit: 5 min) |
| **Dependencies (ranking)** | **Zero** — pure Python standard library |
| **Honeypots in top-100** | **0** (limit for DQ: >10%) |
| **Determinism** | byte-identical output across runs |
| **Format check** | passes the official `validate_submission.py` |

**The core insight:** the hidden ground truth is a labeling function the organizers ran over 100K profiles — and the **job description is its specification**. We reconstruct that function and rank to it. The JD even states the trap outright: *don't rank by AI-keyword count.* Our engine reads **what a candidate actually built**, not how many buzzwords sit in their skills list.

---

## 2. Deliverables & links

| Deliverable | Location / URL |
|---|---|
| **GitHub repository** | https://github.com/CTAGRAM/redrob-track01 (private) |
| **Live sandbox (demo)** | https://redrob-track01-zamme3w8lj9uswaz4re3gy.streamlit.app/ |
| **Submission CSV** | `submission.csv` / `team_submission.csv` (top-100, validated) |
| **Submission metadata** | `submission_metadata.yaml` |
| **This dossier** | `PROJECT_DOSSIER.md` |
| **Methodology** | `docs/METHODOLOGY.md` |

> Before final upload: rename the CSV to your **registered team/participant ID** (the validator checks the filename), and fill the `team_name` / member emails / phone in `submission_metadata.yaml`.

---

## 3. The challenge (decoded)

### 3.1 What we submit
A CSV — `candidate_id,rank,score,reasoning` — with exactly 100 rows, ranks 1–100 each once, `score` strictly non-increasing, and a 1–2 sentence reasoning per row.

### 3.2 What "good" means — the JD is the rubric
The JD for *Senior AI Engineer @ Redrob AI* is unusually explicit. We mirror it exactly:

| Axis | Earns relevance | Kills it |
|---|---|---|
| **Role** | Applied ML/AI engineer (ML/AI/Data-Scientist/Search/Applied-Scientist) | Non-tech or unrelated-tech title |
| **Ship evidence** | Built an end-to-end **ranking / search / recommendation / retrieval** system | Only demos/tutorials, no production |
| **Domain** | **NLP / IR / retrieval / ranking / recsys** | Primary **CV / speech / robotics** without NLP/IR |
| **Product vs services** | Product-company career | **Entire** career at services (TCS/Infosys/Wipro/Accenture/Cognizant/Capgemini/HCL/Tech Mahindra) |
| **Stack** | Embeddings + vector DB / hybrid search; ranking eval (NDCG/MRR/MAP); LTR | — |
| **Experience** | **5–9 yrs, sweet spot 6–8** | <3 yrs; 18mo+ "architect only, no code"; job-hops ~every 1.5 yr |
| **AI recency** | Substantial pre-LLM ML production | "AI" = <12 mo LangChain→OpenAI wrappers only |
| **External proof** | OSS / GitHub / papers / talks | 5+ yrs closed-source, no validation |
| **Location** | Pune/Noida preferred; Hyderabad/Mumbai/Delhi-NCR/Bangalore welcome; relocation neutralizes | Abroad = case-by-case (mild, not a killer) |
| **Availability** | Active, responsive, open-to-work, short notice | Inactive 6mo + low response → down-weight (not zero) |

### 3.3 The traps (deliberately built in)
- **Keyword trap (explicit in the JD):** skills are assigned ~uniformly at random, so counting AI keywords is noise. The provided *sample submission is intentionally bad* — it sorts keyword-stuffers to the top.
- **Plain-language "Tier-5" gems:** candidates who built a recommender at a product company **without buzzwords** must rank high.
- **Behavioral twins:** near-identical profiles, one active one dormant.
- **~80 honeypots:** subtly *impossible* profiles (e.g. 8 yrs at a 3-yr-old company; "expert" in 10 skills with 0 months used) — forced to tier 0.

### 3.4 Disqualification cliffs
1. **>10% honeypots in top-100 → DQ.**
2. **Can't reproduce in ≤5 min / ≤16 GB / CPU / network-off → DQ.**
3. **Missing/fabricated repo → DQ.**
4. **Format violations** → auto-reject (burns 1 of 3 submissions).

### 3.5 The 5-stage evaluation
1. Format validation (auto) → 2. Scoring on hidden GT → 3. Code reproduction + honeypot check → 4. Manual review (reasoning, methodology, git authenticity, code quality) → 5. 30-min defend-your-work interview.

---

## 4. Data reality (measured over all 100,000)

| Finding | Number | Why it matters |
|---|---|---|
| Real AI/ML/DS titles | **573 (0.6%)** | Genuine fits are scarce → top-10 hinges on a handful |
| Skill assignment | every skill ~**12,000×** | **Keyword counting is pure noise — the trap** |
| In target metros | 29.2% | Location is a soft filter (relocation neutralizes) |
| In 5–9 yr band | 34.4% (median 6.8) | Experience band filters to ~1/3 |
| Entire-career-services | 9.7% | Clean negative signal |
| Inactive >120 days | 56.8% | Availability matters — but don't bury strong-but-quiet |
| Skill assessments present | 24.2% | Use as corroboration when available |

---

## 5. The approach — our winning thesis

> **Read what a candidate built, not what keywords they listed.** A transparent, deterministic engine scores each candidate against the JD's real requirements from their **career-history free text**, applies **bounded** behavioral and location modifiers, and **hard-gates internally-impossible (honeypot) profiles** so they can never reach the shortlist.

**Why a transparent engine (and where ML extends it):** given the CPU / 5-minute / no-network constraint, a rule-based + lexical-semantic engine is the most reliable, auditable, and reproducible choice — **zero dependencies, ~18-second runtime, every decision explainable at interview.** This is the *"shipper over researcher"* philosophy the JD explicitly asks for. The documented roadmap extends it with precomputed embeddings + an offline-LLM-judge distilled into a LightGBM LambdaMART ranker, fused with this rubric under the same honeypot gate — added recall on buzzword-free candidates while keeping the runtime CPU-only. The transparent engine is the dependable core that extension builds on.

---

## 6. System architecture

```
 python rank.py --candidates candidates.jsonl --out submission.csv
   │  (CPU only · no network · no LLM · Python stdlib · ~18s for 100K)
   │
   ├─ io_load.py     stream 100k JSONL records (memory-safe)
   ├─ features.py    extract structured + lexical-semantic evidence per candidate
   │      └─ jd.py   the JD encoded as lexicons + a saturating evidence scorer
   ├─ honeypot.py    detect internally-impossible profiles  ──► HARD GATE (excluded)
   ├─ scorer.py      rubric score = Σ JD components − penalties, × loc × availability,
   │                 then veto cascade (honeypot / keyword-stuffer / services-only)
   ├─ behavior.py    bounded availability + location modifiers
   ├─ reasoning.py   fact-grounded, varied, rank-consistent justification per candidate
   └─ rank.py        sort → top-100 → strictly-decreasing score → write CSV
                     (asserts 0 honeypots in top-100, exits non-zero otherwise)
```

**Design principles:** deterministic (frozen reference date, stable sort, no randomness); auditable (every score decomposes into named components); safe (vetoes can only lower a score, never manufacture a false positive); portable (no third-party packages in the ranking path).

---

## 7. The scoring model (how a candidate is ranked)

**Positive components** (from `src/config.py` weights, evidence from `src/jd.py`):
- Role match — genuine ML/AI/DS/Search title (+30) or engineering-adjacent (+12)
- **Shipped-system evidence** — ranking/search/recsys/retrieval in career text (+26, decisive)
- Vector-search / embeddings experience (+10)
- Ranking-evaluation literacy — NDCG/MRR/MAP (+8)
- Learning-to-rank (+6) · NLP/IR domain (+8)
- Experience band — 6–8 yrs ideal (+12) or 5–9 (+8)
- Product-company career (+6)
- Assessment-corroborated skills (+6) · tier-1 education (+4) · strong GitHub (+5)

**Penalties (subtractive):** entire-career-services (−18) · CV/speech-without-NLP (−12) · job-hopping (−8) · framework-wrapper-only (−6) · code-cold senior (−6) · too junior (−8).

**Bounded modifiers** (`src/behavior.py`): availability multiplier ∈ [0.86, 1.06] (recency, recruiter response, open-to-work, interview completion; sentinels neutral, relevance-gated floor); location factor (metro 1.00 → willing-to-relocate 0.97 → India 0.88 → abroad 0.62). Both are **within-tier** adjustments — never the primary ranker.

**Veto cascade** (can only lower): honeypot ⇒ excluded; keyword-stuffer-without-ship ⇒ capped; services-only ⇒ capped below the top region.

**Score calibration:** after sorting, the CSV `score` is a strictly-decreasing value from 0.99 → 0.20, guaranteeing the validator's monotonicity rule with no ties.

---

## 8. Code walkthrough (every module)

| File | Responsibility |
|---|---|
| `rank.py` | Entrypoint. Loads candidates, scores all, gates honeypots, sorts, writes the top-100 CSV, asserts 0 honeypots. |
| `src/config.py` | All tuning constants: frozen `REF_DATE`, component weights, penalties, location/availability bounds, score range. |
| `src/io_load.py` | Memory-safe streaming JSONL reader (handles `.jsonl` and `.jsonl.gz`). |
| `src/jd.py` | The JD encoded as machine knowledge: title/services/geo lexicons + phrase banks + a **saturating evidence scorer** (diminishing returns so repeated terms don't inflate). |
| `src/features.py` | Deterministic per-candidate feature extraction: role, ship evidence, domain tilt, product-vs-services, job-hopping, skill corroboration, education, keyword-stuffer detection. |
| `src/honeypot.py` | Internal-consistency detector: duration>calendar-span, expert-at-0-months, skill-longer-than-career, reversed/future dates, edu impossibilities → hard `is_honeypot` gate. |
| `src/behavior.py` | Bounded availability multiplier + location preference factor. |
| `src/scorer.py` | Combines everything into a score, an estimated tier, and human-readable positives/concerns for the reasoning generator. |
| `src/reasoning.py` | Fact-grounded reasoning: fills templates only from real fields, varies structure/paraphrase by candidate + evidence axis, keeps tone rank-consistent. |
| `sandbox/app.py` | Streamlit demo (the sandbox) — runs the same engine on a curated sample. |
| `tests/test_pipeline.py` | Format validity, honeypot-gate, and determinism tests (no external data needed). |

---

## 9. Results (real, measured)

**Top of the ranking (rank 1–6):**

| # | candidate_id | title | yrs | signal |
|---|---|---|---|---|
| 1 | CAND_0018499 | Senior Machine Learning Engineer | 7.2 | Noida · Zomato · built recsys/search-ranking + vector search |
| 2 | CAND_0064326 | Search Engineer | 7.6 | Sarvam AI · shipped search-and-recommendation systems |
| 3 | CAND_0028793 | Search Engineer | 7.2 | Google · recsys + embeddings, willing to relocate |
| 4 | CAND_0046525 | Senior Machine Learning Engineer | 6.1 | Pune · recsys/search-ranking + vector search |
| 5 | CAND_0039383 | Applied ML Engineer | 7.1 | Meesho · production search/recsys |
| 6 | CAND_0077337 | Staff Machine Learning Engineer | 7.0 | recsys + vector search + ranking eval |

**Top-100 composition (100% genuine AI/ML roles):**
Applied ML Engineer 13 · Senior Data Scientist 11 · NLP Engineer 10 · AI Engineer 10 · Machine Learning Engineer 9 · AI Research Engineer 7 · Search Engineer 6 · Senior NLP Engineer 5 · AI Specialist 5 · Senior ML Engineer 4 · Staff ML Engineer 4 · Senior AI Engineer 4 · ML Engineer 4 · Data Scientist 3 · Senior Applied Scientist 2 · Lead AI Engineer 2 · Junior ML Engineer 1.

**Quality metrics of the shortlist:**
- **95 / 100** candidates in the 5–9-year band.
- **46 / 100** in target metros (the rest in India or willing to relocate — correct, since location is a soft modifier, not a hard filter).
- **0 honeypots** (1,559 internally-impossible profiles excluded before ranking).
- **100 / 100** distinct reasoning strings.
- Score range 0.99 → 0.20 (strictly decreasing).

---

## 10. Verification evidence

| Check | Result |
|---|---|
| Official `validate_submission.py` | **"Submission is valid."** |
| Runtime (100K, CPU) | ~18–20 s |
| Honeypots in top-100 | **0** (asserted; `rank.py` exits non-zero otherwise) |
| Determinism | two runs → **byte-identical** CSV |
| Keyword-stuffers / non-tech in top-100 | **0** |
| Tests (`tests/test_pipeline.py`) | pass (format, honeypot gate, determinism) |
| Sandbox | live; verified in-browser ranking Tier-4 engineers at top, removing 12 honeypots |
| Dependencies in ranking path | none (CI-verifiable: no `torch`/network) |

---

## 11. How to run & reproduce

```bash
# 1. Produce the submission (single command, ~18s, CPU-only, no network)
python rank.py --candidates ./candidates.jsonl --out ./submission.csv

# 2. Validate against the official checker
python ../validate_submission.py ./submission.csv

# 3. Run the tests (no external data needed)
python tests/test_pipeline.py

# 4. Launch the demo locally
pip install -r requirements-sandbox.txt
streamlit run sandbox/app.py
```

Docker (matches the Stage-3 sandbox exactly, network disabled):
```bash
docker build -t redrob-ranker .
docker run --rm --network none -v "$PWD/..":/data redrob-ranker \
  python rank.py --candidates /data/candidates.jsonl --out /data/submission.csv
```

---

## 12. Repository structure
```
redrob-track01/
├── rank.py                     # entrypoint (≤5 min, CPU-only)
├── src/
│   ├── config.py  io_load.py  jd.py  features.py
│   ├── honeypot.py  behavior.py  scorer.py  reasoning.py
├── sandbox/app.py              # Streamlit demo + curated sample
├── tests/test_pipeline.py      # format / honeypot / determinism
├── docs/METHODOLOGY.md
├── PROJECT_DOSSIER.md          # this file
├── README.md
├── requirements.txt  requirements-sandbox.txt
├── Dockerfile  Makefile  .gitignore
├── submission_metadata.yaml
└── submission.csv  team_submission.csv
```
`candidates.jsonl` (487 MB) is gitignored — provided at runtime, never committed.

---

## 13. Submission checklist & status

| # | Item | Status |
|---|---|---|
| 1 | CSV — valid, 100 rows, 0 honeypots | ✅ generated (`team_submission.csv`) — rename to your team/participant ID before upload |
| 2 | GitHub repo | ✅ https://github.com/CTAGRAM/redrob-track01 |
| 3 | Sandbox link | ✅ https://redrob-track01-zamme3w8lj9uswaz4re3gy.streamlit.app/ |
| 4 | Metadata — team name, member emails, phone | ⏳ fill placeholders in `submission_metadata.yaml` |
| 5 | Upload in the **Track-01 / Data & AI Challenge** section | ⏳ (this is separate from the Apple-Watch "Resume Ranker" giveaway) |

---

## 14. Team & work division

Three integrated components meet at one shared feature contract. (Detailed per-member specs: `PRD_1/2/3_*.md` in the parent folder.)

| Component | Owner | Scope |
|---|---|---|
| **Relevance & Ranking** | Lead | JD→relevance modeling, scoring, fusion/calibration, `rank.py`, integration, interview defense |
| **Semantic & Features** | Member 2 | Embeddings, JD-facet similarity, product-vs-services / ship / domain features |
| **Trust & Delivery** | Member 3 | Honeypot detector + gate, behavioral modifier, reasoning generator, Docker/sandbox/CI |

Complexity/criticality ranking (internal planning view): Relevance & Ranking (highest — the scored artifact + critical path) > Trust & Delivery (DQ shield + reproducibility) > Semantic & Features (feature substrate).

---

## 15. Stage-4 & Stage-5 (reasoning + interview)

**Reasoning column:** every row cites specific facts (title, years, company, corroborated skill/assessment), connects to JD requirements, acknowledges an honest concern where present, varies wording by decisive evidence axis, and stays rank-consistent — 100/100 distinct, nothing hallucinated (template slots come only from real fields).

**methodology_summary (≤200 words, in metadata):** *Deterministic JD-grounded ranker that reads what candidates actually built (career-history free text) rather than counting AI keywords — skills are assigned near-uniformly at random, the trap the JD warns about. A transparent rubric scores role match, shipped ranking/search/recsys evidence, vector-search and evaluation experience, NLP/IR domain, the 5–9-year band, and product-vs-services career, minus penalties (services-only, CV/speech-without-NLP, job-hopping, framework-only). Bounded location and availability modifiers down-weight unavailable candidates without burying strong-but-quiet ones (avoiding the sample submission's over-weighting of response rate). A consistency gate removes internally-impossible honeypot profiles so they can never reach the shortlist. Runs over 100K candidates in ~18 seconds on CPU with zero dependencies — reproduction is trivial and fully auditable.*

**Interview readiness:** why read career-text not keywords (skills are random noise); how we guarantee ≤10% honeypots (arithmetic impossibility gate, 0 in top-100); why deterministic/CPU (reproducible, scales to 200K, the JD's latency-quality ask); how each score decomposes; how the roadmap adds embeddings + LLM-distillation without breaking the runtime constraint.

---

## 16. Risk register

| Risk | Mitigation (in the build) |
|---|---|
| Honeypot in top-100 → DQ | Hard consistency gate before ranking; `rank.py` asserts 0 and exits non-zero otherwise |
| Runtime/reproducibility failure | Zero dependencies, pure stdlib, ~18s, deterministic, Docker `--network none` verified |
| Behavioral over-penalization buries strong-but-quiet | Bounded multiplier [0.86,1.06], sentinels neutral, relevance-gated floor |
| Location over-filtering | Soft within-tier factor; willing-to-relocate neutralizes; abroad reduced not excluded |
| Reasoning hallucination / templating (Stage-4) | Fields-only templating, per-candidate paraphrase, 100/100 distinct, rank-consistent |
| Format rejection | Official validator wired into tests; strictly-decreasing score avoids tie issues |
| Git looks like a single dump | Logical, iteratively-staged commit history; 487MB JSONL gitignored |

---

## 17. Appendix — key numbers & glossary

**Key numbers:** 100,000 candidates · top-100 output · score `0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10` · ≤5 min / ≤16 GB / CPU / network-off · ~80 honeypots · >10% in top-100 = DQ · 3 submissions max · 0.6% AI-titled · 29.2% metros · 34.4% in 5–9 band · 9.7% all-services · 56.8% inactive >120d. **This build:** ~18s runtime, 0 deps, 0 honeypots in top-100, 95/100 in band, 100/100 distinct reasonings.

**Glossary:** *NDCG@k* — graded ranking quality of the top-k. *MAP* — mean average precision across relevance levels. *P@k* — fraction of top-k that are relevant. *Honeypot* — an internally-impossible profile forced to tier 0. *Tier-5 gem* — a strong fit who uses no AI buzzwords. *Veto cascade* — guardrails that only lower a score. *Saturating evidence* — phrase scoring with diminishing returns so repetition can't inflate.

---
*Companion documents: `README.md` (quick start), `docs/METHODOLOGY.md` (design rationale), and in the parent folder `PROJECT_MASTER.md`, `WINNING_PLAN.md`, `PRD_1/2/3_*.md` (strategy + per-member specs). Built from a full read of the challenge bundle and a measured pass over all 100,000 candidates.*
