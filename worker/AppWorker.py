from model.TvModel import *
from common.Constants import *
from common.TvController import *
import common.LunaCommands as LunaCommands
import traceback
import json

CURRENT_STATE = 'currentState'
FOREGROUND_APP_INFO = 'foregroundAppInfo'


class AppWorker:
    def __init__(self):
        print('AppWorker.init')
        self.tvController = TvController()

    def searchApp(self, ip, appTitle):
        print('searchApp : ' + appTitle)
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execCommand(LunaCommands.searchApp(self, appTitle))
            self.tvController.disconnect()
        else:
            result.message = MESSAGE_TV_ABNORMAL

        return result

    def inputKey(self, ip, key, times):
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            for i in range(times):
                result = self.tvController.execCommand(LunaCommands.inputKey(self, key))
            self.tvController.disconnect()

        return result

    def checkHomeShowing(self, ip):
        print('checkHomeShowing')
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execCommand(LunaCommands.confirmCurrentState(self))
            self.tvController.disconnect()
            if self.__loadCurrentState(result.resultValue) == STATE_HOME:
                return True, STATE_HOME
            elif self.__loadCurrentState(result.resultValue) == STATE_ALERT:
                print("STATE ALERT!!!!!!!!!!!!!!!!!!!!!")
                return False, STATE_ALERT
            else:
                return False, 'None'

    def checkForegroundAppIsHome(self, ip):
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execCommand(LunaCommands.getForegroundApp(self))
            self.tvController.disconnect()
            foregroundApp = json.loads(result.resultValue)
            for app in foregroundApp[FOREGROUND_APP_INFO]:
                if app["appId"] == "com.webos.app.home":
                    return True
            return False

    def getAppListFromTV(self, ip, path):
        # execNormalCommand
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execNormalCommand("cat "+path)
            self.tvController.disconnect()
            return result
        else:
            return False

    def __loadCurrentState(self, currentState):
        currentStateDict = json.loads(currentState)
        return currentStateDict[CURRENT_STATE]
