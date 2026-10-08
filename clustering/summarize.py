import json
import os
import time

import numpy as np
from dotenv import load_dotenv
from groq import Groq, RateLimitError

from clustering.cluster import load_embeddings, reduce_dimensions, run_hdbscan
from clustering.evaluate import cluster_indices
from utils.prompts import cluster_summary_prompt

load_dotenv()
groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

TOP_N = None        # how many clusters to summarize (largest first); None = all
SAMPLES_PER_CLUSTER = 12
OUT_PATH = "clustering/cluster_summaries.json"


#=========================================================================================
def get_cluster_samples(cluster_idxs, embeddings, documents, metadatas, n):
    # Sample tickets spread across the cluster — from its dense core out to its
    # edges — so large clusters are represented by their full breadth, not just
    # the densest sub-region near the centroid.
    cluster_embs = embeddings[cluster_idxs]
    centroid = cluster_embs.mean(axis=0)
    distances = np.linalg.norm(cluster_embs - centroid, axis=1)
    order = np.argsort(distances)  # nearest-to-centroid first

    if len(order) <= n:
        chosen_local = order
    else:
        positions = np.linspace(0, len(order) - 1, n).astype(int)
        chosen_local = order[positions]

    samples = []
    for local_i in chosen_local:
        global_i = cluster_idxs[int(local_i)]
        samples.append({
            "problem": documents[global_i],
            "resolution": metadatas[global_i].get("answer", ""),
        })
    return samples


#=========================================================================================
def summarize_cluster(samples):
    prompt = cluster_summary_prompt(samples)

    for attempt in range(8):
        try:
            response = groq_client.chat.completions.create(
                model="openai/gpt-oss-20b",
                messages=[{"role": "user", "content": prompt}],
                temperature=0,
            )
            raw = response.choices[0].message.content.strip()
            cleaned = raw.replace("```json", "").replace("```", "").strip()
            return json.loads(cleaned)
        except RateLimitError:
            wait = min(60, 15 * (attempt + 1))  # 60s clears the per-minute token window
            print(f"  rate limited, waiting {wait}s...")
            time.sleep(wait)
        except json.JSONDecodeError:
            print("  could not parse JSON from LLM, skipping cluster")
            return None

    print("  gave up after retries")
    return None


#=========================================================================================
if __name__ == "__main__":
    embeddings, metadatas, documents = load_embeddings()

    print("Reducing + clustering...")
    reduced = reduce_dimensions(embeddings)
    labels = run_hdbscan(reduced)

    idx = cluster_indices(labels)
    sizes = [(c, len(members)) for c, members in idx.items() if c != -1]
    sizes.sort(key=lambda x: x[1], reverse=True)
    top_clusters = [c for c, _ in sizes[:TOP_N]]

    # Resume: load any existing summaries and skip clusters already done, so a
    # re-run only fills the gaps instead of redoing everything.
    summaries = []
    done_ids = set()
    if os.path.exists(OUT_PATH):
        with open(OUT_PATH, "r", encoding="utf-8") as f:
            summaries = json.load(f)
        done_ids = {e["cluster_id"] for e in summaries}
        print(f"Resuming: {len(done_ids)} clusters already done, skipping them.")

    for c in top_clusters:
        if c in done_ids:
            continue

        size = len(idx[c])
        print(f"Summarizing cluster {c} (n={size})...")

        samples = get_cluster_samples(idx[c], embeddings, documents, metadatas, SAMPLES_PER_CLUSTER)
        summary = summarize_cluster(samples)

        if summary:
            summary["cluster_id"] = c
            summary["size"] = size
            summaries.append(summary)
            # Save after each success so progress survives a crash or rate-limit.
            with open(OUT_PATH, "w", encoding="utf-8") as f:
                json.dump(summaries, f, indent=2, ensure_ascii=False)
            print(f"  -> {summary.get('label', '?')}")

    print(f"\nSaved {len(summaries)} knowledge-base entries to {OUT_PATH}")
