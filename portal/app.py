"""
Vinil NFC Player — Setup Portal & Settings
Modes (VINIL_MODE env var):
  setup    → full wizard (WiFi + Spotify), serves on port 80
  oauth    → Spotify OAuth step only, serves on port 80
  settings → settings page alongside player, serves on port 5000
"""
import os
import json
import subprocess
import threading
import time
from pathlib import Path

from flask import Flask, render_template, request, redirect, url_for, jsonify
from dotenv import load_dotenv

BASE_DIR = Path(__file__).parent.parent.resolve()
ENV_FILE = BASE_DIR / ".env"
CACHE_FILE = BASE_DIR / ".spotify_cache"
NETWORKS_CACHE = BASE_DIR / ".wifi_networks_cache"
PORTAL_REDIRECT_URI = "https://vinil-relay.vercel.app/callback"
SCOPES = "user-modify-playback-state user-read-playback-state"

MODE = os.environ.get("VINIL_MODE", "setup")

app = Flask(__name__)
app.secret_key = os.urandom(24)

load_dotenv(ENV_FILE)


# ── WiFi helpers ──────────────────────────────────────────────────────────────

def scan_wifi() -> list:
    if MODE == "setup" and NETWORKS_CACHE.exists():
        try:
            return json.loads(NETWORKS_CACHE.read_text())
        except Exception:
            pass
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY",
             "device", "wifi", "list", "--rescan", "yes"],
            capture_output=True, text=True, timeout=15
        )
        networks = []
        seen = set()
        for line in result.stdout.strip().splitlines():
            parts = line.split(":")
            if len(parts) < 2:
                continue
            ssid = parts[0].strip()
            if not ssid or ssid in seen or ssid == "Vinil Player Setup":
                continue
            seen.add(ssid)
            signal = int(parts[1]) if parts[1].isdigit() else 0
            secured = len(parts) > 2 and parts[2].strip() not in ("", "--")
            networks.append({"ssid": ssid, "signal": signal, "secured": secured})
        return sorted(networks, key=lambda n: -n["signal"])
    except Exception:
        return []


def connect_wifi(ssid: str, password: str) -> tuple:
    cmd = ["sudo", "nmcli", "device", "wifi", "connect", ssid]
    if password:
        cmd += ["password", password]
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
        if result.returncode == 0:
            return True, ""
        return False, result.stderr.strip() or "Falha na conexão"
    except subprocess.TimeoutExpired:
        return False, "Tempo esgotado. Verifique a senha e tente novamente."


def get_current_ssid() -> str:
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "ACTIVE,SSID", "device", "wifi"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            if line.startswith("yes:"):
                return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return ""


def check_wifi_connected() -> bool:
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "CONNECTIVITY", "general"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "full"
    except Exception:
        return False


# ── Spotify OAuth helpers ─────────────────────────────────────────────────────

def get_spotify_oauth():
    load_dotenv(ENV_FILE)
    import spotipy
    from spotipy.oauth2 import SpotifyOAuth
    return SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=PORTAL_REDIRECT_URI,
        scope=SCOPES,
        cache_path=str(CACHE_FILE),
        open_browser=False,
    )


def get_spotify_auth_url() -> str:
    try:
        return get_spotify_oauth().get_authorize_url()
    except Exception:
        return ""


def handle_spotify_callback(code: str) -> tuple:
    try:
        oauth = get_spotify_oauth()
        token = oauth.get_access_token(code, as_dict=False)
        return bool(token), ""
    except Exception as e:
        return False, str(e)


# ── Reboot helper ─────────────────────────────────────────────────────────────

def schedule_reboot(delay: int = 3):
    def _reboot():
        time.sleep(delay)
        subprocess.run(["sudo", "reboot"])
    threading.Thread(target=_reboot, daemon=True).start()


def schedule_restart(delay: int = 2):
    def _restart():
        time.sleep(delay)
        subprocess.run(["sudo", "systemctl", "restart", "vinil.service"])
    threading.Thread(target=_restart, daemon=True).start()


# ── Routes: Setup Wizard ──────────────────────────────────────────────────────

@app.route("/")
def index():
    if MODE == "settings":
        return redirect(url_for("settings"))
    if MODE == "oauth" or check_wifi_connected():
        return redirect(url_for("setup_spotify"))
    return render_template("setup.html", step=1, networks=scan_wifi())


