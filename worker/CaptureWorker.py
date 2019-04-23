from model.TvModel import *
from common.Constants import *
from common.TvController import *
import common.LunaCommands as LunaCommands
import traceback
import time
import cv2, os, time
import numpy as np

class CaptureWorker:
    def __init__(self):
        print('CaptureWorker.init')
        self.tvController = TvController()

    def doScreenCapture(self, ip, fileName):
        fileName = '/tmp/captured_' + fileName + '.png'
        print('captureApp : ' + fileName)
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execCommand(LunaCommands.doScreenCapture(self, fileName))
            if result.resultType == RESULT_SUCCESS:
                result = TvModel()
                result = self.tvController.downloadFile(fileName)
            self.tvController.disconnect()

        return result

    def doScreenCapture_OSD(self, ip, fileName):
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            # result = self.tvController.execCommand(LunaCommands.doScreenCapture(self, fileName))
            os.system("/tmp/usb/sda/sda1/gmd")
            time.sleep(0.5)
            result = TvModel()
            result = self.tvController.downloadFile("/var/log/*.png")
            if result.resultValue == False:
                os.system("cp /var/log/*.png /tmp/usb/sda/sda1/")
                result.resultValue = True
            self.tvController.disconnect()

        return result
