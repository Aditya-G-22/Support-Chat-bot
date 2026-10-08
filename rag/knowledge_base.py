import json

from ingestion.embedder import embed_single, embed_texts
from ingestion.vector_store import cosine_similarity

KB_PATH = "clustering/cluster_summaries.json"
KB_THRESHOLD = 0.4  # minimum query-to-topic similarity to count as a match

_kb_entries = None
_kb_embeddings = None


#=========================================================================================
def load_kb():
    # Load the auto-generated knowledge-base entries and embed each entry's issue
    # text once, so queries can be matched to topics. Cached after first load.
    global _kb_entries, _kb_embeddings

    if _kb_entries is not None:
        return _kb_entries

    try:
        with open(KB_PATH, "r", encoding="utf-8") as f:
            _kb_entries = json.load(f)
    except FileNotFoundError:
        _kb_entries = []
        _kb_embeddings = []
        return _kb_entries

    issues = [e["issue"] for e in _kb_entries]
    _kb_embeddings = embed_texts(issues)
    return _kb_entries


#=========================================================================================
def search_kb(query, threshold=KB_THRESHOLD):
    # Return the single best-matching KB topic for the query, or None if nothing
    # clears the similarity threshold (so irrelevant topics are never forced).
    entries = load_kb()
    if not entries:
        return None

    query_emb = embed_single(query)

    best_idx = None
    best_score = -1.0
    for i, emb in enumerate(_kb_embeddings):
        score = cosine_similarity(query_emb, emb)
        if score > best_score:
            best_score = score
            best_idx = i

    if best_score < threshold:
        return None

    entry = dict(entries[best_idx])
    entry["score"] = best_score
    return entry


#=========================================================================================
def format_kb(entry):
    if not entry:
        return ""

    lines = [
        f"Topic: {entry.get('label', '')}",
        f"Issue: {entry.get('issue', '')}",
        f"Typical resolution: {entry.get('resolution', '')}",
    ]
    return "\n".join(lines)
