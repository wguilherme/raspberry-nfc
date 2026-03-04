"""
Grava um URI do Spotify em uma tag NFC via NDEF.

Uso:
    python3 nfc_write.py spotify:album:4aawyAB9vmqN3uQ7FjRGTy
    python3 nfc_write.py spotify:playlist:37i9dQZF1DXcBWIGoYBM5M
"""
import sys
import board
import busio
from adafruit_pn532.i2c import PN532_I2C


def build_ndef_uri(uri: str) -> bytes:
    """Constrói um NDEF URI Record e empacota no TLV padrão."""
    uri_bytes = uri.encode("utf-8")

    # NDEF Record header para URI Record (TNF=0x01, type="U")
    ndef_type = b"U"
    payload = bytes([0x00]) + uri_bytes  # 0x00 = sem prefixo abreviado

    header = 0xD1  # MB=1, ME=1, SR=1, TNF=0x01
    record = bytes([
        header,
        len(ndef_type),   # Type Length
        len(payload),     # Payload Length (Short Record)
        *ndef_type,
        *payload,
    ])

    # TLV: 0x03 = NDEF Message, comprimento, dados, 0xFE = terminator
    return bytes([0x03, len(record)]) + record + bytes([0xFE])


def write_ndef_to_tag(pn532, data: bytes):
    """Escreve dados NDEF nas páginas do NTAG2xx (começa na página 4)."""
    # Preenche até múltiplo de 4 bytes (tamanho da página)
    padded = data + bytes((-len(data)) % 4)
    pages = [padded[i:i+4] for i in range(0, len(padded), 4)]

    if len(pages) > 36:  # NTAG213 tem 36 páginas de usuário (4–39)
        raise ValueError("URI muito longo para esta tag.")

    for i, page in enumerate(pages):
        pn532.ntag2xx_write_block(4 + i, page)
        print(f"  Página {4 + i} gravada: {page.hex()}")


def main():
    if len(sys.argv) < 2:
        print("Uso: python3 nfc_write.py <spotify_uri>")
        print("Ex:  python3 nfc_write.py spotify:album:4aawyAB9vmqN3uQ7FjRGTy")
        sys.exit(1)

    uri = sys.argv[1]
    print(f"URI a gravar: {uri}")

    i2c = busio.I2C(board.SCL, board.SDA)
    pn532 = PN532_I2C(i2c, debug=False)
    pn532.SAM_configuration()

    ndef_data = build_ndef_uri(uri)
    print(f"NDEF ({len(ndef_data)} bytes): {ndef_data.hex()}")

    print("\nAproximе a tag NFC...")
    while True:
        uid = pn532.read_passive_target(timeout=0.5)
        if uid:
            print(f"Tag detectada: {':'.join(f'{b:02X}' for b in uid)}")
            print("Gravando...")
            write_ndef_to_tag(pn532, ndef_data)
            print("Gravado com sucesso!")
            break


if __name__ == "__main__":
    main()
