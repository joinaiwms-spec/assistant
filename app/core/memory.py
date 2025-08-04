"""Vector memory system using FAISS for long-term storage and retrieval."""

import os
import pickle
import hashlib
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path

import faiss
import numpy as np
from sentence_transformers import SentenceTransformer
from loguru import logger

from app.config import settings


class VectorMemory:
    """Vector memory system for storing and retrieving embeddings."""
    
    def __init__(self, embedding_model: str = None, dimension: int = 384):
        self.embedding_model_name = embedding_model or settings.embedding_model
        self.dimension = dimension
        self.embedding_model = None
        self.index = None
        self.metadata = {}
        self.next_id = 0
        
        # Paths
        self.vector_db_path = Path(settings.vector_db_path)
        self.index_path = self.vector_db_path / "faiss_index.bin"
        self.metadata_path = self.vector_db_path / "metadata.pkl"
        self.config_path = self.vector_db_path / "config.pkl"
        
        # Initialize
        self._load_or_create_index()
        self._load_embedding_model()
    
    def _load_embedding_model(self):
        """Load the sentence transformer model."""
        try:
            self.embedding_model = SentenceTransformer(self.embedding_model_name)
            logger.info(f"Loaded embedding model: {self.embedding_model_name}")
        except Exception as e:
            logger.error(f"Failed to load embedding model: {e}")
            raise
    
    def _load_or_create_index(self):
        """Load existing FAISS index or create a new one."""
        try:
            if self.index_path.exists():
                # Load existing index
                self.index = faiss.read_index(str(self.index_path))
                
                # Load metadata
                if self.metadata_path.exists():
                    with open(self.metadata_path, 'rb') as f:
                        self.metadata = pickle.load(f)
                
                # Load config
                if self.config_path.exists():
                    with open(self.config_path, 'rb') as f:
                        config = pickle.load(f)
                        self.next_id = config.get('next_id', 0)
                        self.dimension = config.get('dimension', self.dimension)
                
                logger.info(f"Loaded existing FAISS index with {self.index.ntotal} vectors")
            else:
                # Create new index
                self.index = faiss.IndexFlatIP(self.dimension)  # Inner product for cosine similarity
                self.metadata = {}
                self.next_id = 0
                logger.info(f"Created new FAISS index with dimension {self.dimension}")
                
        except Exception as e:
            logger.error(f"Failed to load/create FAISS index: {e}")
            # Fallback: create new index
            self.index = faiss.IndexFlatIP(self.dimension)
            self.metadata = {}
            self.next_id = 0
    
    def _save_index(self):
        """Save the FAISS index and metadata to disk."""
        try:
            # Save index
            faiss.write_index(self.index, str(self.index_path))
            
            # Save metadata
            with open(self.metadata_path, 'wb') as f:
                pickle.dump(self.metadata, f)
            
            # Save config
            config = {
                'next_id': self.next_id,
                'dimension': self.dimension,
                'embedding_model': self.embedding_model_name
            }
            with open(self.config_path, 'wb') as f:
                pickle.dump(config, f)
                
            logger.debug("Saved FAISS index and metadata to disk")
        except Exception as e:
            logger.error(f"Failed to save FAISS index: {e}")
    
    def _generate_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for the given text."""
        try:
            embedding = self.embedding_model.encode([text], normalize_embeddings=True)
            return embedding[0].astype(np.float32)
        except Exception as e:
            logger.error(f"Failed to generate embedding: {e}")
            raise
    
    def add_memory(self, text: str, metadata: Dict[str, Any] = None) -> str:
        """Add a new memory to the vector store."""
        try:
            # Generate embedding
            embedding = self._generate_embedding(text)
            
            # Create unique ID
            memory_id = f"mem_{self.next_id}"
            self.next_id += 1
            
            # Add to index
            self.index.add(embedding.reshape(1, -1))
            
            # Store metadata
            self.metadata[memory_id] = {
                'text': text,
                'metadata': metadata or {},
                'created_at': str(np.datetime64('now')),
                'faiss_id': self.index.ntotal - 1
            }
            
            # Save to disk
            self._save_index()
            
            logger.debug(f"Added memory with ID: {memory_id}")
            return memory_id
            
        except Exception as e:
            logger.error(f"Failed to add memory: {e}")
            raise
    
    def search_memories(self, query: str, k: int = 5, threshold: float = 0.7) -> List[Dict[str, Any]]:
        """Search for similar memories."""
        try:
            if self.index.ntotal == 0:
                return []
            
            # Generate query embedding
            query_embedding = self._generate_embedding(query)
            
            # Search
            scores, indices = self.index.search(query_embedding.reshape(1, -1), min(k, self.index.ntotal))
            
            results = []
            for score, idx in zip(scores[0], indices[0]):
                if score >= threshold:
                    # Find memory ID by FAISS index
                    memory_id = None
                    for mid, meta in self.metadata.items():
                        if meta['faiss_id'] == idx:
                            memory_id = mid
                            break
                    
                    if memory_id:
                        result = {
                            'id': memory_id,
                            'text': self.metadata[memory_id]['text'],
                            'score': float(score),
                            'metadata': self.metadata[memory_id]['metadata']
                        }
                        results.append(result)
            
            logger.debug(f"Found {len(results)} similar memories for query")
            return results
            
        except Exception as e:
            logger.error(f"Failed to search memories: {e}")
            return []
    
    def get_memory(self, memory_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve a specific memory by ID."""
        return self.metadata.get(memory_id)
    
    def delete_memory(self, memory_id: str) -> bool:
        """Delete a memory (marks as deleted, doesn't remove from FAISS)."""
        try:
            if memory_id in self.metadata:
                self.metadata[memory_id]['deleted'] = True
                self._save_index()
                logger.debug(f"Marked memory {memory_id} as deleted")
                return True
            return False
        except Exception as e:
            logger.error(f"Failed to delete memory: {e}")
            return False
    
    def get_stats(self) -> Dict[str, Any]:
        """Get memory system statistics."""
        active_memories = sum(1 for meta in self.metadata.values() if not meta.get('deleted', False))
        return {
            'total_memories': len(self.metadata),
            'active_memories': active_memories,
            'faiss_vectors': self.index.ntotal,
            'dimension': self.dimension,
            'embedding_model': self.embedding_model_name
        }


# Global memory instance
memory = VectorMemory()