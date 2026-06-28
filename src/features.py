"""Deterministic feature extraction from a candidate record.

Pulls structured signals (experience, product-vs-services, domain, job-hopping,
skill corroboration, education) and lexical-semantic evidence of what the person
actually built. Pure functions of the input — same input always yields the same
features.
"""

import re

from . import jd

_AI_SKILL = re.compile(
    r"(nlp|llm|fine-?tun|lora|rag|embedding|transformer|bert|gan|tts|speech|"
    r"image classif|pytorch|tensorflow|deep learning|recommend|ranking|retrieval)",
    re.I,
)


def extract(c):
    profile = c.get("profile", {})
    sig = c.get("redrob_signals", {})
    career = c.get("career_history", [])
    skills = c.get("skills", [])
    text = jd.candidate_text(c)

    title = profile.get("current_title", "") or ""
    yoe = profile.get("years_of_experience", 0) or 0

    f = {}
    f["title"] = title
    f["yoe"] = yoe
    f["text"] = text

    # role match
    f["title_ai"] = bool(jd.AI_TITLE.search(title))
    f["title_data_sw"] = bool(jd.DATA_SW_TITLE.search(title))
    f["title_lead"] = bool(jd.LEAD_TITLE.search(title))

    # lexical-semantic evidence of built systems
    f["ship_pts"], f["ship_hits"] = jd.evidence(text, jd.SHIP_PHRASES, 1.0)
    f["vdb_pts"], f["vdb_hits"] = jd.evidence(text, jd.VECTORDB_PHRASES, 1.0)
    f["eval_pts"], f["eval_hits"] = jd.evidence(text, jd.EVAL_PHRASES, 1.0)
    f["nlp_pts"], f["nlp_hits"] = jd.evidence(text, jd.NLP_PHRASES, 1.0)
    f["cv_pts"], f["cv_hits"] = jd.evidence(text, jd.CV_SPEECH_PHRASES, 1.0)
    f["ltr_pts"], f["ltr_hits"] = jd.evidence(text, jd.LTR_PHRASES, 1.0)
    f["prod_pts"], f["prod_hits"] = jd.evidence(text, jd.PRODUCTION_PHRASES, 1.0)
    f["hrtech_pts"], f["hrtech_hits"] = jd.evidence(text, jd.HRTECH_PHRASES, 1.0)
    f["framework_only"] = (
        any(p in text for p in jd.FRAMEWORK_ONLY_PHRASES)
        and f["ship_hits"] == 0 and f["eval_hits"] == 0 and yoe < 6
    )
    f["shipped_system"] = f["ship_hits"] > 0

    # domain tilt
    f["nlp_domain"] = f["nlp_hits"] > 0 or f["ship_hits"] > 0
    f["cv_speech_only"] = f["cv_hits"] >= 2 and f["nlp_hits"] == 0 and f["ship_hits"] == 0

    # product vs services
    comps = [(j.get("company", "") or "").lower() for j in career]
    f["any_services"] = any(any(s in cc for s in jd.SERVICES) for cc in comps if cc)
    f["all_services"] = bool(comps) and all(
        any(s in cc for s in jd.SERVICES) for cc in comps if cc
    )
    f["product_company"] = bool(comps) and not f["any_services"]

    # job-hopping / title chasing
    past_durs = [j.get("duration_months", 0) or 0 for j in career if not j.get("is_current")]
    short = sum(1 for d in past_durs if 0 < d <= 20)
    f["job_hopper"] = len(career) >= 4 and short >= 3

    # "code-cold" senior: recent role is a lead/architect title, lots of experience
    cur = next((j for j in career if j.get("is_current")), career[0] if career else {})
    f["code_cold"] = bool(jd.LEAD_TITLE.search(cur.get("title", "") or "")) and not f["title_ai"] and yoe >= 9

    # skill corroboration via Redrob assessments (only ~24% have these)
    assess = sig.get("skill_assessment_scores", {}) or {}
    f["good_assessments"] = sum(1 for v in assess.values() if v and v >= 70)
    f["assess_present"] = bool(assess)

    # AI skills present but role weak + no built systems => keyword-stuffer
    f["ai_skill_count"] = sum(1 for s in skills if _AI_SKILL.search(s.get("name", "") or ""))
    f["keyword_stuffer"] = (
        not f["title_ai"] and f["ai_skill_count"] >= 7
        and f["ship_hits"] == 0 and f["eval_hits"] == 0 and f["vdb_hits"] == 0
    )

    # education
    tiers = [e.get("tier") for e in c.get("education", [])]
    f["edu_tier1"] = "tier_1" in tiers

    # external validation
    gh = sig.get("github_activity_score", -1)
    f["github_score"] = gh
    f["github_strong"] = gh is not None and gh >= 50

    return f
