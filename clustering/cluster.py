import numpy as np
import umap
from sklearn.cluster import HDBSCAN

from ingestion.vector_store import get_collection


#=========================================================================================
def load_embeddings():
    # Pull the stored ticket embeddings (+ metadata) back out of ChromaDB.
    # Reuses the vectors already computed at ingestion time — no re-embedding.
    col = get_collection()
    result = col.get(include=["embeddings", "metadatas", "documents"])

    embeddings = np.array(result["embeddings"])
    metadatas = result["metadatas"]
    documents = result["documents"]

    return embeddings, metadatas, documents


#=========================================================================================
def reduce_dimensions(embeddings, n_components=5, n_neighbors=15):
    # UMAP compresses 768-dim embeddings to a few dimensions while preserving
    # local neighborhoods — the structure density clustering depends on.
    # metric="cosine" suits text embeddings; min_dist=0.0 lets points pack
    # tightly so HDBSCAN can find dense clumps.
    reducer = umap.UMAP(
        n_components=n_components,
        n_neighbors=n_neighbors,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    return reducer.fit_transform(embeddings)


#=========================================================================================
def run_hdbscan(vectors, min_cluster_size=30):
    clusterer = HDBSCAN(min_cluster_size=min_cluster_size)
    labels = clusterer.fit_predict(vectors)
    return labels


#=========================================================================================
def report_clusters(labels):
    labels = np.array(labels)
    total = len(labels)

    if total == 0:
        print("No embeddings to cluster.")
        return

    noise = int((labels == -1).sum())
    cluster_ids = sorted(c for c in set(labels.tolist()) if c != -1)

    print(f"Total tickets   : {total}")
    print(f"Clusters found  : {len(cluster_ids)}")
    print(f"Noise points    : {noise} ({100 * noise / total:.1f}%)")
    print("\nCluster sizes:")
    for c in cluster_ids:
        size = int((labels == c).sum())
        print(f"  Cluster {c:>3}: {size}")


#=========================================================================================
if __name__ == "__main__":
    embeddings, metadatas, documents = load_embeddings()

    if len(embeddings) == 0:
        print("No embeddings found. Ingest tickets first.")
    else:
        print(f"Loaded {len(embeddings)} embeddings of dimension {embeddings.shape[1]}")

        print("Reducing dimensions with UMAP (this takes a minute)...")
        reduced = reduce_dimensions(embeddings)
        print(f"Reduced to {reduced.shape[1]} dimensions\n")

        labels = run_hdbscan(reduced, min_cluster_size=30)
        report_clusters(labels)
