import redis
import json
import time
import numpy as np
from typing import List, Dict, Any, Optional
import logging

from redis.commands.search.field import TextField, VectorField
from redis.commands.search.index_definition import IndexDefinition, IndexType
from redis.commands.search.query import Query
from config.settings import RedisConfig


logger = logging.getLogger(__name__)

class RedisFilterStore:
    def __init__(self,  config = RedisConfig):
        self.config = config
        self.redis_client = redis.Redis(
            host=config.redis_host,
            port=config.redis_port,
            db=config.redis_db,
            decode_responses=False
        )

    def create_index(self):
        """Create Redis search index"""
        try:
            try:
                self.redis_client.ft(self.config.redis_index_name).info()
                logger.info(f"Index {self.config.redis_index_name} already exists")
                return
            except:
                pass

            schema = [
                VectorField("embedding", "HNSW", {
                    "TYPE": "FLOAT32",
                    "DIM": self.config.redis_embedding_dimension,
                    "DISTANCE_METRIC": "COSINE"
                }),
                TextField("text"),
                TextField("metadata")
            ]

            self.redis_client.ft(self.config.redis_index_name).create_index(
                schema,
                definition=IndexDefinition(
                    prefix=[f"{self.config.redis_index_name}:"],
                    index_type=IndexType.HASH
                )
            )
            logger.info(f"Created Redis index: {self.config.redis_index_name}")

        except Exception as e:
            logger.error(f"Error creating Redis index: {e}")

    def add_documents(self, texts: List[str], metadatas: List[Dict], embeddings: List[List[float]]):
        """Add documents to Redis"""
        try:
            for i, (text, metadata, embedding) in enumerate(zip(texts, metadatas, embeddings)):
                doc_id = f"{self.config.redis_index_name}:{i}"

                embedding_bytes = np.array(embedding, dtype=np.float32).tobytes()

                self.redis_client.hset(doc_id, mapping={
                    b"text": text.encode('utf-8'),
                    b"metadata": json.dumps(metadata).encode('utf-8'),
                    b"embedding": embedding_bytes
                })

            logger.info(f"Added {len(texts)} documents to Redis")

            # Wait for indexing
            time.sleep(2)

            # Force a check
            self._check_index_status()

        except Exception as e:
            logger.error(f"Error adding documents to Redis: {e}")
            raise

    def _check_index_status(self):
        """Check index status and document count"""
        try:
            info = self.redis_client.ft(self.config.redis_index_name).info()
            print(f"Index info: {info}")

            query = Query("*").return_fields("text").paging(0, 5)
            results = self.redis_client.ft(self.config.redis_index_name).search(query)
            logger.info(f"Found {results.total} documents in search")

        except Exception as e:
            logger.error(f"Error checking index: {e}")

    def search_filters(self,
                       query_embedding: np.ndarray,
                       top_k: int = 5,
                       category: Optional[str] = None,
                       score_threshold: float = 0.5) -> List[Dict[str, Any]]:
        """Search filters by vector similarity"""

        # Build query
        base_query = f"*=>[KNN {top_k} @embedding $vec AS score]"
        if category:
            base_query = f"@category:{category} {base_query}"

        query = Query(base_query) \
            .sort_by("score") \
            .paging(0, top_k) \
            .return_fields("text", "metadata", "score") \
            .dialect(2)

        # Execute search
        results = self.redis_client.ft(self.config.redis_index_name).search(
            query,
            query_params={"vec": query_embedding.astype(np.float32).tobytes()}
        )

        # Parse results
        filters = []
        if hasattr(results, 'docs') and results.docs:
            for doc in results.docs:
                try:
                    score = float(getattr(doc, 'score', 1.0))

                    if score > score_threshold:
                        continue

                    # Parse metadata
                    metadata_str = getattr(doc, 'metadata', '{}')
                    if isinstance(metadata_str, bytes):
                        metadata_str = metadata_str.decode('utf-8')

                    metadata = json.loads(metadata_str)

                    filter_data = {
                        "filter_id": metadata.get('id', ''),
                        "display_name": metadata.get('displayName', ''),
                        "type": metadata.get('type', ''),
                        "control_type": metadata.get('controlType', ''),
                        "category": metadata.get('category', ''),
                        "description": metadata.get('description', ''),
                        "operators": metadata.get('operators', []),
                        "options": metadata.get('options', []),
                        "confidence": 1 - score
                    }
                    filters.append(filter_data)

                except Exception as e:
                    logger.error(f"Error parsing document: {e}")
                    continue

        return filters

    def search_filters_batch(self,
                             query_embeddings: List[np.ndarray],
                             top_k: int = 1,
                             category: Optional[str] = None,
                             score_threshold: float = 0.5) -> List[List[Dict[str, Any]]]:
        """Search filters for multiple query embeddings"""

        if not query_embeddings:
            return []

        # Just call the single search method for each embedding
        return [
            self.search_filters(embedding, top_k, category, score_threshold)
            for embedding in query_embeddings
        ]



# Singleton instance
redis_store = RedisFilterStore()