@app.route("/setup/wifi", methods=["POST"])
def setup_wifi():
    ssid = request.form.get("ssid", "").strip()
    password = request.form.get("password", "").strip()
    if not ssid:
        return render_template("setup.html", step=1, networks=scan_wifi(),
                               error="Selecione uma rede Wi-Fi.")
    success, error = connect_wifi(ssid, password)
    if not success:
        return render_template("setup.html", step=1, networks=scan_wifi(),
                               error=f"Erro: {error}")
    return render_template("setup.html", step=2)


@app.route("/setup/reboot", methods=["POST"])
def setup_reboot():
    schedule_reboot(2)
    return render_template("setup.html", step=2, rebooting=True)


@app.route("/setup/spotify")
def setup_spotify():
    auth_url = get_spotify_auth_url()
    if not auth_url:
        return render_template("setup.html", step=3,
                               error="Credenciais Spotify não configuradas. "
                                     "Edite o arquivo .env no Vinil.")
    return render_template("setup.html", step=3, auth_url=auth_url)


@app.route("/callback")
def spotify_callback():
    code = request.args.get("code")
    error = request.args.get("error")
    if error or not code:
        return render_template("setup.html", step=3,
                               error=f"Autorização negada: {error or 'sem código'}")
    success, msg = handle_spotify_callback(code)
    if not success:
        return render_template("setup.html", step=3, error=msg)
    schedule_restart(2)
    return render_template("setup.html", step=4)


# ── Routes: Settings ──────────────────────────────────────────────────────────

@app.route("/settings")
def settings():
    return render_template(
        "settings.html",
        connected=check_wifi_connected(),
        current_ssid=get_current_ssid(),
        has_token=CACHE_FILE.exists(),
    )


@app.route("/settings/wifi", methods=["GET", "POST"])
def settings_wifi():
    if request.method == "GET":
        return render_template("settings.html",
                               section="wifi",
                               networks=scan_wifi(),
                               connected=check_wifi_connected(),
                               current_ssid=get_current_ssid(),
                               has_token=CACHE_FILE.exists())
    ssid = request.form.get("ssid", "").strip()
    password = request.form.get("password", "").strip()
    success, error = connect_wifi(ssid, password)
    if not success:
        return render_template("settings.html",
                               section="wifi",
                               networks=scan_wifi(),
                               error=error,
                               connected=check_wifi_connected(),
                               current_ssid=get_current_ssid(),
                               has_token=CACHE_FILE.exists())
    return redirect(url_for("settings"))


@app.route("/settings/spotify/reset", methods=["POST"])
def settings_spotify_reset():
    CACHE_FILE.unlink(missing_ok=True)
    return redirect(url_for("setup_spotify"))


@app.route("/settings/factory-reset", methods=["POST"])
def settings_factory_reset():
    CACHE_FILE.unlink(missing_ok=True)
    try:
        # Desconecta a interface WiFi
        subprocess.run(
            ["sudo", "nmcli", "device", "disconnect", "wlan0"],
            capture_output=True, timeout=10
        )
        # Remove todos os perfis WiFi salvos (exceto hotspot)
        result = subprocess.run(
            ["nmcli", "-t", "-f", "NAME,TYPE", "connection", "show"],
            capture_output=True, text=True, timeout=5
        )
        for line in result.stdout.splitlines():
            name, _, conn_type = line.partition(":")
            if conn_type.strip() == "802-11-wireless" and name.strip() != "Hotspot":
                subprocess.run(
                    ["sudo", "nmcli", "connection", "delete", name.strip()],
                    capture_output=True, timeout=10
                )
    except Exception:
        pass
    schedule_restart(2)
    return render_template("settings.html",
                           rebooting=True,
                           connected=False, current_ssid="", has_token=False)


@app.route("/settings/reboot", methods=["POST"])
def settings_reboot():
    schedule_reboot(2)
    return render_template("settings.html",
                           rebooting=True,
                           connected=True, current_ssid="", has_token=True)


@app.route("/api/status")
def api_status():
    return jsonify({
        "wifi": check_wifi_connected(),
        "wifi_ssid": get_current_ssid(),
        "spotify": CACHE_FILE.exists(),
        "mode": MODE,
    })


# ── Entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    port = 5000 if MODE == "settings" else 8080
    app.run(host="0.0.0.0", port=port, debug=False)
