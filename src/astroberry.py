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

        self.setGeometry(0,52,800,548)
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
        self.windowHLayout.setContentsMargins(0,0,0,0)
        self.windowHLayout.setSpacing(0)
    
        self.controlsVLayout = QVBoxLayout()
        self.controlsVLayout.setContentsMargins(0,0,0,0)
        self.controlsVLayout.setSpacing(0)
    
        self.controlsExposureHLayout = QHBoxLayout()
        self.controlsExposureHLayout.setContentsMargins(0,0,0,0)
        self.controlsExposureHLayout.setSpacing(0)
        
        self.controlsISOHLayout = QHBoxLayout()
        self.controlsISOHLayout.setContentsMargins(0,0,0,0)
        self.controlsISOHLayout.setSpacing(0)
        
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

        self.controlsExposureLabel = QLabel("Auto")
        font = self.controlsExposureLabel.font()
        font.setPointSize(12)
        self.controlsExposureLabel.setFont(font)
        self.controlsExposureDown = QPushButton("Down")
        self.controlsExposureDown.setFixedSize(80,80)
        font = self.controlsExposureDown.font()
        font.setPointSize(12)
        self.controlsExposureDown.setFont(font)
        self.controlsExposureDown.clicked.connect(self.controlsExposureDownClicked)
        self.controlsExposureUp = QPushButton("Up")
        self.controlsExposureUp.setFixedSize(80, 80)
        font = self.controlsExposureUp.font()
        font.setPointSize(12)
        self.controlsExposureUp.setFont(font)
        self.controlsExposureUp.clicked.connect(self.controlsExposureUpClicked)
        self.controlsExposureHLayout.addWidget( self.controlsExposureDown)
        self.controlsExposureHLayout.addWidget( self.controlsExposureUp)
        self.controlsExposure.setLayout(self.controlsExposureHLayout)

        self.controlsISOLabel = QLabel("Auto")
        font = self.controlsISOLabel.font()
        font.setPointSize(12)
        self.controlsISOLabel.setFont(font)
        self.controlsISODown = QPushButton("Down")
        self.controlsISODown.setFixedSize(80,80)
        font = self.controlsISODown.font()
        font.setPointSize(12)
        self.controlsISODown.setFont(font)
        self.controlsISODown.clicked.connect(self.controlsISODownClicked)
        self.controlsISOUp = QPushButton("Up")
        self.controlsISOUp.setFixedSize(80,80)
        font = self.controlsISOUp.font()
        font.setPointSize(12)
        self.controlsISOUp.setFont(font)
        self.controlsISOUp.clicked.connect(self.controlsISOUpClicked)
        self.controlsISOHLayout.addWidget(self.controlsISODown)
        self.controlsISOHLayout.addWidget(self.controlsISOUp)
        self.controlsISO.setLayout(self.controlsISOHLayout)

        self.controlsExposureMode = QPushButton('Exposure\nMode')
        self.controlsExposureMode.setFixedSize(80,80)
        font = self.controlsExposureMode.font()
        font.setPointSize(12)
        self.controlsExposureMode.setFont(font)
        self.controlsVLayout.addWidget(self.controlsExposureMode)
        self.controlsVLayout.addWidget(self.controlsExposureLabel)
        self.controlsVLayout.addWidget(self.controlsExposure)
        self.controlsVLayout.addWidget(self.controlsISOLabel)
        self.controlsVLayout.addWidget(self.controlsISO)
        self.controlsShutter = QPushButton('Shutter')
        self.controlsShutter.setFixedSize(160,160)
        font = self.controlsShutter.font()
        font.setPointSize(12)
        self.controlsShutter.setFont(font)
        self.controlsVLayout.addWidget(self.controlsShutter)
        self.controls.setLayout(self.controlsVLayout)
        
        
        self.windowHLayout.addWidget(self.display)
        self.windowHLayout.addWidget(self.controls)
        #self.hlayout.addWidget(self.vlayout)
        
        self.window.setLayout(self.windowHLayout)
        self.setCentralWidget(self.window)

    def setUpGst(self):
        self.iso = 0
        self.exposure = 0
        self.pipeline = Gst.parse_launch(
            'rpicamsrc name=source sensor-mode=3 analog-gain='+str(self.iso)+' shutter-speed='+str(self.exposure)+' annotation-mode=0x0000065D ! video/x-raw,width=800,height=608,framerate=0/1 ! videoconvert name = convert ! videoscale ! video/x-raw,width=640,height=480  ! autovideosink name=sink sync=false')  # xvimagesink, ximagesink
        self.source = self.pipeline.get_by_name("source")
        self.videoconvert = self.pipeline.get_by_name("convert")
        self.sink = self.pipeline.get_by_name("sink")
        

        bus =  self.pipeline.get_bus()
        bus.add_signal_watch()
        bus.enable_sync_message_emission()
        bus.connect('sync-message::element', self.on_sync_message)
        bus.set_sync_handler(self.on_message)

    def on_sync_message(self, bus, msg):      
        if msg.get_structure().get_name() == 'prepare-window-handle':
            msg.src.set_window_handle(self.windowId)    

    def on_message(self, bus, msg):
        #if msg.type == Gst.MessageType.STATE_CHANGED and msg.src.name == 'source' and msg.get_structure().get_value('new-state') == Gst.State.PLAYING:
        #    self.exposure = 0
        #    self.source.set_property('shutter-speed',self.exposure)
        return Gst.BusSyncReply.PASS

    def startPrev(self):
        self.pipeline.set_state(Gst.State.PLAYING)

    def controlsISOUpClicked(self):
        if self.iso < 4096:
            self.iso = self.iso + 256
            self.source.set_property('analog-gain', self.iso)
            self.controlsISOLabel.setText('ISO '+str(int(self.iso*100/256)))

    def controlsISODownClicked(self):
        if self.iso > 0:
            self.iso = self.iso - 256
            self.source.set_property('analog-gain', self.iso)
            if self.iso == 0:
                self.controlsISOLabel.setText('Auto')
            else:
                self.controlsISOLabel.setText('ISO '+str(int(self.iso*100/256)))

    def controlsExposureUpClicked(self):

        if self.exposure < 100:
            self.exposure = 100
            self.controlsExposureLabel.setText('1/10000"')
        elif self.exposure < 125:
            self.exposure = 125
            self.controlsExposureLabel.setText('1/9000"')
        elif self.exposure < 143:
            self.exposure = 143
            self.controlsExposureLabel.setText('1/7000"')
        elif self.exposure < 167:
            self.exposure = 167
            self.controlsExposureLabel.setText('1/6000"')
        elif self.exposure < 200:
            self.exposure = 200
            self.controlsExposureLabel.setText('1/5000"')
        elif self.exposure < 250:
            self.exposure = 250
            self.controlsExposureLabel.setText('1/4000"')
        elif self.exposure < 333:
            self.exposure = 333
            self.controlsExposureLabel.setText('1/3000"')
        elif self.exposure < 500:
            self.exposure = 500
            self.controlsExposureLabel.setText('1/2000"')
        elif self.exposure < 1000:
            self.exposure = 1000
            self.controlsExposureLabel.setText('1/1000"')
        elif self.exposure < 1111:
            self.exposure = 1111
            self.controlsExposureLabel.setText('1/900"')
        elif self.exposure < 1250:
            self.exposure = 1250
            self.controlsExposureLabel.setText('1/800"')
        elif self.exposure < 1429:
            self.exposure = 1429
            self.controlsExposureLabel.setText('1/700"')
        elif self.exposure < 1667:
            self.exposure = 1667
            self.controlsExposureLabel.setText('1/600"')  
        elif self.exposure < 2000:
            self.exposure = 2000
            self.controlsExposureLabel.setText('1/500"')
        elif self.exposure < 3333:
            self.exposure = 3333
            self.controlsExposureLabel.setText('1/300"')
        elif self.exposure < 5000:
            self.exposure = 5000
            self.controlsExposureLabel.setText('1/200"')
        elif self.exposure < 10000:
            self.exposure = 10000
            self.controlsExposureLabel.setText('1/100"')
        elif self.exposure < 11111:
            self.exposure = 11111
            self.controlsExposureLabel.setText('1/90"')    
        elif self.exposure < 12500:
            self.exposure = 12500
            self.controlsExposureLabel.setText('1/80"')                
        elif self.exposure < 14286:
            self.exposure = 14286
            self.controlsExposureLabel.setText('1/70"')        
        elif self.exposure < 16667:
            self.exposure = 16667
            self.controlsExposureLabel.setText('1/60"')        
        elif self.exposure < 20000:
            self.exposure = 20000
            self.controlsExposureLabel.setText('1/50"')        
        elif self.exposure < 25000:
            self.exposure = 25000
            self.controlsExposureLabel.setText('1/40"')        
        elif self.exposure < 33333:
            self.exposure = 33333
            self.controlsExposureLabel.setText('1/30"')        
        elif self.exposure < 50000:
            self.exposure = 50000
            self.controlsExposureLabel.setText('1/20"')        
        elif self.exposure < 100000:
            self.exposure = 100000
            self.controlsExposureLabel.setText('1/10"')
        elif self.exposure < 111111:
            self.exposure = 111111
            self.controlsExposureLabel.setText('1/9"') 
        elif self.exposure < 125000:
            self.exposure = 125000
            self.controlsExposureLabel.setText('1/8"')
        elif self.exposure < 142857:
            self.exposure = 142857
            self.controlsExposureLabel.setText('1/7"')
        elif self.exposure < 166667:
            self.exposure = 166667
            self.controlsExposureLabel.setText('1/6"')
        elif self.exposure < 200000:
            self.exposure = 200000
            self.controlsExposureLabel.setText('1/5"')
        elif self.exposure < 250000:
            self.exposure = 250000
            self.controlsExposureLabel.setText('1/4"')
        elif self.exposure < 333333:
            self.exposure = 333333
            self.controlsExposureLabel.setText('1/3"')
        elif self.exposure < 500000:
            self.exposure = 500000
            self.controlsExposureLabel.setText('1/2"')
        elif self.exposure < 1000000:
            self.exposure = 1000000
            self.controlsExposureLabel.setText('1"')
        elif self.exposure < 22000000:
            self.exposure = self.exposure + 1000000
            if self.exposure == 2000000 or self.exposure == 7000000:
                self.pipeline.set_state(Gst.State.NULL)
                self.source.set_property('shutter-speed', self.exposure)
                self.source.set_property('analog-gain', self.iso)
                self.pipeline.set_state(Gst.State.PLAYING)

            self.controlsExposureLabel.setText(str(int(self.exposure/1000000))+'"')
        self.source.set_property('shutter-speed', self.exposure)
        print(self.source.get_property('shutter-speed'))

    def controlsExposureDownClicked(self):
        if self.exposure > 1000000:
            self.exposure = self.exposure - 1000000
            if self.exposure == 1000000 or self.exposure == 6000000:
                self.pipeline.set_state(Gst.State.NULL)
                self.source.set_property('shutter-speed', self.exposure)
                self.source.set_property('analog-gain', self.iso)
                self.pipeline.set_state(Gst.State.PLAYING)
            self.controlsExposureLabel.setText(str(int(self.exposure/1000000))+'"')
        elif self.exposure > 500000:
            self.exposure = 500000
            self.controlsExposureLabel.setText('1/2"')
        elif self.exposure > 333333:
            self.exposure = 333333
            self.controlsExposureLabel.setText('1/3"')
        elif self.exposure > 250000:
            self.exposure = 250000
            self.controlsExposureLabel.setText('1/4"')
        elif self.exposure > 200000:
            self.exposure = 200000
            self.controlsExposureLabel.setText('1/5"')
        elif self.exposure > 166667:
            self.exposure = 166667
            self.controlsExposureLabel.setText('1/6"')
        elif self.exposure > 142857:
            self.exposure = 142857
            self.controlsExposureLabel.setText('1/7"')
        elif self.exposure > 125000:
            self.exposure = 125000
            self.controlsExposureLabel.setText('1/8"')
        elif self.exposure > 111111:
            self.exposure = 111111
            self.controlsExposureLabel.setText('1/9"')
        elif self.exposure > 100000:
            self.exposure = 100000
            self.controlsExposureLabel.setText('1/10"')
        elif self.exposure > 50000:
            self.exposure = 50000
            self.controlsExposureLabel.setText('1/20"')
        elif self.exposure > 33333:
            self.exposure = 33333
            self.controlsExposureLabel.setText('1/30"')
        elif self.exposure > 25000:
            self.exposure = 25000
            self.controlsExposureLabel.setText('1/40"')
        elif self.exposure > 20000:
            self.exposure = 20000
            self.controlsExposureLabel.setText('1/50"')
        elif self.exposure > 16667:
            self.exposure = 16667
            self.controlsExposureLabel.setText('1/60"')
        elif self.exposure > 14286:
            self.exposure = 14286
            self.controlsExposureLabel.setText('1/70"')
        elif self.exposure > 12500:
            self.exposure = 12500
            self.controlsExposureLabel.setText('1/80"')
        elif self.exposure > 11111:
            self.exposure = 11111
            self.controlsExposureLabel.setText('1/90"')
        elif self.exposure > 10000:
            self.exposure = 10000
            self.controlsExposureLabel.setText('1/100"')
        elif self.exposure > 5000:
            self.exposure = 5000
            self.controlsExposureLabel.setText('1/200"')
        elif self.exposure > 3333:
            self.exposure = 3333
            self.controlsExposureLabel.setText('1/300"')
        elif self.exposure > 2500:
            self.exposure = 2500
            self.controlsExposureLabel.setText('1/400"')
        elif self.exposure > 2000:
            self.exposure = 2000
            self.controlsExposureLabel.setText('1/500"')
        elif self.exposure > 1667:
            self.exposure = 1667
            self.controlsExposureLabel.setText('1/600"')
        elif self.exposure > 1429:
            self.exposure = 1429
            self.controlsExposureLabel.setText('1/700"')
        elif self.exposure > 1250:
            self.exposure = 1250
            self.controlsExposureLabel.setText('1/800"')
        elif self.exposure > 1111:
            self.exposure = 1111
            self.controlsExposureLabel.setText('1/900"')
        elif self.exposure > 1000:
            self.exposure = 1000
            self.controlsExposureLabel.setText('1/1000"')
        elif self.exposure > 500:
            self.exposure = 500
            self.controlsExposureLabel.setText('1/2000"')
        elif self.exposure > 333:
            self.exposure = 333
            self.controlsExposureLabel.setText('1/3000"')
        elif self.exposure > 250:
            self.exposure = 250
            self.controlsExposureLabel.setText('1/4000"')
        elif self.exposure > 200:
            self.exposure = 200
            self.controlsExposureLabel.setText('1/5000"')
        elif self.exposure > 167:
            self.exposure = 167
            self.controlsExposureLabel.setText('1/6000"')
        elif self.exposure > 143:
            self.exposure = 143
            self.controlsExposureLabel.setText('1/7000"')
        elif self.exposure > 125:
            self.exposure = 125
            self.controlsExposureLabel.setText('1/8000"')
        elif self.exposure > 111:
            self.exposure = 111
            self.controlsExposureLabel.setText('1/9000"')
        elif self.exposure > 100:
            self.exposure = 100
            self.controlsExposureLabel.setText('1/10000"')
        elif self.exposure == 100:
            self.exposure = 0
            self.controlsExposureLabel.setText('Auto')

        self.source.set_property('shutter-speed', self.exposure)

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