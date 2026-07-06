from flask import Flask, jsonify
from config import Config
from extensions import db, bcrypt, jwt
from flask_cors import CORS


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    CORS(app, supports_credentials=True)

    # Init extensions
    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)

    # Return JSON (not HTML) for all JWT auth errors
    @jwt.unauthorized_loader
    def missing_token(reason):
        return jsonify({"error": "Authentication required", "detail": reason}), 401

    @jwt.invalid_token_loader
    def invalid_token(reason):
        return jsonify({"error": "Invalid token", "detail": reason}), 422

    @jwt.expired_token_loader
    def expired_token(jwt_header, jwt_payload):
        return jsonify({"error": "Token has expired"}), 401

    @jwt.revoked_token_loader
    def revoked_token(jwt_header, jwt_payload):
        return jsonify({"error": "Token has been revoked"}), 401

    # Return JSON for unhandled server errors
    @app.errorhandler(500)
    def internal_error(e):
        return jsonify({"error": "Internal server error", "detail": str(e)}), 500

    @app.errorhandler(404)
    def not_found(e):
        return jsonify({"error": "Not found"}), 404

    # Register blueprints
    from routes.auth import auth_bp
    from routes.user import user_bp
    from routes.transactions import transaction_bp
    from routes.ai import ai_bp
    from routes.contact import contact_bp

    app.register_blueprint(auth_bp)
    app.register_blueprint(user_bp)
    app.register_blueprint(transaction_bp)
    app.register_blueprint(ai_bp)
    app.register_blueprint(contact_bp)

    # Serve frontend pages
    from routes.pages import pages_bp
    app.register_blueprint(pages_bp)

    # Create all tables
    with app.app_context():
        db.create_all()

    return app
