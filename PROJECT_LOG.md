# PROJECT_LOG.md
# Multilingual Customer Support AI System
# Living Engineering Journal

---

## 1. Project Overview

**What we are building:**
A multilingual customer-support AI system that starts from *raw, messy historical support tickets* (CSV/JSON exports) and automatically transforms them into a searchable, structured knowledge base. The system should answer new customer questions in the same language they were asked, with source attribution back to the original tickets.

**Why this is interesting:**
Most support systems start from hand-curated FAQs. This project starts from the raw, unstructured residue of real support conversations and tries to discover the knowledge structure automatically — without requiring a human to label every issue and solution.

**The central engineering challenge:**
Transforming unstructured, noisy, multilingual conversations into structured, retrievable, evidenced knowledge.

---

## 2. Current Status

**Date:** 2026-10-06

**Phase:** Bug fixes complete. Ready to begin Phase 1 (ticket ingestion pipeline).

**Critical gap identified:**
The existing codebase (`cli.py`, `ingestion/`, `rag/`, `utils/`) implements a basic RAG bot over clean, pre-labeled FAQ text (`sample_faq.txt`). This is not the stated project goal. The differentiating component — ingesting raw messy tickets and discovering structure through clustering and summarization — does not yet exist.

---

## 3. What Has Been Implemented

| Component | File(s) | Status | Notes |
|---|---|---|---|
| Document loader (PDF, DOCX, TXT) | `ingestion/loader.py` | Working | Not yet adapted for CSV/JSON tickets |
| Text chunker | `ingestion/chunker.py` | Working (but naive) | Fixed-size chunking ignores semantic boundaries |
| Multilingual embedder | `ingestion/embedder.py` | Working | Good model choice |
| Vector store (ChromaDB) + BM25 | `ingestion/vector_store.py` | Fixed | BM25 now rebuilt from ChromaDB on startup (Bug 2) |
| MMR reranking | `ingestion/vector_store.py` | Fixed | Now reuses ChromaDB embeddings instead of recomputing (Bug 5) |
| Knowledge graph (NetworkX) | `ingestion/graph_builder.py` | Partially broken | In-memory only — graph persistence not yet addressed |
| Graph search | `rag/graph_rag.py` | Fixed | Semantic similarity matching with 0.7 threshold (Bug 4) |
| Retriever | `rag/retriever.py` | Working structure | |
| LangGraph agent | `rag/agent.py` | Fixed | Retry now uses top_k=10 vs top_k=5 on first attempt (Bug 3) |
| Language detection | `utils/language.py` | Working (unreliable for short text) | |
| Prompts | `utils/prompts.py` | Working | |

---

## 4. Known Bugs (Must Fix Before Progress)

### Bug 1: ~~Wrong Groq model name~~ — RESOLVED (NOT A BUG)
`"openai/gpt-oss-20b"` is a valid Groq-hosted model. Groq supports select OpenAI models via its API. Confirmed working by user testing.

### Bug 2: BM25 index lost on restart — FIXED (2026-10-06)
**File:** `ingestion/vector_store.py`
**Problem:** `bm25_index` was a Python in-memory global. Lost on process restart, silently falling back to vector-only retrieval.
**Fix applied:** Added `_rebuild_bm25(col)` helper that fetches all documents from ChromaDB via `col.get()` and rebuilds the index. Called from `get_collection()` on first connection and from `add_chunks()` after every ingestion. Single source of truth: ChromaDB.
**Tested:** BM25 rebuilt message appears correctly on startup and after ingestion.

### Bug 3: Agent retry loop is a no-op — FIXED (2026-10-06)
**File:** `rag/agent.py:47-59`
**Problem:** Retry called `retrieve_context` with identical parameters — same query, same top_k. Returned same documents.
**Fix applied:** `top_k = 5 if iteration_number == 1 else 10` — retry fetches twice as many candidates, increasing the chance of finding the relevant document.

### Bug 4: Graph node matching is exact substring only — FIXED (2026-10-06)
**File:** `rag/graph_rag.py`
**Problem:** `find_matching_nodes` used `if node in query_lower` — literal substring match only. Failed for any paraphrased query.
**Fix applied:** Replaced with semantic similarity. Embeds query and all node names, computes cosine similarity, returns nodes with similarity >= 0.7. Uses existing `embed_single`, `embed_texts`, and `cosine_similarity` from the codebase.

