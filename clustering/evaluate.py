import numpy as np
from collections import Counter, defaultdict
from sklearn.metrics import (
    homogeneity_score,
    completeness_score,
    v_measure_score,
    normalized_mutual_info_score,
)

from clustering.cluster import load_embeddings, reduce_dimensions, run_hdbscan


#=========================================================================================
def cluster_purity(labels, true_labels):
    # Single-label purity: for each cluster, the dominant ground-truth label and
    # what fraction of the cluster shares it. Noise (-1) is ignored.
    buckets = defaultdict(list)
    for i, c in enumerate(labels):
        if c != -1:
            buckets[int(c)].append(true_labels[i])

    results = {}
    total_correct = 0
    total_clustered = 0

    for c, trues in buckets.items():
        dominant, dominant_count = Counter(trues).most_common(1)[0]
        size = len(trues)
        results[c] = {"size": size, "dominant": dominant, "purity": dominant_count / size}
        total_correct += dominant_count
        total_clustered += size

    overall = total_correct / total_clustered if total_clustered else 0.0
    return results, overall


#=========================================================================================
def tag_coverage(labels, tag_lists):
    # Tags are multi-label. For each cluster, count how many of its tickets carry
    # each tag, then take the most common tag and the fraction of the cluster that
    # has it. Also keep the top 3 tags as the cluster's semantic signature.
    buckets = defaultdict(list)
    for i, c in enumerate(labels):
        if c != -1:
            buckets[int(c)].append(tag_lists[i])

    results = {}
    total_covered = 0
    total = 0

    for c, tagsets in buckets.items():
        tag_counts = Counter()
        for tags in tagsets:
            for t in set(tags):
                tag_counts[t] += 1
        size = len(tagsets)
        dominant, dom_count = tag_counts.most_common(1)[0]
        results[c] = {
            "size": size,
            "dominant": dominant,
            "coverage": dom_count / size,
            "top3": tag_counts.most_common(3),
        }
        total_covered += dom_count
        total += size

    overall = total_covered / total if total else 0.0
    return results, overall


#=========================================================================================
def cluster_indices(labels):
    idx = defaultdict(list)
    for i, c in enumerate(labels):
        idx[int(c)].append(i)
    return idx


#=========================================================================================
if __name__ == "__main__":
    embeddings, metadatas, documents = load_embeddings()
    queues = [m.get("queue", "unknown") for m in metadatas]
    tag_lists = [[t for t in m.get("tags", "").split(",") if t] for m in metadatas]

    print("Reducing dimensions with UMAP...")
    reduced = reduce_dimensions(embeddings)

    print("Clustering...")
    labels = run_hdbscan(reduced)

    # --- vs QUEUE (administrative label) ---
    q_results, q_overall = cluster_purity(labels, queues)

    labels_arr = np.array(labels)
    mask = labels_arr != -1
    y_pred = labels_arr[mask].tolist()
    y_true = [queues[i] for i in range(len(labels_arr)) if mask[i]]

    print("\n=== vs QUEUE (administrative label) ===")
    print(f"Overall purity : {q_overall:.1%}")
    print(f"Homogeneity    : {homogeneity_score(y_true, y_pred):.3f}")
    print(f"NMI            : {normalized_mutual_info_score(y_true, y_pred):.3f}")

    # --- vs TAGS (semantic label) ---
    t_results, t_overall = tag_coverage(labels, tag_lists)

    print("\n=== vs TAGS (semantic label) ===")
    print(f"Overall dominant-tag coverage: {t_overall:.1%}")

    # --- Top clusters: queue purity + tag signature + sample subjects ---
    idx = cluster_indices(labels)
    print("\n=== Top 15 clusters by size ===")
    top = sorted(q_results.items(), key=lambda kv: kv[1]["size"], reverse=True)[:15]
    for c, info in top:
        tinfo = t_results[c]
        top_tags = ", ".join(f"{t}({n})" for t, n in tinfo["top3"])
        print(f"\nCluster {c} (n={info['size']})")
        print(f"   queue: {info['purity']:.0%} {info['dominant']}  |  top tags: {top_tags}")
        for i in idx[c][:3]:
            subj = metadatas[i].get("subject", "").strip()
            text = subj if subj else documents[i][:70]
            print(f"   - {text[:72]}")
