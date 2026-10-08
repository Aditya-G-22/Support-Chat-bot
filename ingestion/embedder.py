from sentence_transformers import SentenceTransformer

# This model supports 50+ languages
MODEL_NAME = "paraphrase-multilingual-mpnet-base-v2"
model = None

#========================================================================================
def load_model() :
    global model

    if model is None :
        print("Loading embedding model ..... (First run takes a minute.....)")
        model = SentenceTransformer(MODEL_NAME)
        print("Model loaded.")
    return model

#========================================================================================
# For embedding many chunks during ingestion
def embed_texts(texts : list[str]) -> list[list[float]] :
    embedding_model = load_model()

    embeddings = embedding_model.encode(texts, show_progress_bar = True)

    # Convert numpy arrays to plain python lists for ChromaDB
    embeddings_as_lists = [embedding.tolist() for embedding in embeddings]

    return embeddings_as_lists

#========================================================================================
# For embedding one query at chat time
def embed_single(text : str) -> list[float] :
    embedding_model = load_model()

    embeddings = embedding_model.encode(text)
    return embeddings.tolist()
#========================================================================================