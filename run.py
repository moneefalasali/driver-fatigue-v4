from app import create_app, db, socketio
import os


app = create_app()


def init_db():
    try:
        with app.app_context():
            db.create_all()
    except Exception as exc:
        print(f"Database initialization warning: {exc}")


init_db()


def main():
    # Run the SocketIO server and print the URL to the console
    host = os.environ.get('FLASK_RUN_HOST', '0.0.0.0')
    port = int(os.environ.get('FLASK_RUN_PORT', 5000))
    url_host = '127.0.0.1' if host in ('0.0.0.0', '') else host
    print(f"Starting server at http://{url_host}:{port}")
    app.debug = False
    try:
        socketio.run(app, host=host, port=port, use_reloader=False)
    except OSError as e:
        # Handle common Windows port-in-use error by attempting next port
        if getattr(e, 'winerror', None) == 10048 or 'Address already in use' in str(e):
            alt_port = port + 1
            print(f"Port {port} in use; retrying on port {alt_port}...")
            try:
                socketio.run(app, host=host, port=alt_port, use_reloader=False)
            except Exception as e2:
                print("Failed to start server on alternative port:", e2)
                raise
        else:
            raise


if __name__ == '__main__':
    main()
