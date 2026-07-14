from flask import Flask
from flask_cors import CORS

from backend.routes.route_routes import route_bp
from backend.routes.navigation_routes import navigation_bp
from backend.routes.user_routes import user_bp


def create_app():
    app = Flask(__name__)
    CORS(app)

    app.register_blueprint(route_bp)
    app.register_blueprint(navigation_bp)
    app.register_blueprint(user_bp)

    @app.get("/")
    def home():
        return {
            "message": "Scenic Route backend is running",
            "endpoints": {
                "routes": "/api/routes",
                "navigation": "/api/navigation",
                "users": "/api/users"
            }
        }

    return app


app = create_app()


if __name__ == "__main__":
    app.run(debug=True, port=5000)
  
