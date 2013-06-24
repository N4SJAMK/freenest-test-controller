#FNTS specific class for using the TestLink API
#added 12 Apr 2013
#author: Niko Korhonen

from twisted.python import log
#from testlink.testlinkapi import TestlinkAPIClient
from TestLinkAPI import TestlinkAPIClient


class TestLinkPoller:
    def __init__(self, conf):
        self.conf = conf
        self.client = TestlinkAPIClientFNTS(conf['testlink']['serverURL'], conf['testlink']['devkey'])
        self.data = None
    
    def getCustomFields(self, data):

        self.data = data

        # polling some needed data from TL database using TestLink API
        projectinfo=(self.client.getProjects())
        log.msg('Got Testlink projects info:', projectinfo)

        prefix = ""
        for project in projectinfo:
            if str(project['id']) == str(data['testProjectID']):
                prefix = project['prefix']
                break
        if prefix == "":
            raise Exception("Correct project prefix was not found!")

        tcidlist=(self.client.getTestCaseIDByName(data['testCaseName']))
        log.msg('Got test case IDs from poll:', tcidlist)

        #this part needed to be more specific since TestLinkAPI returns all similarly named test cases from all projects
        i = 0
        while i < len(tcidlist):
            tcinfo=(self.client.getTestCase(prefix + "-" + tcidlist[i]['tc_external_id']))
            if 'full_tc_external_id' in tcinfo[0]:
                if tcinfo[0]['full_tc_external_id'] == (prefix + "-" + tcidlist[i]['tc_external_id']):
                    break
                else:
                    i = i + 1
            else:
                i = i + 1

        if 'full_tc_external_id' in tcinfo[0]:
            log.msg('Got test case information from poll:', tcinfo[0])
        else:
            raise Exception('Failed to find correct test case information')

        variables = []
        
        try:
            cfEngine = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "testingEngine", "")
            variables['engine'] = cfEngine
            log.msg('Got engine from custom field:', cfEngine)
        except:
            pass
        
        try:
            cfScripts = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "scriptNames", "")
            if cfScripts == "":
                raise Exception
            else:
                variables['scripts'] = cfScripts
                log.msg('Got runnable tests from custom field:', cfScripts)
        except Exception:
            pass
    
        try:
            cfRuntimes = int(self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "runTimes", ""))
            variables['runtimes'] = cfRuntimes
            log.msg('Got runtimes from custom field:', cfRuntimes)
        except ValueError:
            pass
    
        try:
            cfTolerance = int(self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "tolerance", ""))
            variables['tolerance'] = cfTolerance
            log.msg('Got tolerance from custom field:', cfTolerance)
        except ValueError:
            pass
        
        try: 
            cfTag = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "tag", "")
            variables['tag'] = cfTag
            log.msg('Got tag from custom field:', cfTag)
        except Exception:
            pass

        try: 
            confFile = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "configFile", "")
            variables['confFile'] = confFile
            log.msg('Got tag from custom field:', cfTag)
        except Exception:
            pass
            
        try:
            sutUrl = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "SutUrl", "")
            if sutUrl != ""
                variables['sutUrl'] = sutUrl
            else:
                raise Exception
        except Exception:
            pass

        return variables
            
# TestlinkAPIClient extensions

class TestlinkAPIClientFNTS(TestlinkAPIClient):

    def reportTCResult(self, tcid, tpid, status):
        """ reportTCResult :
        Report test result directly into Testlink
        """
        data = {"devKey":self.devKey, "testcaseid":tcid, "testplanid":tpid, "status":status, "guess":True}
        return self.server.tl.reportTCResult(data)

    def uploadTestCaseAttachment(self, internalid, title, description, filename, filetype, content):
        """ uploadTestCaseAttachment :
        Upload an attachment for the test case
        """
        data = {"devKey":self.devKey, "testcaseid":internalid, "title":title, "description":description, "filename":filename, "filetype":filetype, "content":content}
        return self.server.tl.uploadTestCaseAttachment(data)

