#!/usr/bin/env python3
"""
Dark Web OSINT - Web Dashboard
Run: python web_app.py
Then open: http://localhost:5000
"""

import json
import sqlite3
import subprocess
import threading
import os
import csv
import io
import queue
from datetime import datetime, timedelta
from flask import Flask, render_template, jsonify, request, Response, send_file

app = Flask(__name__)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "findings.db")
CONFIG_PATH = os.path.join(BASE_DIR, "config.json")

# --- Crawl state ---
_crawl_lock = threading.Lock()
_crawl_process = None
_crawl_active = False
_log_queue = queue.Queue(maxsize=500)


# ─────────────────────────── helpers ────────────────────────────

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def load_config():
    try:
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}


def save_config(data):
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)


def _col(conn, table, *candidates):
    """Return the first existing column name from candidates."""
    cur = conn.execute(f"PRAGMA table_info({table})")
    cols = {row[1] for row in cur.fetchall()}
    for c in candidates:
        if c in cols:
            return c
    return candidates[0]


def _risk_label(score):
    if score is None:
        return "Unknown"
    score = float(score)
    if score >= 85:
        return "Critical"
    if score >= 70:
        return "High"
    if score >= 50:
        return "Medium"
    return "Low"


def _push_log(line):
    try:
        _log_queue.put_nowait(line)
    except queue.Full:
        pass


# ─────────────────────────── routes ─────────────────────────────

@app.route("/")
def index():
    return render_template("index.html")


# ── stats ──────────────────────────────────────────────────────

@app.route("/api/stats")
def api_stats():
    cfg = load_config()
    company = cfg.get("target_company", "")

    if not os.path.exists(DB_PATH):
        return jsonify({"total": 0, "critical": 0, "high": 0, "medium": 0, "low": 0,
                        "extracted": 0, "crawls": 0, "target": company})

    conn = get_db()
    p = (company,)

    total    = conn.execute("SELECT COUNT(*) FROM findings WHERE target_company=?", p).fetchone()[0]
    critical = conn.execute("SELECT COUNT(*) FROM findings WHERE target_company=? AND risk_score >= 85", p).fetchone()[0]
    high     = conn.execute("SELECT COUNT(*) FROM findings WHERE target_company=? AND risk_score >= 70 AND risk_score < 85", p).fetchone()[0]
    medium   = conn.execute("SELECT COUNT(*) FROM findings WHERE target_company=? AND risk_score >= 50 AND risk_score < 70", p).fetchone()[0]
    low      = conn.execute("SELECT COUNT(*) FROM findings WHERE target_company=? AND risk_score < 50", p).fetchone()[0]

    try:
        extracted = conn.execute("SELECT COUNT(*) FROM extracted_data").fetchone()[0]
    except Exception:
        extracted = 0

    try:
        crawls = conn.execute("SELECT COUNT(*) FROM crawl_history WHERE status='success'").fetchone()[0]
    except Exception:
        crawls = 0

    conn.close()
    return jsonify({
        "total": total, "critical": critical, "high": high,
        "medium": medium, "low": low, "extracted": extracted,
        "crawls": crawls, "target": company
    })


# ── chart data ─────────────────────────────────────────────────

