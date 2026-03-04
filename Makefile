up:
	docker compose up

down:
	docker compose down

install:
	sudo apt install -y python3-pip i2c-tools
	sudo pip3 install adafruit-blinka adafruit-circuitpython-pn532 --break-system-packages

nfc-test:
	@python3 -c "import board" 2>/dev/null || make install
	python3 nfc_test.py

motor-test:
	python3 main.py

spin:
	python3 spin.py
