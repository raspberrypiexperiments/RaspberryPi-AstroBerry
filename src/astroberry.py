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
import shutil
import tempfile
import math
import time
import glob
import re
import os
from os import path
from argparse import ArgumentParser
import logging
import inspect
import threading
import signal
import json
import subprocess
import psutil

from gpiozero import DiskUsage, CPUTemperature

import PIL.Image
import PIL.ExifTags

from PyQt5.QtCore import Qt, QEvent, QSize, QObject, pyqtSignal, QThread
from PyQt5.QtGui import QIcon, QMouseEvent, QWheelEvent, QPixmap
from PyQt5.QtWidgets import QGestureRecognizer, QApplication, QLabel, QPushButton, QMainWindow, \
    QWidget, QSwipeGesture, QHBoxLayout, QVBoxLayout, QGestureEvent

import picamera

from pijuice import PiJuice

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo, GLib
from version import __version__



class MouseGestureRecognizer(QGestureRecognizer):
    """
    Mouse Gesture Recognizer
    """

    def __init__(self, parent):
        """
        Initialize Mouse Gesture Recognizer
        """

        super().__init__()

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__parent = parent

        self.__pressed = False
        self.__timestamp = 0
        self.__startpoint = 0
        self.__endpoint = 0
        self.__deg_0 = 0
        self.__deg_90 = 0
        self.__deg_180 = 0
        self.__deg_270 = 0
        self.__samples = 0
        self.__trigger = False

        log = function_name + ': exit'
        logging.info(log)


    def create(self, _):
        """Create QGesture-derived object

        Args:
            _ (QObject): targer object

        Returns:
            QSwipeGesture: swipe gesture
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        swipe_gesture = QSwipeGesture()

        log = function_name + ': exit'
        logging.info(log)

        return swipe_gesture


    def recognize(self, gesture, _, event):
        """Transforms mouse gestures into swipe gestures

        Args:
            gesture (QSwipeGesture): swipe gesture
            _ (QObject): whached object
            event (QMouseEvent): mouse event

        Returns:
            QGestureRecognizer.Result: reflects how much gesture has been
                recognized
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': event.type=' + str(event.type())
        logging.info(log)

        if not self.__pressed and event.type() == QMouseEvent.MouseButtonPress:
            self.__pressed = True
            self.__startpoint = event.pos()
            result = QGestureRecognizer.Ignore
        elif self.__pressed and event.type() == QMouseEvent.MouseButtonPress:
            result = QGestureRecognizer.Ignore
        elif self.__pressed and event.type() == QMouseEvent.MouseButtonRelease:
            self.__pressed = False
            self.__endpoint = event.pos()
            if self.__startpoint == self.__endpoint:
                result = QGestureRecognizer.Ignore
            else:
                delta = self.__endpoint-self.__startpoint
                deg = math.degrees(math.atan2(delta.y(), delta.x()))
                if deg < 0:
                    deg = 360+deg
                if deg < 20 or deg > 340:
                    deg = 0
                if 25 < deg < 65:
                    deg = 45
                if 70 < deg < 110:
                    deg = 90
                if 115 < deg < 155:
                    deg = 135
                if 160 < deg < 200:
                    deg = 180
                if 205 < deg < 245:
                    deg = 225
                if 250 < deg < 290:
                    deg = 270
                if 295 < deg < 335:
                    deg = 315
                gesture.setSwipeAngle(deg)
                result = QGestureRecognizer.TriggerGesture
        elif not self.__pressed and event.type() == QMouseEvent.MouseButtonRelease:
            result = QGestureRecognizer.Ignore
        elif event.type() == QMouseEvent.MouseButtonDblClick:
            self.__pressed = False
            result = QGestureRecognizer.Ignore
        elif event.type() == QWheelEvent.Wheel:

            timestamp = time.time()

            if (
                (timestamp - self.__timestamp > 2 and self.__parent.parameters['photo_camera']) or
                (timestamp - self.__timestamp > 1 and not self.__parent.parameters['photo_camera'])
                ):
                self.__timestamp = timestamp
                self.__samples = 0
            if self.__samples < 30:
                self.__samples = self.__samples + 1
                self.__trigger = True

                point = event.angleDelta()
                if point.x() > 0:
                    self.__deg_0 = self.__deg_0 + 1
                if point.x() < 0:
                    self.__deg_180 = self.__deg_180 + 1
                if point.y() > 0:
                    self.__deg_90 = self.__deg_90 + 1
                if point.y() < 0:
                    self.__deg_270 = self.__deg_270 + 1

                result = QGestureRecognizer.Ignore
            elif self.__trigger:
                self.__trigger = False

                if self.__deg_270 > 0:
                    x = 360
                else:
                    x = 0
                if self.__deg_0 + self.__deg_90 + self.__deg_180 + self.__deg_270 == 0:
                    deg = 0
                else:
                    deg = int(
                        (x*self.__deg_0 + 90*self.__deg_90 + 180*self.__deg_180 +
                        270*self.__deg_270)/
                        (self.__deg_0 + self.__deg_90 + self.__deg_180 + self.__deg_270))
                self.__deg_0 = 0
                self.__deg_180 = 0
                self.__deg_90 = 0
                self.__deg_270 = 0

                if deg < 20 or deg > 340:
                    deg = 0
                if 25 < deg < 65:
                    deg = 45
                if 70 < deg < 110:
                    deg = 90
                if 115 < deg < 155:
                    deg = 135
                if 160 < deg < 200:
                    deg = 180
                if 205 < deg < 245:
                    deg = 225
                if 250 < deg < 290:
                    deg = 270
                if 295 < deg < 335:
                    deg = 315

                gesture.setSwipeAngle(deg)
                result = QGestureRecognizer.TriggerGesture
            else:
                result = QGestureRecognizer.Ignore
        else:
            result = QGestureRecognizer.Ignore

        log = function_name + ': result=' + str(result)
        logging.info(log)

        return result



class Display(QLabel):
    """Display Panel
    """


    def __init__(self, parent = None):
        """Iniztialize Display Panel

        Args:
            parent (QWidget, optional): parent object. Defaults to None.
        """

        super().__init__(parent)

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.grabGesture(QGestureRecognizer.registerRecognizer(MouseGestureRecognizer(parent)))
        self.__parent = parent
        self.__index = 0
        self.__zoom = False
        self.__x = 0
        self.__y = 0

        log = function_name + ': exit'
        logging.info(log)


    def set_index(self, index):
        """Sets index of an image file

        Args:
            index (int): index of an image file
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': index=' + str(index)
        logging.info(log)

        self.__index = index

        log = function_name + ': exit'
        logging.info(log)


    def get_index(self):
        """Gets index of an image file

        Returns:
            int: index of an image file
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        result = self.__index

        log = function_name + ': result=' + str(result)
        logging.info(log)

        return result


    def set_zoom(self, zoom):
        """Indicate if image preview should be zoomed

        Args:
            zoom (bool): indicates if image preview should be zoomed
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': zoom=' + str(zoom)
        logging.info(log)

        self.__zoom = zoom

        log = function_name + ': exit'
        logging.info(log)


    def event(self, event):
        """Handles input events

        Args:
            event (QEvent): event

        Returns:
            bool: indicates if event was recognized
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': event.type=' + str(event.type())
        logging.info(log)

        if event.type() == QEvent.Gesture:
            if self.__parent.parameters['photo_camera']:
                result = self.event_gesture_photo_camera(QGestureEvent(event))
            else:
                result = self.event_gesture_photo_gallery(QGestureEvent(event))
        elif event.type() == QEvent.MouseButtonDblClick:
            if self.__parent.parameters['photo_camera']:
                result = self.event_mouse_photo_camera(QMouseEvent(event))
            else:
                result = self.event_mouse_photo_gallery(QMouseEvent(event))
        else:
            result = QWidget.event(self, event)
        log = function_name + ': result=' + str(result)
        logging.info(log)
        return result


    def event_gesture_photo_camera(self, event):
        """Handles gesture events in Photo Camera display mode

        Args:
            event (QGestureEvent): gesture event

        Returns:
            bool: indicates if event was recognized
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        swipe_gesture = event.gesture(Qt.SwipeGesture)

        if swipe_gesture.horizontalDirection() == QSwipeGesture.Left:
            self.__parent.resolution_up()
            result = True
        elif swipe_gesture.horizontalDirection() == QSwipeGesture.Right:
            self.__parent.resolution_down()
            result = True
        else:
            result = False

        log = function_name + ': result=' + str(result)
        logging.info(log)

        return result


    def event_mouse_photo_camera(self, event):
        """Handles mouse events in Photo Camera display mode

        Args:
            event (QMouseEvent): mouse event

        Returns:
            bool: indicates if event was recognized
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': event.type=' + str(event.type())
        logging.info(log)

        if event.type() == QMouseEvent.MouseButtonDblClick:
            annotation_mode = self.__parent.source.get_property('annotation-mode')
            if annotation_mode == 0x00000000:
                self.__parent.source.set_property('annotation-mode', 0x0000065D)
            else:
                self.__parent.source.set_property('annotation-mode', 0x00000000)
            result = True
        else:
            result = False

        log = function_name + ': result='+str(result)
        logging.info(log)

        return result


    def event_gesture_photo_gallery(self, event):
        """Handles gesture events in Photo Gallery display mode

        Args:
            event (QGestureEvent): gesture event

        Returns:
            bool: indicates if event was recognized
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': event.type=' + str(event.type())
        logging.info(log)

        swipe_gesture = event.gesture(Qt.SwipeGesture)

        if self.__zoom:
            pixmap = QPixmap(
                self.__parent.parameters['media'] + 'DSCF'+str(self.__index).zfill(4)+'.JPG')
            if pixmap.width() < 640:
                pixmap = pixmap.scaled(640,480)
            else:
                if swipe_gesture.horizontalDirection() == QSwipeGesture.Left:
                    self.__x = self.__x + 320*640/pixmap.width()
                if swipe_gesture.horizontalDirection() == QSwipeGesture.Right:
                    self.__x = self.__x - 320*640/pixmap.width()
                if swipe_gesture.verticalDirection() == QSwipeGesture.Up:
                    self.__y = self.__y - 240*480/pixmap.height()
                if swipe_gesture.verticalDirection() == QSwipeGesture.Down:
                    self.__y = self.__y + 240*480/pixmap.height()
                if self.__x >= 639:
                    self.__x = 640 - 320*640/pixmap.width()
                if self.__x <= 0:
                    self.__x = 320*640/pixmap.width()
                if self.__y >= 479:
                    self.__y = 480 - 240*480/pixmap.height()
                if self.__y <= 0:
                    self.__y = 240*480/pixmap.height()
                x = int(self.__x*pixmap.width()/640) - 320
                y = int(self.__y*pixmap.height()/480) - 240
                if x < 0:
                    x = 0
                if y < 0:
                    y = 0
                if pixmap.width() - x < 640:
                    x = pixmap.width() - 640
                if pixmap.height() - y < 480:
                    y = pixmap.height() - 480
            self.setPixmap(pixmap.copy(x, y, 640, 480))
        else:
            images = glob.glob(self.__parent.parameters['media'] + 'DSCF????.JPG')
            images.sort()
            index = images.index(
                self.__parent.parameters['media'] + 'DSCF'+str(self.__index).zfill(4)+'.JPG')
            if swipe_gesture.horizontalDirection() == QSwipeGesture.Left:
                if index + 1 == len(images):
                    index = 0
                else:
                    index = index + 1
            elif swipe_gesture.horizontalDirection() == QSwipeGesture.Right:
                if index == 0:
                    index = len(images) - 1
                else:
                    index = index - 1
            self.__index = int(re.search(r'\d+',images[index]).group())
            self.__parent.panel_control_file_info_label_set_text(self.__index)
            pixmap = QPixmap(
                self.__parent.parameters['media'] + 'DSCF'+str(self.__index).zfill(4)+'.JPG')
            self.setPixmap(pixmap.scaled(640,480))

        log = function_name + ': result=True'
        logging.info(log)

        return True


    def event_mouse_photo_gallery(self, event):
        """Handles gesture events in Photo Gallery display mode

        Args:
            event (QMouseEvent): mouse event

        Returns:
            bool: indicates if event was recognized
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': event.type=' + str(event.type())
        logging.info(log)

        if event.type() == QMouseEvent.MouseButtonDblClick:
            pixmap = QPixmap(
                self.__parent.parameters['media'] + 'DSCF'+str(self.__index).zfill(4)+'.JPG')
            if not self.__zoom:
                self.__zoom = True
                if pixmap.width() < 640:
                    pixmap = pixmap.scaled(640,480)
                else:
                    self.__x = event.pos().x()
                    self.__y = event.pos().y()
                    x = int(self.__x*pixmap.width()/640) - 320
                    y = int(self.__y*pixmap.height()/480) - 240
                    if x < 0:
                        x = 0
                    if y < 0:
                        y = 0
                    if pixmap.width() - x < 640:
                        x = pixmap.width() - 640
                    if pixmap.height() - y < 480:
                        y = pixmap.height() - 480
                self.setPixmap(pixmap.copy(x, y, 640, 480))
                self.__parent.panel_display.setToolTip('Swipe left, right, ' + \
                    'up and down to review an image or double tap to zoom out')
            else:
                self.__zoom = False
                self.setPixmap(pixmap.scaled(640,480))
                self.__parent.panel_display.setToolTip('Swipe left or right ' + \
                    'to select an image or double tap to zoom in')
            result = True
        else:
            result = False

        log = function_name + ': result='+str(result)
        logging.info(log)

        return result



