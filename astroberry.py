# This should be declared first as it can affect how the other 
# imports are referenced
from PyQt5.QtWidgets import *
 
import sys
import gi
gi.require_version('Gst', '1.0')
gi.require_version('GstVideo', '1.0')
from gi.repository import GObject, Gst, GstVideo

Gst.init(None)

from PyQt5.QtCore import *
from PyQt5.QtGui import *
from PyQt5.QtWidgets import *

class WebCam(QMainWindow):
    """Form for Streaming a WebCam"""
    def __init__(self, parent = None):
        super(WebCam, self).__init__(parent)

        self.setGeometry(0,32,640,480)
        self.setWindowTitle("AstroBerry")
        self.setWindowFlags(Qt.Window | Qt.FramelessWindowHint);

        self.window = QWidget()

        self.display = QWidget()
        self.display.setFixedSize(640,480)
        self.windowId = self.display.winId()

        self.controls = QWidget()
        
        
        self.controlsExposure = QWidget()
        
        self.controlsISO = QWidget()

        self.windowHLayout = QHBoxLayout()
    
        self.controlsVLayout = QVBoxLayout()
    
        self.controlsExposureHLayout = QHBoxLayout()
        
        self.controlsISOHLayout = QHBoxLayout()
        
#        self.slider = QSlider(Qt.Horizontal)
#        self.slider.setStyleSheet("\
#        .QSlider {\
#            min-height: 68px;\
#            max-height: 68px;\
#            background: #5F4141;\
#        }\
#        .QSlider::groove:horizontal {\
#            border: 1px solid #262626;\
#            height: 5px;\
#            background: #393939;\
#            margin: 0 12px;\
#        }\
#        .QSlider::handle:horizontal {\
#            background: #22B14C;\
#            border: 5px solid #B5E61D;\
#            width: 23px;\
#            height: 100px;\
#            margin: -24px -12px;\
#        }")
#        self.vlayout.addWidget(self.slider)

        self.controlsExposureDown = QPushButton("Down")
        self.controlsExposureDown.setFixedSize(100,100)
        self.controlsExposureUp = QPushButton("Up")
        self.controlsExposureUp.setFixedSize(100, 100)
        self.controlsExposureHLayout.addWidget( self.controlsExposureDown)
        self.controlsExposureHLayout.addWidget( self.controlsExposureUp)
        self.controlsExposure.setLayout(self.controlsExposureHLayout)

        self.controlsISODown = QPushButton("Down")
        self.controlsISODown.setFixedSize(100,100)
        self.controlsISOUp = QPushButton("Up")
        self.controlsISOUp.setFixedSize(100, 100)
        self.controlsISOHLayout.addWidget(self.controlsISODown)
        self.controlsISOHLayout.addWidget(self.controlsISOUp)
        self.controlsISO.setLayout(self.controlsISOHLayout)

        self.controlsExposureMode = QPushButton('Exposure Mode')
        self.controlsExposureMode.setFixedSize(100,100)
        self.controlsVLayout.addWidget(self.controlsExposureMode)
        self.controlsVLayout.addWidget(self.controlsExposure)
        self.controlsVLayout.addWidget(self.controlsISO)
        self.controlsShutter = QPushButton('Shutter')
        self.controlsShutter.setFixedSize(100,100)
        self.controlsVLayout.addWidget(self.controlsShutter)
        self.controls.setLayout(self.controlsVLayout)
        
        
        self.windowHLayout.addWidget(self.display)
        self.windowHLayout.addWidget(self.controls)
        #self.hlayout.addWidget(self.vlayout)
        
        self.window.setLayout(self.windowHLayout)
        self.setCentralWidget(self.window)

    def setUpGst(self):
        self.pipeline = Gst.parse_launch(
            'rpicamsrc name=source ! video/x-raw,width=800,height=608 ! videoconvert name = convert ! videoscale ! video/x-raw,width=640,height=480  ! autovideosink name=sink sync=false')  # xvimagesink, ximagesink
        self.source = self.pipeline.get_by_name("source")
        self.videoconvert = self.pipeline.get_by_name("convert")
        self.sink = self.pipeline.get_by_name("sink")
        

        bus =  self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)

    def on_sync_message(self, bus, msg):        
        if msg.get_structure().get_name() == 'prepare-window-handle':
            msg.src.set_window_handle(self.windowId)    

    def startPrev(self):
        self.pipeline.set_state(Gst.State.PLAYING)


if __name__ == '__main__':
    app = QApplication(sys.argv)
    screen = WebCam()
    screen.setUpGst()
    screen.startPrev()
    screen.show()
    sys.exit(app.exec_()) 


#from PyQt5.QtWidgets import QApplication, QWidget, QMainWindow, QPushButton
#from PyQt5.QtCore import QSize, Qt, QRect
#import sys
#
#
#class MainWindow(QMainWindow):
#    def __init__(self):
#        super().__init__()
#
#        self.setWindowTitle("AstroBerry")
#
#        button = QPushButton("Press Me!")
#        button.setCheckable(True)
#        button.clicked.connect(self.the_button_was_clicked)
#
#        self.setGeometry(QRect(0,0, 400, 300))
#
#        # Set the central widget of the Window.
#        self.setCentralWidget(button)
#
#    def the_button_was_clicked(self):
#        print("Clicked!")
#
#app = QApplication(sys.argv)
#window = MainWindow()
#window.show()
#app.exec()