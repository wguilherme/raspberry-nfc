"""
Gera o QR code de setup do Vinil.
  - qrcode.png  → imprimir e colar no dispositivo
  - ASCII no terminal → visualização rápida
"""
import sys

try:
    import qrcode
    from qrcode.image.styledpil import StyledPilImage
    from qrcode.image.styles.moduledrawers import RoundedModuleDrawer
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

URL = "http://192.168.4.1:8080"
OUTPUT = "qrcode.png"


def generate_png():
    qr = qrcode.QRCode(
        version=2,
        error_correction=qrcode.constants.ERROR_CORRECT_H,
        box_size=12,
        border=4,
    )
    qr.add_data(URL)
    qr.make(fit=True)

    try:
        img = qr.make_image(
            image_factory=StyledPilImage,
            module_drawer=RoundedModuleDrawer(),
            back_color="white",
            fill_color="black",
        )
    except Exception:
        img = qr.make_image(fill_color="black", back_color="white")

    img.save(OUTPUT)
    print(f"QR code salvo em: {OUTPUT}")
    print(f"URL: {URL}")
    print("Imprima e cole no dispositivo.")


def generate_ascii():
    qr = qrcode.QRCode(border=2)
    qr.add_data(URL)
    qr.make(fit=True)
    print(f"\nQR Code — {URL}\n")
    qr.print_ascii(invert=True)
    print()


if __name__ == "__main__":
    if not PIL_AVAILABLE:
        print("Instale as dependências: pip3 install qrcode[pil]")
        sys.exit(1)

    generate_ascii()

    if "--ascii" not in sys.argv:
        generate_png()