class HardwareButtonMonitor(QObject):
    """Hardware Button Monitor
    """

    clicked = pyqtSignal()


    def __init__(self, pijuice):
        """Initializes Hardware Button Monitor

        Args:
            pijuice (PiJuice): PiJuice device
        """

        super().__init__()

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__pijuice = pijuice

        log = function_name + ': exit'
        logging.info(log)


    def run(self):
        """Monitors hardware button clicks
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': loop'
        logging.info(log)

        while True:
            time.sleep(1)
            button_events = self.__pijuice.status.GetButtonEvents()
            if 'data' in button_events:
                if button_events['data']['SW2'] == 'SINGLE_PRESS':
                    self.__pijuice.status.AcceptButtonEvent('SW2')
                    self.clicked.emit()
            else:
                log = function_name + ': button_events=' + str(button_events)
                logging.warning(log)




class CameraScreen(QMainWindow):
    """Camera Screen
    """


    def __init__(self, parent, params):
        """Initialize Camera Screen

        Args:
            parent (QApplication): application
            params (dict): parameters
        """

        super().__init__(None)

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__parent = parent
        self.parameters = params

        signal.signal(signal.SIGTERM, self.__on_terminate)
        signal.signal(signal.SIGINT, self.__on_terminate)
        signal.signal(signal.SIGABRT, self.__on_terminate)

        self.setGeometry(0,36,800,564)
        self.setWindowTitle('AstroBerry')
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon(self.parameters['icons'] + self.parameters['logo_icon']))

        self.window = QWidget()

        self.panel = QWidget()

        self.panel_display = Display(self)
        self.panel_display.setFixedSize(640,480)
        self.panel_display.setToolTip(
            'Swipe left or right to change resolution or double tap to toggle debug mode')
        self.__win_id = self.panel_display.winId()

        self.panel_control = QWidget()

        self.control = QWidget()
        self.control_menu = QWidget()
        self.control_sharpness = QWidget()
        self.control_sharpness_button = QWidget()
        self.control_exposure = QWidget()
        self.control_exposure_shutter_speed = QWidget()
        self.control_exposure_iso = QWidget()

        window_h_layout = QHBoxLayout()
        window_h_layout.setContentsMargins(0,4,0,0)
        window_h_layout.setSpacing(0)

        panel_v_layout = QVBoxLayout()
        panel_v_layout.setContentsMargins(0,0,0,0)
        panel_v_layout.setSpacing(0)

        panel_control_h_layout = QHBoxLayout()
        panel_control_h_layout.setContentsMargins(0,0,0,0)
        panel_control_h_layout.setSpacing(0)

        control_v_layout = QVBoxLayout()
        control_v_layout.setContentsMargins(0,0,0,0)
        control_v_layout.setSpacing(0)

        control_menu_h_layout = QHBoxLayout()
        control_menu_h_layout.setContentsMargins(0,0,0,0)
        control_menu_h_layout.setSpacing(0)

        control_sharpness_v_layout = QVBoxLayout()
        control_sharpness_v_layout.setContentsMargins(0,0,0,0)
        control_sharpness_v_layout.setSpacing(0)

        control_sharpness_button_h_layout = QHBoxLayout()
        control_sharpness_button_h_layout.setContentsMargins(0,0,0,0)
        control_sharpness_button_h_layout.setSpacing(0)

        control_exposure_h_layout = QHBoxLayout()
        control_exposure_h_layout.setContentsMargins(0,0,0,0)
        control_exposure_h_layout.setSpacing(0)

        control_exposure_shutter_speed_v_layout = QVBoxLayout()
        control_exposure_shutter_speed_v_layout.setContentsMargins(0,0,0,0)
        control_exposure_shutter_speed_v_layout.setSpacing(0)

        control_exposure_iso_v_layout = QVBoxLayout()
        control_exposure_iso_v_layout.setContentsMargins(0,0,0,0)
        control_exposure_iso_v_layout.setSpacing(0)

        self.panel_control_contrast_button_down = QPushButton()
        self.panel_control_contrast_button_down.setFixedSize(80,80)
        self.panel_control_contrast_button_down.setToolTip('Decrease contrast')
        self.panel_control_contrast_button_down.setIcon(QIcon(
            self.parameters['icons'] + 'do_not_disturb_on_FILL0_wght400_GRAD0_opsz48.svg'))
        self.panel_control_contrast_button_down.setIconSize(QSize(80,80))
        self.panel_control_contrast_button_down.clicked.connect(
            self.__on_panel_control_contrast_button_down_clicked)
        if self.parameters['contrast'] == -100:
            self.panel_control_contrast_button_down.setEnabled(False)

        self.panel_control_contrast_label = QLabel(str(self.parameters['contrast']))
        self.panel_control_contrast_label.setFixedSize(40,80)
        self.panel_control_contrast_label.setToolTip('Current contrast')
        font = self.panel_control_contrast_label.font()
        font.setPointSize(12)
        self.panel_control_contrast_label.setFont(font)
        self.panel_control_contrast_label.setAlignment(Qt.AlignCenter)

        self.panel_control_contrast_button_up = QPushButton()
        self.panel_control_contrast_button_up.setFixedSize(80,80)
        self.panel_control_contrast_button_up.setToolTip('Increase contrast')
        self.panel_control_contrast_button_up.setIcon(QIcon(
            self.parameters['icons'] + 'add_circle_FILL1_wght400_GRAD0_opsz48.svg'))
        self.panel_control_contrast_button_up.setIconSize(QSize(80,80))
        self.panel_control_contrast_button_up.clicked.connect(
            self.__on_panel_control_contrast_button_up_clicked)
        if self.parameters['contrast'] == 100:
            self.panel_control_contrast_button_up.setEnabled(False)

        self.panel_control_white_balance_button = QPushButton()
        self.panel_control_white_balance_button.setFixedSize(80,80)
        self.panel_control_white_balance_button.setToolTip('Auto white balance mode')
        self.panel_control_white_balance_button.setIcon(QIcon(
            self.parameters['icons'] + 'wb_auto_FILL0_wght400_GRAD0_opsz48.svg'))
        self.panel_control_white_balance_button.setIconSize(QSize(80,80))
        self.panel_control_white_balance_button.clicked.connect(
            self.__on_panel_control_white_balance_button_clicked)

        self.panel_control_saturation_button_down = QPushButton()
        self.panel_control_saturation_button_down.setFixedSize(80,80)
        self.panel_control_saturation_button_down.setToolTip('Decrease saturation')
        self.panel_control_saturation_button_down.setIcon(QIcon(
            self.parameters['icons'] + 'do_not_disturb_on_FILL1_wght400_GRAD0_opsz48.svg'))
        self.panel_control_saturation_button_down.setIconSize(QSize(80,80))
        self.panel_control_saturation_button_down.clicked.connect(
            self.__on_panel_control_saturation_button_down_clicked)
        if self.parameters['saturation'] == -100:
            self.panel_control_saturation_button_down.setEnabled(False)

        self.panel_control_saturation_label = QLabel(str(self.parameters['saturation']))
        self.panel_control_saturation_label.setFixedSize(40,80)
        self.panel_control_saturation_label.setToolTip('Current saturation')
        font = self.panel_control_saturation_label.font()
        font.setPointSize(12)
        self.panel_control_saturation_label.setFont(font)
        self.panel_control_saturation_label.setAlignment(Qt.AlignCenter)

        self.panel_control_saturation_button_up = QPushButton()
        self.panel_control_saturation_button_up.setFixedSize(80,80)
        self.panel_control_saturation_button_up.setToolTip('Increase saturation')
        self.panel_control_saturation_button_up.setIcon(QIcon(
            self.parameters['icons'] + 'add_circle_FILL0_wght400_GRAD0_opsz48.svg'))
        self.panel_control_saturation_button_up.setIconSize(QSize(80,80))
        self.panel_control_saturation_button_up.clicked.connect(
            self.__on_panel_control_saturation_button_up_clicked)
        if self.parameters['saturation'] == 100:
            self.panel_control_saturation_button_up.setEnabled(False)

        self.panel_control_info_label = QLabel()
        self.panel_control_info_label.setFixedSize(160,80)
        self.panel_control_info_label.setToolTip('Image information')
        font = self.panel_control_info_label.font()
        font.setPointSize(12)
        self.panel_control_info_label.setFont(font)
        self.panel_control_info_label.setAlignment(Qt.AlignCenter)

        panel_control_h_layout.addWidget(self.panel_control_contrast_button_down)
        panel_control_h_layout.addWidget(self.panel_control_contrast_label)
        panel_control_h_layout.addWidget(self.panel_control_contrast_button_up)
        panel_control_h_layout.addWidget(self.panel_control_white_balance_button)
        panel_control_h_layout.addWidget(self.panel_control_saturation_button_down)
        panel_control_h_layout.addWidget(self.panel_control_saturation_label)
        panel_control_h_layout.addWidget(self.panel_control_saturation_button_up)
        panel_control_h_layout.addWidget(self.panel_control_info_label)

        self.panel_control.setLayout(panel_control_h_layout)

        panel_v_layout.addWidget(self.panel_display)
        panel_v_layout.addWidget(self.panel_control)

        self.panel.setLayout(panel_v_layout)

        if self.parameters['exit_action'] == 'NONE':
            exit_handler = self.__on_control_menu_debug_mode_button_clicked
            tooltip = 'Toggle debug mode'
        elif self.parameters['exit_action'] == 'QUIT':
            exit_handler = self.__on_control_menu_quit_button_clicked
            tooltip = 'Quit AstroBerry'
        elif self.parameters['exit_action'] == 'SHUTDOWN':
            exit_handler = self.__on_control_menu_shutdown_button_clicked
            tooltip = 'Shutdown AstroBerry'

        self.control_menu_exit_button = QPushButton()
        self.control_menu_exit_button.setFixedSize(80,80)
        self.control_menu_exit_button.setToolTip(tooltip)
        self.control_menu_exit_button.setIcon(
            QIcon(self.parameters['icons'] + self.parameters['exit_icon']))
        self.control_menu_exit_button.setIconSize(QSize(80,80))
        self.control_menu_exit_button.clicked.connect(exit_handler)

        self.control_menu_photo_gallery_button = QPushButton()
        self.control_menu_photo_gallery_button.setFixedSize(80,80)
        self.control_menu_photo_gallery_button.setToolTip('Photo gallery')
        self.control_menu_photo_gallery_button.setIcon(QIcon(
            self.parameters['icons'] + 'photo_library_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_menu_photo_gallery_button.setIconSize(QSize(80,80))
        self.control_menu_photo_gallery_button.clicked.connect(
            self.__on_control_menu_photo_gallery_button_clicked)

        control_menu_h_layout.addWidget(self.control_menu_photo_gallery_button)
        control_menu_h_layout.addWidget(self.control_menu_exit_button)

        self.control_menu.setLayout(control_menu_h_layout)

        self.control_sharpness_label = QLabel(str(self.parameters['sharpness']))
        self.control_sharpness_label.setFixedSize(160,40)
        self.control_sharpness_label.setToolTip('Current sharpness')
        font = self.control_sharpness_label.font()
        font.setPointSize(12)
        self.control_sharpness_label.setFont(font)
        self.control_sharpness_label.setAlignment(Qt.AlignCenter)

        self.control_sharpness_button_down = QPushButton()
        self.control_sharpness_button_down.setFixedSize(80,80)
        self.control_sharpness_button_down.setToolTip('Decrease sharpness')
        self.control_sharpness_button_down.setIcon(QIcon(
            self.parameters['icons'] + 'do_not_disturb_on_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_sharpness_button_down.setIconSize(QSize(80,80))
        self.control_sharpness_button_down.clicked.connect(
            self.__on_control_sharpness_button_down_clicked)
        if self.parameters['sharpness'] == -100:
            self.control_sharpness_button_down.setEnabled(False)

        self.control_sharpness_button_up = QPushButton()
        self.control_sharpness_button_up.setFixedSize(80,80)
        self.control_sharpness_button_up.setToolTip('Increase sharpness')
        self.control_sharpness_button_up.setIcon(QIcon(
            self.parameters['icons'] + 'add_circle_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_sharpness_button_up.setIconSize(QSize(80,80))
        self.control_sharpness_button_up.clicked.connect(
            self.__on_control_sharpness_button_up_clicked)
        if self.parameters['sharpness'] == 100:
            self.control_sharpness_button_up.setEnabled(False)

        control_sharpness_button_h_layout.addWidget(self.control_sharpness_button_down)
        control_sharpness_button_h_layout.addWidget(self.control_sharpness_button_up)

        self.control_sharpness_button.setLayout(control_sharpness_button_h_layout)

        control_sharpness_v_layout.addWidget(self.control_sharpness_label)

        control_sharpness_v_layout.addWidget(self.control_sharpness_button)

        self.control_sharpness.setLayout(control_sharpness_v_layout)

        self.control_exposure_shutter_speed_button_down = QPushButton()
        self.control_exposure_shutter_speed_button_down.setFixedSize(80,80)
        self.control_exposure_shutter_speed_button_down.setToolTip(
            'Decrease shutter speed')
        self.control_exposure_shutter_speed_button_down.setIcon(QIcon(
            self.parameters['icons'] + 'indeterminate_check_box_FILL1_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_shutter_speed_button_down.setIconSize(QSize(80,80))
        self.control_exposure_shutter_speed_button_down.clicked.connect(
            self.__on_control_exposure_shutter_speed_button_down_clicked)

        if parameters['shutter_speed'] == 0:
            shutter_speed = 'Auto'
            self.control_exposure_shutter_speed_button_down.setEnabled(False)
        else:
            exposure_time = parameters['shutter_speed'] / 1000000
            if int(exposure_time) == 0:
                shutter_speed = '1/'+str(int(1/exposure_time))
            else:
                shutter_speed = str(int(exposure_time)) + '/1'

        self.control_exposure_shutter_speed_label = QLabel(shutter_speed + '"')
        self.control_exposure_shutter_speed_label.setFixedSize(80,40)
        self.control_exposure_shutter_speed_label.setToolTip('Current shutter speed')
        font = self.control_exposure_shutter_speed_label.font()
        font.setPointSize(12)
        self.control_exposure_shutter_speed_label.setFont(font)
        self.control_exposure_shutter_speed_label.setAlignment(Qt.AlignCenter)

        self.control_exposure_shutter_speed_button_up = QPushButton()
        self.control_exposure_shutter_speed_button_up.setFixedSize(80, 80)
        self.control_exposure_shutter_speed_button_up.setToolTip(
            'Increase shutter speed')
        self.control_exposure_shutter_speed_button_up.setIcon(QIcon(
            self.parameters['icons'] + 'add_box_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_shutter_speed_button_up.setIconSize(QSize(80,80))
        self.control_exposure_shutter_speed_button_up.clicked.connect(
            self.__on_control_exposure_shutter_speed_button_up_clicked)
        if parameters['shutter_speed'] == 22000000:
            self.control_exposure_shutter_speed_button_up.setEnabled(False)

        control_exposure_shutter_speed_v_layout.addWidget(
            self.control_exposure_shutter_speed_button_up)
        control_exposure_shutter_speed_v_layout.addWidget(
            self.control_exposure_shutter_speed_label)
        control_exposure_shutter_speed_v_layout.addWidget(
            self.control_exposure_shutter_speed_button_down)

        self.control_exposure_shutter_speed.setLayout(
            control_exposure_shutter_speed_v_layout)

        self.control_exposure_iso_button_down = QPushButton()
        self.control_exposure_iso_button_down.setFixedSize(80,80)
        self.control_exposure_iso_button_down.setToolTip('Decrease ISO')
        self.control_exposure_iso_button_down.setIcon(QIcon(
            self.parameters['icons'] + 'indeterminate_check_box_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_iso_button_down.setIconSize(QSize(90,90))
        self.control_exposure_iso_button_down.clicked.connect(
            self.__on_control_exposure_iso_button_down_clicked)

        if parameters['iso'] == 0:
            iso = 'Auto'
            self.control_exposure_iso_button_down.setEnabled(False)
        else:
            iso = str(int(parameters['iso']*100/256))

        self.control_exposure_iso_label = QLabel('ISO ' + iso)
        self.control_exposure_iso_label.setFixedSize(80,40)
        self.control_exposure_iso_label.setToolTip('Current ISO')
        font = self.control_exposure_iso_label.font()
        font.setPointSize(12)
        self.control_exposure_iso_label.setFont(font)
        self.control_exposure_iso_label.setAlignment(Qt.AlignCenter)

        self.control_exposure_iso_button_up = QPushButton()
        self.control_exposure_iso_button_up.setFixedSize(80,80)
        self.control_exposure_iso_button_up.setToolTip('Increase ISO')
        self.control_exposure_iso_button_up.setIcon(QIcon(
            self.parameters['icons'] + 'add_box_FILL1_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_iso_button_up.setIconSize(QSize(80,80))
        self.control_exposure_iso_button_up.clicked.connect(
            self.__on_control_exposure_iso_button_up_clicked)
        if parameters['iso'] == 4096:
            self.control_exposure_iso_button_up.setEnabled(False)

        control_exposure_iso_v_layout.addWidget(self.control_exposure_iso_button_up)
        control_exposure_iso_v_layout.addWidget(self.control_exposure_iso_label)
        control_exposure_iso_v_layout.addWidget(self.control_exposure_iso_button_down)

        self.control_exposure_iso.setLayout(control_exposure_iso_v_layout)

        control_exposure_h_layout.addWidget(self.control_exposure_shutter_speed)
        control_exposure_h_layout.addWidget(self.control_exposure_iso)

        self.control_exposure.setLayout(control_exposure_h_layout)

        control_v_layout.addWidget(self.control_menu)
        control_v_layout.addWidget(self.control_sharpness)
        control_v_layout.addWidget(self.control_exposure)

        self.control_shutter_button = QPushButton()
        self.control_shutter_button.setFixedSize(160,160)
        self.control_shutter_button.setToolTip('Take a picture')
        self.control_shutter_button.setIcon(
            QIcon(self.parameters['icons'] + 'circle_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_shutter_button.setIconSize(QSize(160,160))
        self.control_shutter_button.clicked.connect(self.__on_control_shutter_button_clicked)

        self.__shutter_clicked = False

        control_v_layout.addWidget(self.control_shutter_button)

        self.control.setLayout(control_v_layout)

        window_h_layout.addWidget(self.panel)
        window_h_layout.addWidget(self.control)

        self.window.setLayout(window_h_layout)
        self.setCentralWidget(self.window)

        images = glob.glob(self.parameters['media'] + 'DSCF????.JPG')
        images.sort()
        if len(images) == 0:
            self.__index = -1
            self.control_menu_photo_gallery_button.setEnabled(False)
        else:
            self.__index = int(re.search(r'\d+',images[len(images)-1]).group())
            self.panel_display.set_index(self.__index)

        cat = subprocess.Popen(['cat', '/boot/config.txt'], stdout=subprocess.PIPE)
        self.__gpu_mem = int(subprocess.check_output(
            ['grep', '-a', 'gpu_mem'],
            stdin=cat.stdout).decode('utf-8').replace('gpu_mem=','').strip())

        self.__sv_mem = round(psutil.virtual_memory().total/1024/1024)

        self.__pijuice = PiJuice()
        if self.__pijuice.config.GetFirmwareVersion() == {}:
            self.__pijuice = None
        else:
            self.__thread = QThread()
            monitor = HardwareButtonMonitor(self.__pijuice)
            monitor.moveToThread(self.__thread)
            self.__thread.started.connect(monitor.run)
            monitor.clicked.connect(self.__on_control_shutter_button_clicked)
            self.__thread.start()

        self.__capturing_contrast = None
        self.__capturing_white_balance = None
        self.__capturing_saturation = None
        self.__capturing_sharpness = None
        self.__capturing_shutter_speed = None
        self.__pipeline = None
        self.source = None
        self.__source_caps = None
        self.__exif = None
        self.__filesink = None

        log = function_name + ': exit'
        logging.info(log)


    def setup(self):
        """Setups streaming pipeline
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        if self.parameters['contrast'] == 0:
            self.__capturing_contrast = 'normal'
        elif self.parameters['contrast'] < 0:
            self.__capturing_contrast = 'soft'
        elif self.parameters['contrast'] > 0:
            self.__capturing_contrast = 'hard'
        if self.parameters['white_balance'] == 1:
            self.__capturing_white_balance = 'daylight'
        elif self.parameters['white_balance'] == 2:
            self.__capturing_white_balance = 'cloudy'
        elif self.parameters['white_balance'] == 3:
            self.__capturing_white_balance = 'manual'
        elif self.parameters['white_balance'] == 4:
            self.__capturing_white_balance = 'tungsten'
        elif self.parameters['white_balance'] == 5:
            self.__capturing_white_balance = 'fluorescent'
        elif self.parameters['white_balance'] == 6:
            self.__capturing_white_balance = '"fluorescent h"'
        elif self.parameters['white_balance'] == 7:
            self.__capturing_white_balance = 'flash'
        elif self.parameters['white_balance'] == 8:
            self.__capturing_white_balance = 'manual'
        elif self.parameters['white_balance'] == 9:
            self.__capturing_white_balance = 'auto'
        if self.parameters['saturation'] == 0:
            self.__capturing_saturation = 'normal'
        elif self.parameters['saturation'] < 0:
            self.__capturing_saturation = 'low-saturation'
        elif self.parameters['saturation'] > 0:
            self.__capturing_saturation = 'high-saturation'
        if self.parameters['sharpness'] == 0:
            self.__capturing_sharpness = 'normal'
        elif self.parameters['sharpness'] < 0:
            self.__capturing_sharpness = 'soft'
        elif self.parameters['sharpness'] > 0:
            self.__capturing_sharpness = 'hard'
        if parameters['shutter_speed'] == 0:
            self.__capturing_shutter_speed = '0/1'
        else:
            exposure_time = parameters['shutter_speed'] / 1000000
            if int(exposure_time) == 0:
                self.__capturing_shutter_speed = '1/'+str(int(1/exposure_time))
            else:
                self.__capturing_shutter_speed = str(int(exposure_time)) + '/1'

        self.__pipeline = Gst.parse_launch(
            'rpicamsrc name=source preview=false fullscreen=false sensor-mode=3' +
            ' annotation-text-size=' + str(self.parameters['annotation_text_size']) +
            ' annotation-mode=' + str(self.parameters['annotation_mode']) +
            ' sharpness=' + str(self.parameters['sharpness']) +
            ' shutter-speed=' + str(self.parameters['shutter_speed']) +
            ' analog-gain=' + str(self.parameters['iso']) +
            ' contrast=' + str(self.parameters['contrast']) +
            ' awb-mode=' + str(self.parameters['white_balance']) +
            ' saturation=' + str(self.parameters['saturation']) +
            ' ! capsfilter name=source-caps caps=video/x-raw' +
            ',width=' + str(self.parameters['width']) +
            ',height=' + str(self.parameters['height']) +
            ' ! tee name=t ! queue ! videoconvert ! videoscale' +
            ' ! video/x-raw,width=640,height=480' +
            ' ! autovideosink sync=false t. ! queue ! jpegenc quality=100' +
            ' ! taginject name=exif tags="capturing-source=dsc' +
            ',capturing-contrast=' + self.__capturing_contrast +
            ',capturing-white-balance=' + self.__capturing_white_balance +
            ',capturing-sharpness=' + self.__capturing_sharpness +
            ',capturing-saturation=' + self.__capturing_saturation +
            ',capturing-shutter-speed=' + self.__capturing_shutter_speed +
            ',capturing-iso-speed=0" ! jifmux name=setter' +
            ' ! multifilesink name=filesink post-messages=true sync=false ' +
            'max-files=1 location=' + tempfile.gettempdir() + '/DSCFTEMP.JPG')
        self.source = self.__pipeline.get_by_name('source')
        self.__source_caps = self.__pipeline.get_by_name('source-caps')
        self.__exif = self.__pipeline.get_by_name('exif')
        Gst.TagSetter.set_tag_merge_mode(
            self.__pipeline.get_by_name('setter'), Gst.TagMergeMode.REPLACE)
        self.__filesink = self.__pipeline.get_by_name('filesink')

        bus =  self.__pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.__on_sync_message)

        self.__panel_control_stream_info_label_set_text()

        log = function_name + ': exit'
        logging.info(log)


    def start(self):
        """Start the video stream from the camera
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__pipeline.set_state(Gst.State.PLAYING)

        GLib.timeout_add_seconds(1, self.__on_stats)

        parameters['photo_camera'] = not parameters['photo_camera']
        self.__on_control_menu_photo_gallery_button_clicked()

        awb_mode = self.source.get_property('awb-mode') - 1
        if awb_mode <= 0:
            awb_mode = 9
        self.source.set_property('awb-mode', awb_mode)
        self.__on_panel_control_white_balance_button_clicked()

        log = function_name + ': exit'
        logging.info(log)


    def panel_control_file_info_label_set_text(self, index):
        """Sets File Info Label based on meta information of the image file selected by index

        Args:
            index (int): index of the image file
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': index=' + str(index)
        logging.info(log)

        image = PIL.Image.open(self.parameters['media'] + 'DSCF'+str(index).zfill(4)+'.JPG')

        if image._getexif() is None:
            exif = {}
        else:
            exif = {
                PIL.ExifTags.TAGS[k]: v
                for k, v in image._getexif().items()
                if k in PIL.ExifTags.TAGS
            }

        log = function_name + ': exif=' + str(exif)
        logging.info(log)

        if 'ExposureTime' in exif:
            if str(exif['ExposureTime']) == '0.0':
                shutter_speed = 'Auto"'
            elif int(exif['ExposureTime']) == 0:
                shutter_speed = '1/'+str(int(1/exif['ExposureTime']))+'"'
            else:
                shutter_speed = str(int(exif['ExposureTime'])) + '/1"'
        else:
            shutter_speed = ''
        if 'ISOSpeedRatings' in exif:
            iso = 'ISO '+str(exif['ISOSpeedRatings'])
            if iso == 'ISO 0':
                iso = 'ISO Auto'
        else:
            iso = ''
        self.panel_control_info_label.setText(
            'DSCF'+str(index).zfill(4) + '.JPG\n'+str(image.width) + 'x' + str(image.height) +
            '\n'+shutter_speed+'\n' + iso)

        log = function_name + ': exit'
        logging.info(log)


    def resolution_up(self):
        """Handles Resolution increase

        160x120 QQVGA -> 160x128
        320x240 QVGA
        640x480 VGA
        800x600 SVGA -> 800x608
        1024x768 XGA
        1280x960 SXGA
        1600x1200 UXGA
        2048x1536 QXGA
        3200x2400 QUXGA
        4056x3040 MAX

        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        structure = self.__source_caps.get_property('caps').get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')

        if (
            (width < 4056 and self.__gpu_mem >= 512 and self.__sv_mem >= 2048-512-256) or
            (width < 3200 and self.__gpu_mem >= 256 and self.__sv_mem >= 1024-256-128) or
            (width < 2048 and self.__gpu_mem >= 128 and self.__sv_mem >= 512-128-64)):
            if width == 3200:
                width = 4056
                height = 3040
            elif width == 2048:
                width = 3200
                height = 2400
            elif width == 1600:
                width = 2048
                height = 1536
            elif width == 1280:
                width = 1600
                height = 1200
            elif width == 1024:
                width = 1280
                height = 960
            elif width == 800:
                width = 1024
                height = 768
            elif width == 640:
                width = 800
                height = 608 # rounded to multiple of 16
            elif width == 320:
                width = 640
                height = 480
            elif width == 160:
                width = 320
                height = 240

            log = function_name + ': width=' + str(width) + ', height=' + str(height)
            logging.info(log)

            self.__pipeline.set_state(Gst.State.NULL)
            caps = Gst.Caps.new_empty_simple('video/x-raw')
            caps.set_value('width', width)
            caps.set_value('height', height)
            self.__source_caps.set_property('caps', caps)
            self.source.set_property('annotation-text-size', int(height/16))
            self.__pipeline.set_state(Gst.State.PLAYING)
            self.__panel_control_stream_info_label_set_text()

        log = function_name + ': entry'
        logging.info(log)


    def resolution_down(self):
        """Handles resolution decrease

        160x120 QQVGA -> 160x128
        320x240 QVGA
        640x480 VGA
        800x608 SVGA -> 800x608
        1024x768 XGA
        1280x960 SXGA
        1600x1200 UXGA
        2048x1536 QXGA
        3200x2400 QUXGA
        4056x3040 MAX
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        structure = self.__source_caps.get_property('caps').get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')

        if width > 160:
            if width == 320:
                width = 160
                height = 128 # rounded to multiple of 16
            elif width == 640:
                width = 320
                height = 240
            elif width == 800:
                width = 640
                height = 480
            elif width == 1024:
                width = 800
                height = 608 # rounded to multiple of 16
            elif width == 1280:
                width = 1024
                height = 768
            elif width == 1600:
                width = 1280
                height = 960
            elif width == 2048:
                width = 1600
                height = 1200
            elif width == 3200:
                width = 2048
                height = 1536
            elif width == 4056:
                width = 3200
                height = 2400

            log = function_name + ': width=' + str(width) + ', height=' + str(height)
            logging.info(log)

            self.__pipeline.set_state(Gst.State.NULL)
            caps = Gst.Caps.new_empty_simple('video/x-raw')
            caps.set_value('width', width)
            caps.set_value('height', height)
            self.__source_caps.set_property('caps', caps)
            self.source.set_property('annotation-text-size', int(height/16))
            self.__pipeline.set_state(Gst.State.PLAYING)
            self.__panel_control_stream_info_label_set_text()

        log = function_name + ': exit'
        logging.info(log)


    def __on_panel_control_contrast_button_down_clicked(self):
        """Handles contrast decrease
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        contrast = int(self.source.get_property('contrast')) - 10

        log = function_name + ': contrast=' + str(contrast)
        logging.info(log)

        if contrast > -110:
            self.panel_control_contrast_button_up.setEnabled(True)
            if contrast == -100:
                self.panel_control_contrast_button_down.setEnabled(False)
            self.panel_control_contrast_label.setText(str(contrast))
            self.source.set_property('contrast', contrast)
            if contrast == 0:
                self.__capturing_contrast = 'normal'
            elif contrast < 0:
                self.__capturing_contrast = 'soft'
            elif contrast > 0:
                self.__capturing_contrast = 'hard'
            self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))

        log = function_name + ': exit'
        logging.info(log)


    def __on_panel_control_contrast_button_up_clicked(self):
        """Handles contrast increase
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        contrast = int(self.source.get_property('contrast')) + 10

        log = function_name + ': contrast=' + str(contrast)
        logging.info(log)

        if contrast < 110:
            self.panel_control_contrast_button_down.setEnabled(True)
            if contrast == 100:
                self.panel_control_contrast_button_up.setEnabled(False)
            self.panel_control_contrast_label.setText(str(contrast))
            self.source.set_property('contrast', contrast)
            if contrast == 0:
                self.__capturing_contrast = 'normal'
            elif contrast < 0:
                self.__capturing_contrast = 'soft'
            elif contrast > 0:
                self.__capturing_contrast = 'hard'
            self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))

        log = function_name + ': exit'
        logging.info(log)


    def __on_panel_control_white_balance_button_clicked(self):
        """Handles white balance control
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        awb_mode = self.source.get_property('awb-mode')

        log = function_name + ': awb_mode=' + str(awb_mode)
        logging.info(log)

        if awb_mode == 1:
            self.panel_control_white_balance_button.setToolTip(
                'Sunlight white balance mode')
            self.panel_control_white_balance_button.setIcon(
                QIcon(self.parameters['icons'] + 'wb_sunny_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 2)
            self.__capturing_white_balance = 'daylight'
        elif awb_mode == 2:
            self.panel_control_white_balance_button.setToolTip(
                'Cloudy white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                self.parameters['icons'] + 'cloudy_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 3)
            self.__capturing_white_balance = 'cloudy'
        elif awb_mode == 3:
            self.panel_control_white_balance_button.setToolTip(
                'Shade white balance mode')
            self.panel_control_white_balance_button.setIcon(
                QIcon(self.parameters['icons'] + 'wb_shade_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 4)
            self.__capturing_white_balance = 'manual'
        elif awb_mode == 4:
            self.panel_control_white_balance_button.setToolTip(
                'Tungsten white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                self.parameters['icons'] + 'emoji_objects_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 5)
            self.__capturing_white_balance = 'tungsten'
        elif awb_mode == 5:
            self.panel_control_white_balance_button.setToolTip(
                'Fluorescent white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                self.parameters['icons'] + 'fluorescent_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 6)
            self.__capturing_white_balance = 'fluorescent'
        elif awb_mode == 6:
            self.panel_control_white_balance_button.setToolTip(
                'Incadescent white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                self.parameters['icons'] + 'wb_incandescent_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 7)
            self.__capturing_white_balance = '"fluorescent h"'
        elif awb_mode == 7:
            self.panel_control_white_balance_button.setToolTip(
                'Flash white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                self.parameters['icons'] + 'flash_on_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 8)
            self.__capturing_white_balance = 'flash'
        elif awb_mode == 8:
            self.panel_control_white_balance_button.setToolTip(
                'Horizon white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                self.parameters['icons'] + 'wb_twilight_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 9)
            self.__capturing_white_balance = 'manual'
        elif awb_mode == 9:
            self.panel_control_white_balance_button.setToolTip(
                'Auto white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                self.parameters['icons'] + 'wb_auto_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 1)
            self.__capturing_white_balance = 'auto'

        self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))

        log = function_name + ': exit'
        logging.info(log)


    def __on_panel_control_saturation_button_down_clicked(self):
        """Handles sturation decrease
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        saturation = self.source.get_property('saturation') - 10

        log = function_name + ': saturation=' + str(saturation)
        logging.info(log)

        if saturation > -110:
            self.panel_control_saturation_button_up.setEnabled(True)
            if saturation == -100:
                self.panel_control_saturation_button_down.setEnabled(False)
            self.panel_control_saturation_label.setText(str(saturation))
            self.source.set_property('saturation', saturation)
            if saturation == 0:
                self.__capturing_saturation = 'normal'
            elif saturation < 0:
                self.__capturing_saturation = 'low-saturation'
            elif saturation > 0:
                self.__capturing_saturation = 'high-saturation'
            self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))

        log = function_name + ': exit'
        logging.info(log)


    def __on_panel_control_saturation_button_up_clicked(self):
        """Handles saturation increase
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        saturation = self.source.get_property('saturation') + 10

        log = function_name + ': saturation=' + str(saturation)
        logging.info(log)

        if saturation < 110:
            self.panel_control_saturation_button_down.setEnabled(True)
            if saturation == 100:
                self.panel_control_saturation_button_up.setEnabled(False)
            self.panel_control_saturation_label.setText(str(saturation))
            self.source.set_property('saturation', saturation)
            if saturation == 0:
                self.__capturing_saturation = 'normal'
            elif saturation < 0:
                self.__capturing_saturation = 'low-saturation'
            elif saturation > 0:
                self.__capturing_saturation = 'high-saturation'
            self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))

        log = function_name + ': exit'
        logging.info(log)


    def __on_panel_control_delete_button_clicked(self):
        """Handles images delete
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        if not self.parameters['photo_camera']:
            self.__index = self.panel_display.get_index()
        images = glob.glob(self.parameters['media'] + 'DSCF????.JPG')
        images.sort()
        index = images.index(self.parameters['media'] + 'DSCF'+str(self.__index).zfill(4)+'.JPG')
        if path.exists(self.parameters['media'] + 'DSCF'+str(self.__index).zfill(4)+'.JPG'):
            os.remove(self.parameters['media'] + 'DSCF'+str(self.__index).zfill(4)+'.JPG')
        if len(images) == 1:
            self.__index = -1
            if not self.parameters['photo_camera']:
                self.panel_display.set_index(self.__index)
                self.__on_control_menu_photo_gallery_button_clicked()
            self.control_menu_photo_gallery_button.setEnabled(False)
        else:
            if index + 1 == len(images):
                index = len(images) - 2
            else:
                index = index + 1
            self.__index = int(re.search(r'\d+', images[index]).group())
            if not self.parameters['photo_camera']:
                self.panel_display.setPixmap(QPixmap(
                    self.parameters['media'] + 'DSCF' + str(self.__index).zfill(4) +
                    '.JPG').scaled(640,480))
                self.panel_display.set_index(self.__index)
                self.panel_display.set_zoom(False)
            self.panel_control_file_info_label_set_text(self.__index)

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_menu_photo_gallery_button_clicked(self):
        """Toggles between Photo Gallery and Photo Camera
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        if self.parameters['photo_camera']:
            self.parameters['photo_camera'] = False
            self.__pipeline.set_state(Gst.State.NULL)
            self.panel_display.setToolTip(
                'Swipe left or right to select an image or double tap to zoom in')
            self.control_menu_photo_gallery_button.setToolTip('Photo camera')
            self.control_menu_photo_gallery_button.setIcon(
                QIcon(self.parameters['icons'] + 'photo_camera_FILL0_wght400_GRAD0_opsz48.svg'))

            self.panel_display.setPixmap(
                QPixmap(self.parameters['media'] + 'DSCF' + str(self.__index).zfill(4) +
                '.JPG').scaled(640,480))
            self.panel_display.set_index(self.__index)
            self.panel_display.set_zoom(False)
            self.control_shutter_button.setIcon(
                QIcon(self.parameters['icons'] + 'delete_FILL0_wght400_GRAD0_opsz48.svg'))
            self.control_shutter_button.setToolTip('Delete a image')
            CameraScreen.reconnect(
                self.control_shutter_button.clicked,
                self.__on_control_shutter_button_clicked,
                self.__on_panel_control_delete_button_clicked)
            self.panel_control_file_info_label_set_text(self.__index)
        else:
            self.parameters['photo_camera'] = True
            self.__pipeline.set_state(Gst.State.PLAYING)
            self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))
            self.panel_display.setToolTip(
                'Swipe left or right to change resolution or double tap to toggle debug mode')
            self.control_menu_photo_gallery_button.setToolTip('Photo gallery')
            self.control_menu_photo_gallery_button.setIcon(
                QIcon(self.parameters['icons'] + 'photo_library_FILL0_wght400_GRAD0_opsz48.svg'))
            self.__index = self.panel_display.get_index()
            self.control_shutter_button.setIcon(
                QIcon(self.parameters['icons'] + 'circle_FILL0_wght400_GRAD0_opsz48.svg'))
            self.control_shutter_button.setToolTip('Take a picture')
            CameraScreen.reconnect(
                self.control_shutter_button.clicked,
                self.__on_panel_control_delete_button_clicked,
                self.__on_control_shutter_button_clicked)
            self.__panel_control_stream_info_label_set_text()

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_menu_debug_mode_button_clicked(self):
        """Toggles between Photo Gallery and Photo Camera
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        annotation_mode = self.source.get_property('annotation-mode')

        log = function_name + ': annotation_mode=' + str(annotation_mode)
        logging.info(log)

        if annotation_mode == 0x00000000:
            self.source.set_property('annotation-mode', 0x0000065D)
            self.control_menu_exit_button.setIcon(
                QIcon(self.parameters['icons'] + 'analytics_FILL1_wght400_GRAD0_opsz48.svg'))
        else:
            self.source.set_property('annotation-mode', 0x00000000)
            self.control_menu_exit_button.setIcon(
                QIcon(self.parameters['icons'] + 'analytics_FILL0_wght400_GRAD0_opsz48.svg'))

        log = function_name + ': exit'
        logging.info(log)


    def __write_parameters(self):
        """Saves parameters to the config file
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        if self.source is not None and self.__source_caps is not None:
            structure = self.__source_caps.get_property('caps').get_structure(0)

            self.parameters['width'] = structure.get_value('width')
            self.parameters['height'] = structure.get_value('height')
            self.parameters['sharpness'] = self.source.get_property('sharpness')
            self.parameters['shutter_speed'] = self.source.get_property('shutter-speed')
            self.parameters['iso'] = self.source.get_property('analog-gain')
            self.parameters['contrast'] = self.source.get_property('contrast')
            self.parameters['white_balance'] = self.source.get_property('awb-mode')
            self.parameters['saturation'] = self.source.get_property('saturation')
            self.parameters['annotation_mode'] = self.source.get_property('annotation-mode')
            self.parameters['annotation_text_size'] = self.source.get_property(
                'annotation-text-size')

            with open(self.parameters['config'], 'w') as config:
                config.write(json.dumps(self.parameters))
            os.sync()

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_menu_quit_button_clicked(self):
        """Closes the application
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__write_parameters()

        self.__parent.quit()

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_menu_shutdown_button_clicked(self):
        """Closes the application
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__write_parameters()

        os.system('sudo shutdown -h now')

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_sharpness_button_down_clicked(self):
        """Handles sharpness decrease
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        sharpness = int(self.source.get_property('sharpness')) - 10

        log = function_name + ': sharpness=' + str(sharpness)
        logging.info(log)

        if sharpness > -110:
            self.control_sharpness_button_up.setEnabled(True)
            if sharpness == -100:
                self.control_sharpness_button_down.setEnabled(False)
            self.control_sharpness_label.setText(str(sharpness))
            self.source.set_property('sharpness', sharpness)
            if sharpness == 0:
                self.__capturing_sharpness = 'normal'
            elif sharpness < 0:
                self.__capturing_sharpness = 'soft'
            elif sharpness > 0:
                self.__capturing_sharpness = 'hard'
            self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_sharpness_button_up_clicked(self):
        """Handles sharpness increase
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        sharpness = int(self.source.get_property('sharpness')) + 10

        log = function_name + ': sharpness=' + str(sharpness)
        logging.info(log)

        if sharpness < 110:
            self.control_sharpness_button_down.setEnabled(True)
            if sharpness == 100:
                self.control_sharpness_button_up.setEnabled(False)
            self.control_sharpness_label.setText(str(sharpness))
            self.source.set_property('sharpness', sharpness)
            if sharpness == 0:
                self.__capturing_sharpness = 'normal'
            elif sharpness < 0:
                self.__capturing_sharpness = 'soft'
            elif sharpness > 0:
                self.__capturing_sharpness = 'hard'
            self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))

        log = function_name + ': exit'
        logging.info(log)


    def __panel_control_stream_info_label_set_text(self):
        """Sets stream information
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)


        if self.parameters['photo_camera']:
            structure = self.__source_caps.get_property('caps').get_structure(0)

            exposure_time = self.source.get_property('shutter-speed')
            if exposure_time == 0:
                shutter_speed = 'Auto'
            else:
                exposure_time = exposure_time / 1000000
                if int(exposure_time) == 0:
                    shutter_speed = '1/' + str(int(1/exposure_time))
                else:
                    shutter_speed = str(int(exposure_time)) + '/1'

            analog_gain = self.source.get_property('analog-gain')
            if analog_gain == 0:
                iso = 'Auto'
            else:
                iso = str(int(analog_gain*100/256))
            self.panel_control_info_label.setText(
                self.parameters['model'] + '\n' + str(structure.get_value('width')) + 'x' +
                str(structure.get_value('height')) + '\n' + shutter_speed + '"\nISO ' + iso)

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_exposure_shutter_speed_button_up_clicked(self):
        """Handles increase of shutter speed
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        shutter_speed = self.source.get_property('shutter-speed')
        if shutter_speed < 100:
            shutter_speed = 100
            self.__capturing_shutter_speed = '1/10000'
        elif shutter_speed < 111:
            shutter_speed = 111
            self.__capturing_shutter_speed = '1/9000'
        elif shutter_speed < 125:
            shutter_speed = 125
            self.__capturing_shutter_speed = '1/8000'
        elif shutter_speed < 143:
            shutter_speed = 143
            self.__capturing_shutter_speed = '1/7000'
        elif shutter_speed < 167:
            shutter_speed = 167
            self.__capturing_shutter_speed = '1/6000'
        elif shutter_speed < 200:
            shutter_speed = 200
            self.__capturing_shutter_speed = '1/5000'
        elif shutter_speed < 250:
            shutter_speed = 250
            self.__capturing_shutter_speed = '1/4000'
        elif shutter_speed < 333:
            shutter_speed = 333
            self.__capturing_shutter_speed = '1/3000'
        elif shutter_speed < 500:
            shutter_speed = 500
            self.__capturing_shutter_speed = '1/2000'
        elif shutter_speed < 1000:
            shutter_speed = 1000
            self.__capturing_shutter_speed = '1/1000'
        elif shutter_speed < 1111:
            shutter_speed = 1111
            self.__capturing_shutter_speed = '1/900'
        elif shutter_speed < 1250:
            shutter_speed = 1250
            self.__capturing_shutter_speed = '1/800'
        elif shutter_speed < 1429:
            shutter_speed = 1429
            self.__capturing_shutter_speed = '1/700'
        elif shutter_speed < 1667:
            shutter_speed = 1667
            self.__capturing_shutter_speed = '1/600'
        elif shutter_speed < 2000:
            shutter_speed = 2000
            self.__capturing_shutter_speed = '1/500'
        elif shutter_speed < 2500:
            shutter_speed = 2500
            self.__capturing_shutter_speed = '1/400'
        elif shutter_speed < 3333:
            shutter_speed = 3333
            self.__capturing_shutter_speed = '1/300'
        elif shutter_speed < 5000:
            shutter_speed = 5000
            self.__capturing_shutter_speed = '1/200'
        elif shutter_speed < 10000:
            shutter_speed = 10000
            self.__capturing_shutter_speed = '1/100'
        elif shutter_speed < 11111:
            shutter_speed = 11111
            self.__capturing_shutter_speed = '1/90'
        elif shutter_speed < 12500:
            shutter_speed = 12500
            self.__capturing_shutter_speed = '1/80'
        elif shutter_speed < 14286:
            shutter_speed = 14286
            self.__capturing_shutter_speed = '1/70'
        elif shutter_speed < 16667:
            shutter_speed = 16667
            self.__capturing_shutter_speed = '1/60'
        elif shutter_speed < 20000:
            shutter_speed = 20000
            self.__capturing_shutter_speed = '1/50'
        elif shutter_speed < 25000:
            shutter_speed = 25000
            self.__capturing_shutter_speed = '1/40'
        elif shutter_speed < 33333:
            shutter_speed = 33333
            self.__capturing_shutter_speed = '1/30'
        elif shutter_speed < 50000:
            shutter_speed = 50000
            self.__capturing_shutter_speed = '1/20'
        elif shutter_speed < 100000:
            shutter_speed = 100000
            self.__capturing_shutter_speed = '1/10'
        elif shutter_speed < 111111:
            shutter_speed = 111111
            self.__capturing_shutter_speed = '1/9'
            if self.parameters['photo_camera']:
                self.__pipeline.set_state(Gst.State.NULL)
                self.__pipeline.set_state(Gst.State.PLAYING)
        elif shutter_speed < 125000:
            shutter_speed = 125000
            self.__capturing_shutter_speed = '1/8'
        elif shutter_speed < 142857:
            shutter_speed = 142857
            self.__capturing_shutter_speed = '1/7'
        elif shutter_speed < 166667:
            shutter_speed = 166667
            self.__capturing_shutter_speed = '1/6'
        elif shutter_speed < 200000:
            shutter_speed = 200000
            self.__capturing_shutter_speed = '1/5'
        elif shutter_speed < 250000:
            shutter_speed = 250000
            self.__capturing_shutter_speed = '1/4'
        elif shutter_speed < 333333:
            shutter_speed = 333333
            self.__capturing_shutter_speed = '1/3'
        elif shutter_speed < 500000:
            shutter_speed = 500000
            self.__capturing_shutter_speed = '1/2'
        elif shutter_speed < 1000000:
            shutter_speed = 1000000
            self.__capturing_shutter_speed = '1/1'
        elif shutter_speed < 22000000:
            shutter_speed = shutter_speed + 1000000
            self.__capturing_shutter_speed = \
                str(int(shutter_speed/1000000)) + '/1'
            if shutter_speed in (2000000, 7000000) and self.parameters['photo_camera']:
                self.__pipeline.set_state(Gst.State.NULL)
                self.__pipeline.set_state(Gst.State.PLAYING)
        else:
            self.control_exposure_shutter_speed_button_up.setEnabled(False)

        log = function_name + ': shutter_speed=' + str(shutter_speed)
        logging.info(log)

        self.source.set_property('shutter-speed', shutter_speed)
        self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))
        self.control_exposure_shutter_speed_label.setText(
            self.__capturing_shutter_speed + '"')
        self.__panel_control_stream_info_label_set_text()
        self.control_exposure_shutter_speed_button_down.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_exposure_shutter_speed_button_down_clicked(self):
        """Handles decrease of shutter speed
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        shutter_speed = self.source.get_property('shutter-speed')
        if shutter_speed > 1000000:
            shutter_speed = shutter_speed - 1000000
            self.__capturing_shutter_speed = str(
                int(shutter_speed/1000000)) + '/1'
            if shutter_speed in (1000000, 6000000) and self.parameters['photo_camera']:
                self.__pipeline.set_state(Gst.State.NULL)
                self.__pipeline.set_state(Gst.State.PLAYING)
        elif shutter_speed > 500000:
            shutter_speed = 500000
            self.__capturing_shutter_speed = '1/2'
        elif shutter_speed > 333333:
            shutter_speed = 333333
            self.__capturing_shutter_speed = '1/3'
        elif shutter_speed > 250000:
            shutter_speed = 250000
            self.__capturing_shutter_speed = '1/4'
        elif shutter_speed > 200000:
            shutter_speed = 200000
            self.__capturing_shutter_speed = '1/5'
        elif shutter_speed > 166667:
            shutter_speed = 166667
            self.__capturing_shutter_speed = '1/6'
        elif shutter_speed > 142857:
            shutter_speed = 142857
            self.__capturing_shutter_speed = '1/7'
        elif shutter_speed > 125000:
            shutter_speed = 125000
            self.__capturing_shutter_speed = '1/8'
        elif shutter_speed > 111111:
            shutter_speed = 111111
            self.__capturing_shutter_speed = '1/9'
        elif shutter_speed > 100000:
            shutter_speed = 100000
            self.__capturing_shutter_speed = '1/10'
        elif shutter_speed > 50000:
            shutter_speed = 50000
            self.__capturing_shutter_speed = '1/20'
        elif shutter_speed > 33333:
            shutter_speed = 33333
            self.__capturing_shutter_speed = '1/30'
        elif shutter_speed > 25000:
            shutter_speed = 25000
            self.__capturing_shutter_speed = '1/40'
        elif shutter_speed > 20000:
            shutter_speed = 20000
            self.__capturing_shutter_speed = '1/50'
        elif shutter_speed > 16667:
            shutter_speed = 16667
            self.__capturing_shutter_speed = '1/60'
        elif shutter_speed > 14286:
            shutter_speed = 14286
            self.__capturing_shutter_speed = '1/70'
        elif shutter_speed > 12500:
            shutter_speed = 12500
            self.__capturing_shutter_speed = '1/80'
        elif shutter_speed > 11111:
            shutter_speed = 11111
            self.__capturing_shutter_speed = '1/90'
        elif shutter_speed > 10000:
            shutter_speed = 10000
            self.__capturing_shutter_speed = '1/100'
        elif shutter_speed > 5000:
            shutter_speed = 5000
            self.__capturing_shutter_speed = '1/200'
        elif shutter_speed > 3333:
            shutter_speed = 3333
            self.__capturing_shutter_speed = '1/300'
        elif shutter_speed > 2500:
            shutter_speed = 2500
            self.__capturing_shutter_speed = '1/400'
        elif shutter_speed > 2000:
            shutter_speed = 2000
            self.__capturing_shutter_speed = '1/500'
        elif shutter_speed > 1667:
            shutter_speed = 1667
            self.__capturing_shutter_speed = '1/600'
        elif shutter_speed > 1429:
            shutter_speed = 1429
            self.__capturing_shutter_speed = '1/700'
        elif shutter_speed > 1250:
            shutter_speed = 1250
            self.__capturing_shutter_speed = '1/800'
        elif shutter_speed > 1111:
            shutter_speed = 1111
            self.__capturing_shutter_speed = '1/900'
        elif shutter_speed > 1000:
            shutter_speed = 1000
            self.__capturing_shutter_speed = '1/1000'
        elif shutter_speed > 500:
            shutter_speed = 500
            self.__capturing_shutter_speed = '1/2000'
        elif shutter_speed > 333:
            shutter_speed = 333
            self.__capturing_shutter_speed = '1/3000'
        elif shutter_speed > 250:
            shutter_speed = 250
            self.__capturing_shutter_speed = '1/4000'
        elif shutter_speed > 200:
            shutter_speed = 200
            self.__capturing_shutter_speed = '1/5000'
        elif shutter_speed > 167:
            shutter_speed = 167
            self.__capturing_shutter_speed = '1/6000'
        elif shutter_speed > 143:
            shutter_speed = 143
            self.__capturing_shutter_speed = '1/7000'
        elif shutter_speed > 125:
            shutter_speed = 125
            self.__capturing_shutter_speed = '1/8000'
        elif shutter_speed > 111:
            shutter_speed = 111
            self.__capturing_shutter_speed = '1/9000'
        elif shutter_speed > 100:
            shutter_speed = 100
            self.__capturing_shutter_speed = '1/10000'
        elif shutter_speed == 100:
            shutter_speed = 0
            self.__capturing_shutter_speed = '0/1'
            self.control_exposure_shutter_speed_button_down.setEnabled(False)

        log = function_name + ': shutter_speed=' + str(shutter_speed)
        logging.info(log)

        self.source.set_property('shutter-speed', shutter_speed)
        self.__set_exif(str(int(self.source.get_property('analog-gain')*100/256)))
        self.__panel_control_stream_info_label_set_text()
        if self.__capturing_shutter_speed == '0/1':
            self.control_exposure_shutter_speed_label.setText('Auto"')
        else:
            self.control_exposure_shutter_speed_label.setText(
                self.__capturing_shutter_speed+'"')
        self.control_exposure_shutter_speed_button_up.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_exposure_iso_button_up_clicked(self):
        """Handles ISO increase
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        analog_gain = self.source.get_property('analog-gain') + 256

        log = function_name + ': analog_gain=' + str(analog_gain)
        logging.info(log)

        if analog_gain == 4096:
            self.control_exposure_iso_button_up.setEnabled(False)
        self.source.set_property('analog-gain', analog_gain)
        iso = str(int(analog_gain*100/256))
        self.__set_exif(iso)
        self.control_exposure_iso_label.setText('ISO ' + iso)
        self.__panel_control_stream_info_label_set_text()
        self.control_exposure_iso_button_down.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_exposure_iso_button_down_clicked(self):
        """Handles ISO decrease
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        analog_gain = self.source.get_property('analog-gain') - 256

        log = function_name = ': analog_gain=' + str(analog_gain)
        logging.info(log)

        self.source.set_property('analog-gain', analog_gain)
        if analog_gain == 0:
            self.control_exposure_iso_label.setText('ISO Auto')
            self.control_exposure_iso_button_down.setEnabled(False)
            iso = '0'
        else:
            iso = str(int(analog_gain*100/256))
            self.control_exposure_iso_label.setText('ISO ' + iso)

        self.__set_exif(iso)
        self.__panel_control_stream_info_label_set_text()
        self.control_exposure_iso_button_up.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __on_control_shutter_button_clicked(self):
        """Handles taking a picture
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__shutter_clicked = True
        self.control_shutter_button.setToolTip('Taking a picture')
        self.control_shutter_button.setIcon(
            QIcon(self.parameters['icons'] + 'circle_FILL1_wght400_GRAD0_opsz48.svg'))

        log = function_name + ': exit'
        logging.info(log)


    def __on_toast(self):
        """Hides toast

        Returns:
            bool: False
        """
        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__panel_control_stream_info_label_set_text()

        log = function_name + ': result=False'
        logging.info(log)

        return False


    def __on_sync_message(self, _, message):
        """Handles sync messages that appear on the pipeline bus

        Args:
            _ (Gst.Bus): bus
            message (Gst.Message): message
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        name = message.get_structure().get_name()
        if name == 'prepare-window-handle':
            message.src.set_window_handle(self.__win_id)
        if name == 'GstMultiFileSink' and self.__shutter_clicked:
            images = glob.glob(self.parameters['media'] + 'DSCF????.JPG')
            images.sort()
            if len(images) == 0:
                self.__index = 0
            else:
                self.__index = int(
                    re.search(r'\d+', images[len(images) - 1]).group()) + 1
                if self.__index == 10000:
                    self.__index = 0

            shutil.copyfile(
                self.__filesink.get_property("location"),
                self.parameters['media'] + 'DSCF'+str(self.__index).zfill(4) + '.JPG')
            self.panel_display.set_index(self.__index)
            self.control_menu_photo_gallery_button.setEnabled(True)
            self.__shutter_clicked = False
            self.control_shutter_button.setToolTip('Take a picture')
            self.control_shutter_button.setIcon(
                QIcon(self.parameters['icons'] + 'circle_FILL0_wght400_GRAD0_opsz48.svg'))
            self.panel_control_file_info_label_set_text(self.__index)
            GLib.timeout_add_seconds(1, self.__on_toast)

        log = function_name + ': exit'
        logging.info(log)


    def __on_stats(self):
        """Sets debug information
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        annotation_text = \
            'CPU: ' + str(psutil.cpu_percent()) + \
            '% MEM: ' + str(psutil.virtual_memory().percent) + \
            '% TMP: ' + str(round(CPUTemperature().temperature, 1)) + \
            'C\n DSK: ' + str(round(DiskUsage().usage, 1)) + \
            '% THR: ' + subprocess.check_output(
                ['vcgencmd', 'get_throttled']).decode('utf-8').replace('throttled=','').strip() + \
            ' VOL: ' + subprocess.check_output(
                ['vcgencmd', 'measure_volts']).decode('utf-8').replace('volt=','').strip() + '\n'
        if self.__pijuice is not None:
            charge_level = self.__pijuice.status.GetChargeLevel()
            if 'data' in charge_level:
                annotation_text = annotation_text + 'BAT: ' + str(charge_level['data']) + '%'
            else:
                log = function_name + ': charge_level=' + str(charge_level)
                logging.warning(log)
            battery_temperature = self.__pijuice.status.GetBatteryTemperature()
            if 'data' in battery_temperature:
                annotation_text = annotation_text + \
                    ' TMP: ' + str(battery_temperature['data']) + 'C'
            else:
                log = function_name + ': battery_temperature=' + str(battery_temperature)
                logging.warning(log)
            battery_voltage = self.__pijuice.status.GetBatteryVoltage()
            if 'data' in battery_voltage:
                annotation_text = annotation_text + \
                    ' VOL: ' + str(battery_voltage['data']/1000) + 'V'
            else:
                log = function_name + ': battery_voltage=' + str(battery_voltage)
                logging.warning(log)
            annotation_text = annotation_text + '\n'
        annotation_text = annotation_text + 'VER: ' + __version__ + ' '
        self.source.set_property('annotation-text', annotation_text)

        log = function_name + ': result=True'
        logging.info(log)

        return True


    def __set_exif(self, iso):
        """Sets exif metadata

        Args:
            iso (str): ISO string
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': iso=' + iso
        logging.info(log)

        self.__exif.set_property(
            'tags', 'capturing-source=dsc,capturing-contrast=' + self.__capturing_contrast +
            ',capturing-white-balance=' + self.__capturing_white_balance +
            ',capturing-saturation=' + self.__capturing_saturation +
            ',capturing-sharpness=' + self.__capturing_sharpness +
            ',capturing-shutter-speed=' + self.__capturing_shutter_speed +
            ',capturing-iso-speed=' + iso)

        log = function_name + ': exit'
        logging.info(log)


    @staticmethod
    def reconnect(pyqt_signal, old_handler=None, new_handler=None):
        """Reconnects signal from old handler to new handler

        Args:
            pyqt_signal (PYQT_SIGNAL): signal
            old_handler (method, optional): old handler. Defaults to None.
            new_handler (method, optional): new handler. Defaults to None.
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        try:
            if old_handler is not None:
                while True:
                    pyqt_signal.disconnect(old_handler)
            else:
                pyqt_signal.disconnect()
        except TypeError:
            pass
        if new_handler is not None:
            pyqt_signal.connect(new_handler)

        log = function_name + ': exit'
        logging.info(log)


    def closeEvent(self, event):
        """Closes the application

        Args:
            event(QCloseEvent): close event
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.warning(log)

        self.__on_control_menu_quit_button_clicked()

        log = function_name + ': exit'
        logging.warning(log)

        event.accept()


    def __on_terminate(self, *_):
        """Terminates application

        Args:
            _ (int): signal identifier
            _ (frame): frame
        """

        function_name = "'" + threading.currentThread().name + "'." + \
            inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.warning(log)

        self.__on_control_menu_quit_button_clicked()

        log = function_name + ': exit'
        logging.warning(log)

        sys.exit()



