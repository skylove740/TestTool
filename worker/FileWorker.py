from model.TvModel import *
from common.Constants import *
from common.TvController import *
import common.LunaCommands as LunaCommands

class FileWorker:
    def __init__(self):
        print('FileWorker.init')
        self.tvController = TvController()

    def downloadFile(self, ip, fileName):
        print('downloadFile : ' + fileName)
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.downloadFile(fileName)
            self.tvController.disconnect()
        else:
            result.message = MESSAGE_TV_ABNORMAL

        return result
