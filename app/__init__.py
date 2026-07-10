from flask import Flask, request
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from flask_socketio import SocketIO
from config import Config

# Extension instances (created here, initialized in create_app)
db = SQLAlchemy()
jwt = JWTManager()
socketio = SocketIO()


def create_app(config_class=Config):
    """Application factory. Returns a configured Flask app instance."""
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Configure JWT to accept tokens from headers only (Authorization: Bearer <token>)
    app.config.setdefault('JWT_TOKEN_LOCATION', ['headers'])

    # Initialize extensions with the Flask app
    db.init_app(app)
    jwt.init_app(app)
    CORS(app)
    socketio.init_app(app, cors_allowed_origins="*")

    # Backend expects Authorization header only. Frontend must send
    # `Authorization: Bearer <token>` for API requests.

    # Register blueprints using relative imports to avoid import-time side effects
    from .auth import auth_bp
    from .admin import admin_bp
    from .routes import main_bp

    app.register_blueprint(auth_bp, url_prefix='/api/auth')
    app.register_blueprint(admin_bp, url_prefix='/api/admin')
    app.register_blueprint(main_bp)

    # Import websocket handlers so they register socket events with `socketio`.
    # Use relative import to avoid ambiguity.
    from . import websocket  # noqa: F401

    # Normalize incoming JWT tokens that have a numeric `sub` claim (older tokens).
    # Some JWT libraries require the `sub` (subject) to be a string. If clients
    # still present legacy tokens where `sub` is an integer, create a new token
    # with a string subject and return it in the `X-Reissued-Token` response header.
    from flask import g
    import base64, json
    from flask_jwt_extended import create_access_token
    from app.models import User

    @app.before_request
    def normalize_jwt_subject():
        auth = request.headers.get('Authorization')
        if not auth or not auth.startswith('Bearer '):
            return
        token = auth.split(None, 1)[1]
        parts = token.split('.')
        if len(parts) != 3:
            return
        try:
            payload_b64 = parts[1]
            # base64 urlsafe decode with padding
            padded = payload_b64 + '=' * ((4 - len(payload_b64) % 4) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode('utf-8'))
            payload = json.loads(decoded)
            sub = payload.get('sub')
            if sub is None or isinstance(sub, str):
                return
            # sub exists and is not a string -> try to reissue token
            try:
                user = User.query.get(int(sub))
            except Exception:
                return
            if not user:
                return
            # Issue a new token with string identity
            new_token = create_access_token(identity=str(user.id))
            g.reissued_token = new_token
        except Exception:
            # If any error occurs, don't block the request here; let JWT handlers
            # produce the usual error response so clients can re-authenticate.
            return

    @app.after_request
    def attach_reissued_token(response):
        if hasattr(g, 'reissued_token'):
            response.headers['X-Reissued-Token'] = g.reissued_token
        return response

    # Ensure the database schema exists on startup so auth routes can work
    # immediately when PostgreSQL is configured.
    with app.app_context():
        try:
            db.create_all()
            db.session.remove()
        except Exception as exc:
            app.logger.warning("Database initialization skipped or failed: %s", exc)

    return app


app = create_app()


__all__ = ['create_app', 'db', 'jwt', 'socketio', 'app']