### Bug 5: MMR re-embeds candidates at query time — FIXED (2026-10-06)
**File:** `ingestion/vector_store.py`
**Problem:** `apply_mmr` called `embed_texts()` on all candidates every query. Embeddings already existed in ChromaDB.
**Fix applied:** `col.query()` now passes `include=["documents", "metadatas", "distances", "embeddings"]`. Each vector candidate carries its `"embedding"` key. `apply_mmr` uses existing embeddings via list comprehension: `c["embedding"] if "embedding" in c else embed_single(c["text"])`. BM25-only candidates still get embedded on demand.

---

## 5. Architecture: Proposed vs. Actual

### Proposed (from spec)
```
Raw Ticket CSV/JSON
  → Ticket Parsing (separate customer/agent)
  → PII Cleaning
  → Embedding
  → Clustering (HDBSCAN)
  → LLM Cluster Summarization
  → Knowledge Graph
  → Vector Database
  → Hybrid Retrieval (Vector + BM25)
  → MMR
  → Graph Traversal
  → Agentic Loop
  → Multilingual Answer + Source Attribution
```

### What Exists
```
Clean FAQ Text (TXT/PDF/DOCX)
  → Simple text chunking (500 chars)
  → Embedding (multilingual model)
  → ChromaDB + in-memory BM25
  → MMR (works, inefficient)
  → Graph (in-memory, broken matching)
  → LangGraph agent (retry is no-op)
  → Language detection + answer
```

### Gap
The entire first half of the pipeline — the part that transforms raw messy tickets into structured knowledge — does not exist.

---

## 6. Decisions

### Decision D-001
**Date:** 2026-10-06
**Decision:** Pause feature additions. Fix critical bugs first.
**Problem:** Multiple components are silently broken (wrong LLM model name, BM25 lost on restart, graph matching fails). Building more on top of a broken foundation produces misleading results.
**Options considered:**
  - Continue building (add ticket pipeline on top of broken retrieval): BAD — you can't evaluate whether new components are working if the foundation is unreliable.
  - Fix bugs first: GOOD — allows honest evaluation of each component.
**Decision:** Fix the 3 critical bugs (Groq model name, BM25 persistence, graph node matching) before adding any new components.
**Reason:** Engineering discipline. You cannot evaluate a system whose behavior is undefined.
**Status:** DECIDED

### Decision D-002
**Date:** 2026-10-06
**Decision:** The next major development phase is the ticket ingestion pipeline, not retrieval refinements.
**Problem:** The system currently ingests clean FAQ documents. The stated project goal is to ingest raw messy support tickets. This is the unsolved core problem.
**Options considered:**
  - Continue refining retrieval on clean FAQ: WRONG — improves something that isn't the hard problem.
  - Build ticket ingestion pipeline: RIGHT — addresses the actual differentiator.
**Decision:** Phase 1 after bug fixes is: CSV/JSON ticket loader → ticket parser (separate customer/agent) → PII cleaning → structured ticket representation.
**Status:** DECIDED

### Decision D-003
**Date:** 2026-10-06
**Decision:** Validate the knowledge graph component through a controlled experiment before treating it as a default component.
**Problem:** The graph adds LLM cost per chunk (one API call per chunk during ingestion), is lost on restart, and the retrieval is broken. We have no evidence it improves answer quality over vector+BM25.
**Experiment planned:** After retrieval is working correctly, compare: (a) vector+BM25 only vs. (b) vector+BM25+graph on a set of test queries. Only keep the graph if it measurably improves recall or answer quality.
**Status:** PROPOSED / EXPERIMENTAL

### Decision D-004
**Date:** 2026-10-06
**Decision:** Use the Kaggle "Customer IT Support - Ticket Dataset" (Tobias Bueck), `dataset-tickets-multi-lang-4-20k.csv` file, as the development dataset.
**Problem:** Needed a realistic ticket dataset to build the ingestion pipeline. Evaluated two candidates: "Customer Support on Twitter" (thoughtvector) and this multilingual one.
**Options considered:**
  - Twitter Customer Support: real human language, multi-turn, but English-only and NO ground-truth labels. Rejected.
  - Multilingual IT Support (chosen): synthetic, but multilingual (EN/DE) AND labeled (queue/type/priority/tags). Labels serve as ground truth for clustering evaluation.
**Reason:** Decisive principle — mess can be added to a dataset later (inject PII, degrade formatting); multilingual coverage and ground-truth labels CANNOT be added after the fact. Pick the dataset with the hard-to-add properties. The project's headline features (multilingual retrieval, measurable structure discovery) both require properties Twitter lacks.
**Known weakness:** Synthetic data weakens the "works on real-world data" claim. Mitigation: optionally degrade it to create realistic mess, and/or run a small real-data slice as a qualitative robustness check later.
**Status:** DECIDED

