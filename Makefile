up:
	docker compose up

down:
	docker compose down

nfc-test:
	ssh raspberry "python3 ~/vinil/nfc_test.py"

motor-test:
	ssh raspberry "python3 ~/vinil/main.py"

spin:
	ssh raspberry "python3 ~/vinil/spin.py"
