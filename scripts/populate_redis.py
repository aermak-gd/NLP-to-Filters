from typing import List, Dict, Any
import time
import logging

from src.infrastructure.redis_client import redis_store
from src.infrastructure.embedding_client import embedding_service
from scripts.sample_filters import SAMPLE_FILTERS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_vector_db(filter_documents: List[Dict[str, Any]]):
    """Initialize Redis vector database with filter definitions"""
    try:
        redis_store.create_index()

        texts = []
        metadatas = []

        for filter_doc in filter_documents:
            searchable_text = create_searchable_text(filter_doc)
            texts.append(searchable_text)
            metadatas.append(filter_doc)
            logger.debug(f"Prepared text: {searchable_text[:100]}...")

        embeddings = embedding_service.embed_batch(texts)
        redis_store.add_documents(texts, metadatas, embeddings)

        logger.info(f"Generating embeddings for {len(texts)} documents...")
        embeddings = embedding_service.embed_batch(texts)

        logger.info(f"Adding documents to Redis...")
        redis_store.add_documents(texts, metadatas, embeddings)

        # Wait for indexing to complete
        time.sleep(2)

        logger.info(f"Vector database initialized with {len(filter_documents)} filter definitions")

        test_search()

    except Exception as e:
        logger.error(f"Error initializing vector database: {e}")
        raise

def create_searchable_text(filter_doc: Dict[str, Any]) -> str:
    """Create searchable text from filter definition"""
    parts = []

    if "displayName" in filter_doc:
        parts.append(filter_doc["displayName"])
    if "description" in filter_doc:
        parts.append(filter_doc["description"])
    if "keywords" in filter_doc and isinstance(filter_doc["keywords"], list):
        parts.extend(filter_doc["keywords"])

    return ", ".join(parts)


def test_search():
    """Test that the search is working"""
    try:
        from redis.commands.search.query import Query
        query = Query("*").return_fields("text").paging(0, 5)
        results = redis_store.redis_client.ft(redis_store.config.redis_index_name).search(query)
        logger.info(f"Test search found {results.total} documents")

        for i, doc in enumerate(results.docs):
            logger.info(f"Document {i}: {doc.text[:100]}...")

    except Exception as e:
        logger.error(f"Test search failed: {e}")

if __name__ == "__main__":
    initialize_vector_db(SAMPLE_FILTERS)
    # Force save data to disk
    redis_store.redis_client.save()
    logger.info("Data saved to disk")