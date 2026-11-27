# GridGuard AI & RAG Data Directory

This directory stores all local persistent data for the **GridGuard AI & RAG Engine**:

1. **`manuals/`**: Stores uploaded original PDF catalogs, engineering manuals, and datasheets from substation equipment manufacturers (ABB, Siemens, Schneider Electric, etc.) ingested through `POST /ingest/manual`.
2. **`chroma_db/`**: Persistent ChromaDB vector database storage containing document embeddings, text chunks, and metadata indexed with cosine distance metric.

> **Note**: Actual PDF files and binary database files in this directory are git-ignored to prevent bloating repository size. Use `.gitkeep` files to preserve directory structure in version control.
