import chromadb
from rank_bm25 import BM25Okapi
from ingestion.embedder import embed_texts, embed_single

COLLECTION_NAME = "support_docs"

client = None
collection = None

bm25_index = None
bm25_corpus = None
bm25_metadata = None


#=========================================================================================
def _rebuild_bm25(col):
    """Rebuild BM25 index from documents already stored in ChromaDB."""
    global bm25_index, bm25_corpus, bm25_metadata

    count = col.count()
    if count == 0:
        return

    result = col.get()
    documents = result["documents"]

    bm25_corpus = documents
    bm25_metadata = result["metadatas"]
    bm25_index = BM25Okapi([doc.lower().split() for doc in documents])
    print(f"BM25 index rebuilt from {count} existing documents")


#=========================================================================================
def get_collection():
    global client, collection

    if client is None:
        client = chromadb.PersistentClient(path="./chroma_db")

    if collection is None:
        collection = client.get_or_create_collection(name=COLLECTION_NAME)
        _rebuild_bm25(collection)

    return collection


#=========================================================================================
def add_documents(ids: list[str], documents: list[str], metadatas: list[dict], batch_size: int = 5000):
    col = get_collection()
    total = len(documents)

    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        print(f"Embedding documents {start}-{end} of {total}....")
        batch_embeddings = embed_texts(documents[start:end])
        col.add(
            ids=ids[start:end],
            documents=documents[start:end],
            embeddings=batch_embeddings,
            metadatas=metadatas[start:end],
        )

    _rebuild_bm25(col)

    print(f"Stored {total} documents")
    print(f"BM25 index built with {col.count()} documents")


#=========================================================================================
def add_chunks(chunks: list[str], source_file: str):
    ids = [f"{source_file}_chunk_{i}" for i in range(len(chunks))]
    metadatas = [{"source": source_file} for _ in chunks]
    add_documents(ids, documents=chunks, metadatas=metadatas)


#=========================================================================================
def search_chunks(query: str, top_k: int = 5) -> list[dict]:
    col = get_collection()

    chunk_count = col.count()
    if chunk_count == 0:
        return []

    query_embedding = embed_single(query)

    fetch_count = top_k * 4

    vector_results = col.query(
        query_embeddings=[query_embedding],
        n_results=min(fetch_count, chunk_count),
        include = ["documents", "metadatas", "distances", "embeddings"]
    )

    vector_chunks = []
    for i in range(len(vector_results["documents"][0])):
        vector_chunks.append({
            "text": vector_results["documents"][0][i],
            "metadata": vector_results["metadatas"][0][i],
            "vector_score": 1 - vector_results["distances"][0][i],
            "embedding": vector_results["embeddings"][0][i]
        })

    bm25_chunks = []

    if bm25_index is not None:
        tokenized_query = query.lower().split()
        bm25_scores = bm25_index.get_scores(tokenized_query)

        scored_chunks = []
        for i in range(len(bm25_corpus)):
            scored_chunks.append((i, bm25_scores[i]))

        scored_chunks.sort(key=lambda x: x[1], reverse=True)
        top_bm25 = scored_chunks[:fetch_count]

        for i, score in top_bm25:
            bm25_chunks.append({
                "text": bm25_corpus[i],
                "metadata": bm25_metadata[i],
                "bm25_score": score
            })

    merged = {}

    for chunk in vector_chunks:
        merged[chunk["text"]] = chunk

    for chunk in bm25_chunks:
        if chunk["text"] not in merged:
            merged[chunk["text"]] = chunk

    all_candidates = list(merged.values())

    final_chunks = apply_mmr(
        query=query,
        candidates=all_candidates,
        top_k=top_k
    )

    return final_chunks


#=========================================================================================
def apply_mmr(query: str, candidates: list[dict], top_k: int, diversity: float = 0.5) -> list[dict]:
    if not candidates:
        return []

    query_embedding = embed_single(query)
    candidate_embeddings = [
        c["embedding"] if "embedding" in c else embed_single(c["text"])
        for c in candidates
    ]

    selected = []
    selected_embeddings = []
    remaining = list(range(len(candidates)))

    for _ in range(min(top_k, len(candidates))):
        best_index = None
        best_score = float("-inf")

        for idx in remaining:
            candidate_emb = candidate_embeddings[idx]

            relevance = cosine_similarity(query_embedding, candidate_emb)

            if selected_embeddings:
                redundancy_scores = [
                    cosine_similarity(candidate_emb, sel_emb)
                    for sel_emb in selected_embeddings
                ]
                redundancy = max(redundancy_scores)
            else:
                redundancy = 0.0

            mmr_score = (1 - diversity) * relevance - diversity * redundancy

            if mmr_score > best_score:
                best_score = mmr_score
                best_index = idx

        selected.append(candidates[best_index])
        selected_embeddings.append(candidate_embeddings[best_index])
        remaining.remove(best_index)

    return selected


#=========================================================================================
def cosine_similarity(vec_a: list[float], vec_b: list[float]) -> float:
    dot_product = sum(a * b for a, b in zip(vec_a, vec_b))

    magnitude_a = sum(a * a for a in vec_a) ** 0.5
    magnitude_b = sum(b * b for b in vec_b) ** 0.5

    if magnitude_a == 0 or magnitude_b == 0:
        return 0.0

    return dot_product / (magnitude_a * magnitude_b)


#=========================================================================================
def get_chunk_count() -> int:
    col = get_collection()
    return col.count()