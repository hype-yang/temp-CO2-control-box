from PySide2.QtWidgets import QApplication,QMainWindow,QPushButton,QPlainTextEdit,QMessageBox,QTextBrowser
from PySide2.QtUiTools import QUiLoader
from PySide2.QtCore import QFile
from PySide2.QtGui import QIcon
from PySide2.QtCore import Signal,QObject
from threading import Thread
from time import sleep
import RPi.GPIO as GPIO
import board
import busio
import adafruit_sgp30
import glob
i2c = busio.I2C(board.SCL, board.SDA, frequency=100000)
sgp30 = adafruit_sgp30.Adafruit_SGP30(i2c)
GPIO.setmode(GPIO.BCM)
GPIO.setup(18,GPIO.OUT)
GPIO.setup(23,GPIO.OUT)
sgp30.iaq_init()
sgp30.set_iaq_baseline(0x8973, 0x8AAE)
GPIO.output(18,GPIO.LOW)
GPIO.output(23,GPIO.LOW)
global i
i=37
j=5
class MySignals(QObject):

    text_print = Signal(str)
class myqt():
    def __init__(self):
        qfile_stats=QFile('control.ui')
        qfile_stats.open(QFile.ReadOnly)
        qfile_stats.close()
        self.ms=MySignals()
        self.ms2=MySignals()
        self.ui=QUiLoader().load(qfile_stats)
        self.ui.textBrowser.setText('{:.1f}'.format(i))
        self.ui.textBrowser_2.setText('{:.1f}'.format(i))
        self.ui.textBrowser_3.setText('{:.2f}'.format(j))
        self.ui.textBrowser_4.setText('{:.2f}'.format(j))
        self.ui.Button.clicked.connect(self.plus1)
        self.ui.Button_3.clicked.connect(self.plus2)
        self.ui.Button_2.clicked.connect(self.substract1)
        self.ui.Button_4.clicked.connect(self.substract2)
        self.ms.text_print.connect(self.CO2_control)
        self.ms2.text_print.connect(self.TEMP_control)
        self.read_CO2()
        self.read_temp()

    def plus1(self):
        global i
        i+=0.1
        self.ui.textBrowser.setText('{:.1f}'.format(i))
    def substract1(self ):
        global i
        i-=0.1
        self.ui.textBrowser.setText('{:.1f}'.format(i))
    def plus2(self):
        global j
        j+=0.1
        self.ui.textBrowser_4.setText('{:.2f}'.format(j))
    def substract2(self):
        global j
        j-=0.1
        self.ui.textBrowser_4.setText('{:.2f}'.format(j))
    def CO2_control(self,text):
        self.ui.textBrowser_3.setText('{:.2f}'.format(float(text)))
    def TEMP_control(self,text):
        self.ui.textBrowser_2.setText('{:.1f}'.format(float(text)))


    def read_temp_raw(self):
        base_dir = '/sys/bus/w1/devices/'
        device_folder = glob.glob(base_dir + '28*')[0]
        device_file = device_folder + '/w1_slave'
        with open(device_file, 'r') as f:
            lines = f.readlines()
    
        return lines
    def read_temp(self):
        def readtemp():
            lines = self.read_temp_raw()
            while lines[0].strip()[-3:] != 'YES':
                sleep(0.2)
                lines = self.read_temp_raw()
            equals_pos = lines[1].find('t=')
            if equals_pos != -1:
                temp_string = lines[1][equals_pos + 2:]
                temp_c = float(temp_string) / 1000.0
                return temp_c
        def run():
            while (1):
               temp_c = readtemp()
               self.ms2.text_print.emit(f'{temp_c}')
               if temp_c <= i-10:
                   GPIO.output(23, GPIO.HIGH)
                   sleep(1)
               elif i-5 >= temp_c > i-10:
                    GPIO.output(23, GPIO.HIGH)
                    for cishu in range(4):
                        temp_c = readtemp()
                        self.ms2.text_print.emit(f'{temp_c}')
                        sleep(1)
                    GPIO.output(23, GPIO.LOW)
                    for cishu in range(1):
                        temp_c = readtemp()
                        self.ms2.text_print.emit(f'{temp_c}')
                        sleep(1)
               elif i > temp_c > i-5:
                    '''GPIO.output(23, GPIO.HIGH)
                    sleep(1)'''
                    GPIO.output(23, GPIO.HIGH)
                    for cishu in range(2):
                        temp_c = readtemp()
                        self.ms2.text_print.emit(f'{temp_c}')
                        if(temp_c >= i):
                            break
                        sleep(1)
                    GPIO.output(23, GPIO.LOW)
                    for cishu in range(3):
                        temp_c = readtemp()
                        self.ms2.text_print.emit(f'{temp_c}')
                        sleep(1)
               else:
                    GPIO.output(23, GPIO.LOW)
                    sleep(1)
        t = Thread(target=run)
        t.setDaemon(True)
        t.start()




    def read_CO2(self):
        def run():
            sleep(10)
            while(1):
                CO2 = float(sgp30.eCO2 / 100)
                self.ms.text_print.emit(f'{CO2}')
                if CO2 < j-0.10:
                    GPIO.output(18, GPIO.HIGH)
                if j+0.10<CO2:
                    GPIO.output(18, GPIO.LOW)
                sleep(1)



        t=Thread(target=run)
        t.setDaemon(True)
        t.start()

mainwindow=QApplication([])
mainwindow.setWindowIcon(QIcon('logo.png'))
start=myqt()
start.ui.showFullScreen()
mainwindow.exec_()