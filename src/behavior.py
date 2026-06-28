"""Behavioral availability + location modifiers.

The JD says to down-weight perfect-on-paper candidates who are not actually
available (inactive for months, near-zero recruiter response). We model this as
a *bounded multiplier* on the relevance score — never the primary ranker. This
deliberately avoids the sample submission's failure mode of sorting candidates
by recruiter_response_rate.

Sentinels (-1 for github / offer_acceptance) are treated as neutral, never as
zero, because ~35% of candidates simply have no GitHub linked.
"""

import datetime as dt

from .config import AVAIL_MAX, AVAIL_MIN, LOC, REF_DATE
from .jd import TARGET_CITIES


def _pdate(s):
    try:
        return dt.date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def location_factor(c):
    profile = c.get("profile", {})
    sig = c.get("redrob_signals", {})
    loc = (profile.get("location", "") + " " + profile.get("country", "")).lower()
    city = profile.get("location", "").split(",")[0].strip().lower()
    in_india = "india" in loc
    in_metro = city in TARGET_CITIES or any(t in loc for t in TARGET_CITIES)
    relocate = bool(sig.get("willing_to_relocate"))

    if in_metro:
        return LOC["metro"], "in a target metro"
    if in_india and relocate:
        return LOC["india_relocate"], "in India, willing to relocate"
    if in_india:
        return LOC["india"], "in India, not flagged for relocation"
    if relocate:
        return LOC["abroad_relocate"], "outside India, willing to relocate"
    return LOC["abroad"], "outside India"


def availability_factor(c, relevance_high):
    """Bounded availability multiplier in [AVAIL_MIN, AVAIL_MAX].

    relevance_high raises the floor so a strong-but-quiet candidate is never
    buried below an irrelevant but active one.
    """
    sig = c.get("redrob_signals", {})
    notes = []

    la = _pdate(sig.get("last_active_date", ""))
    days = (REF_DATE - la).days if la else 365
    if days <= 45:
        recf = 1.0
    elif days <= 90:
        recf = 0.97
    elif days <= 160:
        recf = 0.93
    else:
        recf = 0.88
        notes.append(f"inactive ~{days} days")

    rr = sig.get("recruiter_response_rate")
    if rr is None:
        rrf = 0.97
    else:
        rrf = 0.92 + 0.08 * min(rr / 0.6, 1.0)
        if rr < 0.15:
            notes.append(f"low recruiter response ({rr:.2f})")

    otw = 1.0 if sig.get("open_to_work_flag") else 0.97
    icr = sig.get("interview_completion_rate")
    icf = 1.0 if icr is None else (0.96 + 0.04 * min(icr, 1.0))

    factor = recf * rrf * otw * icf
    floor = AVAIL_MIN if not relevance_high else (AVAIL_MIN + 0.05)
    factor = max(floor, min(AVAIL_MAX, factor))
    return round(factor, 4), notes
