"""
Flask web server - giao diện upload file OCR
"""
import uuid
import threading
import time
from pathlib import Path
from flask import Flask, request, jsonify, send_from_directory

from ocr_engine import OCREngine, detect_ocr_lang, lang_display_name

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config["MAX_CONTENT_LENGTH"] = 50 * 1024 * 1024  # 50 MB

UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

SUPPORTED = {".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".webp", ".pdf"}
_JOB_TTL = 3600  # xoá job sau 1 giờ

jobs: dict[str, dict] = {}
_engine_lock = threading.Lock()
engine_cache: dict[str, OCREngine] = {}


def get_engine(lang: str) -> OCREngine:
    with _engine_lock:
        if lang not in engine_cache:
            engine_cache[lang] = OCREngine(lang=lang, use_gpu=False)
    return engine_cache[lang]


def _do_ocr(engine: OCREngine, file_path: Path, dpi: int):
    is_pdf = file_path.suffix.lower() == ".pdf"
    if is_pdf:
        pages = engine.ocr_pdf(file_path, dpi=dpi)
        text = "\n".join(
            f"\n--- Trang {p['page']} ---\n{p['text']}" for p in pages
        ).strip()
        return text, len(pages)
    blocks = engine.ocr_image(file_path)
    return "\n".join(b["text"] for b in blocks), 1


def run_ocr(job_id: str, file_path: Path, lang: str, dpi: int):
    try:
        is_auto = (lang == "auto")
        first_lang = "en" if is_auto else lang

        jobs[job_id]["status"] = "loading_model"
        engine = get_engine(first_lang)

        jobs[job_id]["status"] = "processing"
        text, page_count = _do_ocr(engine, file_path, dpi)

        detected_lang = first_lang
        if is_auto:
            detected_lang = detect_ocr_lang(text)
            if detected_lang != first_lang:
                jobs[job_id]["status"] = "loading_model"
                engine2 = get_engine(detected_lang)
                jobs[job_id]["status"] = "processing"
                text, page_count = _do_ocr(engine2, file_path, dpi)

        jobs[job_id].update({
            "status": "done",
            "text": text,
            "page_count": page_count,
            "char_count": len(text),
            "detected_lang": detected_lang,
            "detected_lang_name": lang_display_name(detected_lang),
            "finished_at": time.time(),
        })
    except Exception as e:
        import traceback
        jobs[job_id].update({
            "status": "error",
            "error": str(e),
            "trace": traceback.format_exc(),
            "finished_at": time.time(),
        })
    finally:
        try:
            file_path.unlink(missing_ok=True)
        except Exception:
            pass


def _cleanup_jobs():
    while True:
        time.sleep(600)
        cutoff = time.time() - _JOB_TTL
        stale = [jid for jid, j in list(jobs.items()) if j.get("finished_at", 0) < cutoff]
        for jid in stale:
            jobs.pop(jid, None)

threading.Thread(target=_cleanup_jobs, daemon=True).start()

# Warm up engine mặc định khi server start (tiếng Việt)
def _warmup():
    try:
        get_engine("vi")
    except Exception:
        pass

threading.Thread(target=_warmup, daemon=True).start()


@app.route("/")
def index():
    return send_from_directory("templates", "index.html")


@app.route("/upload", methods=["POST"])
def upload():
    if "file" not in request.files:
        return jsonify({"error": "Không có file"}), 400

    file = request.files["file"]
    if not file.filename:
        return jsonify({"error": "Tên file trống"}), 400

    suffix = Path(file.filename).suffix.lower()
    if suffix not in SUPPORTED:
        return jsonify({"error": f"Định dạng không hỗ trợ: {suffix}"}), 400

    lang = request.form.get("lang", "vi")
    try:
        dpi = max(72, min(600, int(request.form.get("dpi", 200))))
    except (ValueError, TypeError):
        dpi = 200

    job_id = uuid.uuid4().hex
    save_path = UPLOAD_DIR / f"{job_id}{suffix}"
    file.save(save_path)

    jobs[job_id] = {"status": "queued", "filename": file.filename}

    thread = threading.Thread(
        target=run_ocr, args=(job_id, save_path, lang, dpi), daemon=True
    )
    thread.start()

    return jsonify({"job_id": job_id, "filename": file.filename})


@app.route("/status/<job_id>")
def status(job_id: str):
    job = jobs.get(job_id)
    if not job:
        return jsonify({"error": "Job không tồn tại"}), 404
    return jsonify(job)


if __name__ == "__main__":
    app.run(host="0.0.0.0", debug=False, port=5000)
