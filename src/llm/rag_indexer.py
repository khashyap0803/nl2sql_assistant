"""
RAG Indexer - FAISS-based vector store for schema documentation
Indexes database schema information for context-aware query generation
"""

import os
import sys
from pathlib import Path
from typing import List, Dict, Optional
import pickle

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.logger import logger

# Try to import FAISS and sentence-transformers
try:
    import faiss
    import numpy as np
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    logger.w("RAG_INIT", "FAISS not installed - RAG features disabled")
    logger.i("RAG_INIT", "To enable: pip install faiss-cpu")

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    logger.w("RAG_INIT", "sentence-transformers not installed - RAG features disabled")
    logger.i("RAG_INIT", "To enable: pip install sentence-transformers")


class RAGIndexer:
    """
    RAG (Retrieval-Augmented Generation) indexer for database schema
    Uses FAISS for efficient similarity search
    """

    def __init__(self, model_name: str = "sentence-transformers/all-MiniLM-L6-v2"):
        """
        Initialize RAG indexer

        Args:
            model_name: Sentence transformer model to use for embeddings
        """
        self.model_name = model_name
        self.model = None
        self.index = None
        self.documents = []
        self.enabled = FAISS_AVAILABLE and SENTENCE_TRANSFORMERS_AVAILABLE

        if not self.enabled:
            logger.w("RAG_INIT", "RAG features disabled - missing dependencies")
            return

        try:
            logger.i("RAG_INIT", f"Loading embedding model: {model_name}")
            self.model = SentenceTransformer(model_name)
            logger.i("RAG_INIT", "Embedding model loaded successfully")
        except Exception as e:
            logger.e("RAG_INIT", f"Failed to load embedding model: {str(e)}", e)
            self.enabled = False

    def create_index(self, schema_file: str = "data/schema_docs.txt") -> bool:
        """
        Create FAISS index from schema documentation

        Args:
            schema_file: Path to schema documentation file

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            logger.w("RAG_INDEX", "Cannot create index - RAG not enabled")
            return False

        try:
            logger.i("RAG_INDEX", f"Creating FAISS index from {schema_file}")

            # Check if file exists
            if not Path(schema_file).exists():
                logger.e("RAG_INDEX", f"Schema file not found: {schema_file}")
                return False

            # Read schema documentation
            with open(schema_file, 'r', encoding='utf-8') as f:
                content = f.read()

            # Split into chunks (documents)
            self.documents = self._split_into_chunks(content)
            logger.d("RAG_INDEX", f"Split schema into {len(self.documents)} chunks")

            # Generate embeddings
            logger.i("RAG_INDEX", "Generating embeddings...")
            embeddings = self.model.encode(self.documents, show_progress_bar=False)
            embeddings = embeddings.astype('float32')

            # Create FAISS index
            dimension = embeddings.shape[1]
            self.index = faiss.IndexFlatL2(dimension)
            self.index.add(embeddings)

            logger.i("RAG_INDEX", f"FAISS index created with {self.index.ntotal} vectors")

            # Save index to disk
            self._save_index()

            return True

        except Exception as e:
            logger.e("RAG_INDEX", f"Failed to create index: {str(e)}", e)
            return False

    def load_index(self, index_dir: str = "data/faiss_index") -> bool:
        """
        Load existing FAISS index from disk

        Args:
            index_dir: Directory containing saved index

        Returns:
            True if successful, False otherwise
        """
        if not self.enabled:
            return False

        try:
            index_path = Path(index_dir)

            if not index_path.exists():
                logger.w("RAG_LOAD", f"Index directory not found: {index_dir}")
                logger.i("RAG_LOAD", "Creating new index...")
                return self.create_index()

            logger.i("RAG_LOAD", f"Loading FAISS index from {index_dir}")

            # Load FAISS index
            index_file = index_path / "index.faiss"
            if index_file.exists():
                self.index = faiss.read_index(str(index_file))
            else:
                logger.w("RAG_LOAD", "Index file not found, creating new index")
                return self.create_index()

            # Load documents
            docs_file = index_path / "documents.pkl"
            if docs_file.exists():
                with open(docs_file, 'rb') as f:
                    self.documents = pickle.load(f)
            else:
                logger.w("RAG_LOAD", "Documents file not found, creating new index")
                return self.create_index()

            logger.i("RAG_LOAD", f"Loaded index with {self.index.ntotal} vectors and {len(self.documents)} documents")
            return True

        except Exception as e:
            logger.e("RAG_LOAD", f"Failed to load index: {str(e)}", e)
            logger.i("RAG_LOAD", "Creating new index...")
            return self.create_index()

    def search(self, query: str, k: int = 3) -> List[str]:
        """
        Search for relevant schema documentation

        Args:
            query: Natural language query
            k: Number of results to return

        Returns:
            List of relevant document chunks
        """
        if not self.enabled or self.index is None:
            logger.w("RAG_SEARCH", "Cannot search - index not available")
            return []

        try:
            logger.d("RAG_SEARCH", f"Searching for: '{query}' (top {k} results)")

            # Generate query embedding
            query_embedding = self.model.encode([query], show_progress_bar=False)
            query_embedding = query_embedding.astype('float32')

            # Search FAISS index
            distances, indices = self.index.search(query_embedding, k)

            # Retrieve documents
            results = []
            for idx, distance in zip(indices[0], distances[0]):
                if idx < len(self.documents):
                    results.append(self.documents[idx])
                    logger.d("RAG_SEARCH", f"Match #{len(results)}: distance={distance:.4f}")

            logger.i("RAG_SEARCH", f"Found {len(results)} relevant documents")
            return results

        except Exception as e:
            logger.e("RAG_SEARCH", f"Search failed: {str(e)}", e)
            return []

    def _split_into_chunks(self, text: str, chunk_size: int = 200, overlap: int = 50) -> List[str]:
        """
        Split text into overlapping chunks

        Args:
            text: Text to split
            chunk_size: Maximum characters per chunk
            overlap: Overlap between chunks

        Returns:
            List of text chunks
        """
        # Split by double newlines first (paragraphs)
        paragraphs = text.split('\n\n')

        chunks = []
        current_chunk = ""

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            # If paragraph is small enough, add it
            if len(current_chunk) + len(para) <= chunk_size:
                current_chunk += para + "\n\n"
            else:
                # Save current chunk if not empty
                if current_chunk:
                    chunks.append(current_chunk.strip())

                # Start new chunk with this paragraph
                if len(para) <= chunk_size:
                    current_chunk = para + "\n\n"
                else:
                    # Split long paragraph
                    words = para.split()
                    temp_chunk = ""
                    for word in words:
                        if len(temp_chunk) + len(word) <= chunk_size:
                            temp_chunk += word + " "
                        else:
                            if temp_chunk:
                                chunks.append(temp_chunk.strip())
                            temp_chunk = word + " "
                    current_chunk = temp_chunk

        # Add last chunk
        if current_chunk:
            chunks.append(current_chunk.strip())

        logger.d("RAG_SPLIT", f"Split text into {len(chunks)} chunks")
        return chunks

    def _save_index(self, index_dir: str = "data/faiss_index"):
        """Save FAISS index and documents to disk"""
        try:
            index_path = Path(index_dir)
            index_path.mkdir(parents=True, exist_ok=True)

            # Save FAISS index
            faiss.write_index(self.index, str(index_path / "index.faiss"))

            # Save documents
            with open(index_path / "documents.pkl", 'wb') as f:
                pickle.dump(self.documents, f)

            logger.i("RAG_SAVE", f"Index saved to {index_dir}")

        except Exception as e:
            logger.e("RAG_SAVE", f"Failed to save index: {str(e)}", e)

    def get_context(self, query: str, k: int = 3) -> str:
        """
        Get formatted context for LLM prompt

        Args:
            query: Natural language query
            k: Number of context chunks to retrieve

        Returns:
            Formatted context string
        """
        if not self.enabled:
            # Return basic schema info as fallback
            return self._get_fallback_context()

        results = self.search(query, k)

        if not results:
            return self._get_fallback_context()

        context = "Database Schema Context:\n\n"
        for i, doc in enumerate(results, 1):
            context += f"[Context {i}]\n{doc}\n\n"

        return context.strip()

    def get_relevant_context(self, query: str, top_k: int = 3) -> str:
        """
        Alias for get_context() - for compatibility with nl2sql_converter

        Args:
            query: Natural language query
            top_k: Number of context chunks to retrieve

        Returns:
            Formatted context string
        """
        return self.get_context(query, k=top_k)

    def _get_fallback_context(self) -> str:
        """Return basic schema context when RAG is not available"""
        return """Database Schema:
Table: sales
Columns: id (INTEGER), date (DATE), amount (DECIMAL), product (VARCHAR), region (VARCHAR)

Common patterns:
- Total: SELECT SUM(amount) FROM sales
- By product: SELECT product, SUM(amount) FROM sales GROUP BY product
- By region: SELECT region, SUM(amount) FROM sales GROUP BY region
"""


# Test function
def test_rag_indexer():
    """Test RAG indexer functionality"""
    logger.section("RAG Indexer Test")

    indexer = RAGIndexer()

    if not indexer.enabled:
        print("⚠️  RAG features not available (missing dependencies)")
        print("   Install: pip install faiss-cpu sentence-transformers")
        return

    # Create/load index
    if indexer.load_index():
        print("✓ Index loaded successfully")

        # Test queries
        test_queries = [
            "total sales",
            "sales by region",
            "product information"
        ]

        for query in test_queries:
            print(f"\nQuery: {query}")
            context = indexer.get_context(query, k=2)
            print(f"Context:\n{context[:200]}...")
            print("-" * 60)
    else:
        print("❌ Failed to load/create index")

    logger.separator()


if __name__ == "__main__":
    test_rag_indexer()
