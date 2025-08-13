from flask import Flask, jsonify, request, render_template, Response, send_file
import io
import csv
import os
import sys

from services.analyzer import analyze_offline
from services.heuristics import ai_needed, readability, density
from services.store import load_db, save_db
from typing import Dict
from services.validate import validate_items
from services.ai import analyze_text
from services.rag import get_context
from services.planner import generate_plan
from services.scheduler import (
    due_cards,
    update_srs,
    build_exercises_from_cards,
    save_progress,
)
from services.parsers import extract_text
from services.webfetch import web_context_from_query
from pathlib import Path
from services.teacher import LocalTeacher

BASE_DIR = getattr(sys, "_MEIPASS", os.path.dirname(os.path.abspath(__file__)))
app = Flask(
    __name__,
    static_folder=os.path.join(BASE_DIR, "static"),
    template_folder=os.path.join(BASE_DIR, "templates"),
)

teacher = LocalTeacher()


# ---- configuration & API key management ----
ENV_FILE = Path(".env")


@app.route("/api/config", methods=["GET", "POST"])
def api_config():
    """Expose presence of OPENAI_API_KEY and allow setting it."""
    if request.method == "GET":
        return jsonify({"has_key": bool(os.getenv("OPENAI_API_KEY"))})

    data = request.get_json(force=True)
    key = data.get("key", "").strip()
    if not key:
        return jsonify({"saved": False}), 400
    os.environ["OPENAI_API_KEY"] = key
    ENV_FILE.write_text(f"OPENAI_API_KEY={key}\n", encoding="utf-8")
    return jsonify({"saved": True})


@app.route("/api/upload", methods=["POST"])
def upload_file():
    """Handle document upload and full analysis pipeline."""
    uploaded = request.files.get("file")
    if not uploaded:
        return jsonify({"error": "no file"}), 400
    use_ai = request.form.get("use_ai", "false").lower() == "true"
    minutes = int(request.form.get("session_minutes", 0))
    import tempfile
    from datetime import date

    tmp = tempfile.NamedTemporaryFile(delete=False)
    uploaded.save(tmp.name)
    try:
        text = extract_text(tmp.name, uploaded.filename)
    finally:
        os.unlink(tmp.name)

    offline_drafts = analyze_offline(text)
    drafts = offline_drafts
    if use_ai and os.getenv("OPENAI_API_KEY"):
        context = get_context(text)
        combined = "\n".join(context) + "\n\n" + text if context else text
        ai_drafts = analyze_text(combined, "upload")
        drafts = validate_items(offline_drafts + ai_drafts)
    else:
        drafts = validate_items(offline_drafts)

    for d in drafts:
        d.setdefault("status", "new")

    db = load_db()
    db["drafts"].extend(drafts)
    for d in drafts:
        payload = d.get("payload", {})
        if d.get("kind") == "card":
            payload.setdefault("id", d.get("id"))
            payload.setdefault(
                "srs",
                {"EF": 2.5, "interval": 1, "reps": 0, "due": date.today().isoformat()},
            )
            db.setdefault("cards", []).append(payload)
        elif d.get("kind") == "exercise":
            db.setdefault("exercises", []).append(payload)
        elif d.get("kind") == "course":
            db.setdefault("courses", []).append(payload)
    save_db(db)

    plan = generate_plan(db.get("drafts", []))
    themes = list({d.get("payload", {}).get("theme", "Général") for d in drafts})
    due = due_cards(db)
    return jsonify({
        "saved": len(drafts),
        "plan": plan,
        "themes": themes,
        "due": due,
        "minutes": minutes,
    })


@app.route("/api/offline/analyze", methods=["POST"])
def offline_analyze():
    data = request.get_json(force=True)
    text = data.get("text", "")
    drafts = analyze_offline(text)
    need_ai = ai_needed(text, drafts)
    meta = {"readability": readability(text), "density": density(text, drafts)}
    return jsonify({"drafts": drafts, "need_ai": need_ai, "meta": meta})


