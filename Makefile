up:
	docker compose up

down:
	docker compose down

nfc-test:
	scp nfc_test.py raspberry:~/vinil/ && ssh raspberry "python3 ~/vinil/nfc_test.py"

motor-test:
	scp main.py raspberry:~/vinil/ && ssh raspberry "python3 ~/vinil/main.py"

spin:
	scp spin.py raspberry:~/vinil/ && ssh raspberry "python3 ~/vinil/spin.py"
