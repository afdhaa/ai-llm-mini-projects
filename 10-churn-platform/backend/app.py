import os
from dotenv import load_dotenv
from flask import Flask, jsonify
from flask_cors import CORS

from routes.common import common_bp
from routes.menu01_ml import menu01_bp
from routes.menu02_llm import menu02_bp
from routes.menu03_hybrid import menu03_bp
from routes.menu04_agent import menu04_bp
from routes.menu05_schema import menu05_bp
from routes.menu06_guarded import menu06_bp
from routes.menu07_evals import menu07_bp
from routes.menu08_rag import menu08_bp
from routes.menu09_langgraph import menu09_bp
from routes.data_manager import data_mgr_bp
load_dotenv()

app = Flask(__name__)
CORS(app, resources={r"/api/*": {"origins": "*"}}, expose_headers=["*"], allow_headers=["*"])

# Register Blueprints
app.register_blueprint(common_bp)
app.register_blueprint(menu01_bp)
app.register_blueprint(menu02_bp)
app.register_blueprint(menu03_bp)
app.register_blueprint(menu04_bp)
app.register_blueprint(menu05_bp)
app.register_blueprint(menu06_bp)
app.register_blueprint(menu07_bp)
app.register_blueprint(menu08_bp)
app.register_blueprint(menu09_bp)
app.register_blueprint(data_mgr_bp)

@app.route("/api/health", methods=["GET"])
def health():
    return jsonify({
        "status": "healthy",
        "service": "Enterprise Churn AI Unified Platform API",
        "version": "1.0.0",
        "active_tiers": ["01-ML", "02-LLM", "03-Hybrid", "04-Agent", "05-Structured", "06-Guarded", "07-Evals", "08-RAG", "09-LangGraph"],
    })


if __name__ == "__main__":
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("DEBUG", "True").lower() == "true"
    print(f"🚀 Churn AI Platform Backend running on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=debug)
