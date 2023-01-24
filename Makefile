# MIT License
#
# Copyright (c) 2022-2023 Marcin Sielski <marcin.sielski@gmail.com>
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all
# copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
# SOFTWARE.

dependencies:
	sudo apt install pijuice-gui -y

install: dependencies
	sudo mkdir -p /opt/astroberry/bin
	sudo mkdir -p /opt/astroberry/src
	sudo mkdir -p /opt/astroberry/share/icons
	sudo mkdir -p /opt/astroberry/share/doc
	mkdir -p /home/$$USER/astroberry/etc
	mkdir -p /home/$$USER/astroberry/media
	sudo cp bin/astroberry.sh /opt/astroberry/bin
	sudo cp src/astroberry.py /opt/astroberry/src
	sudo bash -c "echo __version__ = \'`git rev-parse --short HEAD`\' > /opt/astroberry/src/version.py"
	sudo cp share/icons/* /opt/astroberry/share/icons
	sudo cp share/doc/* /opt/astroberry/share/doc || true
	sudo cp src/astroberry.service /etc/systemd/system
	sudo chmod 755 /opt/astroberry/bin/astroberry.sh
	sudo systemctl enable astroberry.service
	sudo systemctl start astroberry.service || true
	sleep 3
	sudo systemctl status astroberry.service

install_updater:
	sudo mkdir -p /opt/astroberry_updater/bin
	sudo mkdir -p /opt/astroberry_updater/src
	sudo cp bin/astroberry_updater.sh /opt/astroberry_updater/bin
	sudo cp src/astroberry_updater.py /opt/astroberry_updater/src 
	sudo cp src/astroberry_updater.service /etc/systemd/system
	sudo chmod 755 /opt/astroberry_updater/bin/astroberry_updater.sh
	sudo systemctl enable astroberry_updater.service
	sudo systemctl start astroberry_updater.service || true
	sleep 3
	sudo systemctl status astroberry_updater.service

uninstall:
	sudo systemctl stop astroberry.service || true
	sudo systemctl disable astroberry.service
	
	sudo rm -rf /etc/systemd/system/astroberry.service
	sudo rm -rf /opt/astroberry
	sudo rm -rf /home/$$USER/astroberry

uninstall_updater:
	sudo systemctl stop astroberry_updater.service || true
	sudo systemctl disable astroberry_updater.service
	sudo rm -rf /etc/systemd/system/astroberry_updater.service
	sudo rm -rf /opt/astroberry_updater
	

reinstall: uninstall install

reinstall_updater: uninstall_updater install_updater

all: install install_updater

uninstall_all: uninstall uninstall_updater
