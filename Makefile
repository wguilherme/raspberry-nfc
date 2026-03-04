up:
	docker compose up

down:
	docker compose down

setup:
	sudo apt install -y python3-pip i2c-tools python3-flask
	sudo pip3 install adafruit-blinka adafruit-circuitpython-pn532 spotipy python-dotenv flask "qrcode[pil]" --break-system-packages
	sudo raspi-config nonint do_i2c 0
	@echo "Dependências instaladas."
	@[ "$(REBOOT)" = "false" ] || (echo "Reiniciando... (use REBOOT=false para evitar)" && sudo reboot)

qrcode:
	python3 generate_qr.py

install-service:
	sudo cp vinil.service /etc/systemd/system/vinil.service
	sudo cp sudoers.d/vinil /etc/sudoers.d/vinil
	sudo chmod 0440 /etc/sudoers.d/vinil
	sudo systemctl daemon-reload
	sudo systemctl enable vinil.service
	sudo systemctl start vinil.service
	@echo "Serviço instalado e iniciado. Use 'make logs' para acompanhar."

deploy:
	git pull
	sudo cp sudoers.d/vinil /etc/sudoers.d/vinil
	sudo chmod 0440 /etc/sudoers.d/vinil
	sudo systemctl restart vinil.service
	@echo "Deploy concluído. Use 'make logs' para acompanhar."

uninstall-service:
	sudo systemctl stop vinil.service || true
	sudo systemctl disable vinil.service || true
	sudo rm -f /etc/systemd/system/vinil.service /etc/sudoers.d/vinil
	sudo systemctl daemon-reload

logs:
	journalctl -u vinil.service -f

portal:
	VINIL_MODE=setup sudo -E python3 -m portal.app

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
