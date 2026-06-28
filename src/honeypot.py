"""Honeypot / internal-consistency detector.

The ground truth forces ~80 "subtly impossible" profiles to relevance tier 0,
and a top-100 honeypot rate above 10% is an instant disqualification. We catch
them by checking arithmetic impossibilities that no real profile can exhibit —
the same kind of inconsistencies used to construct them.

Design choice: the HARD gate fires only on egregious, unambiguous violations
(e.g. claiming more months in a role than the calendar window allows). Mild or
borderline anomalies are surfaced as a soft score but never ban a candidate, so
we do not collaterally bury legitimate people.
"""

import datetime as dt

from .config import REF_DATE


def _pdate(s):
    if not s:
        return None
    try:
        return dt.date.fromisoformat(s)
    except (ValueError, TypeError):
        return None


def inspect(c):
    """Return (is_honeypot: bool, violations: list[str], soft_score: float).

    is_honeypot is True only when a HARD impossibility is present.
    """
    hard = []
    soft = []

    profile = c.get("profile", {})
    yoe = profile.get("years_of_experience", 0) or 0
    career = c.get("career_history", [])

    career_months = 0
    for job in career:
        dm = job.get("duration_months", 0) or 0
        career_months += dm
        sd = _pdate(job.get("start_date"))
        ed = _pdate(job.get("end_date"))

        if sd and sd > REF_DATE:
            hard.append("career start_date is in the future")
        if sd and ed and sd > ed:
            hard.append("career start_date after end_date")
        if sd:
            end = ed or REF_DATE
            span = (end.year - sd.year) * 12 + (end.month - sd.month)
            # claiming >2 years more tenure than the calendar window allows is impossible
            if dm > span + 24:
                hard.append(f"role duration {dm}mo exceeds calendar span {span}mo")
            elif dm > span + 9:
                soft.append("role duration slightly exceeds calendar span")

    # "expert/advanced in N skills with 0 months used" — the canonical honeypot
    zero_expert = 0
    for sk in c.get("skills", []):
        prof = sk.get("proficiency")
        dur = sk.get("duration_months", 0) or 0
        if prof in ("expert", "advanced") and dur == 0:
            zero_expert += 1
        if yoe and dur > yoe * 12 + 30:
            hard.append("skill used longer than entire career")
    if zero_expert >= 3:
        hard.append(f"{zero_expert} expert/advanced skills with 0 months used")
    elif zero_expert >= 1:
        soft.append("expert/advanced skill claimed with 0 months used")

    # education timeline impossibilities
    for e in c.get("education", []):
        sy, ey = e.get("start_year"), e.get("end_year")
        if sy and ey and ey < sy:
            hard.append("education end_year before start_year")

    # summed career far exceeds stated experience (soft only — roles can overlap)
    if yoe and career_months > yoe * 12 * 1.7 + 36:
        soft.append("summed role durations far exceed stated experience")

    soft_score = min(1.0, 0.5 * len(hard) + 0.12 * len(soft))
    return (len(hard) > 0), hard, round(soft_score, 3)
