help:
	@echo "clean - remove all Python artifacts"
	@echo "lint - check style with flake8"
	@echo "install - install to /usr/bin/"

clean:
	find . -name '*.pyc' -exec rm -f {} +
	find . -name '*.pyo' -exec rm -f {} +
	find . -name '*~' -exec rm -f {} +
	find . -name '__pycache__' -exec rm -fr {} +

lint:
	flake8 pambu.py

install: clean
	install -Dm755 ./pambu.py /usr/bin/pambu

.PHONY: clean help lint install
