import logging
from flask import Flask
from flask_cors import CORS
from src.infrastructure.chat_client import ChatService
from src.api.controllers import register_routes

def create_app():
    app = Flask(__name__)
    CORS(app)  # Enable CORS for all routes

    log = logging.getLogger('werkzeug')
    log.setLevel(logging.WARNING)

    chat_service = ChatService()
    app.chat_service = chat_service

    register_routes(app)

    return app

app = create_app()