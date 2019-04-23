from PyQt5 import uic, QtWidgets, QtGui, QtCore
from PyQt5.QtWidgets import QMessageBox
from PyQt5.QtGui import QPixmap, QImage
import time
import sys
import re
import pickle
import os
import json
from worker.CountryWorker import *
from worker.AppWorker import *
from worker.CaptureWorker import *
from worker.FileWorker import *
from worker.PowerWorker import *
from worker.MatchingWorker import *
from worker.ExcelWorker import *
from common.Constants import *
import common.Utils as Utils
import threading

KEY_IP = 'ip'
KEY_RESOURCE_DIR = 'rscDir'
KEY_EXCEL_DIR = 'excelDir'
KEY_ZIP_DIR = 'zipDir'
KEY_MATCHING_VALUE = 'matchingVal'

class MyWindowClass(QtWidgets.QMainWindow):
    appendResultTextSignal = QtCore.pyqtSignal(str)
    appendListViewSignal = QtCore.pyqtSignal(list)
    setResultTextSignal = QtCore.pyqtSignal(str)
    def __init__(self, parent=None):
        QtWidgets.QMainWindow.__init__(self, parent)
        mainUI = os.path.join('.', 'resources', 'mainForm.ui')
        self.appClosed = False
        self.getStopSignal = False
        self.form_class = uic.loadUi(mainUI, self)## Widget으로 구성된 ui일 경우 index 참조 없이 loadui를 호출하면 된다.
        self.form_class.show()
        self.countryWorker = CountryWorker()
        self.appWorker = AppWorker()
        self.captureWorker = CaptureWorker()
        self.fileWorker = FileWorker()
        self.powerWorker = PowerWorker()
        self.matchingWorker = MatchingWorker()
        self.excelWorker = ExcelWorker()
        self.__initUI()
        self.appendResultTextSignal.connect(self.putResultToWindow)
        self.appendListViewSignal.connect(self.putResultToListViewWindow)
        self.setResultTextSignal.connect(self.setTextToResultWindow)
        self.resultList.doubleClicked.connect(self.resultListItemDoubleClicked)

    def __initUI(self):
        try:
            self.platformCombo2ordering.addItems(PLATFROMS)
            self.divChipCombo.addItems(DIV_CHIP_VALUES)
            self.excelVerCombo.addItems(EXCEL_VERSION)
            self.loadPrevious_btn.addItems(['On', 'Off'])
            if not os.path.exists('mydata.pickle'):
                pickle_file = open('mydata.pickle', 'wb')
                pickle_file.close()
            mydata = pickle.load(open('mydata.pickle', 'rb'))
            self.ipEdit.setText(mydata[KEY_IP])
            self.resourceDir.setText(mydata[KEY_RESOURCE_DIR])
            self.excelDir.setText(mydata[KEY_EXCEL_DIR])
            self.zipDir.setText(mydata[KEY_ZIP_DIR])
            self.matchingValEdit.setText(mydata[KEY_MATCHING_VALUE])
            self.targetCountries = ['BIH', 'DEU', 'FRA', 'HRV', 'HUN', 'MKD', 'MNE', 'SRB', 'SVN']

            self.setPlatVer()

        except Exception as e:
            print('*** __initUI, Caught exception: %s: %s' % (e.__class__, e))
            self.ipEdit.setText('192.168.0.10')
            self.matchingValEdit.setText('95')

    def setPlatVer(self):
        currentPlatVer = self.platformCombo2ordering.currentText().strip()
        if currentPlatVer == PLATFROMS[2]: # 4.5
            self.matchingWorker.setSizeInfo(WO45_SIZE_INFO)
        else: # 3.0 / 3.5 / 4.0
            self.matchingWorker.setSizeInfo(WO40_SIZE_INFO)

    def closeEvent(self, event):
        ip = self.ipEdit.text().strip()
        rscDir = self.resourceDir.text().strip()
        excelDir = self.excelDir.text().strip()
        zipDir = self.zipDir.text().strip()
        matchingVal = self.matchingValEdit.text().strip()

        try:
            mydata = {KEY_IP:ip, KEY_RESOURCE_DIR:rscDir, KEY_EXCEL_DIR:excelDir,
                      KEY_ZIP_DIR:zipDir,KEY_MATCHING_VALUE:matchingVal}
            with open('mydata.pickle', 'wb') as f:
                pickle.dump(mydata, f)

            self.appClosed = True
            self.getStopSignal = True

            if hasattr(self,"needToCheckList"):
                stop_data_w = {'ok_list':self.okList,'ng_list':self.ngList, 'dvb_country_list':self.countryWorker.countryModel.DVBcountryList,
                          'atsc_country_list':self.countryWorker.countryModel.ATSCcountryList, 'arib_country_list':self.countryWorker.countryModel.ARIBcountryList,
                          'need_to_check_country_list':self.needToCheckList}
                with open('stop_data.pickle', 'wb') as f:
                    pickle.dump(stop_data_w, f)
                ####### TBD : report 만들고 끝내기.


            # key release
            # self.powerWorker.keyBlock(ip, False)
            QtWidgets.QMainWindow.closeEvent(self, event)
        except Exception as e:
            print('*** closeEvent, Caught exception: %s: %s' % (e.__class__, e))

    def helpBtnClicked(self):
        try:
            self.showDialog('TYPE_INFORMATION', MESSAGE_GUIDE)
        except Exception as e:
            print('*** helpBtnClicked, Caught exception: %s: %s' % (e.__class__, e))
            traceback.print_exc()
        # help(self)

    def resultListItemDoubleClicked(self):
        self.waitingDelNGList = []
        self.waitingDelOKList = []
        try:
            currentItem = self.resultList.selectedIndexes()[0].data().strip()
            captureDir = "download/captured_"+currentItem.split(':')[0].strip()+".png"

            testState = list(currentItem[-1:-3:-1])
            testState = ''.join(list(reversed(testState)))
            if ORDERING_FILTER[2] == testState:
                dialog = os.path.join('.', 'resources', 'selectedForm.ui')
                self.selectedDialog = uic.loadUi(dialog)
                self.selectedDialog.resultCombo.currentTextChanged.connect(self.changeResult)
                self.selectedDialog.countryName.setText(currentItem.split(":")[0])
                boxLayout = QtWidgets.QHBoxLayout()
                widget = QtWidgets.QWidget()
                #widget.setMinimumWidth(SELECTED_FORM_W * len(self.resultInfoList[currentItem].result))
                #widget.setMaximumWidth(SELECTED_FORM_W * len(self.resultInfoList[currentItem].result))
                widget.setFixedWidth(SELECTED_FORM_W * len(self.resultInfoList[currentItem].result))
                for index in range(len(self.resultInfoList[currentItem].result)):
                    self.makeNGWidget(boxLayout, currentItem, index)
                widget.setLayout(boxLayout)
                self.selectedDialog.ngLists.setWidget(widget)

                im = self.matchingWorker.getOnlyOrderingPartOfCapture(currentItem.split(':')[0].strip())
                im = np.require(im, np.uint8, 'C')
                allOrderingIm = self.toQImage(im)
                self.selectedDialog.capturePic.setScaledContents(True)
                self.selectedDialog.capturePic.setPixmap(QPixmap(allOrderingIm))
                self.selectedDialog.resultCombo.addItems(RESULT_VALUES)
                self.selectedDialog.show()
        except Exception as e:
            print('*** resultListItemDoubleClicked, Caught exception: %s: %s' % (e.__class__, e))

    def makeNGWidget(self, parentLayout, currentItem, index):
        try:
            layout = QtWidgets.QGridLayout()
            orderingIndex = int(self.resultInfoList[currentItem].result[index][0]) + 1
            capturedTextLabel = QtWidgets.QLabel("Captured Icon\n[Index :"+str(orderingIndex)+"]")
            capturedTextLabel.setStyleSheet("QLabel {color: white;}")
            captureImgLabel = QtWidgets.QLabel()
            im = self.resultInfoList[currentItem].result[index][1]
            im = np.require(im, np.uint8, 'C')
            capImg = self.toQImage(im)
            captureImgLabel.setPixmap(QPixmap(capImg))
            layout.addWidget(capturedTextLabel,0,0)
            layout.addWidget(captureImgLabel,1,0)

            layoutRsc = QtWidgets.QVBoxLayout()
            rscTextLabel = QtWidgets.QLabel("Resource Icon")
            rscTextLabel.setStyleSheet("QLabel {color: white;}")
            rscImgLabel = QtWidgets.QLabel()
            im = self.resultInfoList[currentItem].result[index][2][1]
            im = np.require(im, np.uint8, 'C')
            rscImg = self.toQImage(im)
            rscImgLabel.setPixmap(QPixmap(rscImg))
            layout.addWidget(rscTextLabel,0,1)
            layout.addWidget(rscImgLabel,1,1)

            parentLayout.addLayout(layout)
            parentLayout.setSpacing(2)
        except Exception as e:
            print('*** makeNGWidget, Caught exception: %s: %s' % (e.__class__, e))

    def toQImage(self,im, copy=False):
        if im is None:
            return QImage()

        if im.dtype == np.uint8:
            if len(im.shape) == 2:
                qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_Indexed8)
                qim.setColorTable(gray_color_table)
                return qim.copy() if copy else qim

            elif len(im.shape) == 3:
                if im.shape[2] == 3:
                    qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_RGB888);
                    return qim.copy() if copy else qim
                elif im.shape[2] == 4:
                    qim = QImage(im.data, im.shape[1], im.shape[0], im.strides[0], QImage.Format_ARGB32);
                    return qim.copy() if copy else qim

        raise NotImplementedException

    def changeResult(self, selectedResult):
        # TBD : 해당 사항 처리하는 동안, 아니 selected WIndow 떠있는 동안 MainWindow Disable하기
        # TBD : 그리고 selected Win의 close event에 trigger 걸어서 처리 완료 후에 Main Win 다시 enable 하기.
        currentText = self.resultList.selectedIndexes()[0].data().strip()
        modiText = str(currentText.split(":")[0].strip()) + ":" + str(selectedResult)
        items = self.listModel.findItems(currentText)

        if len(items) > 1:
            print("ERROR !!!!! To many items are found.")
        elif len(items) == 1:
            items[0].setText(modiText)
            if selectedResult == RESULT_VALUES[1]: # 변경될 상태 = OK, 일반적인 경우
                # 기존에 포함되어 있던 ngListModel에서 해당 아이템을 삭제
                ngListItem = self.ngListModel.findItems(currentText)
                if len(ngListItem) > 1:
                    print("Need to check why ngListItem len is over one!!!!!!")
                elif len(ngListItem) == 1:
                    ngModelIdx = self.ngListModel.indexFromItem(ngListItem[0])
                    #self.ngList.beginRemoveRows()
                    result = self.ngListModel.removeRow(ngModelIdx.row())
                    #self.ngList.endRemoveRows()
                    # 변경된 상태에 따라 okListModel에 해당 아이템을 추가
                    okModelItem = QtGui.QStandardItem(modiText)
                    okModelItem.setEditable(False)
                    self.okListModel.appendRow(okModelItem)
                    self.modifyResultList(RESULT_VALUES[0], currentText)
                else:
                    print("Need to check why ngListItem len is 0!!!!!!!")
            elif selectedResult == RESULT_VALUES[0]: # 변경될 상태 = NG, OK로 변경했다가 다시 변경할 경우
                # 기존에 포함되어 있던 okListModel에서 해당 아이템을 삭제
                okListItem = self.okListModel.findItems(currentText)
                if len(okListItem) > 1:
                    print("Need to check why okListItem len is over one!!!!!!")
                elif len(okListItem) == 1:
                    okModelIdx = self.okListModel.indexFromItem(okListItem[0])

                    result = self.okListModel.removeRow(okModelIdx.row())
                    # 변경된 상태에 따라 ngListModel에 해당 아이템을 추가
                    ngModelItem = QtGui.QStandardItem(modiText)
                    ngModelItem.setEditable(False)
                    self.ngListModel.appendRow(ngModelItem)
                    self.modifyResultList(RESULT_VALUES[1], currentText)
                else:
                    print("Need to check why okListItem len is 0!!!!!!!")
            else:
                print("ERROR !!!!!!!!!!!!!!!!!!!!")
        else:
            print("ERROR !!!!! Found nothing.")


    def orderingCheckLoop(self, countryModel, testList):
        try:
            excelVer = self.excelVerCombo.currentText().strip()
            excelPath = self.excelDir.text().strip()
            resourcePath = self.resourceDir.text().strip()
            platform = self.platformSelectCombo.currentText().strip()
            currentPlatVer = self.platformCombo2ordering.currentText().strip()
            ip = self.ipEdit.text().strip()
            failList = [] # 국가 변경이나 capture 실패한 것들 재실행을 위한 List
            ngList = [] # check 후 NG인 애들 report용

            for count,i in enumerate(testList):

                if self.getStopSignal or self.appClosed:
                    print("########################################### get Stop Signal!!! or appClosed!!")
                    return self.needToCheckList if len(self.needToCheckList) > 0 else testList[count:]+failList

                self.setResultTextSignal.emit("** The number of country to test : "+str(count+1)+"/"+str(len(testList)))
                if not Utils.isEmpty(self, ip, str(i)):
                    # i번째 국가로 변경 요청
                    resultCountry = self.countryWorker.changeCountry(ip, str(i))
                    if resultCountry.resultType == RESULT_SUCCESS:
                        ## TBD : sleep 구문 적절한걸로 변경
                        ## TV Controller connect 다 동시에 사용하도록 변경해야할듯. ##
                        #time.sleep(1)
                        self.appendResultTextSignal.emit("** Current country : "+countryModel.currentCountry)
                        self.powerWorker.reboot(ip, excelVer)
                        time.sleep(30)
                        # key block
                        # self.powerWorker.keyBlock(ip)
                        # 약관 동의 해제
                        self.powerWorker.setEULA(ip)
                        time.sleep(0.5)
                        # 현재 국가 이름이 요청 국가 이름과 같을 경우
                        if countryModel.currentCountry == str(i):
                            # EXIT Key 4회 누르기. (Popup 등을 죽이기 위함)
                            # 4회인 이유는 혹시 연달아서 뜨는 것들이 있을까봐
                            self.appWorker.inputKey(ip, KEY_EXIT, 4)

                            if currentPlatVer == PLATFROMS[2]: # 4.5
                                self.appWorker.inputKey(ip, KEY_HOME, 1)
                                time.sleep(0.5)
                                isHome = self.appWorker.checkForegroundAppIsHome(ip)
                                while not isHome:
                                    self.appWorker.inputKey(ip, KEY_OK, 1)
                                    time.sleep(0.5)
                                    self.appWorker.inputKey(ip, KEY_HOME, 1)
                                    isHome = self.appWorker.checkForegroundAppIsHome(ip)

                            # 현재 Home이 떠 있는 상황인지 Check
                            else: # webOS 4.5에서는 currunt state가 HOME으로 안옴..
                                self.appWorker.inputKey(ip, KEY_HOME, 1)
                                time.sleep(0.5)
                                isHome, value = self.appWorker.checkHomeShowing(ip)
                                while not isHome:
                                    if value == STATE_ALERT or value == 'None':
                                        self.appWorker.inputKey(ip, KEY_OK, 1)
                                    if value != STATE_HOME:
                                        self.appWorker.inputKey(ip, KEY_HOME, 1)
                                    isHome, value = self.appWorker.checkHomeShowing(ip)
                                # 10칸 오른쪽 옆으로 감 (모든 CP Apps Capture를 위해)
                                self.appWorker.inputKey(ip, KEY_RIGHT, 10)



                            resultCapture = self.captureWorker.doScreenCapture(ip, str(i))
                            # resultCapture = self.captureWorker.doScreenCapture_OSD(ip, str(i))
                            time.sleep(1.5)
                            if resultCapture.resultType == RESULT_SUCCESS:
                                print("Capture Success!!")
                                result = self.matchingWorker.doMatching(excelPath, platform, resourcePath, str(i), excelVer, self.logFileContents, int(self.matchingValEdit.text().strip()))
                                if result == None:
                                    failList.append(str(i))
                                    continue
                                self.needToCheckList = testList[count:] + failList
                                self.needToCheckList = list(set(self.needToCheckList))
                                self.appendListViewSignal.emit(result)
                                time.sleep(1)
                            else:
                                print("Capture Fail!!!!!!")
                                for i in range(3):
                                    resultCapture = self.captureWorker.doScreenCapture(ip, str(i))
                                    time.sleep(1.5)
                                    if resultCapture:
                                        break
                                if resultCapture:
                                    print("Capture Success!!")
                                    result = self.matchingWorker.doMatching(excelPath, platform, resourcePath, str(i), excelVer, self.logFileContents, int(self.matchingValEdit.text().strip()))
                                    if result == None:
                                        failList.append(str(i))
                                        continue
                                    self.appendListViewSignal.emit(result)
                                    time.sleep(1)
                                else:
                                    failList.append(str(i))
                                    print("Fail List : ",failList)
                                    continue

                            # 열려 있는 Launcher를 닫는 용도
                            self.appWorker.inputKey(ip, KEY_EXIT, 1)
                        else: # 현재 국가랑 str i 국가가 다를 경우
                            # 국가 기록하고 continue..
                            print("Not Same country!!!!!!!!!!!!!")
                            failList.append(str(i))
                            print("Fail List : ",failList)
                            continue
                    else: # 국가 변경 실패
                        #self.resultText.setText(result.message)
                        print("FAIL CHANGE COUNTRY!!!!!!!!!!!!!!!!!")
                        failList.append(str(i))
                        print("Fail List : ",failList)
                        continue
                else:
                    self.resultText.setText(MESSAGE_NO_INPUT_CHANGE_COUNTRY)

                if self.getStopSignal or self.appClosed:
                    print("########################################### get Stop Signal!!! or appClosed!!")
                    return failList + testList[count:]
            print("END!!!! Fail List :", failList)

            # key release
            # self.powerWorker.keyBlock(ip, False)

            return failList
        except Exception as e:
            print('*** orderingCheckLoop, Caught exception: %s: %s' % (e.__class__, e))
            traceback.print_exc()

    def saveIndexToDelResultList(self, targetListName, resultText):
        country = resultText.split(":")[0].strip()
        if targetListName == RESULT_VALUES[0]: # NG
            targetList = self.ngList
            saveDelList = self.waitingDelNGList
        else:
            targetList = self.okList
            saveDelList = self.waitingDelOKList
        # (country, [[index, cpImgs[index], iconImgs[index]],[...],...])요소들을 가진 list로 전달됨
        for index, item in enumerate(targetList):
            c = item[0].split(":")[0].strip()
            if c == country:
                saveDelList.append(index)

    # selected win에서 결과 값을 변경 시 report를 만들기 위한 list들도 변경해 줘야함
    # 해당 함수는 바로 그 list의 변경을 위한 것
    def modifyResultList(self, targetListName, resultText):
        country = resultText.split(":")[0].strip()
        if targetListName == RESULT_VALUES[0]: # NG
            targetList = self.ngList
            toMoveList = self.okList
            toMoveResult = RESULT_VALUES[1]
        else:
            targetList = self.okList
            toMoveList = self.ngList
            toMoveResult = RESULT_VALUES[0]
        # (country, [[index, cpImgs[index], iconImgs[index]],[...],...])요소들을 가진 list로 전달됨
        for index, item in enumerate(targetList):
            c = item[0].split(":")[0].strip()
            if c == country:
                item[0] = c + ":" + toMoveResult
                toMoveList.append(item)
                del(targetList[index])
                break

    def orderingTestFunction(self):
        try:
            currentExcelVer = self.excelVerCombo.currentText().strip()
            ip = self.ipEdit.text().strip()
            tryCount = 0
            testList = []
            notIncludedCountries = []
            currentChip = self.divChipCombo.currentText().strip()
            platform = self.platformSelectCombo.currentText().strip()
            self.resultInfoList = {}
            countryModel = self.countryWorker.countryModel
            self.matchingWorker.copyAllIcons(self.zipDir.text().strip(), self.resourceDir.text().strip())

            # temp
            self.logFile = open('./test_log.txt','w')
            self.logFile.close()
            self.logFile = open('./test_log.txt','r+')
            self.logFileContents = self.logFile.read().split('\n')


            countiresFromCountryModel = []
            if currentChip == DIV_CHIP_VALUES[0]: #DVB
                countiresFromCountryModel = self.countryWorker.countryModel.DVBcountryList
            elif currentChip == DIV_CHIP_VALUES[1]: #ATSC
                countiresFromCountryModel = self.countryWorker.countryModel.ATSCcountryList
            else:
                countiresFromCountryModel = self.countryWorker.countryModel.ARIBcountryList

            #### 현재 국가가 엑셀 내에 있을때만 list 넘김: TEST 필요!!!!
            if not hasattr(self,'needToCheckList') or len(self.needToCheckList) == 0 or len(self.needToCheckList) < 1:
                for c in countiresFromCountryModel:
                    ''''
                    check = False
                    for st in self.targetCountries:
                        if st in c:
                            check = True
                            break
                    if not check:
                        continue
                    '''
                    # 국가 이름
                    #curCountry = c.split("(")[0].strip().lower()
                    # 국가 코드 2글자짜리
                    curCountry = c.split("(")[1].split(",")[0].strip()
                    if curCountry in self.matchingWorker.countries:
                        testList.append(c)
                    else:
                        notIncludedCountries.append(c)
                if len(testList) > 0:
                    self.needToCheckList = testList
            else:
                print("!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!! @@@ there is self.needToCheckList")
                if len(self.needToCheckList) > 0:
                    testList = self.needToCheckList

            # testList = [country for country in self.matchingWorker.countries if country in testList_temp]

            failList = self.orderingCheckLoop(countryModel, testList)
            if self.getStopSignal or self.appClosed:
                print("get Stop Signal!!!!!!!!!!")
                self.needToCheckList = failList
                return

            if self.appClosed == True:
                print("app Closed.")
                return

            # 확인에 실패한 국가 list를 최대 100회까지 모두 다 확인하기 위한 while문
            while failList != None and len(failList) != 0 and tryCount < 20:
                failList = self.orderingCheckLoop(countryModel, failList)
                tryCount += 1
                print("******* Try Count : ", tryCount)
            # TBD : 모든 확인 이후 처리구문
            self.logFile.write(''.join(self.logFileContents))
            self.logFile.close()
            if len(failList)>0:
                self.appendResultTextSignal.emit("Test Finished! Some list was not tested : "+str(failList))
            else:
                self.appendResultTextSignal.emit("Test Finished!!! Total count : "+str(self.listModel.rowCount())+"/"+str(len(testList)))
                if os.path.exists("stop_data.pickle"):
                    os.remove("stop_data.pickle")
                if hasattr(self,"needToCheckList"):
                    del(self.needToCheckList)

            # temp

            # key release
            # self.powerWorker.keyBlock(ip, False)

            self.excelWorker.makeResultFile(currentChip, platform, self.ngList, self.okList)
            self.filterCombo.setEnabled(True)
            self.filterCombo.addItems(ORDERING_FILTER)
        except Exception as e:
            print('*** orderingTestFunction, Caught exception: %s: %s' % (e.__class__, e))
            traceback.print_exc()
        '''
        'Home은 app이 아니므로 app정보 api로는 확인 불가'
        luna-send -n 1 -f luna://com.webos.surfacemanager/getCurrentState \'{}\'
        '''

    def setPlatformsOfOrderingTest(self):
        excelPath = self.excelDir.text().strip()
        if excelPath == '':
            return False
        currentExcelVer = self.excelVerCombo.currentText().strip()
        if currentExcelVer == EXCEL_VERSION[0]: # 4.0
            platforsmList =  self.matchingWorker.parsingPlatformExcel(excelPath)
        else: # 3.5
            platforsmList = os.listdir(excelPath)
            for i in range(len(platforsmList)):
                platforsmList[i] = platforsmList[i].split("_")[0].strip("(").strip(")")
        if len(platforsmList) > 0:
            self.platformSelectCombo.addItems(platforsmList)
            return True
        else:
            return False

    def platformChanged(self):
        excelPath = self.excelDir.text().strip()
        selecPlatform = self.platformSelectCombo.currentText().strip()
        currentExcelVer = self.excelVerCombo.currentText().strip()
        self.setPlatVer()
        if currentExcelVer == EXCEL_VERSION[0]: # 4.0
            plat = selecPlatform if '-' not in selecPlatform else selecPlatform.split('-')[1]
            self.matchingWorker.loadAllCountriesInCurrentPlatform(excelPath, plat)
        else: # 3.5
            if self.firstCall == False:
                self.matchingWorker.loadAllCountriesInCurrentPlatformForWO35(excelPath, selecPlatform)
            else:
                self.firstCall = False

    def loadResourceBtnClicked(self):
        currentExcelVer = self.excelVerCombo.currentText().strip()
        if currentExcelVer == EXCEL_VERSION[0] and self.setPlatformsOfOrderingTest() == False:
            self.resultText.setText(MESSAGE_NO_INPUT_EXCEL_PATH)
        elif self.resourceDir.text().strip() == '' or self.zipDir.text().strip() == '':
            self.resultText.setText(MESSAGE_NO_INPUT_RESOURCE_PATH)
        else:
            self.oderingTVCheckStartBtn.setEnabled(True)

    def orderingTVCheckStartBtnClicked(self):
        print('orderingTVCheckStartBtnClicked')
        try:
            ip = self.ipEdit.text().strip()
            platform = self.platformCombo2ordering.currentText()
            startBtnStr = self.oderingTVCheckStartBtn.text().strip()
            if startBtnStr == "Start":
                self.oderingTVCheckStartBtn.setText("Stop")
                self.getStopSignal = False
                # TBD : need to add to get all info from pickle (if it exist)
                if hasattr(self,"needToCheckList"):
                    if not hasattr(self.countryWorker, "countryModel") or not hasattr(self.countryWorker.countryModel, "countryList"):
                        result = self.countryWorker.inquery(ip, platform, DISPLAY_TYPE_NAME, False)
                        if result.resultType != RESULT_SUCCESS:
                            self.resultText.setText(result.message)
                        else:
                            self.countryWorker.devDVBorATSC()
                    self.orderingTestThread = threading.Thread(target=self.orderingTestFunction)
                    self.orderingTestThread.start()
                else:
                    if not os.path.exists("stop_data.pickle") or self.loadPrevious_btn.currentText().strip() == 'Off':
                        # 실행 중 Main UI가 멈추기때문에 Thread로 구현
                        self.resultText.setText("")
                        self.listModel = QtGui.QStandardItemModel()
                        self.okListModel = QtGui.QStandardItemModel()
                        self.ngListModel = QtGui.QStandardItemModel()
                        self.okList = []
                        self.ngList = []
                        self.resultList.setModel(self.listModel)

                        # self.countryWorker.downloadCountryFile(ip)
                        # 국가 정보를 가져옴

                        result = self.countryWorker.inquery(ip, platform, DISPLAY_TYPE_NAME, False)
                        if result.resultType != RESULT_SUCCESS:
                            self.resultText.setText(result.message)
                        else:
                            self.countryWorker.devDVBorATSC()
                            self.orderingTestThread = threading.Thread(target=self.orderingTestFunction)
                            self.orderingTestThread.start()
                    else:
                        if os.path.exists('stop_data.pickle') and not (hasattr(self, 'okList') and
                            hasattr(self, 'ngList')):
                            ###### TBD : 기존 Setting이랑 동일할 때만 가져오기 / 선택지 만들기
                            with open('stop_data.pickle', 'rb') as f:
                                stopData = pickle.load(f)
                            self.resultText.setText("")
                            self.listModel = QtGui.QStandardItemModel()
                            self.okListModel = QtGui.QStandardItemModel()
                            self.ngListModel = QtGui.QStandardItemModel()
                            self.okList = stopData['ok_list']
                            self.ngList = stopData['ng_list']
                            self.resultList.setModel(self.listModel)

                            result = self.countryWorker.inquery(ip, platform, DISPLAY_TYPE_NAME, False)
                            if result.resultType != RESULT_SUCCESS:
                                self.resultText.setText(result.message)
                                self.oderingTVCheckStartBtn.setText("Start")
                            else:
                                self.countryWorker.devDVBorATSC()

                            self.countryWorker.countryModel.DVBcountryList = stopData['dvb_country_list']
                            self.countryWorker.countryModel.ATSCcountryList = stopData['atsc_country_list']
                            self.countryWorker.countryModel.ARIBcountryList = stopData['arib_country_list']
                            if not hasattr(self, "needToCheckList"):
                                self.needToCheckList = stopData['need_to_check_country_list']


                            self.orderingTestThread = threading.Thread(target=self.orderingTestFunction)
                            self.orderingTestThread.start()
                        else:
                            self.orderingTestThread = threading.Thread(target=self.orderingTestFunction)
                            self.orderingTestThread.start()

            else:
                self.oderingTVCheckStartBtn.setText("Start")
                self.getStopSignal = True
                # self.needToCheckList

        except Exception as e:
            print('*** orderingTVCheckStartBtnClicked Caught exception: %s: %s' % (e.__class__, e))
            traceback.print_exc()

    def zipRootSelecBtnClicked(self):
        folderName = QtWidgets.QFileDialog.getExistingDirectory(self, "Open File","")
        if folderName != '':
            self.zipDir.setText(folderName)

    def resourceSelecBtnClicked(self):
        folderName = QtWidgets.QFileDialog.getExistingDirectory(self, "Open File","")
        if folderName != '':
            self.resourceDir.setText(folderName)

    def excelSelecBtnClicked(self):
        currentExcelVer = self.excelVerCombo.currentText().strip()
        if currentExcelVer == EXCEL_VERSION[0]: # WO4.0
            folderName = QtWidgets.QFileDialog.getOpenFileName(self, "Open File","")
            self.excelDir.setText(str(folderName[0]))
        elif currentExcelVer == EXCEL_VERSION[0]: # WO 3.5
            self.firstCall = True
            folderName = QtWidgets.QFileDialog.getExistingDirectory(self, "Open File","")
            if folderName != '':
                self.excelDir.setText(folderName)
                self.setPlatformsOfOrderingTest()

    def remakeReportBtnClicked(self):
        currentChip = self.divChipCombo.currentText().strip()
        platform = self.platformSelectCombo.currentText().strip()
        self.excelWorker.makeResultFile(currentChip, platform, self.ngList, self.okList)

    def setTextToResultWindow(self, res):
        self.resultText.setText(res)

    def putResultToWindow(self, res):
        self.resultText.append(res)

    def putResultToListViewWindow(self, res):
        listModelItem = QtGui.QStandardItem(res[0].strip())
        listModelItem.setEditable(False)
        self.listModel.appendRow(listModelItem)
        # 더블클릭했을 때 보여줄 화면을 위한 resource들을 저장함.
        self.resultInfoList[res[0].strip()] = ResultItemInfo(res)
        testState = list(res[0][-1:-3:-1])
        testState = ''.join(list(reversed(testState)))
        if testState == ORDERING_FILTER[1]:
            okModelItem = QtGui.QStandardItem(res[0].strip())
            okModelItem.setEditable(False)
            self.okListModel.appendRow(okModelItem)
            self.okList.append(res)
        else:
            ngModelItem = QtGui.QStandardItem(res[0].strip())
            ngModelItem.setEditable(False)
            self.ngListModel.appendRow(ngModelItem)
            self.ngList.append(res)
        # TBD : scroll to new

    def changeOrderingFilter(self):
        print("changeOrderingFilter")
        currentFilter = self.filterCombo.currentText().strip()
        if currentFilter == ORDERING_FILTER[1]: # OK
            self.resultList.setModel(self.okListModel)
        elif currentFilter == ORDERING_FILTER[2]: # NG
            self.resultList.setModel(self.ngListModel)
        else:
            self.resultList.setModel(self.listModel)

    def resultComboChanged(self):
        print("resultComboChanged()")
        currentResult = self.resultCombo.currentText().strip()
        if currentResult == ORDERING_FILTER[1]:
            self.showDialog('TYPE_QUESTION', INFO_CHANGERESULT_TO_OK)
            # TBD : cancel 눌렸을때의 처리와, OK로 변경 시 LIST값 변경하는 부분 구현하기

    def preBtnClicked(self):
        print("preBtnClicked()")
        # TBD : 이전 List 결과로 화면 전환하는거 구현하기

    def nextBtnClicked(self):
        print("nextBtnClicked()")
        # TBD : 이후 List 결과로 화면 전환하는거 구현하기

    def simpleTestBtnClicked(self):
        orderingPath = "/usr/palm/customization/launchpoints"
        stubPath = "/mnt/otncabi/usr/palm/applications"
        currentExcelVer = self.excelVerCombo.currentText().strip()
        ip = self.ipEdit.text().strip()
        testList = []
        notIncludedCountries = []
        failList = [] # 국가 변경이나 capture 실패한 것들 재실행을 위한 List
        ngList = [] # check 후 NG인 애들 report용
        currentChip = self.divChipCombo.currentText().strip()
        platform = self.platformSelectCombo.currentText().strip()

        excelVer = self.excelVerCombo.currentText().strip()
        excelPath = self.excelDir.text().strip()
        resourcePath = self.resourceDir.text().strip()
        currentPlatVer = self.platformCombo2ordering.currentText().strip()

        platform_version = self.platformCombo2ordering.currentText()
        result = self.countryWorker.inquery(ip, platform_version, DISPLAY_TYPE_NAME, False)
        if result.resultType != RESULT_SUCCESS:
            self.resultText.setText(result.message)
        else:
            self.countryWorker.devDVBorATSC()

        countryModel = self.countryWorker.countryModel

        countiresFromCountryModel = []
        if currentChip == DIV_CHIP_VALUES[0]: #DVB
            countiresFromCountryModel = self.countryWorker.countryModel.DVBcountryList
        elif currentChip == DIV_CHIP_VALUES[1]: #ATSC
            countiresFromCountryModel = self.countryWorker.countryModel.ATSCcountryList
        else:
            countiresFromCountryModel = self.countryWorker.countryModel.ARIBcountryList

        for c in countiresFromCountryModel:
            curCountry = c.split("(")[1].split(",")[0].strip()
            if curCountry in self.matchingWorker.countries:
                testList.append(c)
            else:
                notIncludedCountries.append(c)

        for idx,country in enumerate(testList):
            if not Utils.isEmpty(self, ip, str(country)):
                countryCode = str(country).split(",")[0].split("(")[-1].strip()
                excelOrdering = self.matchingWorker.parsingOrderingExcel(excelPath, platform, countryCode, excelVer)
                code3 = str(country).split(",")[1].strip()
                applistPath = orderingPath + '/' + code3 + '/applist.json'
                result = self.appWorker.getAppListFromTV(ip, applistPath)
                if not result or str(result).strip() == '' or type(result) != type("str"):
                    failList.append((country,"cannot open applist."))
                else:
                    applist = json.loads(str(result))
                    ordering = applist["applications_dosci"]
                    if len(ordering) != len(excelOrdering.keys()):
                        print("ordering list length is different!!!")
                        failList.append((country,"not matching! tv ordering = "+str(ordering)+" / excel ordering = "+str(excelOrdering)))
                        continue
                    for idx, tv_order in enumerate(ordering):
                        if excelOrdering[idx+1].strip() != tv_order.strip():
                            failList.append((country,"not matching! tv ordering = "+str(ordering)+" / excel ordering = "+str(excelOrdering)))
                            break
        print("failList========\n",failList)
        resultText = ""
        for item in failList:
            for line in item:
                if '/' in line:
                    line = line.split('/')
                    line = '\n'.join(line)
                resultText += str(line) + '\n'
            resultText += '\n'
        self.setResultTextSignal.emit("** failList : \n"+resultText)


    def showDialog(self, msgType, message):
        # print(message)
        msg = QMessageBox()
        if msgType == 'TYPE_WARNING':
            msg.setIcon(QMessageBox.Warning)
            msg.setWindowTitle("Warning")
            msg.setStandardButtons(QMessageBox.Ok)
        elif msgType == 'TYPE_INFORMATION':
            # msg.setIcon(QMessageBox.Information)
            msg.setWindowTitle("Ordering Auto Test 도움말")
            msg.setStandardButtons(QMessageBox.Ok)
        elif msgType == 'TYPE_QUESTION':
            msg.setIcon(QMessageBox.Question)
            msg.setStandardButtons(QMessageBox.Ok | QMessageBox.Cancel)
        else:
            msg.setIcon(QMessageBox.NoIcon)
        msg.setText(message)
        # textEdit = msg.findChild(QtGui.QTextEdit)
        # textEdit.setMaximumWidth(16777215)
        msg.setStyleSheet(self.form_class.styleSheet())
        msg.setWindowIcon(self.form_class.windowIcon())
        msg.setMaximumWidth(2000)
        retval = msg.exec_()

class ResultItemInfo:
    def __init__(self, res):
        self.resultText = res[0]
        if res[1] != None:
            self.result = res[1]


if __name__ == '__main__':
    app = QtWidgets.QApplication(sys.argv)
    myWindow = MyWindowClass(None)
    app.exec_()
