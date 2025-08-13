@app.route("/api/export/<ext>", methods=["GET"])
def export_fiches(ext):
    # Exporter les fiches au format demandé
    if ext == "csv":
        ...
    elif ext == "pdf":
        ...
    elif ext == "docx":
        ...
    return send_file(...)