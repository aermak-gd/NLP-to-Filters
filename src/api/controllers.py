from flask import Blueprint, jsonify, request, current_app
from src.infrastructure.redis_client import redis_store

api_bp = Blueprint('api', __name__)

@api_bp.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200

@api_bp.route('/redis/health', methods=['GET'])
def redis_health_check():
    try:
        redis_store.redis_client.ping()
        info = redis_store.redis_client.info()
        key_count = len(redis_store.redis_client.keys('*'))
        
        return jsonify({
            "status": "connected",
            "redis_version": info.get('redis_version'),
            "total_keys": key_count,
            "host": redis_store.config.redis_host,
            "port": redis_store.config.redis_port
        }), 200
        
    except Exception as e:
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