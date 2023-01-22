#!/usr/bin/env python3

"""
MIT License

Copyright (c) 2022-2023 Marcin Sielski <marcin.sielski@gmail.com>

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
"""

import sys
import signal
import time
import subprocess
import json
import os

from PyQt5.QtWidgets import QApplication, QMessageBox

from version import __version__

if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal.SIG_DFL)
    application = QApplication(sys.argv)
    SLEEP = 60*60

    while True:
        time.sleep(SLEEP)
        try:
            result = json.loads(subprocess.check_output(
                ['curl',
                'https://api.github.com/repos/raspberrypiexperiments'
                '/RaspberryPi-AstroBerry/commits/HEAD']).decode('utf-8'))
            if 'sha' not in result:
                result = {'sha': __version__}
        finally:
            result = {'sha': __version__}

        version = result['sha'][0:7]
        if version != __version__:
            message_box = QMessageBox()
            message_box.setWindowTitle("AstroBerry Updater")
            message_box.setText("New version of AstroBerry available. Do you want to upgrade?")
            message_box.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
            result = message_box.exec()
            if result == QMessageBox.Ok:
                os.system(
                    'cd /home/$USER/workspace/RaspberryPi-AstroBerry && git pull && make reinstall')
            else:
                SLEEP = 60*60*24
    sys.exit()
