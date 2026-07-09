"""Phoenix VPN V10 – config management panel with authentication."""

from __future__ import annotations

import base64
import os
from datetime import datetime, timezone
from io import BytesIO
from pathlib import Path

import qrcode
from auth import PanelUser, build_users, verify_user
from flask import Flask, abort, jsonify, redirect, render_template, request, send_file, url_for
from flask_cors import CORS
from flask_login import LoginManager, current_user, login_required, login_user, logout_user

BASE_DIR = Path(__file__).resolve().parent.parent
CONFIGS_DIR = BASE_DIR / "phoenix-output" / "configs"
SUBSCRIPTIONS_DIR = BASE_DIR / "phoenix-output" / "subscriptions"
LOGS_DIR = BASE_DIR / "phoenix-output" / "logs"

app = Flask(__name__)
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY", "phoenix-secret-key")
CORS(app)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login"
USERS = build_users()


@login_manager.user_loader
def load_user(user_id: str) -> PanelUser | None:
    for user in USERS.values():
        if user.id == user_id:
            return user
    return None


def _safe_config_path(relative: str) -> Path:
    target = (CONFIGS_DIR / relative).resolve()
    configs_root = CONFIGS_DIR.resolve()
    if not str(target).startswith(str(configs_root)):
        abort(403)
    return target


def _collect_configs() -> list[dict]:
    nodes: list[dict] = []
    if not CONFIGS_DIR.exists():
        return nodes
    for protocol in sorted(CONFIGS_DIR.iterdir()):
        if not protocol.is_dir():
            continue
        for node_dir in sorted(protocol.iterdir()):
            if not node_dir.is_dir():
                continue
            for client_file in sorted(node_dir.glob("client.*")):
                try:
                    content = client_file.read_text(encoding="utf-8", errors="replace")
                except OSError:
                    continue
                rel = client_file.relative_to(CONFIGS_DIR)
                nodes.append(
                    {
                        "id": node_dir.name,
                        "protocol": protocol.name,
                        "filename": client_file.name,
                        "path": str(rel).replace("\\", "/"),
                        "content": content,
                        "preview": content[:200] + ("..." if len(content) > 200 else ""),
                    }
                )
    return nodes


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))
    error = None
    if request.method == "POST":
        user = verify_user(USERS, request.form.get("username", ""), request.form.get("password", ""))
        if user:
            login_user(user)
            return redirect(url_for("index"))
        error = "نام کاربری یا رمز عبور اشتباه است"
    return render_template("login.html", error=error)


@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect(url_for("login"))


@app.route("/")
@login_required
def index():
    nodes = _collect_configs()
    return render_template("index.html", nodes=nodes, total=len(nodes))


@app.route("/config/<path:filepath>")
@login_required
def view_config(filepath: str):
    full_path = _safe_config_path(filepath)
    if not full_path.is_file():
        abort(404)
    content = full_path.read_text(encoding="utf-8", errors="replace")
    protocol = Path(filepath).parts[0] if Path(filepath).parts else "unknown"
    return render_template(
        "config_detail.html",
        filename=full_path.name,
        path=filepath,
        content=content,
        protocol=protocol,
    )


@app.route("/download/<path:filepath>")
@login_required
def download_config(filepath: str):
    full_path = _safe_config_path(filepath)
    if not full_path.is_file():
        abort(404)
    return send_file(full_path, as_attachment=True, download_name=full_path.name)


@app.route("/subscriptions")
@login_required
def subscriptions():
    subs: list[dict] = []
    if SUBSCRIPTIONS_DIR.exists():
        for file in sorted(SUBSCRIPTIONS_DIR.glob("*.txt")):
            try:
                content = file.read_text(encoding="utf-8", errors="replace")
            except OSError:
                continue
            subs.append({"name": file.name, "content": content})
    return render_template("subscriptions.html", subscriptions=subs)


@app.route("/how-to")
@login_required
def how_to():
    return render_template("how_to.html")


@app.route("/api/subscriptions/<node_id>")
def api_subscription(node_id: str):
    sub_file = SUBSCRIPTIONS_DIR / f"{node_id}.txt"
    if not sub_file.is_file():
        return jsonify({"error": "Not found"}), 404
    return jsonify({"content": sub_file.read_text(encoding="utf-8", errors="replace")})


@app.route("/api/qr")
@login_required
def generate_qr():
    config = request.args.get("config", "")
    if not config:
        return jsonify({"error": "No config provided"}), 400
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(config)
    qr.make(fit=True)
    img = qr.make_image(fill_color="black", back_color="white")
    if hasattr(img, "get_image"):
        img = img.get_image()
    buffered = BytesIO()
    img.save(buffered, format="PNG")
    return jsonify({"qr": base64.b64encode(buffered.getvalue()).decode()})


@app.route("/admin")
@login_required
def admin():
    stats = {
        "total_configs": 0,
        "total_nodes": set(),
        "protocols": [],
        "last_update": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M UTC"),
    }
    if CONFIGS_DIR.exists():
        for protocol in sorted(CONFIGS_DIR.iterdir()):
            if not protocol.is_dir():
                continue
            node_dirs = [d for d in protocol.iterdir() if d.is_dir()]
            stats["protocols"].append({"name": protocol.name, "nodes": len(node_dirs)})
            stats["total_configs"] += len(node_dirs)
            stats["total_nodes"].update(d.name for d in node_dirs)
    stats["total_nodes"] = len(stats["total_nodes"])

    logs: list[str] = []
    log_file = LOGS_DIR / "phoenix.log"
    if log_file.is_file():
        try:
            logs = log_file.read_text(encoding="utf-8", errors="replace").splitlines()[-30:]
        except OSError:
            pass

    return render_template("admin.html", stats=stats, logs=logs)


@app.route("/api/status")
def api_status():
    count = len(list(CONFIGS_DIR.glob("*/*/client.*"))) if CONFIGS_DIR.exists() else 0
    return jsonify(
        {
            "status": "healthy",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "configs": count,
            "uptime": "running",
        }
    )


@app.route("/api/nodes")
@login_required
def api_nodes():
    seen: set[tuple[str, str]] = set()
    nodes: list[dict] = []
    for item in _collect_configs():
        key = (item["id"], item["protocol"])
        if key in seen:
            continue
        seen.add(key)
        nodes.append(
            {"id": item["id"], "protocol": item["protocol"], "location": item["id"][:8], "status": "active"}
        )
    return jsonify(nodes)


if __name__ == "__main__":
    port = int(os.environ.get("PHOENIX_PANEL_PORT", "5050"))
    debug = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=port, debug=debug)
