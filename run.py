import threading
import argparse
import time
from src.api.app import app
# from src.ui.gradio_app import gradio_app
from src.ui.console_app import run_console_app
from config.settings import FlaskConfig


def run_flask(use_reloader=None):
    """Run Flask app"""
    config = FlaskConfig()
    
    # If use_reloader is not specified, use config value
    if use_reloader is None:
        use_reloader = config.flask_debug

    app.run(
        host=config.flask_host,
        port=config.flask_port,
        debug=config.flask_debug,
        use_reloader=use_reloader
    )


# def run_gradio():
#     """Run Gradio app"""
#     gradio_app.launch(
#         server_name="0.0.0.0",
#         server_port=7860,
#         share=False,
#         quiet=True
#     )


def main():
    config = FlaskConfig()

    parser = argparse.ArgumentParser(description='Filter Assistant Application')
    parser.add_argument(
        '--mode',
        choices=['gradio', 'console', 'both', 'api-only'],
        default='console',
        help='Run mode: gradio (web UI), console (CLI), both, or api-only'
    )
    parser.add_argument(
        '--api-url',
        default=f'http://localhost:{config.flask_port}',
        help='API URL for console mode'
    )

    args = parser.parse_args()

    if args.mode == 'api-only':
        print("Starting Flask API...")
        print(f"Flask API running at: http://localhost:{config.flask_port}")
        print("Press Ctrl+C to stop")
        # Run Flask in main thread with reloader enabled
        run_flask()
        
    elif args.mode in ['both', 'gradio']:
        # Start Flask in separate thread
        flask_thread = threading.Thread(target=lambda: run_flask(use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()

        print("Starting Flask API...")
        time.sleep(2)
        print(f"Flask API running at: http://localhost:{config.flask_port}")

        if args.mode == 'gradio':
            print("Starting Gradio UI...")
            print(f"Gradio UI will be available at: http://localhost:7860")
            # run_gradio()
        elif args.mode == 'both':
            print("Both services started")
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down...")

    elif args.mode == 'console':
        # Start Flask in separate thread
        flask_thread = threading.Thread(target=lambda: run_flask(use_reloader=False))
        flask_thread.daemon = True
        flask_thread.start()

        print("Starting Flask API...")
        time.sleep(1)
        print(f"Flask API running at: http://localhost:{config.flask_port}")

        print("Starting Console Interface...")
        run_console_app(args.api_url)

if __name__ == "__main__":
    main()