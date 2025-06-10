
from flask import Flask, jsonify, request

@app.route('/health', methods=['GET'])
def health_check():
    return jsonify({"status": "healthy"}), 200


@app.route('/api/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        result = chat_service.process_chat_request(
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


return app