def get_parameters(arguments):
    """Gets parameters

    Returns:
        dict: params
    """

    function_name = "'" + threading.currentThread().name + "'." + \
        inspect.currentframe().f_code.co_name

    log = function_name + ': arguments=' + str(arguments)
    logging.info(log)

    try:
        with open(arguments.config, 'r') as config:
            params = json.load(config)
    except FileNotFoundError:
        log = "'" + arguments.config + "' not found"
        logging.warning(log)
        params = {
            'config': arguments.config,
            'icons': 'share/icons/',
            'media': arguments.media,
            'model': 'Unknown',
            'width': 800,
            'height': 608,
            'sharpness': 0,
            'contrast': 0,
            'white_balance': 1,
            'saturation': 0,
            'shutter_speed': 0,
            'iso': 0,
            'annotation_mode': 0x00000000,
            'annotation_text_size': 38,
            'photo_camera': True,
            'exit_action': 'QUIT',
            'exit_icon': 'close_FILL0_wght400_GRAD0_opsz48.svg',
            'logo_icon': 'auto_awesome_FILL0_wght400_GRAD0_opsz48.svg'
        }
        with open(params['config'], 'w') as config:
            config.write(json.dumps(params))
        os.sync()

    if args.exit.upper() == 'QUIT':
        params['exit_action'] = 'QUIT'
        params['exit_icon'] = 'close_FILL0_wght400_GRAD0_opsz48.svg'
    elif args.exit.upper() == 'SHUTDOWN':
        params['exit_action'] = 'SHUTDOWN'
        params['exit_icon'] = 'power_settings_new_FILL0_wght400_GRAD0_opsz48.svg'
    elif args.exit.upper() == 'NONE':
        params['exit_action'] = 'NONE'
        params['exit_icon'] = 'analytics_FILL0_wght400_GRAD0_opsz48.svg'
    else:
        parser.print_help()
        sys.exit()

    log = function_name + ': result=' + str(params)
    logging.info(log)

    return params



