from ingestion.vector_store import search_chunks
from rag.knowledge_base import search_kb, format_kb


#=========================================================================================
def retrieve_context(query: str, top_k: int = 5) -> dict:
    # Match the query to a discovered knowledge-base topic, then pull specific
    # past tickets. Both feed the LLM.

    print("Searching knowledge base...")
    kb_entry = search_kb(query)

    print("Searching vector store...")
    vector_results = search_chunks(query, top_k=top_k)

    kb_context = format_kb(kb_entry)
    vector_context = format_vector_results(vector_results)

    combined_context = build_combined_context(kb_context, vector_context)

    return {
        "combined_context": combined_context,
        "vector_chunks": vector_results,
        "kb_topic": kb_entry,
    }


#=========================================================================================
def format_vector_results(vector_results: list[dict]) -> str:
    if not vector_results:
        return "No relevant past tickets found."

    lines = ["Similar past support tickets:"]

    for i, chunk in enumerate(vector_results):
        metadata = chunk.get("metadata", {})
        problem = chunk.get("text", "")
        resolution = metadata.get("answer", "")
        queue = metadata.get("queue", "")
        ticket_type = metadata.get("type", "")

        header = f"\n[Ticket {i + 1}"
        if queue or ticket_type:
            header += f" — {queue} / {ticket_type}"
        header += "]"

        lines.append(header)
        lines.append(f"Problem: {problem}")
        if resolution:
            lines.append(f"Resolution: {resolution}")

    return "\n".join(lines)


#=========================================================================================
def build_combined_context(kb_context: str, vector_context: str) -> str:
    sections = []

    if kb_context:
        sections.append("=== RELEVANT KNOWLEDGE BASE TOPIC ===")
        sections.append(kb_context)
        sections.append("")

    sections.append("=== RELEVANT PAST TICKETS ===")
    sections.append(vector_context)

    return "\n".join(sections)