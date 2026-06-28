"""Redrob Track-01 — interactive ranking demo (the required sandbox).

A small Streamlit app that runs the *exact same* ranking engine used to produce
the submission, on an uploaded or sample candidate set (<=100 candidates), and
shows the ranked shortlist with scores and the generated reasoning. No network,
no GPU, no hosted-LLM calls — it runs the deterministic engine locally.

Run locally:   streamlit run sandbox/app.py
Deploy:        push the repo to Hugging Face Spaces (Streamlit SDK) or Streamlit Cloud.
"""

import json
import os
import sys

import streamlit as st

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import reasoning
from src.config import SCORE_HI, SCORE_LO
from src.scorer import score_candidate

def _to_csv(rows):
    import csv
    import io
    buf = io.StringIO()
    w = csv.DictWriter(buf, fieldnames=["candidate_id", "rank", "score", "reasoning"])
    w.writeheader()
    for r in rows:
        w.writerow({"candidate_id": r["candidate_id"], "rank": r["rank"],
                    "score": r["score"], "reasoning": r["reasoning"]})
    return buf.getvalue()


st.set_page_config(page_title="Redrob Candidate Ranker", page_icon="🎯", layout="wide")

st.title("🎯 Redrob Track-01 — Intelligent Candidate Ranker")
st.caption(
    "Ranks candidates for the *Senior AI Engineer* JD. Deterministic, CPU-only, "
    "no network or hosted-LLM calls — the same engine that produces our submission."
)

with st.expander("How it works", expanded=False):
    st.markdown(
        "- **Reads what candidates built** (career history free text), not how many AI keywords sit in their skills list — skills are noise in this dataset.\n"
        "- **Scores against the JD rubric**: role match, shipped ranking/search/recsys systems, vector-search & evaluation experience, NLP/IR domain, 5–9-year band, product-vs-services, corroborated skills.\n"
        "- **Bounded behavioral & location modifiers** down-weight unavailable candidates without burying strong-but-quiet ones.\n"
        "- **Honeypot gate** removes internally-impossible profiles so they can never reach the shortlist."
    )

src = st.radio("Candidate input", ["Use sample (50 candidates)", "Upload JSONL (<=100)"], horizontal=True)

candidates = []
if src.startswith("Use sample"):
    sample_path = os.path.join(os.path.dirname(__file__), "sample_candidates.json")
    if os.path.exists(sample_path):
        data = json.load(open(sample_path))
        candidates = data if isinstance(data, list) else [data]
    else:
        st.warning("Sample file not found. Upload a JSONL instead.")
else:
    up = st.file_uploader("Upload candidates .jsonl (one JSON object per line, <=100)", type=["jsonl", "json"])
    if up is not None:
        raw = up.read().decode("utf-8").strip()
        if raw.startswith("["):
            candidates = json.loads(raw)
        else:
            candidates = [json.loads(line) for line in raw.splitlines() if line.strip()]
        candidates = candidates[:100]

topk = st.slider("Show top-K", 5, 100, 20)

if candidates and st.button("Rank candidates", type="primary"):
    results = [score_candidate(c) for c in candidates]
    results = [r for r in results if not r["is_honeypot"]]
    excluded = len(candidates) - len(results)
    results.sort(key=lambda r: (-r["final"], r["candidate_id"]))
    top = results[:topk]

    step = (SCORE_HI - SCORE_LO) / max(len(top) - 1, 1)
    c1, c2, c3 = st.columns(3)
    c1.metric("Candidates scored", len(candidates))
    c2.metric("Impossible profiles removed", excluded)
    c3.metric("Honeypots in shortlist", 0)

    table = []
    for i, r in enumerate(top):
        table.append({
            "rank": i + 1,
            "score": round(SCORE_HI - i * step, 4),
            "candidate_id": r["candidate_id"],
            "title": r["features"]["title"],
            "yrs": round(r["features"]["yoe"], 1),
            "tier~": r["tier"],
            "reasoning": reasoning.build(r, i + 1),
        })
    st.dataframe(table, use_container_width=True, hide_index=True)
    st.download_button(
        "Download ranking CSV",
        data=_to_csv(table),
        file_name="ranking.csv",
        mime="text/csv",
    )