### Dataset Profile (dataset-tickets-multi-lang-4-20k.csv)
**Captured:** 2026-10-06 via `explore.py`
- **20,000 rows, 15 columns:** subject, body, answer, type, queue, priority, language, tag_1…tag_8
- **Languages:** EN (11,923), DE (8,077) — only two. Card advertised EN/DE/ES/FR/PT; ES is in the 4k file, not this one.
- **Missing values:** subject 1,461 (7.3%), body 2, answer 4. Core fields (body/answer) essentially complete.
- **PII masking is inconsistent** — the real cleaning challenge:
  - Two bracket styles: `<tel_num>` (8050) vs `[tel_num]` (771)
  - Multiple spellings per entity: phone = tel_num / telephone_number / phone_number / telefonnummer
  - Multilingual mask tokens: `telefonnummer`, `datum`, `uhrzeit` (DE), `nom` (FR)
- **`<br>` appears 3,699 times — HTML line break, NOT PII.** Separate HTML-stripping task. `[r]`/`[n]` are escape artifacts (noise).
- **Tags:** every row has 1–8 tags (mode 4–5); no empty-tag rows. Collapse tag_1…tag_8 → list, drop NaN.
- **Duplicates:** 0 full-row duplicates, 1 duplicate body. Non-issue.
- **Two PII tasks distinguished:** (a) mask normalization — standardize inconsistent masks, doable with this data; (b) PII detection/removal — find raw unmasked PII, NOT possible with this data (already masked), would require injecting fake PII.

### Target schema for the loader
`subject`, `body` (customer), `answer` (agent), `language`, `queue`, `type`, `priority`, `tags` (collapsed list). `business_type` dropped (only in 4k file, not needed).

### Decision D-005
**Date:** 2026-10-06
**Decision:** Embed `body` only (the customer problem). Store `answer` as the payload to return, not as embedded text.
**Problem:** Needed to decide what text represents each ticket in the vector store.
**Options considered:**
  - body only (chosen): matches how a support bot works — search the problem, return the solution. Keeps question/answer roles clean. Mirrors the old Issue→Solution FAQ structure.
  - body + answer: richer but mixes question and answer in one vector, muddying similarity.
  - subject + body: subject is sparse (7.3% missing) and low-value.
**How to apply:** This is also what clustering operates on later (cluster the problems, not the solutions).
**Status:** DECIDED

### Ticket pipeline components built (2026-10-06)
- **`ingestion/ticket_loader.py`** — `load_tickets(csv_path)` returns `list[Ticket]` (dataclass). 19,994 tickets loaded (20,000 − 6 missing body/answer). Tags collapsed, missing subjects → "".
- **`ingestion/cleaner.py`** — `strip_html`, `normalize_pii` (keyword-based, 9 entity classes), `normalize_whitespace`. PII mask normalization validated at 99.8% coverage (40 leftover of 20,000+, all non-PII/noise). Stopped deliberately — remaining long tail is whack-a-mole.
- **NOT YET INTEGRATED** — these are standalone + unit-tested. Nothing wires tickets → clean → embed → ChromaDB yet. The `ingest` CLI command still processes documents (sample_faq.txt), not tickets. That integration is the next step.

---

## 7. Rejected Ideas (So Far)

### R-001: Using exact substring matching for graph node retrieval
**Reason considered:** Simple to implement, no additional dependencies.
**Reason rejected:** Fails for any query that doesn't contain the exact node label string. This is essentially useless for real queries.
**Alternative:** Embed graph nodes and use semantic similarity to find relevant starting points.

### R-002: Re-embedding candidates at MMR time
**Reason considered:** Simplest approach — no need to store embeddings alongside documents.
**Reason rejected:** Embeddings are already stored in ChromaDB. Recomputing them is unnecessary cost.
**Alternative:** Retrieve embeddings from ChromaDB and pass them directly to MMR.

---

## 8. Open Questions