@app.route("/api/chart-data")
def api_chart_data():
    if not os.path.exists(DB_PATH):
        return jsonify({"risk_dist": {}, "timeline": {}, "keywords": []})

    cfg = load_config()
    company = cfg.get("target_company", "")
    conn = get_db()

    # Risk distribution
    rows = conn.execute("""
        SELECT
            CASE
                WHEN risk_score >= 85 THEN 'Critical'
                WHEN risk_score >= 70 THEN 'High'
                WHEN risk_score >= 50 THEN 'Medium'
                ELSE 'Low'
            END as level,
            COUNT(*) as cnt
        FROM findings
        WHERE target_company=?
        GROUP BY level
    """, (company,)).fetchall()
    risk_dist = {r["level"]: r["cnt"] for r in rows}

    # Findings timeline – last 14 days
    timeline = {}
    for i in range(13, -1, -1):
        day = (datetime.utcnow() - timedelta(days=i)).strftime("%Y-%m-%d")
        timeline[day] = 0

    rows = conn.execute("""
        SELECT DATE(found_at) as day, COUNT(*) as cnt
        FROM findings
        WHERE target_company=? AND found_at >= DATE('now', '-14 days')
        GROUP BY day
    """, (company,)).fetchall()
    for r in rows:
        if r["day"] in timeline:
            timeline[r["day"]] = r["cnt"]

    # Top keywords
    rows = conn.execute("""
        SELECT keyword, COUNT(*) as cnt
        FROM findings
        WHERE target_company=? AND keyword IS NOT NULL
        GROUP BY keyword
        ORDER BY cnt DESC
        LIMIT 8
    """, (company,)).fetchall()
    keywords = [{"keyword": r["keyword"], "count": r["cnt"]} for r in rows]

    conn.close()
    return jsonify({"risk_dist": risk_dist, "timeline": timeline, "keywords": keywords})


# ── findings ───────────────────────────────────────────────────

@app.route("/api/findings")
def api_findings():
    if not os.path.exists(DB_PATH):
        return jsonify({"findings": [], "total": 0})

    cfg = load_config()
    company     = cfg.get("target_company", "")
    risk_filter = request.args.get("risk", "All")
    search      = request.args.get("search", "").strip()
    page        = max(1, int(request.args.get("page", 1)))
    per_page    = 20

    conn = get_db()
    url_col = _col(conn, "findings", "url", "source_url")

    conditions = ["target_company=?"]
    params     = [company]

    risk_ranges = {
        "Critical": "risk_score >= 85",
        "High":     "risk_score >= 70 AND risk_score < 85",
        "Medium":   "risk_score >= 50 AND risk_score < 70",
        "Low":      "risk_score < 50",
    }
    if risk_filter in risk_ranges:
        conditions.append(risk_ranges[risk_filter])

    if search:
        conditions.append(f"({url_col} LIKE ? OR keyword LIKE ?)")
        params += [f"%{search}%", f"%{search}%"]

    where = "WHERE " + " AND ".join(conditions)

    total = conn.execute(f"SELECT COUNT(*) FROM findings {where}", params).fetchone()[0]

    rows = conn.execute(
        f"""SELECT id, {url_col} as url, keyword, risk_score, confidence,
                   classification, found_at, snippet
            FROM findings {where}
            ORDER BY risk_score DESC, found_at DESC
            LIMIT ? OFFSET ?""",
        params + [per_page, (page - 1) * per_page]
    ).fetchall()

    findings = []
    for r in rows:
        findings.append({
            "id":             r["id"],
            "url":            r["url"],
            "keyword":        r["keyword"] or "N/A",
            "risk_score":     round(r["risk_score"] or 0),
            "risk_label":     _risk_label(r["risk_score"]),
            "confidence":     round(r["confidence"] or 0),
            "classification": r["classification"] or "Unknown",
            "found_at":       r["found_at"],
            "snippet":        (r["snippet"] or "")[:200],
        })

    conn.close()
    return jsonify({"findings": findings, "total": total, "page": page, "per_page": per_page})


# ── recent critical ────────────────────────────────────────────

@app.route("/api/recent-critical")
def api_recent_critical():
    if not os.path.exists(DB_PATH):
        return jsonify([])

    cfg = load_config()
    company = cfg.get("target_company", "")
    conn = get_db()
    url_col = _col(conn, "findings", "url", "source_url")
    rows = conn.execute(
        f"""SELECT {url_col} as url, keyword, risk_score, found_at
            FROM findings WHERE target_company=? AND risk_score >= 85
            ORDER BY risk_score DESC, found_at DESC LIMIT 5""",
        (company,)
    ).fetchall()
    conn.close()
    return jsonify([dict(r) for r in rows])