@app.route("/api/ai/analyze", methods=["POST"])
def ai_analyze():
    data = request.get_json(force=True)
    text = data.get("text", "")
    force = data.get("force", False)
    reason = data.get("reason", "")
    offline_drafts = analyze_offline(text)
    need_ai = ai_needed(text, offline_drafts)
    if not (need_ai or force):
        return jsonify({"drafts": validate_items(offline_drafts), "reason": "offline"})
    reason = reason or ("heuristic" if need_ai else "forced")
    context = get_context(text)
    combined = "\n".join(context) + "\n\n" + text if context else text
    ai_drafts = analyze_text(combined, reason)
    drafts = validate_items(offline_drafts + ai_drafts)
    return jsonify({"drafts": drafts, "reason": reason})


@app.route("/api/save", methods=["POST"])
def save_items():
    data = request.get_json(force=True)
    items = data.get("items", [])
    validated = validate_items(items)
    for d in validated:
        d.setdefault("status", "new")
    db = load_db()
    db["drafts"].extend(validated)
    # also populate dedicated card/exercise stores with SRS defaults
    from datetime import date

    for d in validated:
        payload = d.get("payload", {})
        if d.get("kind") == "card":
            payload.setdefault("id", d.get("id"))
            payload.setdefault(
                "srs",
                {"EF": 2.5, "interval": 1, "reps": 0, "due": date.today().isoformat()},
            )
            db.setdefault("cards", []).append(payload)
        elif d.get("kind") == "exercise":
            db.setdefault("exercises", []).append(payload)
    save_db(db)
    return jsonify({"saved": len(validated)})


@app.route("/api/plan", methods=["GET"])
def plan_route():
    db = load_db()
    plan = generate_plan(db.get("drafts", []))
    return jsonify({"plan": plan})


@app.route("/api/due", methods=["GET"])
def due_route():
    db = load_db()
    cards = due_cards(db)
    exercises = db.get("exercises", []) + build_exercises_from_cards(cards)
    return jsonify({"cards": cards, "exercises": exercises})


@app.route("/api/review/<cid>", methods=["POST"])
def review_route(cid: str):
    data = request.get_json(force=True)
    quality = int(data.get("quality", 0))
    db = load_db()
    for c in db.get("cards", []):
        if c.get("id") == cid:
            update_srs(c, quality)
            break
    save_progress(db)
    return jsonify({"ok": True})


@app.route("/api/themes", methods=["GET"])
def themes_route():
    """Return available themes and counts."""
    db = load_db()
    counts: Dict[str, Dict[str, int]] = {}
    for d in db.get("drafts", []):
        theme = d.get("payload", {}).get("theme", "Général")
        entry = counts.setdefault(theme, {"cards": 0, "exercises": 0})
        if d.get("kind") == "card":
            entry["cards"] += 1
        elif d.get("kind") == "exercise":
            entry["exercises"] += 1
    themes = [
        {"name": t, "cards": v["cards"], "exercises": v["exercises"]}
        for t, v in sorted(counts.items())
    ]
    return jsonify({"themes": themes})


@app.route("/api/fiches/<theme>", methods=["GET"])
def fiches_by_theme(theme: str):
    db = load_db()
    items = [
        d
        for d in db.get("drafts", [])
        if d.get("payload", {}).get("theme", "Général") == theme
    ]
    cards = [d for d in items if d.get("kind") == "card"]
    exercises = [d for d in items if d.get("kind") == "exercise"]
    courses = [d for d in items if d.get("kind") == "course"]
    return jsonify({"cards": cards, "exercises": exercises, "courses": courses})


@app.route("/api/card/<cid>/status", methods=["POST"])
def update_card_status(cid: str):
    data = request.get_json(force=True)
    status = data.get("status", "")
    db = load_db()
    for d in db.get("drafts", []):
        if d.get("id") == cid:
            d["status"] = status
            break
    save_db(db)
    return jsonify({"ok": True})