| # | Question | Status | Priority |
|---|---|---|---|
| Q-001 | What real (or realistic synthetic) ticket dataset should we use? | OPEN | HIGH |
| Q-002 | How do we reliably separate customer messages from agent responses in raw tickets? | OPEN | HIGH |
| Q-003 | What PII removal approach balances privacy with preserving semantic information? | OPEN | HIGH |
| Q-004 | Does HDBSCAN produce meaningful clusters on support tickets without ground truth? | OPEN | HIGH |
| Q-005 | Does the knowledge graph actually improve retrieval quality over vector+BM25? | OPEN | MEDIUM |
| Q-006 | Does the MMR implementation improve answer diversity or hurt precision? | OPEN | MEDIUM |
| Q-007 | How do we evaluate cluster quality without labeled ground truth? | OPEN | HIGH |
| Q-008 | How do we prevent LLM cluster summarization from hallucinating solutions not in the tickets? | OPEN | MEDIUM |
| Q-009 | Is `langdetect` reliable enough, or should we use a better language identification model? | OPEN | LOW |
| Q-010 | How do we handle tickets that contain multiple distinct issues? | OPEN | MEDIUM |

---

## 9. Proposed Roadmap

### Phase 0 — Foundation Fix (Current)
- Fix Bug 1: Correct Groq model name
- Fix Bug 2: Persist BM25 corpus to disk
- Fix Bug 3: Design a real retry strategy or remove the no-op retry
- Create a synthetic raw ticket dataset for development

### Phase 1 — Ticket Dataset + Understanding
- Obtain or create a realistic raw ticket dataset (CSV/JSON with noise, multi-turn conversations, agent responses, PII, inconsistent formatting)
- Understand the data: distribution of ticket lengths, languages, topics, fields
- Document what a "raw ticket" actually looks like before building any parser

### Phase 2 — Ticket Parsing
- Build a parser that separates customer messages from agent responses
- Compare: rule-based (sender role field), regex heuristics, structural parsing, LLM-based
- Evaluate: what percentage of tickets does each approach correctly parse?

### Phase 3 — Cleaning and PII Handling
- Build PII removal pipeline
- Compare: regex, spaCy NER, presidio (Microsoft), LLM-based
- Evaluate: what is removed vs. preserved? Does removing PII hurt semantic meaning?

### Phase 4 — Embedding Experiment
- Embed cleaned ticket messages
- Compare at least 2 embedding models on this specific domain
- Evaluate: retrieval quality using Recall@K on a small manual test set

### Phase 5 — Clustering Experiment
- Apply HDBSCAN to ticket embeddings
- Evaluate cluster quality: Silhouette Score, Davies-Bouldin Index, manual inspection
- Compare against K-Means and BERTopic
- Answer: do the clusters represent meaningful support topics?

### Phase 6 — Cluster Summarization
- For each cluster, use LLM to extract: Issue, Likely Cause, Resolution
- Evaluate: is the resolution actually supported by the tickets? (faithfulness)
- Build provenance links: summary → source tickets

### Phase 7 — Knowledge Representation
- Decide: knowledge graph vs. structured metadata on vector chunks
- Run the experiment from D-003 before committing to the graph
- Only build the graph if experiments show it helps

### Phase 8 — Retrieval Baseline
- Fix BM25 persistence
- Establish Baseline 0 (keyword only), Baseline 1 (vector only), Baseline 2 (hybrid)
- Evaluate each baseline on a test query set

### Phase 9 — Retrieval Improvements
- Evaluate MMR: does it improve diversity without hurting relevance?
- Evaluate reranking models (if graph approach is dropped)
- Build a working retry strategy for the agent loop

### Phase 10 — Multilingual Support
- Test cross-lingual retrieval with multilingual embeddings
- Evaluate query→English→retrieve→translate-back vs. multilingual-embed directly
- Build a multilingual test set (English + Hindi + Spanish queries)

### Phase 11 — UI
- Build a recruiter-facing interface showing the full trace
- Upload raw tickets → watch processing → ask questions → see sources

### Phase 12 — Model Evaluation
- Separate evaluation projects per component
- Reusable scripts, documented results

### Phase 13 — Application Evaluation
- End-to-end evaluation on a test dataset
- Compare architecture variants

---

## 10. Experiments

### Experiment E-001: Does knowledge graph improve retrieval?
**Hypothesis:** Adding graph traversal to hybrid vector+BM25 retrieval improves answer correctness or recall.
**Setup:** Fixed test set of 20+ queries. Compare: (a) vector+BM25 only, (b) vector+BM25+graph.
**Metrics:** Answer correctness (manual evaluation), source recall (were the right tickets retrieved?).
**Status:** PENDING (waiting for retrieval bugs to be fixed first)