# ── crawl history ──────────────────────────────────────────────

@app.route("/api/crawl-history")
def api_crawl_history():
    if not os.path.exists(DB_PATH):
        return jsonify([])

    conn = get_db()
    try:
        rows = conn.execute(
            """SELECT url, status, status_code, crawled_at, duration_seconds
               FROM crawl_history ORDER BY crawled_at DESC LIMIT 50"""
        ).fetchall()
        conn.close()
        return jsonify([dict(r) for r in rows])
    except Exception:
        conn.close()
        return jsonify([])


# ── config ─────────────────────────────────────────────────────

@app.route("/api/config", methods=["GET"])
def api_config_get():
    return jsonify(load_config())


@app.route("/api/config", methods=["POST"])
def api_config_post():
    cfg = load_config()
    data = request.get_json(force=True)
    if "target_company" in data:
        cfg["target_company"] = data["target_company"]
    if "keywords" in data:
        cfg["keywords"] = data["keywords"]
    if "max_workers" in data:
        cfg.setdefault("crawling", {})["max_workers"] = int(data["max_workers"])
    if "timeout" in data:
        cfg.setdefault("tor", {})["timeout"] = int(data["timeout"])
    # Telegram fields
    if "telegram" in data:
        tg = data["telegram"]
        cfg.setdefault("alerts", {}).setdefault("telegram", {})
        if "bot_token" in tg and tg["bot_token"]:
            cfg["alerts"]["telegram"]["bot_token"] = tg["bot_token"]
        if "chat_id" in tg:
            cfg["alerts"]["telegram"]["chat_id"] = tg["chat_id"]
        if "enabled" in tg:
            cfg["alerts"]["telegram"]["enabled"] = bool(tg["enabled"])
    if "min_risk_score" in data:
        cfg.setdefault("alerts", {})["min_risk_score"] = int(data["min_risk_score"])
    save_config(cfg)
    return jsonify({"ok": True})


@app.route("/api/telegram/test", methods=["POST"])
def api_telegram_test():
    try:
        from alerts import AlertManager
        am = AlertManager(CONFIG_PATH)
        result = am.test_telegram_connection()
        return jsonify(result)
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


# ── crawl control ──────────────────────────────────────────────

@app.route("/api/crawl/start", methods=["POST"])
def api_crawl_start():
    global _crawl_active, _crawl_process

    with _crawl_lock:
        if _crawl_active:
            return jsonify({"ok": False, "message": "Crawl already running"})
        _crawl_active = True

    def _run():
        global _crawl_active, _crawl_process
        _push_log("[~] Starting crawl cycle...")
        try:
            proc = subprocess.Popen(
                ["python", os.path.join(BASE_DIR, "orchestrator.py")],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                cwd=BASE_DIR,
            )
            _crawl_process = proc
            for line in proc.stdout:
                _push_log(line.rstrip())
            proc.wait()
            _push_log(f"[+] Crawl finished (exit {proc.returncode})")
        except Exception as e:
            _push_log(f"[!] Crawl error: {e}")
        finally:
            with _crawl_lock:
                _crawl_active = False
                _crawl_process = None

    threading.Thread(target=_run, daemon=True).start()
    return jsonify({"ok": True})


@app.route("/api/findings/clear", methods=["POST"])
def api_findings_clear():
    """Delete all findings for the current target company and reset the URL queue"""
    cfg = load_config()
    company = cfg.get("target_company", "")
    conn = get_db()
    deleted = conn.execute(
        "DELETE FROM findings WHERE target_company=?", (company,)
    ).rowcount
    conn.execute("DELETE FROM url_queue")
    conn.commit()
    conn.close()
    _push_log(f"[~] Cleared {deleted} findings and URL queue for '{company}'")
    return jsonify({"ok": True, "deleted": deleted})


