from model.TvModel import *
from common.Constants import *
from common.TvController import *
import common.LunaCommands as LunaCommands
import traceback
import cv2
import numpy as np
import xlrd
import os
import json
import shutil
import collections
from PIL import Image
import os
from pathlib import Path

class MatchingWorker:
    def __init__(self):
        self.tvController = TvController()
        self.countries = []
        self.sizeInfo = None


        # temp
        self.logFileContents = None

    def setSizeInfo(self, size_info):
        self.sizeInfo = size_info

    # Capture 이미지를 load해서 CP기준으로 자른 이미지 list return
    def loadCaptureAndCrop(self, fileName):
        captureDir = "download/"+fileName
        if not os.path.exists(captureDir):
            os.makedirs(captureDir)
        capture = self.getOnlyOrderingPartOfCapture(fileName)
        cps = self.divImg(capture, captureDir)
        return cps

    def getCpsForDemo(self, captureDir):
        lists = os.listdir(captureDir)
        lists_m = [int(n.split('.')[0]) for n in lists]
        lists = [str(n)+".png" for n in sorted(lists_m)]
        resultImg = []
        for file in lists:
            path = captureDir + '/' + file
            capture = cv2.imread(path, cv2.IMREAD_UNCHANGED)
            capture = cv2.cvtColor(capture, cv2.COLOR_BGR2RGB)
            resultImg.append(capture)
        return resultImg

    def getOnlyOrderingPartOfCapture(self, fileName):
        capturePath = "download/captured_"+fileName+".png"

        capture = cv2.imread(capturePath, cv2.IMREAD_UNCHANGED)
        capture = cv2.cvtColor(capture, cv2.COLOR_BGR2RGB)
        # capture = cv2.resize(capture, None, fx=FX_FY, fy=FX_FY)
        # resize, 1920 1080 캡쳐일때
        # capture = cv2.resize(capture, (1280, 720))

        capture = capture[int(self.sizeInfo['crop_y_start']*FX_FY):int(self.sizeInfo['crop_y_end']*FX_FY)\
        if int(self.sizeInfo['crop_y_end']*FX_FY) <= capture.shape[0] else capture.shape[0], :, :]

        return capture

    # Capture 이미지의 각 CP를 잘라서 return
    def divImg(self, img, captureDir):
        """
        width = 133 # 133
        gap = 40
        y_margin = 20
        startX = 44 + gap
        """
        width = int(self.sizeInfo['width']*FX_FY)
        gap = int(self.sizeInfo['gap']*FX_FY)
        y_margin = int(self.sizeInfo['y_margin']*FX_FY)
        startX = int(self.sizeInfo['startX']*FX_FY)
        resultImg = []
        index = 0
        while startX <= img.shape[1]:
            startX -= gap
            im = img[y_margin:-y_margin, startX:startX+width,:]
            resultImg.append(im)
            cv2.imwrite(captureDir+"/"+str(index)+".png", cv2.cvtColor(im, cv2.COLOR_RGB2BGR))
            startX += width
            index += 1
        return resultImg

    def loadAllCountriesInCurrentPlatform(self, excelPath, platform):
        workbook = xlrd.open_workbook(excelPath)
        sheet_num = 0
        sheet = workbook.sheet_by_index(sheet_num)
        rowcnt = sheet.nrows # sheet의 row수
        colcnt = sheet.ncols # sheet의 column수

        for row in range(rowcnt):
            # loadPlatform = sheet.cell_value(row, 0)  # 0번 Index가 Product-Platform
            loadPlatform = sheet.row_values(row)[sheet.row_values(0).index("Product-Platform")]
            if platform in loadPlatform:
                #loadCountry = sheet.cell_value(row, 4)  # 4번 Index가 Country name
                # loadCountry = sheet.cell_value(row, 5)  # 5번 Index가 Country code
                loadCountry = sheet.row_values(row)[sheet.row_values(0).index("Country Code")]
                loadCountry = loadCountry.strip()
                if loadCountry not in self.countries:
                    self.countries.append(loadCountry)

    def loadAllCountriesInCurrentPlatformForWO35(self, excelFolderPath, platform):
        files = os.listdir(excelFolderPath)
        for f in files:
            if platform in f:
                try:
                    excelPath = Path(Path(excelFolderPath) / Path(f))
                    workbook = xlrd.open_workbook(excelPath)
                    for sheet_num in range(4):
                        sheet = workbook.sheet_by_index(sheet_num)
                        rowcnt = sheet.nrows # sheet의 row수
                        colcnt = sheet.ncols # sheet의 column수

                        for row in range(rowcnt):
                            # loadCountry = sheet.cell_value(row, 4).strip()  # 5번 Index가 Country code
                            loadCountry = sheet.row_values(row)[sheet.row_values(0).index("Country Code")]
                            if loadCountry not in self.countries:
                                if loadCountry != "Country Code":
                                    self.countries.append(loadCountry)
                except IndexError:
                    print("현재 Excel의 sheet 수는 기존보다 적습니다.")
                    continue

    def parsingPlatformExcel(self, excelPath):
        workbook = xlrd.open_workbook(excelPath)
        sheet_num = 0
        sheet = workbook.sheet_by_index(sheet_num)
        rowcnt = sheet.nrows # sheet의 row수
        colcnt = sheet.ncols # sheet의 column수
        platforsmList = []

        for row in range(rowcnt):
            # loadPlatform = sheet.cell_value(row, 0)  # 0번 Index가 Product-Platform
            loadPlatform = sheet.row_values(row)[sheet.row_values(0).index("Product-Platform")]
            platformStr = loadPlatform.split(',')
            for plat in platformStr:
                stripPlat = plat.strip()
                if stripPlat not in platforsmList:
                    platforsmList.append(stripPlat)

        return platforsmList

    def parsingOrderingExcel(self, excelPath, platform, countryCode, excelVer):
        strAppIds = {}
        if excelVer == EXCEL_VERSION[0]: #4.0
            workbook = xlrd.open_workbook(excelPath)
            sheet_num = 0
            sheet = workbook.sheet_by_index(sheet_num)
            rowcnt = sheet.nrows # sheet의 row수
            colcnt = sheet.ncols # sheet의 column수

            # 현재 platform에 맞는 rows만 가져와야함
            # Order Type이 HOME인것만 남겨둠
            # Country Code에 일치하는 것만 남겨둠
            for row in range(rowcnt):
                # loadPlatform = sheet.cell_value(row, 0) # 0번 Index가 Product-Platform
                # loadCountryCode = sheet.cell_value(row, 5) # 5번 Index가 Country Code
                # loadOrderType = sheet.cell_value(row, 6) # 6번 Index가 Order Type
                loadPlatform = sheet.row_values(row)[sheet.row_values(0).index("Product-Platform")]
                loadCountryCode = sheet.row_values(row)[sheet.row_values(0).index("Country Code")]
                loadOrderType = sheet.row_values(row)[sheet.row_values(0).index("Order Type")]
                if platform in loadPlatform and ORDER_TYPE == loadOrderType\
                and countryCode == loadCountryCode:
                    # loadOrderNumber = sheet.cell_value(row, 10) # 10번 Index가 Order Number
                    loadOrderNumber = sheet.row_values(row)[sheet.row_values(0).index("Order Number")]
                    # strAppIds[int(loadOrderNumber)] = sheet.cell_value(row, 9) # 10번 Index가 Str App Id
                    strAppIds[int(loadOrderNumber)] = sheet.row_values(row)[sheet.row_values(0).index("Str App Id")]
        else:
            files = os.listdir(excelPath)
            for f in files:
                if platform in f:
                    workbookPath = Path(Path(excelPath) / Path(f))
                    workbook = xlrd.open_workbook(workbookPath)
                    for sheet_num in range(4):
                        try:
                            sheet = workbook.sheet_by_index(sheet_num)
                            rowcnt = sheet.nrows # sheet의 row수
                            colcnt = sheet.ncols # sheet의 column수
                            for row in range(rowcnt):
                                # loadCountryCode = sheet.cell_value(row, 4).strip() # 4번 Index가 Country Code
                                loadCountryCode = sheet.row_values(row)[sheet.row_values(0).index("Country Code")]
                                if countryCode == loadCountryCode:
                                    # loadOrderNumber = sheet.cell_value(row, 5).strip() # 5번 Index가 Order Number
                                    loadOrderNumber = sheet.row_values(row)[sheet.row_values(0).index("Order Number")]
                                    if loadOrderNumber != '-':
                                        # strAppIds[int(loadOrderNumber)] = sheet.cell_value(row, 9) # 9번 Index가 Str App Id
                                        strAppIds[int(loadOrderNumber)] = sheet.row_values(row)[sheet.row_values(0).index("Str App Id")]
                        except IndexError:
                            print("현재 Excel의 sheet 수는 기존보다 적습니다.")
                            continue
        # Str App Id를 받아옴
        '''
        for row in activateRows:
            loadOrderNumber = sheet.cell_value(row, 10) # 10번 Index가 Order Number
            strAppIds[loadOrderNumber] = sheet.cell_value(row, 9) # 10번 Index가 Str App Id
        '''
        strAppIds = collections.OrderedDict(sorted(strAppIds.items()))
        return strAppIds

    def copyAllIcons(self, zipPath, loadPath):
        ### TBD : 나중에 Path 다 받아와야함
        #zipPath = "C:/Program Files/7-Zip"
        folderPath = loadPath
        ipkList = []
        ipkName = []

        for files in os.listdir(folderPath):
            if files.find('.ipk') != -1:
                ipkList.append(files)

        currPath = os.getcwd()
        os.chdir(zipPath)
        for ipk in ipkList:
            try:
                temp = ipk.split('.')
                ipkName.append(temp[0])
                for dir in os.listdir(folderPath):
                    if dir == temp[0]:
                        break;
                else:
                    os.system('7z x ' + folderPath + '\\'+ipk + ' -o'+folderPath+'\\'+temp[0])
                    os.system('7z x ' + folderPath + '\\'+temp[0] + '\\data.tar.gz' + ' -o'+folderPath+'\\'+temp[0]+'\\data.tar')
                    os.system('7z x ' + folderPath + '\\'+temp[0] + '\\data.tar\\data.tar' + ' -o'+folderPath+'\\'+temp[0]+'\\data.tar\\data')
            except:
                print('fail to unzip '+temp)

        os.chdir(currPath)
        self.copyIcons(ipkName, loadPath)

    def copyIcons(self, ipkName, loadPath):
        dstDir = loadPath+'/__serverResource'
        try:
            os.mkdir(dstDir)
        except:
            print('__serverResource is already exist!')

        for value in ipkName:
            path = loadPath+'/' + value + '/data.tar/data/usr/palm/applications/'
            forders = os.listdir(path)
            for forder in forders:
                appForderPath = path + forder
                appinfoFile = open(appForderPath+'/appinfo.json','r',encoding="utf8")
                appinfo = json.loads(appinfoFile.read())
                appinfoFile.close()
                try:
                    dstPath = dstDir+'/'+appinfo['id']
                    os.mkdir(dstPath)
                    # TBD : 받은 리소스에 mediumLargeIcon.png 가 있으면 이걸로 바꾸기
                    iconFileName = appinfo['icon']
                    targetIconPath = appForderPath + '/' + iconFileName
                    shutil.copy(targetIconPath, dstPath+"/icon.png")
                except:
                    print(forder,'is already exist!')

    def readIcons(self, loadPath, strAppIds):
        # cpstub-apps 폴더에서 file list 받아옴
        # file list loop하며 strAppId와 일치하는 폴더 아래의 icon.png를 read해서 순서대로 배열 저장
        # 배열 return
        try:
            imgs = {}
            loadPath = loadPath+"/__serverResource"
            filenames = os.listdir(loadPath)
            index = 0
            includeCheck = False
            extenstions = ['png','jpg','jpeg','gif','bmp']
            nonImg = cv2.imread(str(Path(NONE_ICON_PATH)), cv2.IMREAD_UNCHANGED)
            nonImg = cv2.cvtColor(nonImg, cv2.COLOR_BGR2RGB)
            for strIDKey in strAppIds.keys():
                for filename in filenames:
                    if strAppIds[strIDKey] == filename:
                        filePath = os.path.join(loadPath, filename)
                        if os.path.isdir(filePath):
                            iconPath = os.path.join(filePath, "mediumLargeIcon.png")
                            if os.path.exists(iconPath):
                                img = cv2.imread(str(Path(iconPath)), cv2.IMREAD_UNCHANGED)
                                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                imgs[index] = (iconPath, img)
                                index += 1
                                includeCheck = True
                            else:
                                print("!!!!!!!!!!!!!!!!! Can't find mediumLargeIcon.png !!!!!!!!!!!!!!!!!!!!!!")
                                filePathNames = os.listdir(filePath)
                                check = False
                                for f in filePathNames:
                                    f_ex = f.split(".")[-1]
                                    if f_ex in extenstions:
                                        iconPath = str(Path(filePath) / f)
                                        #iconPath = os.path.join(filePath, f)
                                        img = cv2.imread(iconPath, cv2.IMREAD_UNCHANGED)
                                        if type(img) is None:
                                            print("img is None!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                                            imgs[index] = (NONE_ICON_PATH, nonImg)
                                            index += 1
                                        else:
                                            height, width, _ = img.shape
                                            if height == width == 115:
                                            # if height == width == 130:
                                                img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
                                                imgs[index] = (iconPath, img)
                                                index += 1
                                                check = True
                                                break
                                if check == False:
                                    print(strIDKey,"is not exists!!!!!")
                                    imgs[index] = (NONE_ICON_PATH, nonImg)
                                    index += 1
                                includeCheck = True
                        else:
                            print(filePath, "is not a dir!")
                            imgs[index] = (NONE_ICON_PATH, nonImg)
                            index += 1
                        break
                if includeCheck == False:
                    print("index",strAppIds[strIDKey],"can't find!!!!!")
                    imgs[index] = (NONE_ICON_PATH, nonImg)
                    index += 1
            return imgs
        except Exception as e:
            print('*** readIcons, Caught exception: %s: %s' % (e.__class__, e))

    def getImgPyramid(self, targetImg, min_range=0.8, max_range=1.5, gap=0.05):
        tmp = targetImg.copy()
        pyramid = []
        pyramid.append(tmp)
        rate = min_range
        while rate <= max_range:
            tmp1 = cv2.resize(tmp, None, fx=rate, fy=rate)
            pyramid.append(tmp1)
            rate += gap

        return pyramid

    # iconImage가 baseImage에 포함되어있는지를 확인하는 함수
    def checkImageIncluded(self, baseImg, iconImg, matchingValue=1.0):
        global logFile, logFileContents
        #baseImg = cv2.imread(baseImgPath, cv2.IMREAD_COLOR)
        #iconImg = cv2.imread(iconImagePath, cv2.IMREAD_COLOR)

        baseImgCopy = baseImg.copy()
        #res = cv2.matchTemplate(baseImgCopy, iconImg, cv2.TM_CCOEFF_NORMED)
        res = cv2.matchTemplate(baseImgCopy, iconImg, cv2.TM_CCOEFF_NORMED)
        ### temp
        max = np.max(res)
        print("######################## max = ",max)
        self.logFileContents.append("max = "+str(max)+"\n")

        loc = np.where(res > matchingValue)
        count = 0
        for i in zip(*loc[::-1]):
            count += 1
        if count>0:
            return True
        else:
            return False

    def checkColorPixcel(self, base, icon):
        NG_case = []
        height, width, _ = icon.shape
        for _x in range(width):
            for _y in range(height):
                if abs(icon[_x][_y][0] - base[_x][_y][0]) > 15:
                    NG_case.append(("color", _x, _y, icon[_x][_y], base[_x][_y]))
                if abs(icon[_x][_y][1] - base[_x][_y][1]) > 15:
                    NG_case.append(("color", _x, _y, icon[_x][_y], base[_x][_y]))
                if abs(icon[_x][_y][2] - base[_x][_y][2]) > 15:
                    NG_case.append(("color", _x, _y, icon[_x][_y], base[_x][_y]))

        return NG_case

    def matchingByPixcel(self, baseImg, iconImg, matchingValue=1.0):
        global logFile, logFileContents
        #baseImg = cv2.imread(baseImgPath, cv2.IMREAD_COLOR)
        #iconImg = cv2.imread(iconImagePath, cv2.IMREAD_COLOR)

        baseImgCopy = baseImg.copy()
        #res = cv2.matchTemplate(baseImgCopy, iconImg, cv2.TM_CCOEFF_NORMED)
        print("!!!!!!!!!!!!!!!!!! baseImgCopy size == ",baseImgCopy.shape)
        print("!!!!!!!!!!!!!!!!!! iconImg size == ",iconImg.shape)
        res = cv2.matchTemplate(baseImgCopy, iconImg, cv2.TM_CCOEFF_NORMED)
        ### temp
        max = np.max(res)
        print("######################## max = ",max)
        self.logFileContents.append("max = "+str(max)+"\n")
        print("update logFileContents,",logFileContents)

        min_val, max_val, min_loc, max_loc = cv2.minMaxLoc(res)
        top_left = max_loc
        height, width, _ = iconImg.shape
        bottom_right = (top_left[0]+width, top_left[1]+height)
        baseImgCrop = baseImgCopy[top_left[1]:bottom_right[1], top_left[0]:bottom_right[0]]
        # cv2.imshow('test',baseImgCrop)
        # cv2.imshow('test2',iconImg)
        # cv2.waitKey(0)
        NG_pixcel = []
        icon_gray = cv2.cvtColor(iconImg, cv2.COLOR_BGR2GRAY)
        base_gray = cv2.cvtColor(baseImgCrop, cv2.COLOR_BGR2GRAY)
        for idx_x in range(width):
            for idx_y in range(height):
                if (icon_gray[idx_y][idx_x] != base_gray[idx_y][idx_x]).all():
                    NG_pixcel.append(("shape", idx_x, idx_y, icon_gray[idx_y][idx_x], base_gray[idx_y][idx_x]))

        color_result = self.checkColorPixcel(baseImgCrop, iconImg)
        NG_pixcel.extend(color_result)

        if len(NG_pixcel) > 0:
            if not os.path.exists("matching_value.txt"):
                file=open("matching_value.txt", "w")
            else:
                file=open("matching_value.txt", "a")
            file.write("="*100+'\n')
            for pix in NG_pixcel:
                print(pix)
                file.write(str(pix)+'\n')
            file.write("="*100+'\n')
            file.close()

            return False
        else:
            return True


    def doMatching(self, excelPath, platform, loadIconPath, captureFileName, excelVer, logFileCnt, matchingValue=100.0):
        if self.logFileContents == None:
            self.logFileContents = logFileCnt
        countryCode = captureFileName.split('(')[1].split(',')[0] # get Country code from captureFileName
        countryName = captureFileName.strip('.png').strip()
        strAppIds = self.parsingOrderingExcel(excelPath, platform, countryCode, excelVer)
        ngIcons = []
        #################### TBD : 여기서 일단 현재 국가의 오더링을 소스로 비교
        if strAppIds != None:
            # iconImage = (iconPath, img)
            iconImgs = self.readIcons(loadIconPath, strAppIds) # 0부터 시작
            cpImgs = self.loadCaptureAndCrop(captureFileName) # 0부터 시작
            preResultCondition = True

            for index in range(len(iconImgs)):
                resCondition = False
                self.logFileContents.append("iconImgs[index][0] == "+iconImgs[index][0]+"\n")

                resCondition = self.checkImageIncluded(cpImgs[index], iconImgs[index][1], matchingValue/100)
                if resCondition == False:
                    # index도 0부터 시작
                    ngIcons.append([index, cpImgs[index], iconImgs[index]])
                # List 중 하나라도 False가 있을 경우 전체 False
                self.logFileContents.append("resCondition == "+str(resCondition)+"\n")
                preResultCondition = preResultCondition and resCondition
            if preResultCondition:
                return [countryName+":"+ORDERING_FILTER[1], None]
            else:
                return [countryName+":"+ORDERING_FILTER[2], ngIcons]
        else:
            return None
