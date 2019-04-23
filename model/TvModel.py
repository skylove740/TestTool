from common.Constants import *

class TvModel:
    def __init__(self):
        self.resultType = RESULT_FAIL
        self.resultValue = ''
        self.message = ''

    def printData(self):
        print('resultType : ' + self.resultType)
        print('resultValue : ' + self.resultValue)
        print('message : ' + self.message)
