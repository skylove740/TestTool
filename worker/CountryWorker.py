from xml.etree import ElementTree
import json
import traceback
from model.CountryModel import *
from model.TvModel import *
from common.Constants import *
from common.TvController import *
import common.LunaCommands as LunaCommands
import os, time

KEY_AREA_OPTION = 'com.webos.app.factorywin.areaOption'
KEY_CONFIG = 'configs'
KEY_LANGUAGE_COUNTRY = 'tv.model.languageCountrySel'
KEY_HW_SETTING = 'tv.model.hwSettingGroup'
KEY_CONTINENT_INDX = 'tv.model.continentIndx'
KEY = 'key'
KEY_VALUE = 'value'
KEY_MAX = 'max'
KEY_MIN = 'min'
KEY_SCALE = 'scale'
KEY_SETTING = 'settings'
KEY_SERVICE_COUNTRY_CODE3 = 'smartServiceCountryCode3'
KEY_COUNTRY_GROUP = 'contiLangCountrySel'

class CountryWorker:

    def __init__(self):
        print('CountryWorker.init')
        self.tvController = TvController()

    def inquery(self, ip, platform, displayType, hasGroup):
        print('inquery : ' + platform)
        result = TvModel()
        self.countryModel = CountryModel()
        self.countryModel.platform = platform
        self.countryModel.displayType = displayType
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execCommand(LunaCommands.getAreaOptionValues(self))
            if result.resultType == RESULT_SUCCESS:
                try:
                    self.__loadAreaOption(result.resultValue)
                    if hasGroup:
                        result = self.__refreshSettingValueWithGroup(result)
                    else:
                        result = self.__refreshSettingValue(result)
                except Exception as e:
                    print('*** Caught exception: %s: %s' % (e.__class__, e))
                    traceback.print_exc()
                    result.message = MESSAGE_ERROR + str(e)
            self.tvController.disconnect()
        else:
            result.message = MESSAGE_TV_ABNORMAL

        return result

    def __loadAreaOption(self, areaOption):
        print('__loadAreaOption')
        areaOptionDict = json.loads(areaOption)
        self.countryModel.continentIndexList = []
        for data in areaOptionDict[KEY_CONFIG][KEY_AREA_OPTION]:
            if data[KEY] == KEY_CONTINENT_INDX:
                num = data[KEY_VALUE][KEY_MIN]
                while num <= data[KEY_VALUE][KEY_MAX]:
                    self.countryModel.continentIndexList.append(str(num))
                    num += data[KEY_VALUE][KEY_SCALE]
            if data[KEY] == KEY_LANGUAGE_COUNTRY:
                self.countryModel.languageCountryList = data[KEY_VALUE]
                self.countryModel.languageCountryList.sort()
            if data[KEY] == KEY_HW_SETTING:
                self.countryModel.hwSettingsList = data[KEY_VALUE]
                self.countryModel.hwSettingsList.sort()

    def __refreshSettingValueWithGroup(self, result):
        result = self.tvController.execCommand(LunaCommands.getCurrentAreaOption(self))
        if result.resultType == RESULT_SUCCESS:
            self.__loadCurrentAreaOption(result.resultValue)
            result = self.tvController.execCommand(LunaCommands.getLanguageCountry(self))
            if result.resultType == RESULT_SUCCESS:
                self.__loadServiceCountryFileWithGroup(result.resultValue)
                result = self.tvController.execCommand(LunaCommands.getCountry(self))
                if result.resultType == RESULT_SUCCESS:
                    self.__loadCurrentCountry(result.resultValue)

        return result

    def __refreshSettingValue(self, result):
        result = self.tvController.execCommand(LunaCommands.getCurrentAreaOption(self))
        if result.resultType == RESULT_SUCCESS:
            self.__loadCurrentAreaOption(result.resultValue)
            self.__loadServiceCountryFile()
            result = self.tvController.execCommand(LunaCommands.getCountry(self))
            if result.resultType == RESULT_SUCCESS:
                self.__loadCurrentCountry(result.resultValue)

        return result

    def __loadServiceCountries(self, languageCountry):
        countryGroup = languageCountryDic[languageCountry]
        if countryGroup in ('langSelNordic', 'langSelNonNordic'):
            countryGroup = 'EU'
        else:
            countryGroupLen = len(countryGroup)
            countryGroup = countryGroup[countryGroupLen-2:countryGroupLen]
        print('__loadServiceCountryFile : ' + countryGroup)
        fileName = PLATFROMS_FILE[self.countryModel.platform]
        schemaFile = os.path.join('.', 'resources', fileName)
        tree = ElementTree.parse(schemaFile)
        root = tree.getroot()
        self.countryModel.countryList = {}
        self.countryModel.countryNameList = []
        countryList = self.countryModel.countryList
        countryNameList = self.countryModel.countryNameList

        for group in root.getchildren():
            code = group.get(KEY_CODE)
            if code == countryGroup:
                for country in group.getchildren():
                    fullName = country.get(KEY_FULL_NAME)
                    code2 = country.get(KEY_CODE2)
                    code3 = country.get(KEY_CODE3)
                    countryName =  self.__makeCountryName(fullName, code2, code3, code)
                    countryList[countryName] = {KEY_CODE2:code2, KEY_CODE3:code3, KEY_FULL_NAME:fullName, KEY_CODE:code}
                    countryNameList.append(countryName)
        self.countryModel.countryNameList.sort()


    def __loadCurrentAreaOption(self, currentAreaOption):
        print('__loadCurrentAreaOption')
        currentAreaOptionDic = json.loads(currentAreaOption)
        self.countryModel.currentLanguageCountry = currentAreaOptionDic[KEY_CONFIG][KEY_LANGUAGE_COUNTRY]
        self.countryModel.currentHwSettings = currentAreaOptionDic[KEY_CONFIG][KEY_HW_SETTING]
        self.countryModel.currentContinentIndex = currentAreaOptionDic[KEY_CONFIG][KEY_CONTINENT_INDX]

    def __loadServiceCountryFileWithGroup(self, languageCountry):
        languageCountryDic = json.loads(languageCountry)
        countryGroup = languageCountryDic[KEY_COUNTRY_GROUP]
        if countryGroup in ('langSelNordic', 'langSelNonNordic'):
            countryGroup = 'EU'
        else:
            countryGroupLen = len(countryGroup)
            countryGroup = countryGroup[countryGroupLen-2:countryGroupLen]
        print('__loadServiceCountryFile : ' + countryGroup)
        fileName = PLATFROMS_FILE[self.countryModel.platform]
        schemaFile = os.path.join('.', 'resources', fileName)
        tree = ElementTree.parse(schemaFile)
        root = tree.getroot()
        self.countryModel.countryList = {}
        self.countryModel.countryNameList = []
        countryList = self.countryModel.countryList
        countryNameList = self.countryModel.countryNameList

        for group in root.getchildren():
            code = group.get(KEY_CODE)
            if code == countryGroup:
                for country in group.getchildren():
                    fullName = country.get(KEY_FULL_NAME)
                    code2 = country.get(KEY_CODE2)
                    code3 = country.get(KEY_CODE3)
                    countryName =  self.__makeCountryName(fullName, code2, code3)
                    countryList[countryName] = {KEY_CODE2:code2, KEY_CODE3:code3, KEY_FULL_NAME:fullName, KEY_CODE:code}
                    countryNameList.append(countryName)
        self.countryModel.countryNameList.sort()

    def __makeCountryName(self, fullName, code2, code3, code=''):
        displayType = self.countryModel.displayType
        if displayType == DISPLAY_TYPE_CODE2:
            return code2 + ' (' + fullName + ', ' + code3 +')'
        elif displayType == DISPLAY_TYPE_CODE3:
            return code3 + ' (' + fullName + ', ' + code2 +')'
        else:
            return fullName + ' (' + code2 + ', ' + code3 + ', ' + code +')' if code != '' else fullName + ' (' + code2 + ', ' + code3 +')'

    def __loadServiceCountryFile(self):
        print('__loadServiceCountryFileForAll')
        fileName = PLATFROMS_FILE[self.countryModel.platform]
        schemaFile = os.path.join('.', 'resources', fileName)
        tree = ElementTree.parse(schemaFile)
        root = tree.getroot()
        self.countryModel.countryList = {}
        self.countryModel.countryNameList = []
        countryList = self.countryModel.countryList
        countryNameList = self.countryModel.countryNameList

        for group in root.getchildren():
            code = group.get(KEY_CODE)
            for country in group.getchildren():
                fullName = country.get(KEY_FULL_NAME)
                code2 = country.get(KEY_CODE2)
                code3 = country.get(KEY_CODE3)
                countryName =  self.__makeCountryName(fullName, code2, code3, code)
                if not countryName in countryNameList:
                    countryList[countryName] = {KEY_CODE2:code2, KEY_CODE3:code3, KEY_FULL_NAME:fullName, KEY_CODE:code}
                    countryNameList.append(countryName)

        self.countryModel.countryNameList.sort()

    def __loadCurrentCountry(self, currentCountry):
        print('__loadCurrentCountry : ' + currentCountry)
        currentCountryDict = json.loads(currentCountry)
        self.countryModel.setCurrentCountryByCode3(currentCountryDict[KEY_SETTING][KEY_SERVICE_COUNTRY_CODE3])

    def changeAreaOption(self, ip, continentIndex, languageCountry, hwSettings):
        print('changeAreaOption : ' + languageCountry + ', ' + hwSettings)
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execCommand(LunaCommands.changeAreaOption(self, languageCountry, hwSettings, continentIndex))
            if result.resultType == RESULT_SUCCESS:
                try:
                    result = self.tvController.execCommand(LunaCommands.setContinentIndex(self, continentIndex))
                    if result.resultType == RESULT_SUCCESS:
                        result = self.tvController.execCommand(LunaCommands.setLanguageCountry(self, languageCountry))
                        if result.resultType == RESULT_SUCCESS:
                            result = self.tvController.execCommand(LunaCommands.setHwSettings(self, hwSettings))
                            if result.resultType == RESULT_SUCCESS:
                                result = self.__refreshSettingValueWithGroup(result)

                except Exception as e:
                    print('*** Caught exception: %s: %s' % (e.__class__, e))
                    traceback.print_exc()
                    result.message = MESSAGE_ERROR + str(e)
            self.tvController.disconnect()
        else:
            result.message = MESSAGE_TV_ABNORMAL

        return result

    def changeCountryWithGroup(self, ip, countryName):
        print('changeCountry : ' + countryName)
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if isConnected:
            country = self.countryModel.getCountryByName(countryName)
            if country != None:
                result = self.tvController.execCommand(LunaCommands.changeCountry(self, country[KEY_CODE2], country[KEY_CODE3]))

            self.tvController.disconnect()

        else:
            result.message = MESSAGE_TV_ABNORMAL

        return result

    def changeCountry(self, ip, countryName):
        print('changeCountryAndGroup : ' + countryName)
        result = TvModel()
        isConnected = self.tvController.connect(ip)
        if not isConnected:
            for i in range(7):
                isConnected = self.tvController.connect(ip)
                if isConnected:
                    break
                time.sleep(0.5)

        if isConnected:
            country = self.countryModel.getCountryByName(countryName)
            if country != None:
                self.countryModel.currentLanguageCountry = country[KEY_CODE]
                languageCountry = self.countryModel.currentLanguageCountry
                hwSettings = self.countryModel.currentHwSettings
                continentIndx = str(self.countryModel.currentContinentIndex)
                result = self.tvController.execCommand(LunaCommands.changeAreaOption(self, languageCountry, hwSettings, continentIndx))
                if result.resultType == RESULT_SUCCESS:
                    result = self.tvController.execCommand(LunaCommands.setLanguageCountry(self, languageCountry))
                    if result.resultType == RESULT_SUCCESS:
                        result = self.tvController.execCommand(LunaCommands.setHwSettings(self, hwSettings))
                        if result.resultType == RESULT_SUCCESS:
                            result = self.tvController.execCommand(LunaCommands.changeCountry(self, country[KEY_CODE2], country[KEY_CODE3]))
                            if result.resultType == RESULT_SUCCESS:
                                self.countryModel.currentCountry = countryName
            self.tvController.disconnect()

        else:
            result.message = MESSAGE_TV_ABNORMAL

        return result

    def checkIncludeCountryName(self, countryName, list):
        for item in list:
            if countryName in item:
                return True

        return False

    def devDVBorATSC(self):
        for country in self.countryModel.countryList.keys():
            code = self.countryModel.countryList[country]["code"]
            # 마지막 code이름만 제외한 Name
            countryName = ''.join(list(country)[:-4])

            if code == 'EU' or code == 'AJ' or code == 'JA' \
                or code == 'CS' or code == 'TW' or code == 'CO' \
                or code == 'CN' or code == 'HK' or code == 'IL' \
                or code == 'PA' or code == 'IR':
                if not self.checkIncludeCountryName(countryName, self.countryModel.DVBcountryList):
                    self.countryModel.DVBcountryList.append(country)
            elif code == 'JP':
                if not self.checkIncludeCountryName(countryName, self.countryModel.ARIBcountryList):
                    self.countryModel.ARIBcountryList.append(country)
            else:
                if not self.checkIncludeCountryName(countryName, self.countryModel.ATSCcountryList):
                    self.countryModel.ATSCcountryList.append(country)

    def downloadCountryFile(self, ip):
        print('downloadCountryFile : ')
        result = TvModel()

        #### TBD : 확인해보기
        self.countryModel = CountryModel()



        isConnected = self.tvController.connect(ip)
        if isConnected:
            result = self.tvController.execCommand(LunaCommands.getCountryListPath(self))
            if result.resultType == RESULT_SUCCESS:
                try:
                    res = json.loads(result.resultValue)
                    countryListPath = res['path'].strip()

                    # cmd = 'cp '+str(countryListPath)+' /tmp/'
                    # print("cmd === ",cmd)
                    # self.tvController.execSimpleCommand(cmd)
                    # time.sleep(0.3)
                    fileName = countryListPath.split('/')[-1]
                    if os.path.exists('download/'+fileName):
                        print("already existed!!!")
                    else:
                        result = self.tvController.downloadFile(countryListPath)
                        if result.resultType == RESULT_SUCCESS:
                            try:
                                # cmd = 'mv ../download/'+str(fileName)+' ../resources/'
                                # print("cmd === ",cmd)
                                # self.tvController.execSimpleCommand(cmd)
                                # time.sleep(0.3)
                                # if os.exist('../resources/'+fileName):
                                #     self.countryModel.countryFilePath = '../resources/'+fileName
                                if os.path.exists('download/'+fileName):
                                    self.countryModel.countryFilePath = 'download/'+fileName
                                else:
                                    print("error anything!!!")
                            except Exception as e:
                                print('*** Caught move exception: %s: %s' % (e.__class__, e))
                                traceback.print_exc()
                                result.message = MESSAGE_ERROR + str(e)
                        else:
                            print("download fail!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!!")
                except Exception as e:
                    print('*** Caught download exception: %s: %s' % (e.__class__, e))
                    traceback.print_exc()
                    result.message = MESSAGE_ERROR + str(e)
            self.tvController.disconnect()
        else:
            result.message = MESSAGE_TV_ABNORMAL

        return result
