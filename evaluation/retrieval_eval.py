import random

import numpy as np

import ingestion.vector_store as vs

SAMPLE_SIZE = 150
TOP_K = 5
RRF_K = 60        # reciprocal-rank-fusion constant for the hybrid baseline
POOL = TOP_K * 4  # candidate pool size per strategy before fusion


#=========================================================================================
def load_all():
    # get_collection() also rebuilds the in-memory BM25 index (vs.bm25_*).
    col = vs.get_collection()
    result = col.get(include=["documents", "metadatas", "embeddings"])
    return result["documents"], result["metadatas"], np.array(result["embeddings"])


#=========================================================================================
def tags_of(metadata):
    return set(t for t in metadata.get("tags", "").split(",") if t)


#=========================================================================================
def vector_search(query_emb, k, exclude_text):
    res = vs.get_collection().query(
        query_embeddings=[query_emb],
        n_results=k + 5,
        include=["documents", "metadatas"],
    )
    docs = res["documents"][0]
    metas = res["metadatas"][0]
    return [(d, m) for d, m in zip(docs, metas) if d != exclude_text][:k]


#=========================================================================================
def bm25_ranking(query, limit, exclude_text):
    scores = vs.bm25_index.get_scores(query.lower().split())
    order = np.argsort(scores)[::-1]

    out = []
    for i in order:
        doc = vs.bm25_corpus[i]
        if doc == exclude_text:
            continue
        out.append((doc, vs.bm25_metadata[i]))
        if len(out) >= limit:
            break
    return out


#=========================================================================================
def hybrid_search(query, query_emb, k, exclude_text):
    # Reciprocal Rank Fusion: combine the vector and BM25 rankings by rank, which
    # sidesteps the fact that cosine scores and BM25 scores live on different scales.
    vres = vs.get_collection().query(
        query_embeddings=[query_emb],
        n_results=POOL + 5,
        include=["documents", "metadatas"],
    )
    vdocs = [d for d in vres["documents"][0] if d != exclude_text][:POOL]
    meta_lookup = {d: m for d, m in zip(vres["documents"][0], vres["metadatas"][0])}

    bm25 = bm25_ranking(query, POOL, exclude_text)
    bdocs = [d for d, _ in bm25]
    for d, m in bm25:
        meta_lookup.setdefault(d, m)

    rrf = {}
    for rank, d in enumerate(vdocs):
        rrf[d] = rrf.get(d, 0.0) + 1.0 / (RRF_K + rank + 1)
    for rank, d in enumerate(bdocs):
        rrf[d] = rrf.get(d, 0.0) + 1.0 / (RRF_K + rank + 1)

    ranked = sorted(rrf.items(), key=lambda kv: kv[1], reverse=True)[:k]
    return [(d, meta_lookup[d]) for d, _ in ranked]


#=========================================================================================
def precision_at_k(results, query_tags):
    if not results:
        return 0.0
    hits = sum(1 for _, m in results if tags_of(m) & query_tags)
    return hits / len(results)


#=========================================================================================
if __name__ == "__main__":
    documents, metadatas, embeddings = load_all()
    n = len(documents)

    random.seed(42)
    sample_idx = random.sample(range(n), min(SAMPLE_SIZE, n))

    v_scores, b_scores, h_scores = [], [], []

    for count, i in enumerate(sample_idx, 1):
        query = documents[i]
        query_tags = tags_of(metadatas[i])
        if not query_tags:
            continue
        query_emb = embeddings[i].tolist()

        v = vector_search(query_emb, TOP_K, query)
        b = bm25_ranking(query, TOP_K, query)
        h = hybrid_search(query, query_emb, TOP_K, query)

        v_scores.append(precision_at_k(v, query_tags))
        b_scores.append(precision_at_k(b, query_tags))
        h_scores.append(precision_at_k(h, query_tags))

        if count % 25 == 0:
            print(f"  {count}/{len(sample_idx)} queries done")

    print(f"\n=== Retrieval tag-precision@{TOP_K} ({len(v_scores)} queries) ===")
    print(f"Vector-only : {np.mean(v_scores):.1%}")
    print(f"BM25-only   : {np.mean(b_scores):.1%}")
    print(f"Hybrid (RRF): {np.mean(h_scores):.1%}")
