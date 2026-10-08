from ingestion.vector_store import get_collection

col = get_collection()
result = col.get(ids=["ticket_0"], include=["documents", "metadatas"])

print("DOCUMENT (embedded body):")
print(result["documents"][0])
print("\nMETADATA:")
for key, value in result["metadatas"][0].items():
    print(f"  {key}: {value}")