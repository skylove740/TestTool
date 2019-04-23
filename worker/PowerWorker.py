from model.TvModel import *
from common.Constants import *
from common.TvController import *
import common.LunaCommands as LunaCommands
import traceback
import json
import time

class PowerWorker:
    def __init__(self):
        self.tvController = TvController()

    def reboot(self, ip, excelVer):
        try:
            result = TvModel()
            isConnected = self.tvController.connect(ip)
            time.sleep(0.1)
            if isConnected:
                if excelVer == EXCEL_VERSION[0]:
                    result = self.tvController.execCommand(LunaCommands.reboot(self))
                else:
                    result = self.tvController.execCommandForWO35(LunaCommands.reboot(self))
                self.tvController.disconnect()
            else:
                self.reboot(ip, excelVer)
                time.sleep(3)
            return result
        except Exception as e:
            print('*** reboot, Caught exception: %s: %s' % (e.__class__, e))
            self.reboot(ip, excelVer)
            time.sleep(3)

    def keyBlock(self, ip, block=True):
        try:
            result = TvModel()
            isConnected = self.tvController.connect(ip)
            time.sleep(0.1)
            if isConnected:
                print('key block!!!')
                result = self.tvController.execCommand(LunaCommands.keyBlock(block))
                self.tvController.disconnect()
            else:
                self.keyBlock(ip, block)
                time.sleep(3)
            return result
        except Exception as e:
            print('*** keyBlock, Caught exception: %s: %s' % (e.__class__, e))
            self.keyBlock(ip, block)
            time.sleep(3)

    # 약관 동의 해제
    def setEULA(self, ip, state=False):
        try:
            result = TvModel()
            isConnected = self.tvController.connect(ip)
            time.sleep(0.1)
            if isConnected:
                print('set EULA to - ',state)
                result = self.tvController.execCommand(LunaCommands.setEULA(ip, state))
                self.tvController.disconnect()
            else:
                self.setEULA(ip, state)
                time.sleep(3)
            return result
        except Exception as e:
            print('*** keyBlock, Caught exception: %s: %s' % (e.__class__, e))
            self.setEULA(ip, state)
            time.sleep(3)
