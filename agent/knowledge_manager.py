"""Knowledge base management using ChromaDB directly with lightweight embeddings."""

import os
import re
from pathlib import Path
from typing import List

from agent.settings import AGENT_CONFIG


class SimpleEmbeddingFunction:
    """Lightweight sentence embedding using word-frequency vectorization.
    
    Falls back to a simple TF-IDF-like approach when heavy ML libraries
    aren't available. Good enough for keyword + semantic-ish search over
    a small sysadmin knowledge base.
    """
    
    def __init__(self):
        self.stopwords = {
            'the', 'a', 'an', 'is', 'are', 'was', 'were', 'be', 'been',
            'being', 'have', 'has', 'had', 'do', 'does', 'did', 'will',
            'would', 'could', 'should', 'may', 'might', 'must', 'shall',
            'can', 'need', 'dare', 'ought', 'used', 'to', 'of', 'in',
            'for', 'on', 'with', 'at', 'by', 'from', 'as', 'into',
            'through', 'during', 'before', 'after', 'above', 'below',
            'between', 'under', 'and', 'but', 'or', 'yet', 'so', 'if',
            'because', 'although', 'though', 'while', 'where', 'when',
            'that', 'which', 'who', 'whom', 'whose', 'what', 'this',
            'these', 'those', 'i', 'you', 'he', 'she', 'it', 'we', 'they',
            'me', 'him', 'her', 'us', 'them', 'my', 'your', 'his', 'her',
            'its', 'our', 'their', 'mine', 'yours', 'hers', 'ours', 'theirs',
            'all', 'each', 'every', 'both', 'few', 'more', 'most', 'other',
            'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'than',
            'too', 'very', 'just', 'now', 'then', 'here', 'there', 'once',
            'again', 'further', 'also', 'non', 'll', 've', 're', 'don', 't',
            's', 'd', 'didn', 'doesn', 'hadn', 'hasn', 'haven', 'isn', 'let',
            'mustn', 'needn', 'shan', 'shouldn', 'wasn', 'weren', 'won', 'wouldn',
        }
        self.vocab = {}
        self.vocab_index = 0
    
    def _tokenize(self, text: str) -> List[str]:
        """Simple tokenization."""
        return re.findall(r'\b[a-z][a-z0-9_-]*\b', text.lower())
    
    def _vectorize(self, text: str) -> List[float]:
        """Create a sparse vector from text."""
        tokens = self._tokenize(text)
        # Build vocab on-the-fly
        for tok in tokens:
            if tok not in self.stopwords and len(tok) > 2:
                if tok not in self.vocab:
                    self.vocab[tok] = self.vocab_index
                    self.vocab_index += 1
        
        vec = [0.0] * max(256, self.vocab_index + 1)
        for tok in tokens:
            if tok in self.vocab:
                vec[self.vocab[tok]] += 1.0
        
        # Normalize
        import math
        norm = math.sqrt(sum(v * v for v in vec))
        if norm > 0:
            vec = [v / norm for v in vec]
        return vec
    
    def embed_documents(self, texts: List[str]) -> List[List[float]]:
        return [self._vectorize(t) for t in texts]
    
    def embed_query(self, text: str) -> List[float]:
        return self._vectorize(text)


class KnowledgeManager:
    """Manages vector-based knowledge retrieval using ChromaDB directly."""
    
    def __init__(self):
        self.knowledge_dir = AGENT_CONFIG["knowledge_dir"]
        self.vector_db_dir = AGENT_CONFIG["vector_db_dir"]
        self.vector_db_dir.mkdir(parents=True, exist_ok=True)
        
        self._client = None
        self._collection = None
        self._embedding_fn = None
    
    def _init_db(self):
        """Lazy-load ChromaDB client."""
        if self._client is not None:
            return
        
        try:
            import chromadb
            
            self._client = chromadb.PersistentClient(path=str(self.vector_db_dir))
            
            # Use ChromaDB's built-in default embedding (onnx/all-MiniLM-L6-v2)
            # which is lightweight and doesn't need torch/sentence-transformers
            self._collection = self._client.get_or_create_collection(
                name="sysadmin_knowledge",
            )
        except Exception as e:
            print(f"[!] ChromaDB init failed: {e}")
            self._client = None
            self._collection = None
    
    def search(self, query: str, k: int = 3) -> List[str]:
        """Search knowledge base for relevant documents."""
        self._init_db()
        if self._collection is None:
            return ["Knowledge base not initialized (ChromaDB unavailable)."]
        
        try:
            results = self._collection.query(
                query_texts=[query],
                n_results=k,
            )
            documents = results.get("documents", [[]])[0]
            if not documents:
                return ["No relevant knowledge found."]
            return documents
        except Exception as e:
            return [f"Knowledge search error: {e}"]
    
    def _chunk_text(self, text: str, chunk_size: int = 500, overlap: int = 50) -> List[str]:
        """Split text into overlapping chunks."""
        chunks = []
        start = 0
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            chunks.append(chunk)
            start = end - overlap
            if start <= 0:
                break
        return chunks
    
    def add_document(self, file_path: str):
        """Add a text document to the knowledge base."""
        self._init_db()
        if self._collection is None:
            raise RuntimeError("Vector database not available")
        
        file_path = Path(file_path)
        text = file_path.read_text(encoding="utf-8")
        chunks = self._chunk_text(text)
        
        doc_id_base = file_path.stem
        ids = [f"{doc_id_base}_chunk_{i}" for i in range(len(chunks))]
        metadatas = [{"source": str(file_path), "chunk": i} for i in range(len(chunks))]
        
        self._collection.add(
            documents=chunks,
            ids=ids,
            metadatas=metadatas,
        )
        return len(chunks)
    
    def index_all(self):
        """Index all .txt files in the knowledge directory."""
        self._init_db()
        if self._collection is None:
            print("[!] Cannot index: ChromaDB not available")
            return 0
        
        # Check what's already indexed
        existing = set()
        try:
            all_meta = self._collection.get(include=["metadatas"])
            for meta in all_meta.get("metadatas", []):
                if meta and "source" in meta:
                    existing.add(meta["source"])
        except Exception:
            pass
        
        total = 0
        for txt_file in self.knowledge_dir.rglob("*.txt"):
            source = str(txt_file.resolve())
            if source in existing:
                print(f"[SKIP] Already indexed: {txt_file.name}")
                continue
            try:
                chunks = self.add_document(source)
                print(f"[OK] Indexed {txt_file.name} ({chunks} chunks)")
                total += chunks
            except Exception as e:
                print(f"[FAIL] Failed to index {txt_file}: {e}")
        return total
