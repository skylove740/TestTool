from jira.client import *
from model.TvModel import *
from common.Constants import *
import common.LunaCommands as LunaCommands
import traceback

# HLM Dev. Tracker
HLM_DEV_URL = "http://hlm.lge.com/issue"
# HLM Q Tracker
HLM_Q_URL = "http://hlm.lge.com/qi"

class JiraWorker:
    def __init__(self):
        print('JiraWorker.init')

    def attachFiles(self, id, passwd, issueId, fileList, isQissue):
        # create instance as jira.client.JIRA class with given url, account
        print('attachFiles : ')
        try:
            serverUrl = HLM_Q_URL if isQissue else HLM_DEV_URL
            tracker = JIRA(server=serverUrl, basic_auth=(id, passwd))
            issue = tracker.issue(issueId)
            for file in fileList:
                tracker.add_attachment(issue, file)
                print('attach file : ' + file)
            return RESULT_SUCCESS
        except Exception as e:
            print('*** Caught exception: %s: %s' % (e.__class__, e))
            traceback.print_exc()
            return str(e)
