"""
Vinil NFC Player
Lê tag NFC, extrai URI do Spotify e inicia reprodução no dispositivo ativo.
"""
import os
import time
import board
import busio
from adafruit_pn532.i2c import PN532_I2C
from dotenv import load_dotenv
import spotipy
from spotipy.oauth2 import SpotifyOAuth

load_dotenv()

SCOPES = "user-modify-playback-state user-read-playback-state"


def get_spotify():
    return spotipy.Spotify(auth_manager=SpotifyOAuth(
        client_id=os.environ["SPOTIFY_CLIENT_ID"],
        client_secret=os.environ["SPOTIFY_CLIENT_SECRET"],
        redirect_uri=os.environ["SPOTIFY_REDIRECT_URI"],
        scope=SCOPES,
        cache_path=".spotify_cache",
        open_browser=False,
    ))


def parse_ndef_uri(data: bytes) -> str | None:
    """Extrai URI de um bloco NDEF lido da tag."""
    try:
        # Procura pelo TLV NDEF (0x03)
        i = 0
        while i < len(data):
            tlv_type = data[i]
            if tlv_type == 0xFE:
                break
            if tlv_type == 0x03:
                length = data[i + 1]
                record = data[i + 2: i + 2 + length]
                # Pula header NDEF (4 bytes: header, type_len, payload_len, type)
                payload = record[4:]
                # Primeiro byte é o identificador de prefixo URI (0x00 = nenhum)
                uri = payload[1:].decode("utf-8")
                return uri
            i += 2 + data[i + 1]
    except Exception:
        pass
    return None


def read_ndef_from_tag(pn532) -> str | None:
    """Lê páginas NTAG2xx e retorna o URI NDEF."""
    raw = b""
    for page in range(4, 20):
        block = pn532.ntag2xx_read_block(page)
        if block is None:
            break
        raw += bytes(block)
    return parse_ndef_uri(raw)


def play_uri(sp: spotipy.Spotify, uri: str):
    devices = sp.devices()
    if not devices["devices"]:
        print("Nenhum dispositivo Spotify ativo encontrado.")
        print("Abra o Spotify em algum dispositivo e tente novamente.")
        return

    device = devices["devices"][0]
    print(f"Tocando em: {device['name']} ({device['type']})")

    uri_type = uri.split(":")[1]  # album, playlist, track, artist
    if uri_type == "track":
        sp.start_playback(device_id=device["id"], uris=[uri])
    else:
        sp.start_playback(device_id=device["id"], context_uri=uri)

    print(f"Reproduzindo: {uri}")


def main():
    print("Vinil NFC Player iniciando...")
    sp = get_spotify()
    print("Spotify autenticado.")

    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    pn532.SAM_configuration()
    print("NFC pronto. Aproxime um vinil...\n")

    last_uid = None

    while True:
        uid = pn532.read_passive_target(timeout=0.5)

        if uid is None:
            last_uid = None
            time.sleep(0.1)
            continue

        uid_str = ":".join(f"{b:02X}" for b in uid)

        if uid_str == last_uid:
            time.sleep(0.1)
            continue

        last_uid = uid_str
        print(f"Tag detectada: {uid_str}")

        uri = read_ndef_from_tag(pn532)
        if not uri:
            print("Tag sem URI Spotify gravado. Use nfc_write.py para gravar.")
            continue

        if not uri.startswith("spotify:"):
            print(f"URI não reconhecido: {uri}")
            continue

        try:
            play_uri(sp, uri)
        except spotipy.exceptions.SpotifyException as e:
            print(f"Erro Spotify: {e}")

        time.sleep(0.5)


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\nEncerrado.")
