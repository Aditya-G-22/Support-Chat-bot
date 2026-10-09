from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from rag.agent import run_agent

app = FastAPI()

# react dev server (runs on port 5173)
app.add_middleware(
    CORSMiddleware,
    allow_origins = ["http://localhost:5173"],
    allow_methods = ["*"],
    allow_headers = ["*"],
)

class ChatRequest(BaseModel) :
    question : str

@app.post("/chat")
def chat(req : ChatRequest) :
    result = run_agent(req.question)

    source = []
    for chunk in result["vector_chunks"] :
        metadata = chunk.get("metadata", {})
        source.append({
            "queue" : metadata.get("queue", "unknown"),
            "text" : chunk.get("text", "")[:200],
        })

    return {
        "answer" : result["answer"],
        "language" : result["language"],
        "matched_topic" : result.get("kb_topic"),
        "sources" : source
    }