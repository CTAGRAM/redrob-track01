"""The rubric scorer: turns features into a relevance score, an estimated tier,
and human-readable positives/concerns used by the reasoning generator.

The score is built additively from JD-aligned components, reduced by penalties,
then modulated by bounded location and availability factors. Honeypots and
keyword-stuffers are vetoed so they cannot reach the top.
"""

from . import behavior, features, honeypot
from .config import LOC, PENALTY, W


def score_candidate(c):
    """Return a dict with score, tier, positives, concerns, and diagnostics."""
    f = features.extract(c)
    is_hp, hp_reasons, hp_soft = honeypot.inspect(c)

    pos, neg = [], []
    s = 0.0

    # --- role ---------------------------------------------------------------
    if f["title_ai"]:
        s += W["title_ai"]; pos.append(("role", f"{f['title']} (applied-ML role)"))
    elif f["title_data_sw"]:
        s += W["title_data_sw"]; pos.append(("role", f"{f['title']} (engineering-adjacent role)"))

    # --- evidence of built systems (the decisive signal) --------------------
    if f["ship_hits"]:
        s += W["ship_evidence"] * f["ship_pts"]
        pos.append(("ship", "career describes building ranking/search/recommendation systems"))
    if f["vdb_hits"]:
        s += W["vector_db"] * f["vdb_pts"]
        pos.append(("vectordb", "embeddings / vector-search experience"))
    if f["eval_hits"]:
        s += W["ranking_eval"] * f["eval_pts"]
        pos.append(("eval", "ranking-evaluation literacy (NDCG/MRR/MAP)"))
    if f["ltr_hits"]:
        s += W["ltr"] * f["ltr_pts"]
        pos.append(("ltr", "learning-to-rank experience"))
    if f["hrtech_hits"]:
        s += W["hrtech"] * f["hrtech_pts"]

    # --- domain -------------------------------------------------------------
    if f["nlp_domain"]:
        s += W["nlp_domain"]; pos.append(("nlp", "NLP / IR domain"))

    # --- experience band ----------------------------------------------------
    yoe = f["yoe"]
    if 6 <= yoe <= 8:
        s += W["years_ideal"]; pos.append(("years", f"{yoe:.1f} yrs (ideal band)"))
    elif 5 <= yoe <= 9:
        s += W["years_band"]; pos.append(("years", f"{yoe:.1f} yrs (in range)"))
    elif 4 <= yoe < 10:
        s += W["years_band"] * 0.4

    # --- product company ----------------------------------------------------
    if f["product_company"]:
        s += W["product_company"]; pos.append(("product", "product-company career"))

    # --- corroboration / education / OSS ------------------------------------
    if f["good_assessments"] >= 2:
        s += W["assessment"]; pos.append(("assess", f"{f['good_assessments']} skill assessments >= 70"))
    if f["edu_tier1"]:
        s += W["edu_tier1"]; pos.append(("edu", "tier-1 institution"))
    if f["github_strong"]:
        s += W["github"]; pos.append(("github", f"strong GitHub activity ({f['github_score']:.0f})"))

    # --- penalties ----------------------------------------------------------
    if f["all_services"]:
        s -= PENALTY["services_only"]; neg.append("entire career at services/consulting firms")
    if f["cv_speech_only"]:
        s -= PENALTY["cv_speech_only"]; neg.append("CV/speech focus without NLP/IR")
    if f["job_hopper"]:
        s -= PENALTY["job_hopper"]; neg.append("frequent short tenures")
    if f["framework_only"]:
        s -= PENALTY["framework_only"]; neg.append("recent work leans on LLM-wrapper frameworks")
    if f["code_cold"]:
        s -= PENALTY["code_cold"]; neg.append("recent roles are lead/architect rather than hands-on")
    if yoe < 3:
        s -= PENALTY["too_junior"]; neg.append(f"only {yoe:.1f} yrs of experience")

    raw_pos = max(s, 0.0)

    # --- relevance tier estimate (for ordering sanity & reasoning tone) ------
    tier = _estimate_tier(f)

    # --- bounded modifiers --------------------------------------------------
    locf, loc_note = behavior.location_factor(c)
    relevance_high = raw_pos >= 60
    availf, avail_notes = behavior.availability_factor(c, relevance_high)
    final = raw_pos * locf * availf

    # --- vetoes: can only push DOWN, never up -------------------------------
    vetoed = None
    if is_hp:
        final = -1e9; vetoed = "honeypot"
    elif f["keyword_stuffer"]:
        final = min(final, 5.0); vetoed = "keyword_stuffer"; neg.append("AI keywords without supporting role/experience")
    elif f["all_services"]:
        final = min(final, 22.0)

    if avail_notes:
        neg.extend(avail_notes)

    return {
        "candidate_id": c["candidate_id"],
        "facts": _facts(c),
        "final": final,
        "raw": round(raw_pos, 2),
        "tier": tier,
        "loc_factor": locf,
        "loc_note": loc_note,
        "avail_factor": availf,
        "positives": pos,
        "concerns": neg,
        "is_honeypot": is_hp,
        "honeypot_reasons": hp_reasons,
        "vetoed": vetoed,
        "features": f,
    }


_RELEVANT_SKILL = jd_relevant = None  # set below


def _facts(c):
    """Pull a few real, citable specifics from the profile for varied reasoning."""
    from . import jd as _jd
    profile = c.get("profile", {})
    sig = c.get("redrob_signals", {})
    skills = c.get("skills", [])

    # a JD-relevant skill the candidate actually lists, corroborated if possible
    relevant = []
    for s in skills:
        nm = (s.get("name", "") or "")
        low = nm.lower()
        if any(k in low for k in (
            "nlp", "rank", "retriev", "search", "embedding", "recommend", "llm",
            "transformer", "bert", "elasticsearch", "faiss", "vector", "rag",
            "learning to rank", "information retrieval", "fine-tun",
        )):
            relevant.append((nm, s.get("endorsements", 0) or 0, s.get("duration_months", 0) or 0))
    relevant.sort(key=lambda x: (-(x[1]), -(x[2])))
    named_skill = relevant[0][0] if relevant else None

    # highest Redrob skill assessment, if any
    assess = sig.get("skill_assessment_scores", {}) or {}
    assessed_skill, assessed_score = None, None
    if assess:
        assessed_skill, assessed_score = max(assess.items(), key=lambda kv: kv[1] or 0)

    return {
        "company": profile.get("current_company", "") or "",
        "response_rate": sig.get("recruiter_response_rate"),
        "notice_days": sig.get("notice_period_days"),
        "named_skill": named_skill,
        "assessed_skill": assessed_skill,
        "assessed_score": assessed_score,
    }


def _estimate_tier(f):
    """Coarse 0-4 tier estimate mirroring the ground-truth definition."""
    if f["keyword_stuffer"] or f["all_services"]:
        return 1
    strong_role = f["title_ai"] or f["ship_hits"] > 0
    product = f["product_company"] or not f["all_services"]
    in_band = 5 <= f["yoe"] <= 9
    if strong_role and f["ship_hits"] > 0 and f["nlp_domain"] and product and in_band and not f["cv_speech_only"]:
        return 4
    if strong_role and (f["ship_hits"] > 0 or f["vdb_hits"] > 0) and product and not f["cv_speech_only"]:
        return 3
    if f["title_ai"] or f["title_data_sw"] or f["nlp_domain"]:
        return 2
    return 1
