up:
	docker compose up

down:
	docker compose down

setup:
	sudo apt install -y python3-pip i2c-tools
	sudo pip3 install adafruit-blinka adafruit-circuitpython-pn532 spotipy python-dotenv --break-system-packages
	sudo raspi-config nonint do_i2c 0
	sudo reboot

nfc-test:
	@python3 -c "import board" 2>/dev/null || make setup
	python3 nfc_test.py

nfc-write:
	@[ "$(URI)" ] || (echo "Uso: make nfc-write URI=spotify:album:xxx" && exit 1)
	python3 nfc_write.py $(URI)

motor-test:
	python3 main.py

spin:
	python3 spin.py

play:
	python3 vinil.py
