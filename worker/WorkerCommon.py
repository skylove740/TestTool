from common.TvController import *
import time

class WorkerCommon:
    '''
    Ordering Test를 위해 만든 class
    '''
    def __init__(self):
        self.tvController = TvController()

    def connect(self, ip):
        tryCount = 0
        self.connection = self.tvController.connect(ip)
        while not self.connection and tryCount < 20:
            self.connection = self.tvController.connect(ip)
            tryCount += 1
            time.sleep(0.5)
        print("Connected to ", ip)

    def disconnect(self):
        self.tvController.disconnect()
        self.connection = False

    def isConnected(self):
        self.connection = self.tvController.tvTransport.isAlive
        return self.connection