### Experiment E-002: Does HDBSCAN cluster tickets meaningfully? — DONE (2026-10-07), VALIDATED
**Hypothesis:** HDBSCAN on ticket embeddings produces clusters corresponding to distinct support issues.
**Setup (final):** All 19,994 ticket body embeddings (768-dim) → **UMAP** (n_components=5, n_neighbors=15, min_dist=0.0, metric=cosine, random_state=42) → **HDBSCAN** (min_cluster_size=30). Code: `clustering/cluster.py`, `clustering/evaluate.py`.
**Key finding — dimensionality reduction is mandatory:** HDBSCAN directly on 768-dim was computationally intractable (ran for a long time, no result). UMAP→HDBSCAN finished in ~2 min. This is the curse of dimensionality showing up as *slowness*, not just quality.
**Result:** 79 clusters, 21.4% noise.
**Evaluation — the yardstick matters:**
  - vs `queue` (administrative label): 39.5% purity, homogeneity 0.163, NMI 0.117 → LOW
  - vs `tags` (semantic label): **85.1% dominant-tag coverage** → STRONG
  - Specific discriminative tags per cluster: Login 96%, Billing 95%, Security 92%, Network 87%.
**Conclusion:** Clustering successfully discovers coherent semantic topics. Low queue score is NOT failure — `queue` is a routing label, not a content label (proven: Billing, the one semantic queue, scored 96%; Cluster 0 looked "muddy" at 39% queue but is 92% Security by tag). Clusters capture problem content, which is what a knowledge base needs.
**Not done:** Silhouette score (used extrinsic label-based metrics instead, which the ground-truth labels made possible). K-Means / BERTopic comparison not run.
**Status:** DONE — clustering validated.

### Decision D-006
**Date:** 2026-10-07
**Decision:** Use UMAP (not PCA) for dimensionality reduction before clustering. Added `umap-learn` dependency.
**Reason:** UMAP preserves local neighborhood structure (what density clustering needs); PCA preserves only global variance. UMAP→HDBSCAN made clustering both tractable and high-quality (85% tag coverage).
**Status:** DECIDED

### Cluster summarization built + first run (2026-10-07)
**Component:** `clustering/summarize.py` + `cluster_summary_prompt` in `utils/prompts.py`. For the top 15 clusters (by size), picks the 8 centroid-nearest tickets, sends problem+resolution to Groq, gets back JSON {label, issue, cause, resolution}. Saved to `clustering/cluster_summaries.json`.
**Result:** 15 coherent knowledge-base entries. Labels/issues/causes are specific and grounded (e.g., "Login failure after update", "Unexpected invoice charges", "Device Network Disconnections").
**KEY FINDING — faithful summaries expose a data ceiling on resolutions:** Almost all *technical* clusters resolve to the same generic text ("ask for details, schedule a call, investigate") — NOT actual fixes. This is NOT a pipeline bug: the dataset's agent `answer` fields are mostly first-response *triage*, not final resolutions, and the LLM faithfully reflects that (the "don't invent steps" instruction working).
  - **Proof of faithfulness:** clusters where agents gave *real* content have specific resolutions — Cluster 44 (security) → "AES-256, RBAC, firewalls, HIPAA"; Cluster 13 (marketing) → "SEO, email campaigns, content". Where answers were triage, summaries are generic. The variation tracks the data, not the code.
  - **Implication:** rich resolutions need source data with full resolution threads (conversation → fix), not a better prompt. A real limitation of synthetic/triage-only answers.
**Minor:** Cluster 0 (2,929, broad Security) got labeled narrowly "Medical Data Breach" — 8 centroid samples were hospital-heavy. Large clusters need more/spread-out samples for representative labels. → sampling improvement next.

### Lesson L-007
Faithful LLM summarization makes source-data quality visible. Generic outputs can mean the *data* is generic, not that the model failed. Verify by contrast (do any clusters produce specific output?) before blaming the pipeline.

### Knowledge base connected to answering — DONE (2026-10-07)
**Component:** `rag/knowledge_base.py` — loads `cluster_summaries.json`, embeds each topic's `issue`, matches a query to the best topic via cosine similarity with a 0.4 threshold (so irrelevant topics are never forced). Wired into `retriever.retrieve_context` (adds a `=== RELEVANT KNOWLEDGE BASE TOPIC ===` section), threaded through `agent.AgentState.kb_topic`, surfaced in CLI as `[Matched topic: X (Y% match)]`.
**Closes the core loop:** discover topics from raw tickets → match a new question to a topic → use that topic's distilled knowledge in the answer AND show it to the user.
**Verified end-to-end (2026-10-07):**
  - "I can't log in after the latest update" → matched "Login Failure After Update" (67%), answer grounded, cross-lingual sources (German login tickets for an English query).
  - "how do I change my email address?" → NO topic matched (below threshold, correct — no such topic in the 15); honest "not enough info" fallback; Bug-3 retry visibly escalated to top_k=10 (10 sources on attempt 2).
