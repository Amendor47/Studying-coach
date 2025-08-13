from flask import Flask, jsonify, request

from services.store import load_db, save_db
from services.validate import seed_seen_hashes, validate_items


app = Flask(__name__)


def _persist_items(db, items):
    """Insert validated items into the in-memory database structure."""
    for item in items:
        kind = item.get("kind")
        payload = item.get("payload", {})
        if kind == "card":
            db.setdefault("cards", []).append(payload)
        elif kind == "exercise":
            db.setdefault("exercises", []).append(payload)


@app.route("/api/upload", methods=["POST"])
def upload():
    db = load_db()
    seed_seen_hashes(db)
    items = request.get_json(force=True)
    validated = validate_items(items)
    _persist_items(db, validated)
    save_db(db)
    return jsonify({"count": len(validated)})


@app.route("/api/save", methods=["POST"])
def save():
    db = load_db()
    seed_seen_hashes(db)
    items = request.get_json(force=True)
    validated = validate_items(items)
    _persist_items(db, validated)
    save_db(db)
    return jsonify({"count": len(validated)})


@app.route("/api/web/enrich", methods=["POST"])
def web_enrich():
    db = load_db()
    seed_seen_hashes(db)
    payload = request.get_json(force=True)
    items = payload.get("items", []) if isinstance(payload, dict) else []
    validated = validate_items(items)
    _persist_items(db, validated)
    save_db(db)
    return jsonify({"count": len(validated)})


@app.route("/api/export/<ext>", methods=["GET"])
def export_fiches(ext):
    """Placeholder export route."""
    return jsonify({"ext": ext})


if __name__ == "__main__":
    app.run(debug=True)

