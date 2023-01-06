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

import PIL.Image
import PIL.ExifTags

from PyQt5.QtCore import Qt, QEvent, QSize
from PyQt5.QtGui import QIcon, QMouseEvent, QWheelEvent, QPixmap
from PyQt5.QtWidgets import QGestureRecognizer, QApplication, QLabel, QPushButton, QMainWindow, \
    QWidget, QSwipeGesture, QHBoxLayout, QVBoxLayout, QGestureEvent

import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import Gst, GstVideo
Gst.init(None)


class MouseGestureRecognizer(QGestureRecognizer):
    """
    Mouse Gesture Recognizer
    """

    def __init__(self):
        """
        Initialize Mouse Gesture Recognizer
        """

        super().__init__()

        function_name = "'" + threading.currentThread().name + "'." + \
            type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__pressed = False
        self.__timestamp = 0
        self.__startpoint = 0
        self.__endpoint = 0

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

        if self.__pressed is False and event.type() == QMouseEvent.MouseButtonPress:
            self.__pressed = True
            self.__startpoint = event.pos()
            result = QGestureRecognizer.Ignore
        elif self.__pressed is True and event.type() == QMouseEvent.MouseButtonPress:
            result = QGestureRecognizer.Ignore
        elif self.__pressed is True and event.type() == QMouseEvent.MouseButtonRelease:
            self.__pressed = False
            self.__endpoint = event.pos()
            if self.__startpoint == self.__endpoint:
                result = QGestureRecognizer.Ignore
            else:
                delta = self.__endpoint-self.__startpoint
                deg = math.degrees(math.atan2(delta.y(), delta.x()))
                if deg < 0:
                    deg = 360+deg
                gesture.setSwipeAngle(deg)
                result = QGestureRecognizer.TriggerGesture
        elif self.__pressed is False and event.type() == QMouseEvent.MouseButtonRelease:
            result = QGestureRecognizer.Ignore
        elif event.type() == QMouseEvent.MouseButtonDblClick:
            self.__pressed = False
            result = QGestureRecognizer.Ignore
        elif event.type() == QWheelEvent.Wheel:
            timestamp = time.time()
            if timestamp-self.__timestamp < 0.7:
                result = QGestureRecognizer.Ignore
            else:
                self.__timestamp = timestamp
                point = event.angleDelta()
                if point.x() > 0:
                    gesture.setSwipeAngle(0)
                    self.__timestamp = timestamp
                    result = QGestureRecognizer.TriggerGesture
                elif point.x() < 0:
                    gesture.setSwipeAngle(180)
                    self.__timestamp = timestamp
                    result = QGestureRecognizer.TriggerGesture
                elif point.y() > 0:
                    gesture.setSwipeAngle(90)
                    self.__timestamp = timestamp
                    result = QGestureRecognizer.TriggerGesture
                elif point.y() < 0:
                    gesture.setSwipeAngle(270)
                    self.__timestamp = timestamp
                    result = QGestureRecognizer.TriggerGesture
                else:
                    self.__timestamp = timestamp
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

        self.grabGesture(QGestureRecognizer.registerRecognizer(MouseGestureRecognizer()))
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
            if self.__parent.control_menu_photo_camera is True:
                result = self.event_gesture_photo_camera(QGestureEvent(event))
            else:
                result = self.event_gesture_photo_gallery(QGestureEvent(event))
        if event.type() == QEvent.MouseButtonDblClick:
            if self.__parent.control_menu_photo_camera is True:
                result = self.event_mouse_photo_camera(QMouseEvent(event))
            else:
                result = self.event_mouse_photo_gallery(QMouseEvent(event))
        result = QWidget.event(self, event)
        log = function_name + ': result=' + str(result)
        logging.info(log)
        return result


    def event_gesture_photo_camera(self, event):
        """Handles gesture events in Photo Camera display mode

        Args:
            event (QGestureEvent): gesture event

        Returns:
            bool: True
        """

        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        result = QWidget.event(self, event)

        log = function_name + ': result=' + str(result)
        logging.info(log)

        return result


    def event_mouse_photo_camera(self, event):
        """Handles mouse events in Photo Camera display mode

        Args:
            event (QMouseEvent): mouse event

        Returns:
            bool: True
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
        if swipe_gesture is None:
            log = function_name + ': result=False'
            logging.info(log)
            return False
        if self.__zoom is True:
            pixmap = QPixmap('media/DSCF'+str(self.__index).zfill(4)+'.JPG')
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
                if self.__x >= 640:
                    self.__x = 639
                if self.__x < 0:
                    self.__x = 0
                if self.__y >= 480:
                    self.__y = 479
                if self.__y < 0:
                    self.__y = 0
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
            images = glob.glob('media/DSCF????.JPG')
            images.sort()
            index = images.index('media/DSCF'+str(self.__index).zfill(4)+'.JPG')
            if swipe_gesture.horizontalDirection() == QSwipeGesture.Left:
                if index + 1 == len(images):
                    index = 0
                else:
                    index = index + 1
            else:
                if index == 0:
                    index = len(images) - 1
                else:
                    index = index - 1
            self.__index = int(re.search(r'\d+',images[index]).group())
            self.__parent.panel_control_file_info_label_set_text(self.__index)
            pixmap = QPixmap('media/DSCF'+str(self.__index).zfill(4)+'.JPG')
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
            pixmap = QPixmap('media/DSCF'+str(self.__index).zfill(4)+'.JPG')
            if self.__zoom is False:
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



class CameraScreen(QMainWindow):
    """Camera Screen
    """


    def __init__(self, parent = None, application = None):
        """Initialize Camera Screen

        Args:
            parent (_type_, optional): _description_. Defaults to None.
            application (_type_, optional): _description_. Defaults to None.
        """

        super().__init__(parent)

        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.setGeometry(0,36,800,564)
        self.setWindowTitle('AstroBerry')
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint)
        self.setWindowIcon(QIcon('share/icons/astroberry_logo.svg'))

        self.window = QWidget()

        self.panel = QWidget()

        self.panel_display = Display(self)
        self.panel_display.setFixedSize(640,480)
        self.panel_display.setToolTip('Double tap to toggle debug mode')
        self.__win_id = self.panel_display.winId()

        self.panel_control = QWidget()

        self.control = QWidget()
        self.control_menu = QWidget()
        self.control_resolution = QWidget()
        self.control_resolution_button = QWidget()
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

        control_resolution_v_layout = QVBoxLayout()
        control_resolution_v_layout.setContentsMargins(0,0,0,0)
        control_resolution_v_layout.setSpacing(0)

        control_resolution_button_h_layout = QHBoxLayout()
        control_resolution_button_h_layout.setContentsMargins(0,0,0,0)
        control_resolution_button_h_layout.setSpacing(0)

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
            'share/icons/do_not_disturb_on_FILL0_wght400_GRAD0_opsz48.svg'))
        self.panel_control_contrast_button_down.setIconSize(QSize(80,80))
        self.panel_control_contrast_button_down.clicked.connect(
            self.__panel_control_contrast_button_down_clicked)

        self.panel_control_contrast_label = QLabel('0')
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
            'share/icons/add_circle_FILL1_wght400_GRAD0_opsz48.svg'))
        self.panel_control_contrast_button_up.setIconSize(QSize(80,80))
        self.panel_control_contrast_button_up.clicked.connect(
            self.__panel_control_contrast_button_up_clicked)


        self.panel_control_white_balance_button = QPushButton()
        self.panel_control_white_balance_button.setFixedSize(80,80)
        self.panel_control_white_balance_button.setToolTip('Auto white balance mode')
        self.panel_control_white_balance_button.setIcon(QIcon(
            'share/icons/wb_auto_FILL0_wght400_GRAD0_opsz48.svg'))
        self.panel_control_white_balance_button.setIconSize(QSize(80,80))
        self.panel_control_white_balance_button.clicked.connect(
            self.__panel_control_white_balance_button_clicked)

        self.panel_control_saturation_button_down = QPushButton()
        self.panel_control_saturation_button_down.setFixedSize(80,80)
        self.panel_control_saturation_button_down.setToolTip('Decrease saturation')
        self.panel_control_saturation_button_down.setIcon(QIcon(
            'share/icons/do_not_disturb_on_FILL1_wght400_GRAD0_opsz48.svg'))
        self.panel_control_saturation_button_down.setIconSize(QSize(80,80))
        self.panel_control_saturation_button_down.clicked.connect(
            self.__panel_control_saturation_button_down_clicked)

        self.panel_control_saturation_label = QLabel('0')
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
            'share/icons/add_circle_FILL0_wght400_GRAD0_opsz48.svg'))
        self.panel_control_saturation_button_up.setIconSize(QSize(80,80))
        self.panel_control_saturation_button_up.clicked.connect(
            self.__panel_control_saturation_button_up_clicked)

        self.panel_control_delete_button = QPushButton()
        self.panel_control_delete_button.setFixedSize(80,80)
        self.panel_control_delete_button.setToolTip('Delete an image')
        self.panel_control_delete_button.setIcon(QIcon(
            'share/icons/delete_FILL0_wght400_GRAD0_opsz48.svg'))
        self.panel_control_delete_button.setIconSize(QSize(80,80))
        self.panel_control_delete_button.clicked.connect(
            self.__panel_control_delete_button_clicked)

        self.panel_control_file_info_label = QLabel()
        self.panel_control_file_info_label.setFixedSize(80,80)
        self.panel_control_file_info_label.setToolTip('Image information')
        font = self.panel_control_file_info_label.font()
        font.setPointSize(10)
        self.panel_control_file_info_label.setFont(font)
        self.panel_control_file_info_label.setAlignment(Qt.AlignCenter)

        panel_control_h_layout.addWidget(self.panel_control_contrast_button_down)
        panel_control_h_layout.addWidget(self.panel_control_contrast_label)
        panel_control_h_layout.addWidget(self.panel_control_contrast_button_up)
        panel_control_h_layout.addWidget(self.panel_control_white_balance_button)
        panel_control_h_layout.addWidget(self.panel_control_saturation_button_down)
        panel_control_h_layout.addWidget(self.panel_control_saturation_label)
        panel_control_h_layout.addWidget(self.panel_control_saturation_button_up)
        panel_control_h_layout.addWidget(self.panel_control_delete_button)
        panel_control_h_layout.addWidget(self.panel_control_file_info_label)

        self.panel_control.setLayout(panel_control_h_layout)

        panel_v_layout.addWidget(self.panel_display)
        panel_v_layout.addWidget(self.panel_control)

        self.panel.setLayout(panel_v_layout)

        self.control_menu_exit_button = QPushButton()
        self.control_menu_exit_button.setFixedSize(80,80)
        self.control_menu_exit_button.setToolTip('Close AstroBerry')
        self.control_menu_exit_button.setIcon(QIcon(
            'share/icons/close_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_menu_exit_button.setIconSize(QSize(80,80))
        self.control_menu_exit_button.clicked.connect(application.quit)

        self.control_menu_photo_gallery_button = QPushButton()
        self.control_menu_photo_gallery_button.setFixedSize(80,80)
        self.control_menu_photo_gallery_button.setToolTip('Photo gallery')
        self.control_menu_photo_gallery_button.setIcon(QIcon(
            'share/icons/photo_library_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_menu_photo_gallery_button.setIconSize(QSize(80,80))
        self.control_menu_photo_gallery_button.clicked.connect(
            self.__control_menu_photo_gallery_button_clicked)

        self.control_menu_photo_camera = True

        control_menu_h_layout.addWidget(self.control_menu_photo_gallery_button)
        control_menu_h_layout.addWidget(self.control_menu_exit_button)

        self.control_menu.setLayout(control_menu_h_layout)

        self.control_resolution_label = QLabel('800x608')
        self.control_resolution_label.setFixedSize(160,40)
        self.control_resolution_label.setToolTip('Current resolution')
        font = self.control_resolution_label.font()
        font.setPointSize(12)
        self.control_resolution_label.setFont(font)
        self.control_resolution_label.setAlignment(Qt.AlignCenter)

        self.control_resolution_button_down = QPushButton()
        self.control_resolution_button_down.setFixedSize(80,80)
        self.control_resolution_button_down.setToolTip('Decrease resolution')
        self.control_resolution_button_down.setIcon(QIcon(
            'share/icons/do_not_disturb_on_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_resolution_button_down.setIconSize(QSize(80,80))
        self.control_resolution_button_down.clicked.connect(
            self.__control_resolution_button_down_clicked)

        self.control_resolution_button_up = QPushButton()
        self.control_resolution_button_up.setFixedSize(80,80)
        self.control_resolution_button_up.setToolTip('Increase resolution')
        self.control_resolution_button_up.setIcon(QIcon(
            'share/icons/add_circle_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_resolution_button_up.setIconSize(QSize(80,80))
        self.control_resolution_button_up.clicked.connect(
            self.__control_resolution_button_up_clicked)

        control_resolution_button_h_layout.addWidget(self.control_resolution_button_down)
        control_resolution_button_h_layout.addWidget(self.control_resolution_button_up)

        self.control_resolution_button.setLayout(control_resolution_button_h_layout)

        control_resolution_v_layout.addWidget(self.control_resolution_label)

        control_resolution_v_layout.addWidget(self.control_resolution_button)

        self.control_resolution.setLayout(control_resolution_v_layout)

        self.control_exposure_shutter_speed_button_down = QPushButton()
        self.control_exposure_shutter_speed_button_down.setFixedSize(80,80)
        self.control_exposure_shutter_speed_button_down.setToolTip(
            'Decrease shutter speed')
        self.control_exposure_shutter_speed_button_down.setIcon(QIcon(
            'share/icons/indeterminate_check_box_FILL1_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_shutter_speed_button_down.setIconSize(QSize(80,80))
        self.control_exposure_shutter_speed_button_down.clicked.connect(
            self.__control_exposure_shutter_speed_button_down_clicked)
        self.control_exposure_shutter_speed_button_down.setEnabled(False)

        self.control_exposure_shutter_speed_label = QLabel('Auto"')
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
            'share/icons/add_box_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_shutter_speed_button_up.setIconSize(QSize(80,80))
        self.control_exposure_shutter_speed_button_up.clicked.connect(
            self.__control_exposure_shutter_speed_button_up_clicked)

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
            'share/icons/indeterminate_check_box_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_iso_button_down.setIconSize(QSize(90,90))
        self.control_exposure_iso_button_down.clicked.connect(
            self.__control_exposure_iso_button_down_clicked)
        self.control_exposure_iso_button_down.setEnabled(False)

        self.control_exposure_iso_label = QLabel("ISO Auto")
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
            'share/icons/add_box_FILL1_wght400_GRAD0_opsz48.svg'))
        self.control_exposure_iso_button_up.setIconSize(QSize(80,80))
        self.control_exposure_iso_button_up.clicked.connect(
            self.__control_exposure_iso_button_up_clicked)

        control_exposure_iso_v_layout.addWidget(self.control_exposure_iso_button_up)
        control_exposure_iso_v_layout.addWidget(self.control_exposure_iso_label)
        control_exposure_iso_v_layout.addWidget(self.control_exposure_iso_button_down)

        self.control_exposure_iso.setLayout(control_exposure_iso_v_layout)

        control_exposure_h_layout.addWidget(self.control_exposure_shutter_speed)
        control_exposure_h_layout.addWidget(self.control_exposure_iso)

        self.control_exposure.setLayout(control_exposure_h_layout)

        control_v_layout.addWidget(self.control_menu)
        control_v_layout.addWidget(self.control_resolution)
        control_v_layout.addWidget(self.control_exposure)

        self.control_shutter = QPushButton()
        self.control_shutter.setFixedSize(160,160)
        self.control_shutter.setToolTip('Take a picture')
        self.control_shutter.setIcon(QIcon('share/icons/circle_FILL0_wght400_GRAD0_opsz48.svg'))
        self.control_shutter.setIconSize(QSize(160,160))
        self.control_shutter.clicked.connect(self.__control_shutter_clicked)

        self.__shutter_clicked = False

        control_v_layout.addWidget(self.control_shutter)

        self.control.setLayout(control_v_layout)

        window_h_layout.addWidget(self.panel)
        window_h_layout.addWidget(self.control)

        self.window.setLayout(window_h_layout)
        self.setCentralWidget(self.window)

        images = glob.glob('media/DSCF????.JPG')
        images.sort()
        if len(images) == 0:
            self.__index = -1
            self.control_menu_photo_gallery_button.setEnabled(False)
            self.panel_control_delete_button.setEnabled(False)
            self.panel_control_file_info_label.setText('No images')
        else:
            self.__index = int(re.search(r'\d+',images[len(images)-1]).group())
            self.panel_display.set_index(self.__index)
            self.panel_control_file_info_label_set_text(self.__index)

        self.__capturing_shutter_speed = None
        self.__pipeline = None
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

        self.__capturing_shutter_speed = '0/1'
        self.__pipeline = Gst.parse_launch(
            'rpicamsrc name=source preview=false fullscreen=false ' +
            'sensor-mode=3 annotation-text-size=38 ' +
            '! capsfilter name=source-caps ' +
            'caps=video/x-raw,width=800,height=608,framerate=0/1 ' +
            '! tee name=t ! queue ! videoconvert ! videoscale ' +
            '! video/x-raw,width=640,height=480 ' +
            '! autovideosink sync=false t. ! queue ! jpegenc ' +
            '! taginject name=exif tags="capturing-shutter-speed=' +
            self.__capturing_shutter_speed + ',capturing-iso-speed=0" ' +
            '! jifmux name=setter ' +
            '! multifilesink name=filesink post-messages=true sync=false ' +
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

        log = function_name + ': exit'
        logging.info(log)


    def panel_control_file_info_label_set_text(self, index):
        """Sets File Info Label based on meta information of the image file
            selected by index

        Args:
            index (int): index of the image file
        """

        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': index=' + str(index)
        logging.info(log)

        image = PIL.Image.open('media/DSCF'+str(index).zfill(4)+'.JPG')

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
        self.panel_control_file_info_label.setText(
            'DSCF'+str(index).zfill(4) + '.\nJPG\n'+str(image.width) + 'x' + str(image.height) +
            '\n'+shutter_speed+'\n' + iso)

        log = function_name + ': exit'
        logging.info(log)


    def __panel_control_contrast_button_down_clicked(self):
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

        log = function_name + ': exit'
        logging.info(log)


    def __panel_control_contrast_button_up_clicked(self):
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

        log = function_name + ': exit'
        logging.info(log)


    def __panel_control_white_balance_button_clicked(self):
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
                QIcon('share/icons/wb_sunny_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 2)
        elif awb_mode == 2:
            self.panel_control_white_balance_button.setToolTip(
                'Cloudy white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                'share/icons/cloudy_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 3)
        elif awb_mode == 3:
            self.panel_control_white_balance_button.setToolTip(
                'Shade white balance mode')
            self.panel_control_white_balance_button.setIcon(
                QIcon('share/icons/wb_shade_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 4)
        elif awb_mode == 4:
            self.panel_control_white_balance_button.setToolTip(
                'Tungsten white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                'share/icons/emoji_objects_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 5)
        elif awb_mode == 5:
            self.panel_control_white_balance_button.setToolTip(
                'Fluorescent white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                'share/icons/fluorescent_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 6)
        elif awb_mode == 6:
            self.panel_control_white_balance_button.setToolTip(
                'Incadescent white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                'share/icons/wb_incandescent_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 7)
        elif awb_mode == 7:
            self.panel_control_white_balance_button.setToolTip(
                'Flash white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                'share/icons/flash_on_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 8)
        elif awb_mode == 8:
            self.panel_control_white_balance_button.setToolTip(
                'Horizon white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                'share/icons/wb_twilight_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 9)
        elif awb_mode == 9:
            self.panel_control_white_balance_button.setToolTip(
                'Auto white balance mode')
            self.panel_control_white_balance_button.setIcon(QIcon(
                'share/icons/wb_auto_FILL0_wght400_GRAD0_opsz48.svg'))
            self.source.set_property('awb-mode', 1)

        log = function_name + ': exit'
        logging.info(log)


    def __panel_control_saturation_button_down_clicked(self):
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

        log = function_name + ': exit'
        logging.info(log)


    def __panel_control_saturation_button_up_clicked(self):
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

        log = function_name + ': exit'
        logging.info(log)


    def __panel_control_delete_button_clicked(self):
        """Handles images delete
        """

        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        if self.control_menu_photo_camera is False:
            self.__index = self.panel_display.get_index()
        images = glob.glob('media/DSCF????.JPG')
        images.sort()
        index = images.index('media/DSCF'+str(self.__index).zfill(4)+'.JPG')
        if path.exists('media/DSCF'+str(self.__index).zfill(4)+'.JPG'):
            os.remove('media/DSCF'+str(self.__index).zfill(4)+'.JPG')
        if len(images) == 1:
            self.__index = -1
            self.panel_control_delete_button.setEnabled(False)
            if self.control_menu_photo_camera is False:
                self.panel_display.set_index(self.__index)
                self.__control_menu_photo_gallery_button_clicked()

            self.control_menu_photo_gallery_button.setEnabled(False)
            self.panel_control_file_info_label.setText('No images')
        else:
            if index + 1 == len(images):
                index = len(images) - 2
            else:
                index = index + 1
            self.__index = int(re.search(r'\d+', images[index]).group())
            if self.control_menu_photo_camera is False:
                self.panel_display.setPixmap(
                    QPixmap('media/DSCF' + str(self.__index).zfill(4) + '.JPG').scaled(640,480))
                self.panel_display.set_index(self.__index)
                self.panel_display.set_zoom(False)

            self.panel_control_file_info_label_set_text(self.__index)

        log = function_name + ': exit'
        logging.info(log)


    def __control_menu_photo_gallery_button_clicked(self):
        """Toogles between Photo Gallery and Photo Camera
        """

        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        if self.control_menu_photo_camera is True:
            self.control_menu_photo_camera = False
            self.__pipeline.set_state(Gst.State.NULL)
            self.panel_display.setToolTip(
                'Swipe left or right to select an image or double tap to zoom in')
            self.control_menu_photo_gallery_button.setToolTip('Photo camera')
            self.control_menu_photo_gallery_button.setIcon(
                QIcon('share/icons/photo_camera_FILL0_wght400_GRAD0_opsz48.svg'))

            self.panel_display.setPixmap(
                QPixmap('media/DSCF'+str(self.__index).zfill(4)+'.JPG').scaled(640,480))
            self.panel_display.set_index(self.__index)
            self.panel_display.set_zoom(False)
            self.control_shutter.setEnabled(False)
        else:
            self.control_menu_photo_camera = True
            self.__pipeline.set_state(Gst.State.PLAYING)
            analog_gain = self.source.get_property('analog-gain')
            self.__exif.set_property(
                'tags', 'capturing-shutter-speed=' + self.__capturing_shutter_speed +
                ',capturing-iso-speed=' + str(int(analog_gain*100/256)))
            self.panel_display.setToolTip('Double tap to toggle debug mode')
            self.control_menu_photo_gallery_button.setToolTip('Photo gallery')
            self.control_menu_photo_gallery_button.setIcon(
                QIcon('share/icons/photo_library_FILL0_wght400_GRAD0_opsz48.svg'))
            self.__index = self.panel_display.get_index()
            self.control_shutter.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __control_resolution_button_up_clicked(self):
        """Handles Resolution Button Up click

        160x120 QQVGA -> 160x128
        320x240 QVGA
        640x480 VGA
        800x600 SVGA -> 800x608
        1024x768 XGA
        1280x960 SXGA
        1600x1200 UXGA
        2048x1536 QXGA
        3200x2400 QUXGA

        """

        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        structure = self.__source_caps.get_property('caps').get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')

        if width == 2048:
            width = 3200
            height = 2400
            self.control_resolution_button_up.setEnabled(False)
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
            height = 608
        elif width == 320:
            width = 640
            height = 480
        elif width == 160:
            width = 320
            height = 240
        if width < 3200:

            log = function_name + ': width=' + str(width) + ', height=' + str(height)
            logging.info(log)

            self.__pipeline.set_state(Gst.State.NULL)
            caps = Gst.Caps.new_empty_simple('video/x-raw')
            caps.set_value('width', width)
            caps.set_value('height', height)
            self.__source_caps.set_property('caps', caps)
            self.source.set_property('annotation-text-size', int(height/16))
            self.__pipeline.set_state(Gst.State.PLAYING)
            self.control_resolution_label.setText(str(width)+'x'+str(height))
            self.control_resolution_button_down.setEnabled(True)

        log = function_name + ': entry'
        logging.info(log)


    def __control_resolution_button_down_clicked(self):
        """Handles resolution increase

        160x120 QQVGA -> 160x128
        320x240 QVGA
        640x480 VGA
        800x608 SVGA -> 800x608
        1024x768 XGA
        1280x960 SXGA
        1600x1200 UXGA
        2048x1536 QXGA
        3200x2400 QUXGA
        """
        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        structure = self.__source_caps.get_property('caps').get_structure(0)
        width = structure.get_value('width')
        height = structure.get_value('height')

        if width == 320:
            width = 160
            height = 128 # rounded to multiple of 16
            self.control_resolution_button_down.setEnabled(False)
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
        if width > 160:

            log = function_name + ': width=' + str(width) + ', height=' + str(height)
            logging.info(log)

            self.__pipeline.set_state(Gst.State.NULL)
            caps = Gst.Caps.new_empty_simple('video/x-raw')
            caps.set_value('width', width)
            caps.set_value('height', height)
            self.__source_caps.set_property('caps', caps)
            self.source.set_property('annotation-text-size', int(height/16))
            self.__pipeline.set_state(Gst.State.PLAYING)
            self.control_resolution_label.setText(str(width)+'x'+str(height))
            self.control_resolution_button_up.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __control_exposure_shutter_speed_button_up_clicked(self):
        """Hnadles increase of shutter speed
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
            # Unknown why it works fine for 800
            if self.__source_caps.get_property('caps').get_structure(0).\
                get_value('width') != 800:
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
            if shutter_speed in (2000000, 7000000):
                self.__pipeline.set_state(Gst.State.NULL)
                self.__pipeline.set_state(Gst.State.PLAYING)
        else:
            self.control_exposure_shutter_speed_button_up.setEnabled(False)

        log = function_name + ': shutter_speed=' + str(shutter_speed)
        logging.info(log)

        self.source.set_property('shutter-speed', shutter_speed)
        analog_gain = self.source.get_property('analog-gain')
        self.__exif.set_property(
            'tags','capturing-shutter-speed=' +
            self.__capturing_shutter_speed + ', capturing-iso-speed=' +
            str(int(analog_gain*100/256)))
        self.control_exposure_shutter_speed_label.setText(
            self.__capturing_shutter_speed + '"')
        self.control_exposure_shutter_speed_button_down.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __control_exposure_shutter_speed_button_down_clicked(self):
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
            if shutter_speed in (1000000, 6000000):
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
        analog_gain = self.source.get_property('analog-gain')
        self.__exif.set_property(
            'tags','capturing-shutter-speed=' +
            self.__capturing_shutter_speed + ',capturing-iso-speed=' +
            str(int(analog_gain*100/256)))
        if self.__capturing_shutter_speed == '0/1':
            self.control_exposure_shutter_speed_label.setText('Auto"')
        else:
            self.control_exposure_shutter_speed_label.setText(
                self.__capturing_shutter_speed+'"')
        self.control_exposure_shutter_speed_button_up.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __control_exposure_iso_button_up_clicked(self):
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
        self.control_exposure_iso_label.setText('ISO ' + iso)
        self.__exif.set_property(
            'tags', 'capturing-shutter-speed=' + self.__capturing_shutter_speed +
            ',capturing-iso-speed=' + iso)
        self.control_exposure_iso_button_down.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __control_exposure_iso_button_down_clicked(self):
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
            self.__exif.set_property(
                'tags','capturing-shutter-speed=' + self.__capturing_shutter_speed +
                ',capturing-iso-speed=0')
            self.control_exposure_iso_button_down.setEnabled(False)
        else:
            iso = str(int(analog_gain*100/256))
            self.control_exposure_iso_label.setText('ISO ' + iso)
            self.__exif.set_property(
                'tags','capturing-shutter-speed=' + self.__capturing_shutter_speed +
                ',capturing-iso-speed=' + iso)
        self.control_exposure_iso_button_up.setEnabled(True)

        log = function_name + ': exit'
        logging.info(log)


    def __control_shutter_clicked(self):
        """Handles taking a picture
        """

        function_name = "'" + threading.currentThread().name + "'." + \
			type(self).__name__ + '.' + inspect.currentframe().f_code.co_name

        log = function_name + ': entry'
        logging.info(log)

        self.__shutter_clicked = True
        self.control_shutter.setToolTip('Taking a picture')
        self.control_shutter.setIcon(QIcon('share/icons/circle_FILL1_wght400_GRAD0_opsz48.svg'))

        log = function_name + ': exit'
        logging.info(log)


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
        if name == 'GstMultiFileSink' and self.__shutter_clicked is True:
            images = glob.glob('media/DSCF????.JPG')
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
                'media/DSCF'+str(self.__index).zfill(4) + '.JPG')
            self.panel_display.set_index(self.__index)
            structure = self.__source_caps.get_property('caps').get_structure(0)
            if self.__capturing_shutter_speed == '0/1':
                shutter_speed = 'Auto'
            else:
                shutter_speed = self.__capturing_shutter_speed
            analog_gain = self.source.get_property('analog-gain')
            if analog_gain == 0:
                iso = 'Auto'
            else:
                iso = str(int(analog_gain*100/256))
            self.panel_control_file_info_label.setText(
                'DSCF' + str(self.__index).zfill(4) + '.\nJPG\n' +
                str(structure.get_value('width')) + 'x' + str(structure.get_value('height')) +
                '\n' + shutter_speed + '"\nISO ' + iso)
            self.panel_control_delete_button.setEnabled(True)
            self.control_menu_photo_gallery_button.setEnabled(True)
            self.__shutter_clicked = False
            self.control_shutter.setToolTip('Take a picture')
            self.control_shutter.setIcon(QIcon('share/icons/circle_FILL0_wght400_GRAD0_opsz48.svg'))

        log = function_name + ': exit'
        logging.info(log)



if __name__ == '__main__':

    signal.signal(signal.SIGINT, signal.SIG_DFL)

    app = QApplication(sys.argv)

    parser = ArgumentParser()
    parser.add_argument(
        '-d', '--debug', type=str, nargs='?', const='DEBUG', default='WARNING',
        help="enable debug level (DEBUG by default): NOTSET, DEBUG, INFO, "
        "WARNING, ERROR, CRITICAL")
    args = parser.parse_args()


    if getattr(logging, args.debug.upper()):
        logging.basicConfig(
            format="%(asctime)s %(levelname)s: %(message)s",
			level=getattr(logging, args.debug.upper()))

        Gst.debug_set_colored(False)
        Gst.debug_set_default_threshold((50 - logging.getLogger().getEffectiveLevel() + 10)/10)
        Gst.debug_set_active(True)

    try:
        with open('etc/astroberry.json', 'r') as config:
            parameters = json.load(config)
    except:
        logging.warning("'etc/astroberry.json' not found")

    screen = CameraScreen(application = app)
    screen.setup()
    screen.start()
    screen.show()

    sys.exit(app.exec_())
