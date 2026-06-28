"""Fact-grounded reasoning generator.

Produces the 1-2 sentence justification for each ranked candidate. Every clause
is filled only from real profile facts and computed features, so nothing is
hallucinated. Both the sentence structure and the phrasing of each evidence axis
are selected deterministically from several variants, seeded by the candidate id,
so rows read as substantively different while the tone stays consistent with the
rank.
"""

_AXIS_ORDER = ["ship", "vectordb", "eval", "ltr", "nlp", "role", "product", "years", "assess", "github", "edu"]

# Several truthful paraphrases per axis. Selected by seed so wording varies row to row.
# Predicate-style paraphrases so any two can be joined with "and" / "; Also".
_PARAPHRASE = {
    "ship": [
        "built ranking, search and recommendation systems",
        "has shipped search-and-recommendation systems",
        "centers their career on ranking and retrieval systems",
        "describes production search/recsys work",
        "built recommendation and search-ranking systems",
    ],
    "vectordb": [
        "uses embeddings and vector search",
        "works with vector databases and embeddings",
        "applies embedding-based retrieval",
        "is experienced with vector search",
    ],
    "eval": [
        "evaluates rankers with NDCG/MRR/MAP",
        "measures relevance with offline ranking metrics",
        "knows ranking metrics (NDCG/MRR)",
    ],
    "ltr": ["uses learning-to-rank models", "applies learning-to-rank"],
    "nlp": ["works in NLP/IR", "has an NLP/information-retrieval background"],
    "role": ["matches the role directly", "is well-matched on role"],
    "product": ["has a product-company career", "worked at product companies"],
    "years": ["sits in the target experience band", "is at the right seniority"],
    "assess": ["has corroborating skill assessments", "is backed by Redrob assessments"],
    "github": ["is active in open source", "has notable GitHub activity"],
    "edu": ["studied at a tier-1 institution"],
}


def _seed(candidate_id, n_axes):
    digits = "".join(ch for ch in candidate_id if ch.isdigit())
    return int(digits or "0") + n_axes


def _phr(axis, seed, fallback):
    opts = _PARAPHRASE.get(axis)
    if not opts:
        return fallback
    return opts[seed % len(opts)]


def _cited_axes(positives):
    by_axis = {axis: msg for axis, msg in positives}
    return [(a, by_axis[a]) for a in _AXIS_ORDER if a in by_axis]


_REL = ("nlp", "rank", "retriev", "search", "embedding", "recommend", "llm",
        "transformer", "bert", "elasticsearch", "faiss", "vector", "rag",
        "fine-tun", "lora", "information retrieval")


def _skill_clause(facts):
    sk, sc = facts.get("assessed_skill"), facts.get("assessed_score")
    if sk and sc is not None and any(k in sk.lower() for k in _REL):
        return f"scored {sc:.0f}/100 on the {sk} assessment"
    if facts.get("named_skill"):
        return f"lists {facts['named_skill']} among their skills"
    if sk and sc is not None:
        return f"scored {sc:.0f}/100 on the {sk} assessment"
    return ""


def build(result, rank):
    f = result["features"]
    facts = result.get("facts", {})
    axes = _cited_axes(result["positives"])
    concerns = result["concerns"]
    title = f["title"] or "Candidate"
    yrs = f"{f['yoe']:.1f} yrs"
    company = facts.get("company")
    skill = _skill_clause(facts)
    seed = _seed(result["candidate_id"], len(axes))

    lead = _phr(axes[0][0], seed, axes[0][1]) if axes else "shows adjacent skills only"
    second = _phr(axes[1][0], seed + 1, axes[1][1]) if len(axes) > 1 else None

    v = seed % 3
    if v == 0:
        s = f"{title} with {yrs}"
        if company:
            s += f" at {company}"
        s += f" — {lead}"
        if second:
            s += f", and {second}"
        s += "."
    elif v == 1:
        cap = lead[0].upper() + lead[1:]
        s = f"{cap}; a {yrs} {title}"
        if company:
            s += f" at {company}"
        s += "."
        if second:
            s += f" Also {second}."
    else:
        s = f"{yrs} {title}"
        if company:
            s += f" ({company})"
        s += f" who {lead}"
        if second:
            s += f" and {second}"
        s += "."

    if skill:
        s += f" {skill[0].upper() + skill[1:]}."
    s += f" {result['loc_note'].capitalize()}."

    if concerns:
        label = "Concern" if rank > 60 else "Noted"
        s += f" {label}: {concerns[0]}."

    return " ".join(s.split())[:300]
