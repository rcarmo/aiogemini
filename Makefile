serve:
	python3 server.py

cert:
	 openssl req -newkey rsa:2048 -nodes -keyout gemini.key -x509 -days 365 -out gemini.crt