**Honest limitation:** The KB's *visible* contribution is the surfaced topic label; its influence on answer TEXT is subtle because the KB resolutions are generic (same data ceiling as L-007). Stronger KB influence needs richer source resolutions or a KB-weighted prompt.
**Coverage note:** All 79 clusters now summarized (2026-10-07) — full KB coverage. `summarize.py` is resumable (skips already-done clusters, saves after each) and retries up to 60s to ride out Groq's per-minute token limit; the first all-79 run left 4 small clusters unfilled on rate-limit, a resumed run completed them.

### Scope guardrail fix — DONE (2026-10-07)
**Bug found:** Off-topic questions ("how to make eggs?", "where is New Delhi?") were answered from the LLM's general knowledge. The evaluator *correctly* flagged context insufficient (NO), but the "generate anyway" fallback produced an off-topic answer because `answer_generation_prompt` was a generic "helpful assistant" that only weakly said "don't make up info".
**Fix:** Rewrote `answer_generation_prompt` — scoped to customer support, strict grounding (answer ONLY from context, no outside knowledge), and an explicit decline when context is irrelevant OR the question is off-topic. No graph-flow change needed: the fallback now generates a graceful decline instead of an off-topic answer.
**Verified:** eggs + New Delhi → decline; "app keeps crashing" + "login after update" → still answer correctly with matched topics. No regression.
**Minor future opt:** off-topic queries still run 2 retries before declining. Could short-circuit when KB match is None and first eval is NO.

### Phase 8 — Retrieval baselines (Experiment E-004) — DONE (2026-10-07)
**Component:** `evaluation/retrieval_eval.py`. Uses 150 sampled stored ticket embeddings as queries (excluding self by text), measures **tag-precision@5** (fraction of top-5 retrieved sharing ≥1 tag with the query) for three strategies. Hybrid = Reciprocal Rank Fusion of vector + BM25 rankings (no MMR, for a clean comparison).
**Result:**
  - Vector-only : 97.1%
  - BM25-only   : 95.3%
  - Hybrid (RRF): 96.9%
**Finding:** BM25 adds no measurable value — Hybrid (96.9%) ≤ Vector-only (97.1%). Vector search alone is as good.
**Caveats:** (1) Metric is lenient — tags are common (~5/ticket), so scores are high and bunched; but the *relative* vector-vs-hybrid comparison is still fair. (2) BM25's real strength (exact-term matching: error codes, product names) is NOT probed by a random sample, so this doesn't rule out BM25 value for exact-code queries.

### Decision D-007
**Date:** 2026-10-07
**Decision:** Keep BM25 / hybrid retrieval, despite E-004 showing no measured improvement over vector-only.
**Reason:** The eval metric doesn't test BM25's one real advantage (exact-term matching of error codes / product names), and BM25 is already built and working. Low cost to keep as a safety net.
**Revisit if:** simplification becomes a priority, or a stricter/exact-term eval confirms BM25 never helps.
**Status:** DECIDED

### Decision D-008 — Knowledge graph CUT (2026-10-07). Resolves D-003.
**Decision:** Remove the knowledge graph entirely rather than validate it.
**Why (reasoning, cost aside):** The graph is a poor *fit* for a local-Q&A support bot, independent of cost.
  - The bot's job is similarity Q&A (find similar past resolutions) — vectors already do this at 97% (E-004), and the clustering/KB adds topic structure. Graphs win at *global/aggregative* corpus questions (GraphRAG), not *local* "fix my problem" questions.
  - The graph's one genuine edge (linking related-but-not-textually-similar issues via explicit relationships) is marginal for self-contained support questions.
  - It was **dead code**: `ingest-tickets` never built a graph, so it returned empty on every query. In-memory only, FAQ-oriented entity schema unsuited to messy tickets.
  - Even ignoring LLM cost, an LLM-extracted graph over messy multilingual tickets would be noisy — a bad graph can *hurt* retrieval. And it's redundant with the already-validated clustering/KB route to structured knowledge.
