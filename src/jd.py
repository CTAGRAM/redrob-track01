"""The job description, encoded as machine-readable knowledge.

This module is the rubric: it turns the JD's prose requirements, disqualifiers,
and ideal-candidate description into lexicons and a lightweight lexical-semantic
evidence scorer. We deliberately score what a candidate *describes having built*
(career history free text) rather than how many AI keywords sit in their skills
list — skills are assigned near-uniformly at random in this dataset, so keyword
counting is noise. This is how we see past the keyword trap.
"""

import re

# --- Title lexicons ----------------------------------------------------------
AI_TITLE = re.compile(
    r"(ai engineer|a\.?i\.? engineer|ml engineer|machine learning|data scientist|"
    r"nlp engineer|applied scientist|applied ml|research engineer|deep learning|"
    r"mlops|ai/ml|ai specialist|ai research|search engineer|relevance engineer)",
    re.I,
)
DATA_SW_TITLE = re.compile(
    r"(data engineer|analytics engineer|data analyst|backend engineer|"
    r"software engineer|full stack|platform engineer|senior software)",
    re.I,
)
LEAD_TITLE = re.compile(r"(architect|principal|director|vp |head of|engineering manager|tech lead)", re.I)

# --- Services / consulting firms (entire-career-here is a hard negative) ------
SERVICES = [
    "tcs", "tata consultancy", "infosys", "wipro", "accenture", "cognizant",
    "capgemini", "hcl technologies", "tech mahindra", "mindtree", "ltimindtree",
    "mphasis", "dxc", "larsen & toubro infotech",
]

# --- Target geography (JD: Pune/Noida preferred; metros welcome) --------------
TARGET_CITIES = {
    "pune", "noida", "hyderabad", "mumbai", "delhi", "new delhi", "gurgaon",
    "gurugram", "bangalore", "bengaluru", "ghaziabad", "faridabad",
    "greater noida", "navi mumbai", "thane", "secunderabad",
}

# --- Lexical-semantic evidence phrase banks (matched against career text) ------
# Each phrase carries weight; the scorer rewards distinct matches with
# diminishing returns, so a candidate must describe varied real work to score.
SHIP_PHRASES = [
    "recommendation", "recommender", "recsys", "ranking", "learning to rank",
    "learning-to-rank", "retrieval", "search engine", "search system",
    "search relevance", "search ranking", "semantic search", "personalization",
    "personalisation", "matching engine", "candidate matching", "nearest neighbor",
    "ann index", "information retrieval", "relevance tuning", "query understanding",
]
VECTORDB_PHRASES = [
    "vector database", "vector db", "vector search", "embedding", "embeddings",
    "sentence-transformers", "sentence transformers", "faiss", "pinecone",
    "weaviate", "qdrant", "milvus", "opensearch", "elasticsearch", "elastic search",
    "bm25", "hybrid search", "hybrid retrieval", "bge", "e5 embeddings",
]
EVAL_PHRASES = [
    "ndcg", "mrr", "mean average precision", "map@", "precision@", "recall@",
    "a/b test", "ab test", "offline metric", "online metric", "ranking metric",
    "relevance evaluation", "offline-online", "click-through rate", "ctr uplift",
]
NLP_PHRASES = [
    "nlp", "natural language", "language model", "llm", "transformer", "bert",
    "text classification", "named entity", "question answering", "rag",
    "retrieval augmented", "tokeniz", "word embedding", "semantic", "summarization",
]
CV_SPEECH_PHRASES = [
    "computer vision", "image classification", "object detection", "segmentation",
    "speech recognition", "text-to-speech", "tts", "asr", "robotics", "opencv",
    "yolo", "pose estimation", "optical character", "gan", "image generation",
]
LTR_PHRASES = ["xgboost", "lightgbm", "lambdamart", "learning to rank", "gradient boosted ranker", "ranknet"]
FRAMEWORK_ONLY_PHRASES = ["langchain", "llamaindex", "prompt engineering", "openai api", "chatgpt wrapper"]
PRODUCTION_PHRASES = [
    "production", "deployed", "at scale", "millions of", "real-time", "real time",
    "high throughput", "low latency", "qps", "served", "shipped", "users",
]
HRTECH_PHRASES = ["recruit", "hiring", "talent", " ats ", "applicant", "job matching", "marketplace", "candidate"]

_WORD = re.compile(r"[a-z0-9][a-z0-9\+\#\.\-/]*")


def candidate_text(c):
    """Concatenate the free-text a candidate *wrote about their work*."""
    p = c.get("profile", {})
    parts = [p.get("summary", ""), p.get("headline", ""), p.get("current_title", "")]
    for job in c.get("career_history", []):
        parts.append(job.get("title", ""))
        parts.append(job.get("description", ""))
    return " ".join(parts).lower()


def evidence(text, phrases, cap):
    """Saturating evidence score: distinct phrase hits with diminishing returns.

    Returns a value in [0, cap]. The first couple of distinct matches carry most
    of the weight, so stuffing the same term repeatedly does not inflate score.
    """
    hits = 0
    for ph in phrases:
        if ph in text:
            hits += 1
    if hits == 0:
        return 0.0, 0
    # diminishing returns: 1->0.55, 2->0.8, 3->0.92, 4+->~1.0 of cap
    frac = 1.0 - 0.55 ** hits
    return round(cap * frac, 3), hits
