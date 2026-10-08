import os
from typing import TypedDict
from dotenv import load_dotenv
from groq import Groq
from langgraph.graph import StateGraph, END
from rag.retriever import retrieve_context
from utils.language import detect_language
from utils.prompts import evaluation_prompt, answer_generation_prompt

load_dotenv()

groq_client = Groq(api_key=os.getenv("GROQ_API_KEY"))

MAX_ITERATIONS = 2  # how many times the agent can re-search before giving up


#=========================================================================================
# State is a shared dictionary that flows through every node in the graph
class AgentState(TypedDict):
    query           : str
    language        : str
    context         : str
    vector_chunks   : list
    kb_topic        : dict
    answer          : str
    iterations      : int
    is_sufficient   : bool


#=========================================================================================
# Node 1: Detect what language the user is writing in
def node_detect_language(state: AgentState) -> AgentState:
    print("\n[Agent] Detecting language...")

    detected_language = detect_language(state["query"])
    print(f"[Agent] Language detected: {detected_language}")

    state["language"] = detected_language
    state["iterations"] = 0
    state["is_sufficient"] = False

    return state


#=========================================================================================
# Node 2: Run vector search + graph search and store results in state
def node_retrieve(state: AgentState) -> AgentState:
    iteration_number = state["iterations"] + 1
    top_k = 5 if iteration_number == 1 else 10
    print(f"\n[Agent] Retrieving context (attempt {iteration_number})...")

    results = retrieve_context(state["query"], top_k = top_k)

    state["context"]        = results["combined_context"]
    state["vector_chunks"]  = results["vector_chunks"]
    state["kb_topic"]       = results.get("kb_topic")
    state["iterations"]     = iteration_number

    return state


#=========================================================================================
# Node 3: Ask the LLM if the retrieved context is enough to answer the question
def node_evaluate(state: AgentState) -> AgentState:
    print("\n[Agent] Evaluating if context is sufficient...")

    prompt = evaluation_prompt(state["query"], state["context"])

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0
    )

    verdict = response.choices[0].message.content.strip().upper()
    print(f"[Agent] Context sufficient: {verdict}")

    state["is_sufficient"] = verdict == "YES"

    return state


#=========================================================================================
# Node 4: Generate the final answer in the user's language
def node_generate_answer(state: AgentState) -> AgentState:
    print("\n[Agent] Generating final answer...")

    prompt = answer_generation_prompt(state["query"], state["context"], state["language"])

    response = groq_client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[{"role": "user", "content": prompt}],
        temperature=0.3
    )

    answer = response.choices[0].message.content.strip()
    state["answer"] = answer

    return state


#=========================================================================================
# Decision function: should we search again or move to generating the answer?
def decide_next_step(state: AgentState) -> str:
    if state["is_sufficient"]:
        print("[Agent] Context is good. Moving to answer generation.")
        return "generate"

    if state["iterations"] >= MAX_ITERATIONS:
        print("[Agent] Max search attempts reached. Generating answer with what we have.")
        return "generate"

    print("[Agent] Context not sufficient. Searching again...")
    return "retrieve_again"


#=========================================================================================
# Build and compile the LangGraph agent
def build_agent():
    graph = StateGraph(AgentState)

    # Add all nodes
    graph.add_node("detect_language",   node_detect_language)
    graph.add_node("retrieve",          node_retrieve)
    graph.add_node("evaluate",          node_evaluate)
    graph.add_node("generate_answer",   node_generate_answer)

    # Add edges (flow between nodes)
    graph.set_entry_point("detect_language")
    graph.add_edge("detect_language", "retrieve")
    graph.add_edge("retrieve", "evaluate")

    # Conditional edge: after evaluation, either search again or generate answer
    graph.add_conditional_edges(
        "evaluate",
        decide_next_step,
        {
            "generate"      : "generate_answer",
            "retrieve_again": "retrieve"
        }
    )

    graph.add_edge("generate_answer", END)

    return graph.compile()


#=========================================================================================
# Main function to run the agent on a query
def run_agent(query: str) -> dict:
    agent = build_agent()

    initial_state = AgentState(
        query           = query,
        language        = "",
        context         = "",
        vector_chunks   = [],
        kb_topic        = None,
        answer          = "",
        iterations      = 0,
        is_sufficient   = False
    )

    final_state = agent.invoke(initial_state)

    return {
        "answer"        : final_state["answer"],
        "language"      : final_state["language"],
        "iterations"    : final_state["iterations"],
        "vector_chunks" : final_state["vector_chunks"],
        "kb_topic"      : final_state.get("kb_topic")
    }