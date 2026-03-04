import board
import busio
from adafruit_pn532.i2c import PN532_I2C

i2c = busio.I2C(board.SCL, board.SDA)
pn532 = PN532_I2C(i2c, debug=False)

ic, ver, rev, support = pn532.firmware_version
print(f"PN532 detectado — firmware {ver}.{rev}")
print("Aproxime uma tag NFC... (Ctrl+C para sair)")

pn532.SAM_configuration()

while True:
    uid = pn532.read_passive_target(timeout=0.5)
    if uid:
        print(f"Tag detectada: {':'.join([f'{b:02X}' for b in uid])}")
