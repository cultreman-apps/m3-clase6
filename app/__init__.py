import os

from flask import Flask, jsonify, request

STAGES = (
    {"id": 1, "name": "Código"},
    {"id": 2, "name": "Análisis"},
    {"id": 3, "name": "Construcción"},
    {"id": 4, "name": "Regresión"},
    {"id": 5, "name": "Despliegue"},
)


def calculate_progress(completed: int, total: int) -> int:
    if total <= 0:
        raise ValueError("total debe ser mayor que cero")

    safe_completed = min(max(completed, 0), total)
    return round((safe_completed / total) * 100)


def create_app() -> Flask:
    app = Flask(__name__)

    @app.get("/")
    def index():
        return jsonify(
            {
                "name": "FormaTEC CI/CD API",
                "documentation": {
                    "health": "/health",
                    "stages": "/api/stages",
                    "progress": "/api/progress?completed=3",
                },
            }
        )

    @app.get("/health")
    def health():
        return jsonify(
            {
                "status": "ok",
                "environment": os.getenv("APP_ENV", "local"),
                "version": os.getenv("APP_VERSION", "development"),
            }
        )

    @app.get("/api/stages")
    def stages():
        return jsonify({"count": len(STAGES), "items": STAGES})

    @app.get("/api/progress")
    def progress():
        raw_completed = request.args.get("completed", "0")
        try:
            completed = int(raw_completed)
        except ValueError:
            return jsonify({"error": "completed debe ser un número entero"}), 400

        return jsonify(
            {
                "completed": min(max(completed, 0), len(STAGES)),
                "total": len(STAGES),
                "percentage": calculate_progress(completed, len(STAGES)),
            }
        )

    return app
