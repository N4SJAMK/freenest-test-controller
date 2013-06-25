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

        variables = {}

        # Set variables that _helperGetCustomFieldString function uses
        self._testCaseID = prefix + "-" + tcidlist[i]['tc_external_id']
        self._testCaseVersion = tcinfo[0]['version']
        self._testProjectID = data['testProjectID']
        
        #try:
        #    cfEngine = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "testingEngine", "")
        #    variables['engine'] = cfEngine
        #    log.msg('Got engine from custom field:', cfEngine)
        #except:
        #    pass
        engine = self._helperGetCustomFieldString("testingEngine")
        if engine:
            variables['engine'] = engine
        
        #try:
        #    cfScripts = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "scriptNames", "")
        #    if cfScripts == "":
        #        raise Exception
        #    else:
        #        variables['scripts'] = cfScripts
        #        log.msg('Got runnable tests from custom field:', cfScripts)
        #except Exception:
        #    pass
        scripts = self._helperGetCustomFieldString("scriptNames")
        if scripts:
            variables['scripts'] = scripts
    
        #try:
        #    cfRuntimes = int(self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "runTimes", ""))
        #    variables['runtimes'] = cfRuntimes
        #    log.msg('Got runtimes from custom field:', cfRuntimes)
        #except ValueError:
        #    pass
        runtimes = self._helperGetCustomFieldInt("runTimes")
        if runtimes:
            variables['runtimes'] = runtimes
    
        #try:
        #    cfTolerance = int(self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "tolerance", ""))
        #    variables['tolerance'] = cfTolerance
        #    log.msg('Got tolerance from custom field:', cfTolerance)
        #except ValueError:
        #    pass
        tolerance = self._helperGetCustomFieldInt("tolerance")
        if tolerance:
            variables['tolerance'] = tolerance
        
        #try: 
        #    cfTag = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "tag", "")
        #    variables['tag'] = cfTag
        #    log.msg('Got tag from custom field:', cfTag)
        #except Exception:
        #    pass
        tag = self._helperGetCustomFieldString("tag")
        if tag:
            variables['tag'] = tag

        #try: 
        #    confFile = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "configFile", "")
        #    variables['confFile'] = confFile
        #    log.msg('Got tag from custom field:', cfTag)
        #except Exception:
        #    pass
        confFile = self._helperGetCustomFieldString("configFile")
        if confFile:
            variables['confFile'] = confFile
            
        #try:
        #    sutUrl = self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "SutUrl", "")
        #    if isinstance(sutUrl, str) and sutUrl != "":
        #        variables['sutUrl'] = sutUrl
        #    else:
        #        raise Exception
        #except Exception:
        #    pass
        sutUrl = self._helperGetCustomFieldString("SutUrl")
        if sutUrl:
            variables['sutUrl'] = sutUrl

        return variables

    def _helperGetCustomFieldString(self, customField):
        try:
            value = self.client.getTestCaseCustomFieldDesignValue(self._testCaseID, self._testCaseVersion, self._testProjectID, customField, "")
            if isinstance(value, str) and value != "":
                return value
            else:
                return False
        except Exception:
            return False

    def _helperGetCustomFieldInt(self, customField):
        try:
            value = self.client.getTestCaseCustomFieldDesignValue(self._testCaseID, self._testCaseVersion, self._testProjectID, customField, "")
            if isinstance(value, str) and value != "":
                return int(value)
            else:
                return False
        except ValueError:
            raise Exception("Can't convert customfield " + customField + " to int")
        except Exception:
            return False
            
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