@app.route("/api/crawl/stop", methods=["POST"])
def api_crawl_stop():
    global _crawl_active, _crawl_process
    with _crawl_lock:
        if _crawl_process:
            _crawl_process.terminate()
            _push_log("[!] Crawl terminated by user")
        _crawl_active = False
    return jsonify({"ok": True})


@app.route("/api/crawl/status")
def api_crawl_status():
    return jsonify({"active": _crawl_active})


# ── live log stream (SSE) ──────────────────────────────────────

@app.route("/api/logs/stream")
def api_log_stream():
    def generate():
        while True:
            try:
                line = _log_queue.get(timeout=30)
                yield f"data: {json.dumps(line)}\n\n"
            except queue.Empty:
                yield "data: \n\n"   # heartbeat

    return Response(generate(), mimetype="text/event-stream",
                    headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


# ── report ────────────────────────────────────────────────────

REPORT_PATH = os.path.join(BASE_DIR, "osint_full_report.pdf")

@app.route("/api/report/generate", methods=["POST"])
def api_report_generate():
    _push_log("[~] Generating PDF report...")
    try:
        proc = subprocess.Popen(
            ["python", os.path.join(BASE_DIR, "generate_full_report.py"),
             REPORT_PATH, "30"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            cwd=BASE_DIR,
        )
        out, _ = proc.communicate(timeout=120)
        for line in out.splitlines():
            _push_log(line)
        if proc.returncode == 0 and os.path.exists(REPORT_PATH):
            _push_log("[✓] Report generated: osint_full_report.pdf")
            return jsonify({"ok": True})
        else:
            _push_log(f"[!] Report generation failed (exit {proc.returncode})")
            return jsonify({"ok": False, "message": "Generation failed"})
    except subprocess.TimeoutExpired:
        proc.kill()
        return jsonify({"ok": False, "message": "Timed out"})
    except Exception as e:
        return jsonify({"ok": False, "message": str(e)})


@app.route("/api/report/download")
def api_report_download():
    if not os.path.exists(REPORT_PATH):
        return "Report not found. Generate it first.", 404
    return send_file(REPORT_PATH, as_attachment=True,
                     download_name="osint_full_report.pdf",
                     mimetype="application/pdf")


@app.route("/api/report/status")
def api_report_status():
    exists = os.path.exists(REPORT_PATH)
    mtime  = None
    if exists:
        mtime = datetime.fromtimestamp(os.path.getmtime(REPORT_PATH)).strftime("%Y-%m-%d %H:%M")
    return jsonify({"exists": exists, "generated_at": mtime})


# ── export CSV ─────────────────────────────────────────────────

@app.route("/api/export/csv")
def api_export_csv():
    if not os.path.exists(DB_PATH):
        return "No database found", 404

    cfg = load_config()
    company = cfg.get("target_company", "")
    conn = get_db()
    url_col = _col(conn, "findings", "url", "source_url")
    rows = conn.execute(
        f"""SELECT id, {url_col} as url, keyword, risk_score, confidence,
                   classification, found_at
            FROM findings WHERE target_company=? ORDER BY risk_score DESC""",
        (company,)
    ).fetchall()
    conn.close()

    buf = io.StringIO()
    writer = csv.writer(buf)
    writer.writerow(["ID", "URL", "Keyword", "Risk Score", "Risk Level",
                     "Confidence", "Classification", "Date"])
    for r in rows:
        writer.writerow([
            r["id"], r["url"], r["keyword"],
            round(r["risk_score"] or 0), _risk_label(r["risk_score"]),
            round(r["confidence"] or 0), r["classification"], r["found_at"]
        ])

    buf.seek(0)
    filename = f"findings_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
    return Response(
        buf.getvalue(),
        mimetype="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"}
    )


# ─────────────────────────── main ───────────────────────────────

if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "templates"), exist_ok=True)
    print("=" * 50)
    print("  Dark Web OSINT Dashboard")
    print("  http://localhost:5000")
    print("=" * 50)
    app.run(debug=False, host="0.0.0.0", port=5000, threaded=True)