if __name__ == '__main__':

    application = QApplication(sys.argv)

    parser = ArgumentParser()
    parser.add_argument(
        '-d', '--debug', type=str, nargs='?', const='DEBUG', default='WARNING',
        help="enable debug level (DEBUG by default): NOTSET, DEBUG, INFO, WARNING, ERROR, CRITICAL")
    parser.add_argument(
        '-e', '--exit', type=str, nargs='?', const='SHUTDOWN', default='QUIT',
        help="define application exit behavior (QUIT by default): QUIT, SHUTDOWN, NONE")
    parser.add_argument(
        '-c', '--config', type=str, nargs='?', const='etc/astroberry.json',
        default='etc/astroberry.json',
        help="path to configuration file ('etc/astroberry.json' by default)")
    parser.add_argument(
        '-m', '--media', type=str, nargs='?', const='media/',
        default='media/',
        help="location of media folder ('media/' by default)")
    args = parser.parse_args()

    try:
        attr = getattr(logging, args.debug.upper())
        logging.basicConfig(format="%(asctime)s %(levelname)s: %(message)s",level=attr)
    except AttributeError:
        parser.print_help()
        sys.exit()

    Gst.init(None)
    Gst.debug_set_colored(False)
    Gst.debug_set_default_threshold((50 - logging.getLogger().getEffectiveLevel() + 10)/10)
    Gst.debug_set_active(True)

    parameters = get_parameters(args)

    try:
        with picamera.PiCamera() as camera:
            parameters['model'] = camera.revision

        screen = CameraScreen(application, parameters)
        screen.setup()
        screen.start()
        screen.show()
        sys.exit(application.exec_())
    except picamera.exc.PiCameraMMALError:
        logging.error('Failed to acquire the camera. Close another instance of the application')
