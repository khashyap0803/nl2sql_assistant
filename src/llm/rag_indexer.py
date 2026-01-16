import os
import sys
from pathlib import Path
from typing import List, Optional

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from src.utils.logger import logger


class RAGIndexer:

    def __init__(self, schema_file: str = "data/schema_docs.txt"):
        self.schema_file = schema_file
        self.documents = []
        self.enabled = False
        
        if self._load_schema():
            self.enabled = True
            logger.i("RAG_INIT", f"Loaded {len(self.documents)} schema sections")

    def _load_schema(self) -> bool:
        try:
            if not Path(self.schema_file).exists():
                logger.e("RAG_INIT", f"Schema file not found: {self.schema_file}")
                return False
            
            with open(self.schema_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            self.documents = [doc.strip() for doc in content.split('\n\n') if doc.strip()]
            
            return True
            
        except Exception as e:
            logger.e("RAG_INIT", f"Failed to load schema: {e}")
            return False

    def load_index(self, index_dir: str = None) -> bool:
        return self._load_schema()

    def create_index(self, schema_file: str = None) -> bool:
        if schema_file:
            self.schema_file = schema_file
        return self._load_schema()

    def search(self, query: str, k: int = 5) -> List[str]:
        if not self.enabled or not self.documents:
            return []
        
        query_lower = query.lower()
        query_words = set(query_lower.split())
        
        scored_docs = []
        for doc in self.documents:
            doc_lower = doc.lower()
            doc_words = set(doc_lower.split())
            
            matches = len(query_words & doc_words)
            
            if query_lower in doc_lower:
                matches += 10
            
            for term in ['select', 'sum', 'count', 'avg', 'group', 'where', 'order']:
                if term in query_lower and term in doc_lower:
                    matches += 2
            
            if matches > 0:
                scored_docs.append((matches, doc))
        
        scored_docs.sort(key=lambda x: x[0], reverse=True)
        
        return [doc for _, doc in scored_docs[:k]]

    def get_context(self, query: str, k: int = 5) -> str:
        if not self.enabled:
            return self._get_full_context()
        
        results = self.search(query, k)
        
        if results:
            context = "\n\n".join(results)
            logger.d("RAG_SEARCH", f"Found {len(results)} relevant sections")
            return context
        
        return self._get_full_context()

    def get_relevant_context(self, query: str, top_k: int = 5) -> str:
        return self.get_context(query, k=top_k)

    def _get_full_context(self) -> str:
        if self.documents:
            return "\n\n".join(self.documents[:10])
        
        return """Database Schema:
Table: sales
Columns: 
- id (INTEGER, Primary Key)
- date (DATE, format YYYY-MM-DD)
- amount (DECIMAL, sales amount in Rs)
- product (VARCHAR: Laptop, Desktop, Monitor, Keyboard, Mouse, Headphones, Webcam, Tablet, Smartphone, Router)
- region (VARCHAR: North, South, East, West)
- quantity (INTEGER, units sold)
- customer_type (VARCHAR: Regular, Business, Premium)

Common Patterns:
- Total: SELECT SUM(amount) FROM sales
- By product: SELECT product, SUM(amount) FROM sales GROUP BY product
- By region: SELECT region, SUM(amount) FROM sales GROUP BY region
"""


def test_rag_indexer():
    print("=" * 60)
    print("Simple RAG Indexer Test")
    print("=" * 60)
    
    indexer = RAGIndexer()
    
    if indexer.enabled:
        print(f"Loaded {len(indexer.documents)} sections")
        
        test_queries = [
            "total sales",
            "sales by region",
            "top products"
        ]
        
        for query in test_queries:
            print(f"\nQuery: {query}")
            context = indexer.get_context(query, k=2)
            print(f"Context length: {len(context)} chars")
            print(f"Preview: {context[:200]}...")
    else:
        print("Failed to initialize RAG indexer")


if __name__ == "__main__":
    test_rag_indexer()
