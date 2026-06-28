"""Central configuration: the single place tuning constants live.

Everything here is deterministic. The ranking step performs no I/O beyond
reading the candidates file and writing the CSV, makes no network calls, and
uses only the Python standard library.
"""

import datetime as dt

# Frozen reference date for all recency / availability math. Never use
# datetime.now() anywhere in the ranking path — it would make the output
# non-reproducible and break the Stage-3 reproduction check.
# The dataset's latest last_active_date is ~2026-05-20, so this is a sane "today".
REF_DATE = dt.date(2026, 6, 1)

TOP_N = 100  # we rank exactly the top 100 candidates

# --- Scoring weights (rubric components) -------------------------------------
# These mirror the job description's stated requirements. Each is the maximum
# points that component can contribute before modifiers/vetoes.
W = {
    "title_ai": 30.0,         # current/recent title is a genuine ML/AI/DS role
    "title_data_sw": 12.0,    # data / software engineering adjacent title
    "ship_evidence": 26.0,    # built a ranking/search/recsys/retrieval system (career text)
    "vector_db": 10.0,        # vector DB / embeddings / hybrid search experience
    "ranking_eval": 8.0,      # ranking evaluation literacy (NDCG/MRR/MAP/AB)
    "nlp_domain": 8.0,        # NLP / IR domain
    "ltr": 6.0,               # learning-to-rank (XGBoost / neural)
    "years_ideal": 12.0,      # 6-8 years sweet spot
    "years_band": 8.0,        # 5-9 years band
    "product_company": 6.0,   # career at product companies (not services-only)
    "assessment": 6.0,        # Redrob skill assessments corroborate claimed skills
    "edu_tier1": 4.0,         # tier-1 institution
    "github": 5.0,            # strong external/open-source validation
    "hrtech": 4.0,            # recruiting / marketplace / HR-tech exposure
}

# --- Penalties (subtractive) -------------------------------------------------
PENALTY = {
    "services_only": 18.0,    # entire career at services/consulting firms
    "cv_speech_only": 12.0,   # CV/speech/robotics primary, no NLP/IR
    "job_hopper": 8.0,        # title-chasing / very short tenures
    "framework_only": 6.0,    # shallow recent LangChain-wrapper-only profile
    "code_cold": 6.0,         # senior who hasn't been an IC recently
    "too_junior": 8.0,        # < 3 years of experience
}

# --- Location preference (within-tier modifier, bounded) ---------------------
# Multiplicative factor on the positive score. Location never demotes across a
# tier on its own; willing_to_relocate neutralizes the non-metro penalty.
LOC = {
    "metro": 1.00,            # Pune / Noida / Hyderabad / Mumbai / Delhi-NCR / Bangalore
    "india_relocate": 0.97,
    "india": 0.88,
    "abroad_relocate": 0.78,  # JD: outside India is "case-by-case", not excluded
    "abroad": 0.62,
}

# Availability modifier bounds — keeps behavioral signals as a *modifier*, not a
# primary ranker (avoids the sample submission's failure of sorting by response rate).
AVAIL_MIN, AVAIL_MAX = 0.86, 1.06

# Display score range for the CSV (strictly decreasing, in-range, collision-proof).
SCORE_HI, SCORE_LO = 0.990, 0.200