**Removed:** `ingestion/graph_builder.py`, `rag/graph_rag.py` (deleted); `networkx` dependency; all graph refs in `retriever.py`, `agent.py`, `cli.py`, `prompts.py` (entity_extraction_prompt). Imports verified clean; `langgraph` (the agent state machine) is unrelated and kept.
**Status:** DONE. D-003 resolved (the "only keep if experiments show it helps" bar was never cleared, and the cost to clear it far exceeded the expected payoff given a working alternative).
**Hypothesis:** MMR with lambda=0.5 improves diversity of retrieved chunks without significantly reducing relevance.
**Setup:** For 10 queries, retrieve with and without MMR. Compare: (a) manual relevance rating, (b) redundancy rate (% of retrieved chunks that are near-duplicates).
**Status:** PENDING

---

## 11. Implementation Progress

| Component | Status |
|---|---|
| CLI | Done (basic) |
| Document loader (PDF/DOCX/TXT) | Done |
| Text chunker | Done (naive, needs improvement) |
| Multilingual embedder | Done |
| ChromaDB vector store | Done |
| BM25 (in-memory) | Fixed — rebuilt from ChromaDB on startup (Bug 2) |
| MMR | Fixed — reuses ChromaDB embeddings (Bug 5) |
| Knowledge graph (NetworkX) | Partially broken — in-memory only, graph persistence not addressed |
| Graph search | Fixed — semantic similarity matching (Bug 4) |
| LangGraph agent | Fixed — retry uses larger top_k (Bug 3) |
| Language detection | Done |
| Ticket CSV/JSON loader | NOT STARTED |
| Customer/agent parser | NOT STARTED |
| PII cleaning | NOT STARTED |
| Clustering (HDBSCAN) | NOT STARTED |
| Cluster summarization | NOT STARTED |
| Evaluation framework | NOT STARTED |

---

## 12. Research Notes

### Multilingual Embeddings
`paraphrase-multilingual-mpnet-base-v2` (SBERT) supports 50+ languages and produces a single embedding space where semantically similar sentences in different languages are close together. This means a Hindi query can retrieve an English document if they mean the same thing. This is a strong foundation for cross-lingual retrieval.

Alternative to evaluate: `intfloat/multilingual-e5-large` — consistently outperforms paraphrase-multilingual-mpnet-base-v2 on MTEB multilingual benchmarks as of 2024, but is larger (560M vs 278M parameters).

### BM25 and Its Limitations for Multilingual Use
BM25 (`rank_bm25`) uses tokenized word overlap. For English, simple whitespace tokenization is adequate. For languages without clear word boundaries (Chinese, Japanese) or with morphological complexity (Hindi, Arabic), this approach will fail — a Hindi user's query tokens will not match the English document tokens. BM25 for multilingual retrieval requires language-aware tokenization or should be restricted to monolingual retrieval.

### HDBSCAN vs. K-Means for Support Tickets
K-Means requires specifying K in advance. The number of issue categories in a real support dataset is unknown. K-Means also forces every point into a cluster — noisy/irrelevant tickets get assigned to the nearest cluster rather than being identified as outliers. HDBSCAN does not require K and identifies noise points. This makes HDBSCAN a more defensible first choice for unknown-category ticket clustering.

However: HDBSCAN's quality depends heavily on the `min_cluster_size` and `min_samples` hyperparameters, and the density structure of the embedding space. It requires experimentation.

BERTopic (by Maarten Grootendorst) wraps HDBSCAN with TF-IDF-based topic representation and is worth evaluating alongside raw HDBSCAN, as it provides more interpretable cluster labels.

### PII Removal Options
- **Regex**: Fast, deterministic, easy to understand. Misses context-dependent PII (e.g., "Contact John at extension 5432" — 5432 looks like an account number to regex).
- **spaCy NER**: Identifies PERSON, ORG, GPE entities. More context-aware than regex, but may miss domain-specific PII (internal ticket IDs, account numbers).
- **Microsoft Presidio**: Purpose-built PII detection library. Combines regex, NER, and context rules. Supports multiple languages. Worth evaluating.
- **LLM-based**: Expensive, slow, non-deterministic. Overkill for PII removal unless the dataset is very small and domain-specific PII is unusual.
- **Hybrid (Presidio + regex)**: Likely the best practical approach.

---

## 13. Lessons Learned

