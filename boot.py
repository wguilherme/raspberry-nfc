#!/usr/bin/env python3
"""
Vinil NFC Player — Boot Manager
Decides which mode to start based on current state:
  - No WiFi  → hotspot + setup wizard (Flask porta 80)
  - WiFi ok, sem token → Spotify OAuth (Flask porta 80)
  - Tudo ok  → player + settings server em paralelo
"""
import os
import sys
import json
import time
import subprocess
import threading
from pathlib import Path

BASE_DIR = Path(__file__).parent.resolve()
CACHE_FILE = BASE_DIR / ".spotify_cache"
ENV_FILE = BASE_DIR / ".env"
NETWORKS_CACHE = BASE_DIR / ".wifi_networks_cache"


def check_wifi_connected() -> bool:
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "CONNECTIVITY", "general"],
            capture_output=True, text=True, timeout=5
        )
        return result.stdout.strip() == "full"
    except Exception:
        return False


def check_spotify_token() -> bool:
    if not CACHE_FILE.exists():
        return False
    try:
        data = json.loads(CACHE_FILE.read_text())
        return bool(data.get("access_token"))
    except Exception:
        return False


def check_env_configured() -> bool:
    if not ENV_FILE.exists():
        return False
    content = ENV_FILE.read_text()
    return "SPOTIFY_CLIENT_ID=" in content and "SPOTIFY_CLIENT_SECRET=" in content


def scan_and_cache_networks():
    print("[boot] Escaneando redes WiFi...")
    try:
        result = subprocess.run(
            ["nmcli", "-t", "-f", "SSID,SIGNAL,SECURITY", "device", "wifi", "list", "--rescan", "yes"],
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
        networks.sort(key=lambda n: -n["signal"])
        NETWORKS_CACHE.write_text(json.dumps(networks))
        print(f"[boot] {len(networks)} redes encontradas.")
    except Exception as e:
        print(f"[boot] Erro ao escanear redes: {e}")
        NETWORKS_CACHE.write_text("[]")


def start_hotspot():
    print("[boot] Iniciando hotspot 'Vinil'...")
    subprocess.run([
        "sudo", "nmcli", "device", "wifi", "hotspot",
        "ifname", "wlan0",
        "ssid", "Vinil Player Setup",
        "password", "vinil1234"
    ], capture_output=True)
    time.sleep(3)


def run_flask(mode: str):
    env = os.environ.copy()
    env["VINIL_MODE"] = mode
    subprocess.run(
        [sys.executable, "-m", "portal.app"],
        cwd=str(BASE_DIR), env=env
    )


def run_player():
    subprocess.run(
        [sys.executable, str(BASE_DIR / "vinil.py")],
        cwd=str(BASE_DIR)
    )


def main():
    print("[boot] Verificando estado do sistema...")

    env_ok = check_env_configured()
    if not env_ok:
        print("[boot] .env não configurado. Iniciando wizard completo.")
        start_hotspot()
        run_flask("setup")
        return

    wifi_ok = check_wifi_connected()
    if not wifi_ok:
        print("[boot] Sem WiFi. Iniciando hotspot + wizard.")
        scan_and_cache_networks()
        start_hotspot()
        run_flask("setup")
        return

    token_ok = check_spotify_token()
    if not token_ok:
        print("[boot] WiFi ok, mas sem token Spotify. Iniciando OAuth.")
        run_flask("oauth")
        return

    # Fully configured: run settings server in background + player in foreground
    print("[boot] Tudo configurado. Iniciando player + settings server.")
    settings_thread = threading.Thread(
        target=lambda: run_flask("settings"), daemon=True
    )
    settings_thread.start()
    run_player()


if __name__ == "__main__":
    main()
