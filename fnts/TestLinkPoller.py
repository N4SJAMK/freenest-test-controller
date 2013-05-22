#FNTC specific class for using the TestLink API
#added 12 Apr 2013
#author: Niko Korhonen

#from testlink.testlinkapi import TestlinkAPIClient
from TestLinkAPI import TestlinkAPIClient

class TestLinkPoller:
    def __init__(self, server_url, devKey):
        self.client = TestlinkAPIClient(server_url, devKey)


    def getCustomFields(self, data, log, conf):
        try:
            fields = []

            # polling some needed data from TL database using TestLink API
            projectinfo=(self.client.getProjects())
            log.msg('Got Testlink projects info:', projectinfo)
            '''
            {'testPlanID': '1420', 'executionMode': 'now', 'platformID': 0, 'testCaseID': '1959',
              'buildID': 5, 'testCaseVersionID': 1960, 'testCaseName': 'LoginAdminUser', 'testProjectID': '15'}
            '''


            #log.msg(len(projectinfo)) #just for debugging
            prefix = ""
            for project in projectinfo:
                if str(project['id']) == str(data['testProjectID']):
                    prefix = project['prefix']
                    break
                #else:
                #    log.msg(str(project)) #just for debugging
                #    log.msg(str(project['id']))
                #    log.msg(str(data['testProjectID']))
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


            tclist=(self.client.getTestCasesForTestPlan(data['buildID']))
            log.msg('Got all test cases for Plan')

            cfEngine = (self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "testingEngine", ""))
            log.msg('Got engine from custom field:', cfEngine)

            cfScripts = (self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "scriptNames", ""))
            log.msg('Got runnable tests from custom field:', cfScripts)
 
            runtimes = (self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "runTimes", ""))
            log.msg('Got runtimes from custom field:', runtimes)

            tolerance = (self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "tolerance", ""))
            log.msg('Got tolerance from custom field:', tolerance)

            tag=(self.client.getTestCaseCustomFieldDesignValue(prefix + "-" + tcidlist[i]['tc_external_id'], tcinfo[0]['version'], data['testProjectID'], "tag", ""))
            if tag == "":
                tag = "null"
                log.msg('No tags found, going to run the newest tests.')
            else:
                log.msg('Got version tag from custom field:', tag)

            fields.append(cfEngine)
            fields.append(cfScripts)
            fields.append(runtimes) 
            fields.append(tolerance)
            fields.append(tag)

        except Exception, e:
            #TestlinkAPI might be broken
            log.msg('Getting data with TestlinkAPI failed:', str(e))
            log.msg('Using default values')

            fields.append(conf['variables']['default_engine'])

            fields.append(data['testCaseName'] + ".txt")
            fields.append(conf['variables']['default_runtimes'])
            fields.append(conf['variables']['default_tolerance'])
            fields.append("null")

        return fields

# TestlinkAPIClient extensions

class TestlinkAPIClient(TestlinkAPIClient):
    pass
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

