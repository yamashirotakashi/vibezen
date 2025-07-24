"""
Optimized semantic cache with vector similarity search.

Uses efficient vector operations and batch processing.
"""

import numpy as np
import asyncio
import time
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass
import pickle
import faiss
from sentence_transformers import SentenceTransformer

from ..cache.semantic_cache import SemanticCache, CachedItem
from ..performance import BatchProcessor


@dataclass
class VectorIndex:
    """Efficient vector index for similarity search."""
    
    index: faiss.Index
    id_map: Dict[int, str]  # faiss_id -> cache_key
    key_map: Dict[str, int]  # cache_key -> faiss_id
    dimension: int
    
    def add_vectors(self, keys: List[str], vectors: np.ndarray):
        """Add vectors to the index."""
        start_id = len(self.id_map)
        num_vectors = len(vectors)
        
        # Add to FAISS index
        self.index.add(vectors)
        
        # Update mappings
        for i, key in enumerate(keys):
            faiss_id = start_id + i
            self.id_map[faiss_id] = key
            self.key_map[key] = faiss_id
    
    def search(
        self,
        query_vector: np.ndarray,
        k: int = 5,
        threshold: float = 0.0,
    ) -> List[Tuple[str, float]]:
        """Search for similar vectors."""
        # Search in FAISS
        distances, indices = self.index.search(query_vector.reshape(1, -1), k)
        
        # Convert to results
        results = []
        for dist, idx in zip(distances[0], indices[0]):
            if idx >= 0 and dist >= threshold:
                key = self.id_map.get(int(idx))
                if key:
                    results.append((key, float(dist)))
        
        return results
    
    def remove(self, key: str):
        """Remove a vector from the index."""
        # FAISS doesn't support removal, so we track deleted keys
        if key in self.key_map:
            faiss_id = self.key_map[key]
            del self.key_map[key]
            del self.id_map[faiss_id]


