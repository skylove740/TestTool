KEY_COUNTRY_NAME = 'countryName'
KEY_FULL_NAME = 'fullname'
KEY_CODE = 'code'
KEY_CODE2 = 'code2'
KEY_CODE3 = 'code3'

class CountryModel:
    def __init__(self):
        self.continentIndexList = []
        self.languageCountryList = []
        self.hwSettingsList = []
        self.countryNameList = [] # Country Full Name을 저장하고 있음. 형식은 CountryName(2자리 code, 3자리 code)
        self.DVBcountryList = []
        self.ATSCcountryList = []
        self.ARIBcountryList = []
        self.countryList = {}
        self.currentLanguageCountry = ''
        self.currentHwSettings = ''
        self.currentContinentIndex = 0
        self.currentCountry = ''
        self.platform = ''
        self.displayType = ''
        self.countryFilePath = ''

    def setCurrentCountryByCode3(self, code3):
        for countryName in self.countryList.keys():
            if self.countryList[countryName][KEY_CODE3] == code3:
                self.currentCountry = countryName

    def getCountryByName(self, selectedCountryName):
        for countryName in self.countryList.keys():
            if countryName == selectedCountryName:
                return self.countryList[countryName]
        return None
