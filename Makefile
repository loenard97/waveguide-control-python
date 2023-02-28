VENV	= ./venv
PYTHON	= $(VENV)/bin/python
PIP		= $(VENV)/bin/pip
CWD		= $(shell pwd)


all:
	sudo apt-get install -y python3-venv
	python3 -m venv $(VENV)
	$(PYTHON) -m pip install --upgrade pip
	$(PIP) install -r requirements.txt

install: all
	echo "[Desktop Entry]" > meca.desktop
	echo "Name=MECA GUI" >> meca.desktop
	echo "Comment=Waveguide Control GUI" >> meca.desktop
	echo "Icon=$(CWD)/src/images/icon.svg" >> meca.desktop
	echo "Path=$(CWD)" >> meca.desktop
	echo "Exec=make run" >> meca.desktop
	echo "Type=Application" >> meca.desktop
	mv meca.desktop /usr/share/applications/meca.desktop

uninstall:
	rm -f /usr/share/applications/meca.desktop

clean:
	rm -rf logs

debug:
	$(PYTHON) main.py --debug

run:
	$(PYTHON) main.py


.PHONY: all install uninstall clean debug run