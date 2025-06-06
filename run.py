import threading
import argparse
import time
from src.app import app
# from src.ui.gradio_app import gradio_app
from src.ui.console_app import run_console_app
from config.settings import FlaskConfig


def run_flask():
    """Run Flask app"""
    config = FlaskConfig()

    app.run(
        host=config.flask_host,
        port=config.flask_port,
        debug=config.flask_debug,
        use_reloader=False
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

    # Always start Flask API except in 'console' mode where it will be started anyway below
    if args.mode in ['both', 'gradio', 'api-only']:
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        print("Starting Flask API...")
        time.sleep(2)
        print(f"Flask API running at: http://localhost:{config.flask_port}")

    if args.mode == 'console':
        flask_thread = threading.Thread(target=run_flask)
        flask_thread.daemon = True
        flask_thread.start()

        print("Starting Flask API...")
        time.sleep(1)
        print(f"Flask API running at: http://localhost:{config.flask_port}")

        print("Starting Console Interface...")
        run_console_app(args.api_url)

    elif args.mode == 'gradio':
        print("Starting Gradio UI...")
        print(f"Gradio UI will be available at: http://localhost:7860")
        # run_gradio()

    # elif args.mode == 'both':
    #     gradio_thread = threading.Thread(target=run_gradio)
    #     gradio_thread.daemon = True
    #     gradio_thread.start()
    #
    #     print("Starting Gradio UI in background...")
    #     print(f"Gradio UI available at: http://localhost:7860")
    #     time.sleep(2)
    #
    #     print("\nStarting Console Interface...")
    #     run_console_app()

    elif args.mode == 'api-only':
        print("Running API only mode...")
        print("Press Ctrl+C to stop")
        try:
            while True:
                time.sleep(1)
        except KeyboardInterrupt:
            print("\nShutting down...")

if __name__ == "__main__":
    main()