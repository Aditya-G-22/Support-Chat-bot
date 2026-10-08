#=========================================================================================
# Used in: rag/agent.py
# Purpose: Ask LLM if the retrieved context is enough to answer the question
def evaluation_prompt(query: str, context: str) -> str:
    prompt = f"""
You are evaluating whether the retrieved context is enough to answer the user's question.

User question: {query}

Retrieved context:
{context}

Is the context above sufficient to give a helpful and accurate answer?
Reply with only one word: YES or NO
"""
    return prompt


#=========================================================================================
# Used in: rag/agent.py
# Purpose: Generate the final answer in the user's language
def answer_generation_prompt(query: str, context: str, language: str) -> str:
    prompt = f"""
You are a customer support assistant for our company's products and services.
You ONLY help with customer-support questions, using the context provided below.

Rules:
- Answer ONLY using the information in the context below. Do not use outside knowledge.
- If the context does not contain the information needed, OR the question is not a
  customer-support question about our products or services, do NOT answer it.
  Instead, politely say you can only help with support questions about our
  products and services.
- Always reply in this language: {language}

Context:
{context}

User question: {query}

Answer:
"""
    return prompt


#=========================================================================================
# Used in: clustering/summarize.py
# Purpose: Distill a cluster of similar tickets into one knowledge-base entry
def cluster_summary_prompt(samples: list[dict]) -> str:
    tickets_text = ""
    for i, s in enumerate(samples, 1):
        problem = s["problem"][:500]
        resolution = s["resolution"][:500]
        tickets_text += f"\n[{i}] Problem: {problem}\n    Resolution: {resolution}\n"

    prompt = f"""You are building a knowledge base from customer support tickets.
The tickets below all come from the same cluster — they describe similar problems.
Summarize them into ONE knowledge base entry.

Return ONLY a valid JSON object in this exact format:
{{
    "label": "short topic name, 3-5 words",
    "issue": "the common problem these tickets describe",
    "cause": "the most likely underlying cause",
    "resolution": "how it is typically resolved"
}}

Base the resolution ONLY on the actual agent resolutions shown — do not invent steps.
Write the summary in English even if some tickets are in another language.

Tickets:
{tickets_text}
"""
    return prompt