import argparse
import os
from dotenv import load_dotenv

from ingestion.loader import load_document
from ingestion.chunker import chunk_text
from ingestion.vector_store import add_chunks, add_documents, get_chunk_count
from ingestion.ticket_loader import load_tickets
from ingestion.cleaner import clean_text
from rag.agent import run_agent

load_dotenv()


#=========================================================================================
def ingest(file_path: str):
    print(f"\nLoading document: {file_path}")
    text = load_document(file_path)

    print(f"Document loaded. Total characters: {len(text)}")

    print("\nChunking text...")
    chunks = chunk_text(text)

    print(f"Created {len(chunks)} chunks")

    print("\nStoring chunks in vector store...")
    source_name = os.path.basename(file_path)
    add_chunks(chunks, source_file=source_name)

    print("\n--- Ingestion Complete ---")
    print(f"Chunks stored : {get_chunk_count()}")


#=========================================================================================
def ingest_tickets(csv_path: str, limit: int = None):
    print(f"\nLoading tickets from: {csv_path}")
    tickets = load_tickets(csv_path)

    if limit:
        tickets = tickets[:limit]

    print(f"Processing {len(tickets)} tickets")

    ids = []
    documents = []
    metadatas = []

    for i, ticket in enumerate(tickets):
        clean_body = clean_text(ticket.body)
        clean_answer = clean_text(ticket.answer)

        ids.append(f"ticket_{i}")
        documents.append(clean_body)
        metadatas.append({
            "answer": clean_answer,
            "subject": ticket.subject,
            "language": ticket.language,
            "queue": ticket.queue,
            "type": ticket.type,
            "priority": ticket.priority,
            "tags": ",".join(ticket.tags),
        })

    print("\nStoring tickets in vector store...")
    add_documents(ids, documents, metadatas)

    print("\n--- Ticket Ingestion Complete ---")
    print(f"Tickets stored: {get_chunk_count()}")


#=========================================================================================
def chat():
    print("\n--- Customer Support Bot ---")
    print("Type your question in any language.")
    print("Type 'exit' to quit.\n")

    while True:
        user_input = input("You: ").strip()

        if not user_input:
            continue

        if user_input.lower() == "exit":
            print("Goodbye!")
            break

        print()
        result = run_agent(user_input)

        print(f"\nBot ({result['language']}): {result['answer']}")

        if result.get("kb_topic"):
            topic = result["kb_topic"]
            print(f"\n[Matched topic: {topic['label']} ({topic['score']:.0%} match)]")

        print(f"\n[Searched {result['iterations']} time(s)]")

        # Show sources
        if result["vector_chunks"]:
            print("\n--- Sources ---")
            for chunk in result["vector_chunks"]:
                metadata = chunk.get("metadata", {})
                queue = metadata.get("queue", "unknown")
                text_preview = chunk.get("text", "")[:100]
                print(f"  [{queue}] {text_preview}...")

        print("\n" + "-" * 50 + "\n")


#=========================================================================================
def inspect():
    print(f"\n--- Vector Store ---")
    print(f"Total chunks stored: {get_chunk_count()}")


#=========================================================================================
def main():
    parser = argparse.ArgumentParser(description="Multilingual Customer Support Bot")

    subparsers = parser.add_subparsers(dest="command")

    # Ingest command
    ingest_parser = subparsers.add_parser("ingest", help="Load and process a document")
    ingest_parser.add_argument("--file", required=True, help="Path to the document")

    # Ingest tickets command
    tickets_parser = subparsers.add_parser("ingest-tickets", help="Load and process a ticket CSV")
    tickets_parser.add_argument("--file", required=True, help="Path to the ticket CSV")
    tickets_parser.add_argument("--limit", type=int, default=None, help="Only ingest the first N tickets")

    # Chat command
    subparsers.add_parser("chat", help="Start the chat loop")

    # Inspect command
    subparsers.add_parser("inspect", help="Show vector store summary")

    args = parser.parse_args()

    if args.command == "ingest":
        ingest(args.file)

    elif args.command == "ingest-tickets":
        ingest_tickets(args.file, args.limit)

    elif args.command == "chat":
        chat()

    elif args.command == "inspect":
        inspect()

    else:
        parser.print_help()


#=========================================================================================
if __name__ == "__main__":
    main()