- **L-001**: A functional RAG system over clean text is not the same as a system that ingests raw tickets. Always verify the actual input format matches the stated problem.
- **L-002**: Global in-memory state (BM25 index, NetworkX graph) creates silent degradation after process restart. Any state that needs to persist across process boundaries must be explicitly serialized.
- **L-003**: Before adding complexity (agent loops, graph traversal), verify that the simpler components are actually working correctly. A broken foundation makes new features impossible to evaluate.
- **L-004**: BM25 has no persistence mechanism — it is always in-memory. The correct approach is to treat ChromaDB as the single source of truth and rebuild BM25 from it on startup. Never serialize BM25 separately.
- **L-005**: ChromaDB's `col.query()` returns embeddings if you ask for them via `include=["embeddings"]`. Always check what a library returns before computing things yourself.
- **L-006**: Semantic similarity for entity matching requires a threshold. 0.7 is a reasonable starting point for short entity names, but it should be validated experimentally once real data exists.

---

## 14. Current TODO (Actionable)

**Immediate (Phase 0):**
1. [x] Fix Groq model name — confirmed `openai/gpt-oss-20b` is valid (NOT A BUG)
2. [x] BM25 persistence — rebuilt from ChromaDB on startup (Bug 2 fixed)
3. [x] Agent retry — now uses top_k=10 on retry (Bug 3 fixed)
4. [x] Graph node matching — semantic similarity with 0.7 threshold (Bug 4 fixed)
5. [x] MMR efficiency — reuses ChromaDB embeddings (Bug 5 fixed)
6. [x] Dataset selected — Kaggle multilingual IT support (20k file). See D-004. Data profiled via explore.py.

**Next (Phase 1):**
7. [x] Build CSV ticket loader → Ticket dataclass (ticket_loader.py). See D-004 schema.
8. [x] HTML stripping (remove `<br>`) — strip_html in cleaner.py
9. [x] PII mask normalization — normalize_pii in cleaner.py, 99.8% coverage
10. [x] Customer/agent separation — NOT NEEDED, columns already separate (body=customer, answer=agent)
11. [x] Decide embedding text — body only (D-005)

**Integration — ingestion side DONE (2026-10-06):**
12. [x] Wire ticket pipeline: load_tickets → clean (body/answer) → embed body → store with metadata. Orchestrated in `cli.ingest_tickets()`.
13. [x] Store answer + metadata as payload — metadata = {answer, subject, language, queue, type, priority, tags-joined}. Verified via ChromaDB get().
14. [x] CLI command `ingest-tickets --file <csv> [--limit N]` added.
15. [x] No chunking — one vector per ticket (body). Accept ~128-token truncation. (D-005)

Architecture: `vector_store.add_documents(ids, documents, metadatas)` is the generic storage primitive; `add_chunks` now delegates to it; `cleaner.clean_text()` composes the three cleaning steps.

**Integration — retrieval side DONE (2026-10-06):**
16. [x] Fixed `search_chunks` — carries full `metadata` (both vector + BM25). `_rebuild_bm25` now keeps `bm25_metadata` parallel to the corpus so BM25 matches have metadata too.
17. [x] Surface `answer` — `format_vector_results` now emits `[Ticket N — Queue/Type]` + Problem + Resolution.
18. [x] Answers flow via LLM synthesis from retrieved resolutions (D-005 follow-through; chosen over verbatim return).
19. [x] CLI "sources" display shows `queue`; retriever context header = "RELEVANT PAST TICKETS".

**Verified end-to-end (2026-10-06):** 100-ticket ingest, English query "data analytics platform keeps crashing" retrieved 5 relevant tickets INCLUDING a German one (cross-lingual retrieval proven — the headline multilingual feature). Answer grounded, no crash.

**Known limitations / future refinements:**
- Answers are grounded but **generic** — the prompt says "use the context" but doesn't push the LLM to cite the specific retrieved resolutions. Prompt-tuning opportunity.
- `ingest-tickets` does NOT build a knowledge graph, so graph context is always empty for tickets. Graph remains deferred (D-003).
- Full 20k not yet ingested (only 100). Embedding all 20k on CPU is slow (~1 hr).

---

## 15. Future Ideas (Intentionally Postponed)

- **Streaming responses**: Not needed for a portfolio demo. Add after everything else works.
- **Web UI**: Build after the core pipeline is validated end-to-end.
- **Real-time ticket ingestion**: Out of scope for current phase.
- **Fine-tuning embedding models**: Consider only after baseline evaluation shows the pre-trained multilingual model is insufficient.
- **Neo4j or other graph databases**: Evaluate only if in-memory NetworkX is proven to be a bottleneck or if the graph provides proven value.
- **Cross-encoder reranking models**: Evaluate after hybrid retrieval + MMR are evaluated. May replace MMR rather than add to it.