class OptimizedSemanticCache(SemanticCache):
    """Semantic cache with optimized vector operations."""
    
    def __init__(
        self,
        *args,
        use_gpu: bool = False,
        index_type: str = "IVF",
        batch_size: int = 32,
        **kwargs
    ):
        super().__init__(*args, **kwargs)
        
        self.use_gpu = use_gpu
        self.index_type = index_type
        self.batch_size = batch_size
        
        # Vector index
        self._vector_index: Optional[VectorIndex] = None
        
        # Batch processor for embeddings
        self._embedding_processor = BatchProcessor(
            processor=self._batch_encode,
            batch_size=batch_size,
            batch_timeout=0.05,
        )
        
        # Lazy loading for encoder
        self._encoder: Optional[SentenceTransformer] = None
        self._encoder_lock = asyncio.Lock()
    
    async def initialize(self):
        """Initialize optimized cache."""
        await super().initialize()
        
        # Start batch processor
        await self._embedding_processor.start()
        
        # Initialize vector index
        await self._initialize_index()
    
    async def cleanup(self):
        """Cleanup resources."""
        await self._embedding_processor.stop()
        await super().cleanup()
    
    async def _get_encoder(self) -> SentenceTransformer:
        """Get or create encoder with lazy loading."""
        if self._encoder is None:
            async with self._encoder_lock:
                if self._encoder is None:
                    # Load model on CPU first
                    self._encoder = SentenceTransformer(self.model_name)
                    
                    # Move to GPU if available and requested
                    if self.use_gpu:
                        try:
                            import torch
                            if torch.cuda.is_available():
                                self._encoder = self._encoder.to('cuda')
                        except ImportError:
                            pass
        
        return self._encoder
    
    async def _initialize_index(self):
        """Initialize FAISS index."""
        # Determine vector dimension
        encoder = await self._get_encoder()
        dimension = encoder.get_sentence_embedding_dimension()
        
        # Create appropriate index
        if self.index_type == "Flat":
            # Exact search
            index = faiss.IndexFlatIP(dimension)  # Inner product for cosine similarity
        elif self.index_type == "IVF":
            # Approximate search with inverted file
            quantizer = faiss.IndexFlatIP(dimension)
            index = faiss.IndexIVFFlat(quantizer, dimension, 100)  # 100 clusters
            # Train on initial vectors if available
            if self._cache:
                vectors = await self._get_all_vectors()
                if len(vectors) > 100:
                    index.train(vectors)
        elif self.index_type == "HNSW":
            # Hierarchical Navigable Small World graph
            index = faiss.IndexHNSWFlat(dimension, 32)  # 32 connections
        else:
            # Default to flat index
            index = faiss.IndexFlatIP(dimension)
        
        # Use GPU if available
        if self.use_gpu:
            try:
                gpu_index = faiss.index_cpu_to_gpu(
                    faiss.StandardGpuResources(),
                    0,  # GPU id
                    index
                )
                index = gpu_index
            except:
                pass  # Fall back to CPU
        
        self._vector_index = VectorIndex(
            index=index,
            id_map={},
            key_map={},
            dimension=dimension,
        )
        
        # Add existing vectors
        await self._rebuild_index()
    
    async def _rebuild_index(self):
        """Rebuild the vector index from cache."""
        if not self._vector_index:
            return
        
        # Get all cached items
        all_items = []
        for items in self._cache.values():
            all_items.extend(items)
        
        if not all_items:
            return
        
        # Extract texts and keys
        texts = [item.text for item in all_items]
        keys = [item.key for item in all_items]
        
        # Batch encode
        embeddings = await self._batch_encode_async(texts)
        
        # Normalize for cosine similarity
        embeddings = embeddings / np.linalg.norm(
            embeddings, axis=1, keepdims=True
        )
        
        # Add to index
        self._vector_index.add_vectors(keys, embeddings)
    
    async def set(
        self,
        key: str,
        value: Any,
        text: Optional[str] = None,
        ttl: Optional[int] = None,
    ):
        """Set with optimized embedding generation."""
        # Generate embedding using batch processor
        embedding_future = self._embedding_processor.submit(
            request_id=key,
            data=text or str(value),
        )
        
        # Store item while embedding is being generated
        await super().set(key, value, text, ttl)
        
        # Wait for embedding
        try:
            embedding = await embedding_future
            
            # Update item with embedding
            hash_key = self._hash_key(key)
            if hash_key in self._cache:
                for item in self._cache[hash_key]:
                    if item.key == key:
                        item.embedding = embedding
                        break
            
            # Add to vector index
            if self._vector_index and embedding is not None:
                embedding_normalized = embedding / np.linalg.norm(embedding)
                self._vector_index.add_vectors(
                    [key],
                    embedding_normalized.reshape(1, -1)
                )
                
        except Exception:
            # Continue without embedding
            pass
    
    async def get_similar(
        self,
        text: str,
        threshold: float = 0.8,
        max_results: int = 5,
    ) -> List[Tuple[str, Any, float]]:
        """Get similar items using optimized vector search."""
        if not self._vector_index:
            # Fall back to base implementation
            return await super().get_similar(text, threshold, max_results)
        
        # Generate query embedding
        embedding = await self._encode_text(text)
        if embedding is None:
            return []
        
        # Normalize
        embedding = embedding / np.linalg.norm(embedding)
        
        # Search in vector index
        results = self._vector_index.search(
            embedding,
            k=max_results * 2,  # Get more candidates
            threshold=threshold,
        )
        
        # Retrieve items
        similar_items = []
        for key, similarity in results:
            hash_key = self._hash_key(key)
            if hash_key in self._cache:
                for item in self._cache[hash_key]:
                    if item.key == key and not item.is_expired():
                        similar_items.append((key, item.value, similarity))
                        break
        
        # Sort by similarity and limit results
        similar_items.sort(key=lambda x: x[2], reverse=True)
        return similar_items[:max_results]
    
    async def _batch_encode(self, texts: List[str]) -> List[Optional[np.ndarray]]:
        """Batch encode texts to embeddings."""
        encoder = await self._get_encoder()
        
        try:
            # Encode all texts at once
            embeddings = encoder.encode(
                texts,
                batch_size=self.batch_size,
                show_progress_bar=False,
                convert_to_numpy=True,
            )
            
            return [embeddings[i] for i in range(len(texts))]
            
        except Exception:
            # Return None for all on error
            return [None] * len(texts)
    
    async def _batch_encode_async(self, texts: List[str]) -> np.ndarray:
        """Async wrapper for batch encoding."""
        encoder = await self._get_encoder()
        
        # Run in thread pool
        loop = asyncio.get_event_loop()
        embeddings = await loop.run_in_executor(
            None,
            encoder.encode,
            texts,
            self.batch_size,
            False,  # show_progress_bar
            True,   # convert_to_numpy
        )
        
        return embeddings
    
    async def _get_all_vectors(self) -> np.ndarray:
        """Get all vectors from cache for training."""
        all_items = []
        for items in self._cache.values():
            all_items.extend(items)
        
        if not all_items:
            return np.array([])
        
        # Extract embeddings
        embeddings = []
        for item in all_items:
            if item.embedding is not None:
                embeddings.append(item.embedding)
        
        if not embeddings:
            # Generate embeddings for items without them
            texts = [item.text for item in all_items if item.embedding is None]
            if texts:
                new_embeddings = await self._batch_encode_async(texts)
                embeddings.extend(new_embeddings)
        
        return np.vstack(embeddings) if embeddings else np.array([])
    
    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics including vector index info."""
        stats = super().get_cache_stats()
        
        if self._vector_index:
            stats["vector_index"] = {
                "type": self.index_type,
                "dimension": self._vector_index.dimension,
                "num_vectors": len(self._vector_index.key_map),
                "gpu_enabled": self.use_gpu,
            }
        
        stats["batch_processor"] = self._embedding_processor.get_stats()
        
        return stats
    
    async def warm_up(self, common_queries: List[str]):
        """Pre-compute embeddings for common queries."""
        # Batch encode all queries
        embeddings = await self._batch_encode_async(common_queries)
        
        # Cache embeddings for faster lookup
        for query, embedding in zip(common_queries, embeddings):
            # Store in a special cache namespace
            cache_key = f"_warmup_{self._hash_key(query)}"
            await self.set(
                cache_key,
                {"query": query, "embedding": embedding},
                text=query,
                ttl=3600,  # 1 hour
            )
    
    async def optimize_index(self):
        """Optimize the vector index for better performance."""
        if not self._vector_index:
            return
        
        # Get current vectors
        vectors = await self._get_all_vectors()
        
        if len(vectors) < 1000:
            # Not enough data to optimize
            return
        
        # Retrain IVF index if applicable
        if hasattr(self._vector_index.index, 'train'):
            self._vector_index.index.train(vectors)
        
        # Consider upgrading index type for large datasets
        if len(vectors) > 10000 and self.index_type == "Flat":
            # Upgrade to IVF for better scalability
            await self._initialize_index()
            
    async def save_index(self, path: str):
        """Save vector index to disk."""
        if not self._vector_index:
            return
        
        # Save FAISS index
        faiss.write_index(self._vector_index.index, f"{path}.faiss")
        
        # Save mappings
        with open(f"{path}.mappings", "wb") as f:
            pickle.dump({
                "id_map": self._vector_index.id_map,
                "key_map": self._vector_index.key_map,
                "dimension": self._vector_index.dimension,
            }, f)
    
    async def load_index(self, path: str):
        """Load vector index from disk."""
        # Load FAISS index
        index = faiss.read_index(f"{path}.faiss")
        
        # Load mappings
        with open(f"{path}.mappings", "rb") as f:
            mappings = pickle.load(f)
        
        self._vector_index = VectorIndex(
            index=index,
            id_map=mappings["id_map"],
            key_map=mappings["key_map"],
            dimension=mappings["dimension"],
        )