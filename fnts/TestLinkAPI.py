"""

TestLinkAPI - v0.20
Created on 5 nov. 2011
@author: Olivier Renault (admin@sqaopen.net)

Initially based on the James Stock testlink-api-python-client R7.
 

"""
import xmlrpclib


#FNTC specific class for using the TestLink API
#added 12 Apr 2013
#author: Niko Korhonen
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

            fields.append("robotEngine")
            fields.append(data['testCaseName'] + ".txt")
            fields.append(conf['variables']['default_runtimes'])
            fields.append(conf['variables']['default_tolerance'])
            fields.append("null")

        return fields


#Testlink API, can be used by any python script
class TestlinkAPIClient:        
  
    def __init__(self, server_url, devKey):
        self.server = xmlrpclib.Server(server_url)
        self.devKey = devKey
        self.stepsList = []

    #
    #  BUILT-IN API CALLS
    #
    
    def checkDevKey(self):
        """ checkDevKey :
        check if Developer Key exists   
        """
        argsAPI = {'devKey' : self.devKey}     
        return self.server.tl.checkDevKey(argsAPI)  
    
    def about(self):
        """ about :
        Gives basic information about the API    
        """
        return self.server.tl.about()
  
    def ping(self):
        """ ping :   
        """
        return self.server.tl.ping()

    def echo(self, message):
        return self.server.tl.repeat({'str': message})

    def doesUserExist(self, user):
        """ doesUserExist :
        Checks if a user name exists 
        """
        argsAPI = {'devKey' : self.devKey,
                'user':str(user)}   
        return self.server.tl.doesUserExist(argsAPI)
        
    def getBuildsForTestPlan(self, testplanid):
        """ getBuildsForTestPlan :
        Gets a list of builds within a test plan 
        """
        argsAPI = {'devKey' : self.devKey,
                'testplanid':str(testplanid)}   
        return self.server.tl.getBuildsForTestPlan(argsAPI)
	  	  
    def getFirstLevelTestSuitesForTestProject(self,testprojectid):
        """ getFirstLevelTestSuitesForTestProject :
        Get set of test suites AT TOP LEVEL of tree on a Test Project 
        """  
        argsAPI = {'devKey' : self.devKey,
                'testprojectid':str(testprojectid)}   
        return self.server.tl.getFirstLevelTestSuitesForTestProject(argsAPI)
        
    def getFullPath(self,nodeid):
        """ getFullPath :
        Gets full path from the given node till the top using 
        nodes_hierarchy_table 
        """
        argsAPI = {'devKey' : self.devKey,
                'nodeid':str(nodeid)}    
        return self.server.tl.getFullPath(argsAPI)

    def getLastExecutionResult(self, testplanid, testcaseid):
        """ getLastExecutionResult :
        Gets the result of LAST EXECUTION for a particular testcase on a 
        test plan, but WITHOUT checking for a particular build 
        """
        argsAPI = {'devKey' : self.devKey,
                'testplanid' : str(testplanid),
                'testcaseid' : str(testcaseid)}     
        return self.server.tl.getLastExecutionResult(argsAPI)

    def getLatestBuildForTestPlan(self, testplanid):
        """ getLastExecutionResult :
        Gets the latest build by choosing the maximum build id for a 
        specific test plan  
        """  
        argsAPI = {'devKey' : self.devKey,
                'testplanid':str(testplanid)}  
        return self.server.tl.getLatestBuildForTestPlan(argsAPI)

    def getProjects(self):
        """ getProjects: 
        Gets a list of all projects 
        """
        argsAPI = {'devKey' : self.devKey} 
        return self.server.tl.getProjects(argsAPI)

    def getProjectTestPlans(self, testprojectid):
        """ getLastExecutionResult :
        Gets a list of test plans within a project 
        """ 
        argsAPI = {'devKey' : self.devKey,
                'testprojectid':str(testprojectid)}  
        return self.server.tl.getProjectTestPlans(argsAPI)

    def getTestCase(self, testcaseexternalid):
        """ getTestCase :
        Gets test case specification using external or internal id  
        """
        argsAPI = {'devKey' : self.devKey,
                'testcaseexternalid' : str(testcaseexternalid)}  
        return self.server.tl.getTestCase(argsAPI)          

    def getTestCaseAttachments(self, testcaseid):
        """ getTestCaseAttachments :
        Gets attachments for specified test case  
        """
        argsAPI = {'devKey' : self.devKey,
                'testcaseID':str(testcaseid)}  
        return self.server.tl.getTestCaseAttachments(argsAPI)    

    def getTestCaseCustomFieldDesignValue(self, testcaseexternalid, version, 
                                     testprojectid, customfieldname, details):
        """ getTestCaseCustomFieldDesignValue :
        Gets value of a Custom Field with scope='design' for a given Test case  
        """
        argsAPI = {'devKey' : self.devKey,
                'testcaseexternalid' : str(testcaseexternalid),
                'version' : int(version),
                'testprojectid' : str(testprojectid),
                'customfieldname' : str(customfieldname),
                'details' : str(details)}
        return self.server.tl.getTestCaseCustomFieldDesignValue(argsAPI)                                                

    def getTestCaseIDByName(self, testCaseName):
        """ getTestCaseIDByName :
        Find a test case by its name   
        """    
        argsAPI = {'devKey' : self.devKey,
                'testcasename':str(testCaseName)}
        return self.server.tl.getTestCaseIDByName(argsAPI)
                                                   
    def getTestCasesForTestPlan(self, *args):
        """ getTestCasesForTestPlan :
        List test cases linked to a test plan    
            Mandatory parameters : testplanid
            Optional parameters : testcaseid, buildid, keywordid, keywords,
                executed, assignedto, executestatus, executiontype, getstepinfo 
        """        
        testplanid = args[0]
        argsAPI = {'devKey' : self.devKey,
                'testplanid' : str(testplanid)}
        if len(args)>1:
            params = args[1:] 
            for param in params:
              paramlist = param.split("=")                     
              argsAPI[paramlist[0]] = paramlist[1]  
        return self.server.tl.getTestCasesForTestPlan(argsAPI)   
            
    def getTestCasesForTestSuite(self, testsuiteid, deep, details):
        """ getTestCasesForTestSuite :
        List test cases within a test suite    
        """        
        argsAPI = {'devKey' : self.devKey,
                'testsuiteid' : str(testsuiteid),
                'deep' : str(deep),
                'details' : str(details)}                  
        return self.server.tl.getTestCasesForTestSuite(argsAPI)
  
    def getTestPlanByName(self, testprojectname, testplanname):
        """ getTestPlanByName :
        Gets info about target test project   
        """
        argsAPI = {'devKey' : self.devKey,
                'testprojectname' : str(testprojectname),
                'testplanname' : str(testplanname)}    
        return self.server.tl.getTestPlanByName(argsAPI)

    def getTestPlanPlatforms(self, testplanid):
        """ getTestPlanPlatforms :
        Returns the list of platforms associated to a given test plan    
        """
        argsAPI = {'devKey' : self.devKey,
                'testplanid' : str(testplanid)}    
        return self.server.tl.getTestPlanPlatforms(argsAPI)  

    def getTestProjectByName(self, testprojectname):
        """ getTestProjectByName :
        Gets info about target test project    
        """
        argsAPI = {'devKey' : self.devKey,
                'testprojectname' : str(testprojectname)}    
        return self.server.tl.getTestProjectByName(argsAPI)    
  
    def getTestSuiteByID(self, testsuiteid):
        """ getTestSuiteByID :
        Return a TestSuite by ID    
        """
        argsAPI = {'devKey' : self.devKey,
                'testsuiteid' : str(testsuiteid)}    
        return self.server.tl.getTestSuiteByID(argsAPI)   
  
    def getTestSuitesForTestPlan(self, testplanid):
        """ getTestSuitesForTestPlan :
        List test suites within a test plan alphabetically     
        """
        argsAPI = {'devKey' : self.devKey,
                'testplanid' : str(testplanid)}    
        return self.server.tl.getTestSuitesForTestPlan(argsAPI)  
        
    def getTestSuitesForTestSuite(self, testsuiteid):
        """ getTestSuitesForTestSuite :
        get list of TestSuites which are DIRECT children of a given TestSuite     
        """
        argsAPI = {'devKey' : self.devKey,
                'testsuiteid' : str(testsuiteid)}    
        return self.server.tl.getTestSuitesForTestSuite(argsAPI)        
        
    def getTotalsForTestPlan(self, testplanid):
        """ getTotalsForTestPlan :
        Gets the summarized results grouped by platform    
        """
        argsAPI = {'devKey' : self.devKey,
                'testplanid' : str(testplanid)}    
        return self.server.tl.getTotalsForTestPlan(argsAPI)  

    def createTestProject(self, *args):
        """ createTestProject :
        Create a test project  
            Mandatory parameters : testprojectname, testcaseprefix
            Optional parameters : notes, options, active, public
            Options: map of requirementsEnabled, testPriorityEnabled, 
                            automationEnabled, inventoryEnabled 
        """        
        testprojectname = args[0]
        testcaseprefix = args[1]
        options={}
        argsAPI = {'devKey' : self.devKey,
                   'testprojectname' : str(testprojectname), 
                   'testcaseprefix' : str(testcaseprefix)}
        if len(args)>2:
            params = args[2:] 
            for param in params:
              paramlist = param.split("=")
              if paramlist[0] == "options":
                  optionlist = paramlist[1].split(",")
                  for option in optionlist:
                      optiontuple = option.split(":")
                      options[optiontuple[0]] = optiontuple[1]  
                  argsAPI[paramlist[0]] = options   
              else:
                  argsAPI[paramlist[0]] = paramlist[1]  
        return self.server.tl.createTestProject(argsAPI)
        
    def createBuild(self, testplanid, buildname, buildnotes):
        """ createBuild :
        Creates a new build for a specific test plan     
        """
        argsAPI = {'devKey' : self.devKey,
                'testplanid' : str(testplanid),
                'buildname' : str(buildname),
                'buildnotes' : str(buildnotes)}                  
        return self.server.tl.createBuild(argsAPI)        
    
    def createTestPlan(self, *args):
        """ createTestPlan :
        Create a test plan 
            Mandatory parameters : testplanname, testprojectname
            Optional parameters : notes, active, public   
        """        
        testplanname = args[0]
        testprojectname = args[1]
        argsAPI = {'devKey' : self.devKey,
                'testplanname' : str(testplanname),
                'testprojectname' : str(testprojectname)}
        if len(args)>2:
            params = args[2:] 
            for param in params:
              paramlist = param.split("=")       
              argsAPI[paramlist[0]] = paramlist[1]  
        return self.server.tl.createTestPlan(argsAPI)    
 
    def createTestSuite(self, *args):
        """ createTestSuite :
        Create a test suite  
          Mandatory parameters : testprojectid, testsuitename, details
          Optional parameters : parentid, order, checkduplicatedname, 
                                actiononduplicatedname   
        """        
        argsAPI = {'devKey' : self.devKey,
                'testprojectid' : str(args[0]),
                'testsuitename' : str(args[1]),
                'details' : str(args[2])}
        if len(args)>3:
            params = args[3:] 
            for param in params:
              paramlist = param.split("=")       
              argsAPI[paramlist[0]] = paramlist[1]  
        return self.server.tl.createTestSuite(argsAPI)       

    def createTestCase(self, *args):
        """ createTestCase :
        Create a test case  
          Mandatory parameters : testcasename, testsuiteid, testprojectid, 
                                 authorlogin, summary, steps 
          Optional parameters : preconditions, importance, execution, order, 
                       internalid, checkduplicatedname, actiononduplicatedname   
        """
        argsAPI = {'devKey' : self.devKey,
                'testcasename' : str(args[0]),
                'testsuiteid' : str(args[1]),
                'testprojectid' : str(args[2]),
                'authorlogin' : str(args[3]),
                'summary' : str(args[4]),
                'steps' : self.stepsList}
        if len(args)>5:
            params = args[5:] 
            for param in params:
              paramlist = param.split("=")       
              argsAPI[paramlist[0]] = paramlist[1]
        ret = self.server.tl.createTestCase(argsAPI) 
        self.stepsList = []                    
        return ret 

    # added by Niko Korhonen
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

                        
    #
    #  ADDITIONAL FUNCTIONS
    #                                   

    def countProjects(self):
        """ countProjects :
        Count all the test project   
        """
        projects=TestlinkAPIClient.getProjects(self)
        return len(projects)
    
    def countTestPlans(self):
        """ countProjects :
        Count all the test plans   
        """
        projects=TestlinkAPIClient.getProjects(self)
        nbTP = 0
        for project in projects:
            ret = TestlinkAPIClient.getProjectTestPlans(self,project['id'])
            nbTP += len(ret)
        return nbTP

    def countTestSuites(self):
        """ countProjects :
        Count all the test suites   
        """
        projects=TestlinkAPIClient.getProjects(self)
        nbTS = 0
        for project in projects:
            TestPlans = TestlinkAPIClient.getProjectTestPlans(self,
                                                                 project['id'])
            for TestPlan in TestPlans:
                TestSuites = TestlinkAPIClient.getTestSuitesForTestPlan(self, 
                                                                TestPlan['id'])
                nbTS += len(TestSuites)
        return nbTS
               
    def countTestCasesTP(self):
        """ countProjects :
        Count all the test cases linked to a Test Plan   
        """
        projects=TestlinkAPIClient.getProjects(self)
        nbTC = 0
        for project in projects:
            TestPlans = TestlinkAPIClient.getProjectTestPlans(self, 
                                                                 project['id'])
            for TestPlan in TestPlans:
                TestCases = TestlinkAPIClient.getTestCasesForTestPlan(self,
                                                                TestPlan['id'])
                nbTC += len(TestCases)
        return nbTC
        
    def countTestCasesTS(self):
        """ countProjects :
        Count all the test cases linked to a Test Suite   
        """
        projects=TestlinkAPIClient.getProjects(self)
        nbTC = 0
        for project in projects:
            TestPlans = TestlinkAPIClient.getProjectTestPlans(self,
                                                                 project['id'])
            for TestPlan in TestPlans:
                TestSuites = TestlinkAPIClient.getTestSuitesForTestPlan(self,
                                                                TestPlan['id'])
                for TestSuite in TestSuites:
                    TestCases = TestlinkAPIClient.getTestCasesForTestSuite(self,
                                                 TestSuite['id'],'true','full')
                    for TestCase in TestCases:
                        nbTC += len(TestCases)
        return nbTC

    def countPlatforms(self):
        """ countPlatforms :
        Count all the Platforms  
        """
        projects=TestlinkAPIClient.getProjects(self)
        nbPlatforms = 0
        for project in projects:
            TestPlans = TestlinkAPIClient.getProjectTestPlans(self,
                                                                 project['id'])
            for TestPlan in TestPlans:
                Platforms = TestlinkAPIClient.getTestPlanPlatforms(self,
                                                                TestPlan['id'])
                nbPlatforms += len(Platforms)
        return nbPlatforms
        
    def countBuilds(self):
        """ countBuilds :
        Count all the Builds  
        """
        projects=TestlinkAPIClient.getProjects(self)
        nbBuilds = 0
        for project in projects:
            TestPlans = TestlinkAPIClient.getProjectTestPlans(self,
                                                                 project['id'])
            for TestPlan in TestPlans:
                Builds = TestlinkAPIClient.getBuildsForTestPlan(self,
                                                                TestPlan['id'])
                nbBuilds += len(Builds)
        return nbBuilds
        
    def listProjects(self):
        """ listProjects :
        Lists the Projects (display Name & ID)  
        """
        projects=TestlinkAPIClient.getProjects(self)
        for project in projects:
          print "Name: %s ID: %s " % (project['name'], project['id'])
  

    def initStep(self, actions, expected_results, execution_type):
        """ initStep :
        Initializes the list which stores the Steps of a Test Case to create  
        """
        self.stepsList = []
        list = {}
        list['step_number'] = '1'
        list['actions'] = actions
        list['expected_results'] = expected_results
        list['execution_type'] = str(execution_type)
        self.stepsList.append(list)
        return True
        
    def appendStep(self, actions, expected_results, execution_type):
        """ appendStep :
        Appends a step to the steps list  
        """
        list = {}
        list['step_number'] = str(len(self.stepsList)+1)
        list['actions'] = actions
        list['expected_results'] = expected_results
        list['execution_type'] = str(execution_type)
        self.stepsList.append(list)
        return True                
                                        
    def getProjectIDByName(self, projectName):   
	  	  projects=self.server.tl.getProjects({'devKey' : self.devKey})
	  	  for project in projects:
		  	    if (project['name'] == projectName): 
		    	  	  result = project['id']
		  	    else:
		    	  	  result = -1
	  	  return result
	  	  
     