@app.route("/api/export/<fmt>", methods=["GET"])
def export_route(fmt: str):
    db = load_db()
    cards = db.get("cards", [])
    if fmt == "csv":
        buf = io.StringIO()
        writer = csv.writer(buf, delimiter=";")
        writer.writerow(["front", "back", "tags"])
        for c in cards:
            writer.writerow([c.get("front"), c.get("back"), c.get("theme", "")])
        buf.seek(0)
        return Response(
            buf.getvalue(),
            mimetype="text/csv",
            headers={"Content-Disposition": "attachment; filename=fiches.csv"},
        )
    if fmt == "pdf":
        try:
            from reportlab.lib.pagesizes import letter
            from reportlab.pdfgen import canvas
            buf = io.BytesIO()
            c = canvas.Canvas(buf, pagesize=letter)
            y = 750
            for card in cards:
                c.drawString(72, y, f"{card.get('front')}: {card.get('back')}")
                y -= 20
                if y < 72:
                    c.showPage()
                    y = 750
            c.save()
            buf.seek(0)
            return send_file(buf, as_attachment=True, download_name="fiches.pdf", mimetype="application/pdf")
        except Exception:
            return jsonify({"error": "pdf export unavailable"}), 500
    if fmt == "docx":
        try:
            from docx import Document
            buf = io.BytesIO()
            doc = Document()
            for card in cards:
                doc.add_heading(card.get("front"), level=2)
                doc.add_paragraph(card.get("back"))
            doc.save(buf)
            buf.seek(0)
            return send_file(buf, as_attachment=True, download_name="fiches.docx")
        except Exception:
            return jsonify({"error": "docx export unavailable"}), 500
    return jsonify({"error": "format inconnu"}), 400


@app.route("/api/web/search", methods=["GET"])
def web_search():
    q = request.args.get("q", "").strip()
    if not q:
        return jsonify({"results": []})
    try:
        results = web_context_from_query(q, k_pages=5)
    except Exception:
        results = []
    return jsonify({
        "results": [
            {"title": r["title"], "url": r["url"], "excerpt": r["excerpt"][:300]}
            for r in results
        ]
    })


@app.route("/api/web/enrich", methods=["POST"])
def web_enrich():
    data = request.get_json(force=True)
    query = data.get("query", "").strip()
    use_ai = bool(data.get("use_ai", False))
    if not query:
        return jsonify({"added": 0, "drafts": [], "citations": []})

    try:
        pages = web_context_from_query(query, k_pages=3, max_chars=5000)
    except Exception:
        pages = []
    combined = "\n\n".join([p["excerpt"] for p in pages])
    offline_drafts = analyze_offline(combined)

    drafts = offline_drafts
    if use_ai and os.getenv("OPENAI_API_KEY"):
        context_text = "".join(f"\n# {p['title']}\n{p['excerpt']}\n" for p in pages)
        ai_drafts = analyze_text(context_text, reason="web+rag")
        drafts = validate_items(offline_drafts + ai_drafts)
    else:
        drafts = validate_items(offline_drafts)

    db = load_db()
    from datetime import date
    for d in drafts:
        d.setdefault("status", "new")
        db["drafts"].append(d)
        payload = d.get("payload", {})
        if d.get("kind") == "card":
            payload.setdefault("id", d.get("id"))
            payload.setdefault(
                "srs",
                {"EF": 2.5, "interval": 1, "reps": 0, "due": date.today().isoformat()},
            )
            db.setdefault("cards", []).append(payload)
        elif d.get("kind") == "exercise":
            db.setdefault("exercises", []).append(payload)
        elif d.get("kind") == "course":
            db.setdefault("courses", []).append(payload)
    save_db(db)

    citations = [{"title": p["title"], "url": p["url"]} for p in pages]
    return jsonify({"added": len(drafts), "drafts": drafts, "citations": citations})


@app.route("/api/chat", methods=["POST"])
def chat_route():
    data = request.get_json(force=True)
    msg = data.get("message", "")
    answer = teacher.chat(msg)
    return jsonify({"answer": answer})


@app.route("/")
def index():
    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True)
