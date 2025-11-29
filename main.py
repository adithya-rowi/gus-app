"""
Gus App - Islamic Q&A Chatbot
Inspired by Gus Baha's warm, merciful teaching style.

DISCLAIMER: Ini adalah chatbot edukasi, bukan fatwa resmi.
"""

import os
from flask import Flask, render_template, request, jsonify

from generator import generate_response

app = Flask(__name__)


@app.route("/")
def index():
    """Serve the chat interface."""
    return render_template("index.html")


@app.route("/chat", methods=["POST"])
def chat():
    """
    Main chat endpoint.
    Returns response with source citations.
    """
    try:
        data = request.get_json() or {}
        query = (data.get("message") or "").strip()
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Pertanyaan kosong / Empty question"
            }), 400
        
        # Generate response with RAG
        result = generate_response(query, use_rag=True)
        
        if result.get("error"):
            return jsonify({
                "success": False,
                "error": result["error"]
            }), 500
        
        return jsonify({
            "success": True,
            "response": result["response"],
            "language": result.get("language", "id"),
            "context_used": result.get("context_used", False),
            "sources": result.get("sources", [])  # Citations for frontend
        })
        
    except Exception as e:
        print(f"Chat error: {e}")
        return jsonify({
            "success": False,
            "error": "Maaf, ada gangguan teknis. Coba lagi ya."
        }), 500


@app.route("/health", methods=["GET"])
def health():
    """Health check endpoint."""
    return jsonify({
        "status": "ok",
        "service": "gus-app"
    })


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
