# Methodology

## 1. Problem framing
The hidden ground truth is a relevance labeling function the organizers ran over 100,000 profiles, and the released job description **is its specification**. Our job is to reconstruct that function and rank to it. The score weights `0.50·NDCG@10 + 0.30·NDCG@50 + 0.15·MAP + 0.05·P@10`, so **top-10 quality dominates** — the system is tuned to put the scarce genuine fits in the first ten positions, in the right order, with zero honeypots.

## 2. What the data told us (measured over all 100K)
- **Only 0.6%** of candidates carry a real AI/ML/Data-Scientist title → genuine fits are scarce; the top-10 hinges on a handful.
- **Skills are assigned near-uniformly at random** — every skill appears ~12,000 times. Counting AI keywords is noise. This is the trap the JD warns about, and the provided sample submission demonstrates the failure (it ranks keyword-stuffing HR Managers and Accountants at the top).
- **29%** are in target metros, **34%** are in the 5–9-year band, **9.7%** have entire-career-at-services, **57%** have been inactive for 120+ days.

These shaped every weight: read built-systems evidence, not keywords; treat experience band and product-vs-services as real filters; treat availability as a gentle modifier, not a sorter.

## 3. The scoring model
A transparent additive rubric (`src/scorer.py`) over JD-aligned components (`src/config.py` weights), reduced by penalties, then modulated by two bounded modifiers, then gated.

**Positive components:** role match · shipped ranking/search/recsys evidence · vector-search experience · ranking-evaluation literacy · learning-to-rank · NLP/IR domain · 5–9-year band (6–8 ideal) · product-company career · assessment-corroborated skills · tier-1 education · strong GitHub.

**Penalties:** entire-career-at-services · CV/speech-without-NLP · job-hopping · framework-wrapper-only · code-cold senior · too junior.

**Evidence scoring** (`src/jd.py`) matches curated phrase banks against the candidate's career free-text with **saturating, diminishing returns**, so repeating a term does not inflate the score — only describing varied real work does.

**Bounded modifiers** (`src/behavior.py`):
- *Availability* — recency of last activity, recruiter response rate, open-to-work, interview completion — combined into a multiplier clamped to [0.86, 1.06]. Sentinels (`-1` GitHub / offer rate) are treated as neutral, never zero. A relevance-gated floor keeps strong-but-quiet candidates from being buried.
- *Location* — Pune/Noida/metros = full; willing-to-relocate neutralizes the non-metro/abroad penalty; outside-India is reduced but not excluded (the JD says "case-by-case").

## 4. Honeypot defense (`src/honeypot.py`)
A top-100 honeypot rate above 10% is an instant disqualification. We detect the ~80 "subtly impossible" profiles via arithmetic impossibilities — a role claiming more months than its calendar window allows, "expert" proficiency in 3+ skills with 0 months used, a skill used longer than the entire career, reversed/future dates. The **hard gate fires only on egregious, unambiguous violations** and excludes those candidates before ranking; milder anomalies are surfaced but never ban a candidate, so legitimate people are not collaterally removed. `rank.py` re-checks the final top-100 and exits non-zero if any honeypot survived.

## 5. Reasoning generation (`src/reasoning.py`)
Each ranked candidate gets a 1–2 sentence justification filled **only** from real profile facts and computed features — current title, years, current company, a JD-relevant assessed-skill score, the decisive evidence axes, and an honest concern when one exists. Wording is selected from several structures, seeded deterministically by candidate id and which axes fired, so rows are substantively different and the tone is consistent with the rank. Nothing is hallucinated because every slot is a real field.

## 6. Calibration
Raw scores are sorted; the CSV `score` column is a strictly-decreasing display value in [0.20, 0.99]. This guarantees the validator's monotonicity rule and removes any score-tie ambiguity. Ties in raw score are broken by `candidate_id` ascending (matching the validator's tie rule).

## 7. Why a transparent engine (and where ML extends it)
Given the CPU / 5-minute / no-network constraint, a deterministic rule-based + lexical-semantic engine is the most reliable, auditable, and reproducible choice — it has no dependencies, runs in ~18 seconds, and every decision can be explained at interview. The natural extension (documented for the roadmap) is to add precomputed sentence embeddings for semantic similarity and distill an offline LLM-judge into a LightGBM LambdaMART ranker, fused with this rubric under the same honeypot gate — gaining recall on buzzword-free candidates while keeping the runtime CPU-only. The transparent engine is the dependable core that this would build on.

## 8. Results snapshot
The top-100 is composed entirely of genuine AI/ML roles (Senior ML / Search / Applied-ML / NLP Engineers, Data Scientists, Applied Scientists), the large majority in the 5–9-year band and in target metros, with **zero honeypots**. The keyword-stuffer archetype (non-technical title with many AI skills but no built systems) is vetoed out of contention by construction.
