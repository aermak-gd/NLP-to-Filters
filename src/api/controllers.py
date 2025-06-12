from flask import Blueprint, jsonify, request, current_app
from src.infrastructure.redis_client import redis_store

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@api_bp.route('/redis/health', methods=['GET'])
def redis_health_check():
    try:
        # Basic connection check
        redis_store.redis_client.ping()
        info = redis_store.redis_client.info()
        key_count = len(redis_store.redis_client.keys('*'))
        
        # Index information
        index_info = {}
        filter_documents = []
        sample_documents = []
        
        try:
            # Get index information
            index = redis_store.redis_client.ft(redis_store.config.redis_index_name)
            index_info = index.info()
            
            # Get filter documents
            from redis.commands.search.query import Query
            query = Query("*").return_fields("text", "metadata").paging(0, 100)
            results = index.search(query)
            
            if hasattr(results, 'docs') and results.docs:
                for doc in results.docs:
                    try:
                        # Parse metadata
                        metadata_str = getattr(doc, 'metadata', '{}')
                        if isinstance(metadata_str, bytes):
                            metadata_str = metadata_str.decode('utf-8')
                        
                        import json
                        metadata = json.loads(metadata_str)
                        
                        filter_documents.append({
                            "displayName": metadata.get('displayName', ''),
                            "type": metadata.get('type', ''),
                            "category": metadata.get('category', ''),
                            "description": metadata.get('description', '')[:100] + "..." if len(metadata.get('description', '')) > 100 else metadata.get('description', ''),
                            "controlType": metadata.get('controlType', ''),
                            "operators": metadata.get('operators', []),
                            "keywords": metadata.get('keywords', [])
                        })
                        
                    except Exception as e:
                        continue
                
                # Take first 3 documents as examples
                sample_documents = filter_documents[:3]
                
            # Statistics by categories
            categories = {}
            control_types = {}
            for doc in filter_documents:
                cat = doc.get('category', 'Unknown')
                ctrl_type = doc.get('controlType', 'Unknown')
                
                categories[cat] = categories.get(cat, 0) + 1
                control_types[ctrl_type] = control_types.get(ctrl_type, 0) + 1
        
        except Exception as e:
            index_info = {"error": f"Could not get index info: {str(e)}"}
        
        return jsonify({
            "status": "connected",
            "redis_info": {
                "version": info.get('redis_version'),
                "host": redis_store.config.redis_host,
                "port": redis_store.config.redis_port,
                "total_keys": key_count,
                "used_memory_human": info.get('used_memory_human'),
                "connected_clients": info.get('connected_clients')
            },
            "vector_database": {
                "index_name": redis_store.config.redis_index_name,
                "embedding_dimension": redis_store.config.redis_embedding_dimension,
                "total_documents": len(filter_documents),
                "index_info": {
                    "num_docs": index_info.get('num_docs', 'N/A'),
                    "index_status": index_info.get('indexing', 'N/A'),
                    "vector_size": index_info.get('vector_size', 'N/A')
                } if not index_info.get('error') else index_info
            },
            "filter_statistics": {
                "total_filters": len(filter_documents),
                "categories": categories,
                "control_types": control_types
            },
            "sample_filters": sample_documents
        }), 200
        
    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "status": "error",
            "error": str(e)
        }), 500

@api_bp.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        result = current_app.chat_service.process_chat_request(
            user_query=data.get('query', ''),
            active_filters=data.get('active_filters', []),
            session_id=data.get('session_id')
        )
        return jsonify(result), 200

    except Exception as e:
        import traceback
        traceback.print_exc()
        return jsonify({
            "error": str(e),
            "message": "Sorry, I encountered an error processing your request."
        }), 500

def register_routes(app):
    app.register_blueprint(api_bp)