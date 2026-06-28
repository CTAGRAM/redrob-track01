"""Pipeline tests: format validity, honeypot gate, and determinism.

Run from the repo root:  python -m pytest tests/ -q   (or just: python tests/test_pipeline.py)
These tests build a tiny synthetic pool so they need no external data.
"""

import json
import os
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _candidate(cid, title="Machine Learning Engineer", yoe=6.0, desc="built a search ranking and recommendation system with embeddings", honeypot=False):
    start, end, dur = "2021-01-01", None, 30
    if honeypot:
        dur = 300  # impossible: 300 months in a ~5-year window
    return {
        "candidate_id": cid,
        "profile": {
            "anonymized_name": "X", "headline": title, "summary": desc,
            "location": "Pune, Maharashtra", "country": "India",
            "years_of_experience": yoe, "current_title": title,
            "current_company": "Acme", "current_company_size": "201-500",
            "current_industry": "Internet",
        },
        "career_history": [{
            "company": "Acme", "title": title, "start_date": start, "end_date": end,
            "duration_months": dur, "is_current": True, "industry": "Internet",
            "company_size": "201-500", "description": desc,
        }],
        "education": [], "skills": [{"name": "NLP", "proficiency": "advanced", "endorsements": 10, "duration_months": 24}],
        "certifications": [], "languages": [],
        "redrob_signals": {
            "profile_completeness_score": 90, "signup_date": "2025-01-01",
            "last_active_date": "2026-05-20", "open_to_work_flag": True,
            "profile_views_received_30d": 10, "applications_submitted_30d": 1,
            "recruiter_response_rate": 0.6, "avg_response_time_hours": 10,
            "skill_assessment_scores": {"NLP": 85}, "connection_count": 100,
            "endorsements_received": 20, "notice_period_days": 30,
            "expected_salary_range_inr_lpa": {"min": 20, "max": 40},
            "preferred_work_mode": "hybrid", "willing_to_relocate": True,
            "github_activity_score": 60, "search_appearance_30d": 50,
            "saved_by_recruiters_30d": 3, "interview_completion_rate": 0.9,
            "offer_acceptance_rate": 0.5, "verified_email": True,
            "verified_phone": True, "linkedin_connected": True,
        },
    }


def _make_pool(path, n_real=120, n_honeypot=20):
    with open(path, "w") as f:
        for i in range(n_real):
            f.write(json.dumps(_candidate(f"CAND_{i:07d}")) + "\n")
        for i in range(n_honeypot):
            f.write(json.dumps(_candidate(f"CAND_{900000 + i:07d}", honeypot=True)) + "\n")


def _run(pool, out):
    subprocess.check_call([sys.executable, os.path.join(ROOT, "rank.py"), "--candidates", pool, "--out", out],
                          stderr=subprocess.DEVNULL)


def test_valid_and_honeypot_free_and_deterministic():
    with tempfile.TemporaryDirectory() as d:
        pool = os.path.join(d, "pool.jsonl")
        out1, out2 = os.path.join(d, "s1.csv"), os.path.join(d, "s2.csv")
        _make_pool(pool)
        _run(pool, out1)
        _run(pool, out2)

        # determinism: identical bytes
        assert open(out1, "rb").read() == open(out2, "rb").read(), "non-deterministic output"

        # official validator passes
        rc = subprocess.call([sys.executable, os.path.join(ROOT, "..", "validate_submission.py"), out1],
                             stdout=subprocess.DEVNULL)
        # validator lives one level up in the bundle; only assert if present
        if os.path.exists(os.path.join(ROOT, "..", "validate_submission.py")):
            assert rc == 0, "official validator rejected the submission"

        # no honeypot id (CAND_09xxxxx) in the top-100
        import csv
        ids = [r["candidate_id"] for r in csv.DictReader(open(out1))]
        assert len(ids) == 100
        assert not any(i.startswith("CAND_09") for i in ids), "honeypot leaked into top-100"
    print("OK: valid, honeypot-free, deterministic")


if __name__ == "__main__":
    test_valid_and_honeypot_free_and_deterministic()
