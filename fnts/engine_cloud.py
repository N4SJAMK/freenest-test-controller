import math, socket, os, time 
from xml.etree import ElementTree as ET

from twisted.python import log

from Cloud import Cloud
from engine import Engine
from parabot import para

class cloudEngine(Engine):
    
    def __init__(self, conf, vScheduled):
        self.conf = conf
        self.scheduled = vScheduled
        self.cloud = None
        self.testdir = conf['general']['testingdirectory']
        self.vOutputdir = conf['general']['outputdirectory']
        self.result = -2
        self.skippedTests = []
    
    def cloudInit(self, cloud):
        if cloud is None:
            print("Initialize cloud API")
            cloud = Cloud(self.conf)
            cloud.getToken()
        self.cloud = cloud
        return cloud
        
    def run_tests(self, pTestCaseName, pTestList, pRuntimes, daemon):
        
        # Check that the tests exist
        
        foundtests = []
        tests = ""
        gridresult = ""
        
        for t in pTestList:
            if os.path.exists(self.testdir + t):
                if os.path.isdir(self.testdir + t):
                    for filename in os.listdir(self.testdir + t):
                        ext = ".txt", ".html", ".htm", ".xhtml", ".tsv", ".robot", ".rst", ".rest"
                        if filename.endswith(ext):
                            foundtests.append(t + filename)
                        else:
                            pass
                else:
                    foundtests.append(t)
            else:
                self.skippedTests.append(t)
                log.msg('Test not found, skipping', t)
        
        # adding found tests to the command
        
        if foundtests != []:
            for ft in foundtests:
                tests = tests + " " + self.testdir + ft
        else:
            log.msg('No runnable tests found!')
            gridresult = "No runnable tests found!"
            
            
        testlist = tests.split()

        # We want one node per test
        predictNodeNeed = len(foundtests)
        if predictNodeNeed == 0:
            predictNodeNeed = 1
        
        waiting = []
        nodesNeeded = 0
        nodesLaunching = 0
        nodesResuming = 0
        
        # Update current status
        self.cloud.InstanceManager.getNodeInstances()
        
        nodesAvailable = len(self.cloud.InstanceManager.active) - self.cloud.InstanceManager.busy
        
        #FIXME: turn this into thread safe function
        
        # See if we need to launch additional nodes
        if predictNodeNeed > nodesAvailable:
            nodesNeeded = predictNodeNeed - nodesAvailable
            
            # First resume suspended if any, then try to launch additional
            if len(self.cloud.InstanceManager.suspended) > 0:
                nodesNeedResumed = nodesNeeded - len(self.cloud.InstanceManager.suspended)
                if nodesNeedResumed < 0:
                    nodesLaunching = math.fabs(nodesNeedResumed)
                    nodesResuming = len(self.cloud.InstanceManager.suspended)
                elif nodesNeedResumed == 0:
                    nodesResuming = 1
                else:
                    nodesResuming = nodesNeedResumed
                    nodesLaunching = nodesNeeded - nodesResuming
            else:
                nodesLaunching = nodesNeeded
            
            # We can't exceed the maximum nodes allowed
            if (nodesLaunching + self.cloud.InstanceManager.instances) > self.conf['cloud']['max_nodes']:
                log.msg("Would launch " + str(nodesLaunching) + " additional nodes, but it would exceed the configured maximum of " + str(self.conf['cloud']['max_nodes']))
                nodesLaunching = nodesLaunching - self.cloud.InstanceManager.instances
            
            
            if nodesResuming > 0:
                log.msg("Resuming " + str(nodesResuming) + " suspended nodes")
                for _n in range(0, nodesResuming):
                    instanceId = self.cloud.InstanceManager.suspended.pop()
                    r = self.cloud.InstanceManager.resumeInstance(instanceId)
                    waiting.append({"server":{"id": instanceId }}) 
            
            if nodesLaunching > 0:
                
                log.msg("Launching " + str(nodesLaunching) + " additional nodes")
                for _n in range(0, nodesLaunching):
                    r = self.cloud.InstanceManager.launchInstance()
                    waiting.append(r)
                    
            if len(waiting) > 0:
                #TODO: parallel poll
                for i in waiting:
                    retry = 12
                    instanceId = i['server']['id']
                    active = False
                    ready = False
                    
                    while not active:
                        if retry == 0:
                            raise Exception("Instance launch delayed")
                        time.sleep(5)
                        details = self.cloud.InstanceManager.getInstanceDetails(instanceId)
                        if details['server']['status'] == "ACTIVE":
                            active = True
                            log.msg(details['server']['nodeName'] + ' active')
                        else:
                            retry = retry - 1
                    
                    time.sleep(5) # not much to do while the system boots (grub wait and kernel load)
                    #TODO: set grub timeout to 0 in node image
                    
                    ip = ""
                    addresses = details['server']['addresses']
                    for address in addresses:
                        if addresses[address][0]['version'] == 4:
                                ip = addresses[address][0]['addr']
                                
                    s = socket.socket()
                    s.settimeout(3.0)
                    
                    while not ready:
                        if retry == 0:
                            raise Exception("Instance launch delayed")
                        time.sleep(5)
                        
                        try:
                            s.connect((ip, 5555))
                            s.close()
                            ready = True
                            log.msg(details['server']['nodeName'] + ' ready')
                        except Exception, e:
                            log.msg(str(e))
                            retry = retry - 1
                        
        
        # Begin to test
        
        i = 1
        if gridresult == "":
            while i <= pRuntimes:
                try:
                    # output directory, each test case has its own folder and if one doesn't exist, it will be created.
                    outputdir = self.vOutputdir + pTestCaseName + "/" + str(i) + "/" # own folder for each test run

                    if not os.path.exists(outputdir):
                        os.makedirs(outputdir)

                    log.msg('Sending tests for parabot:', tests)

                    parabot = para(self.conf, pTestCaseName, outputdir, self.testdir, testlist)
                    grid = parabot.run()
                    self.hosts = grid

                    # check and raise an exception if Robot fails to start
                    if grid[0] != "ok":
                        raise Exception(grid[0])
                    else:
                        gridresult = "ok"


                except Exception, e:
                    gridresult = str(e)
                    break   # only if robot fails to start or something is seriously wrong

                i = i + 1

        return gridresult

    def get_test_results(self, testCaseName, runTimes, tolerance):
        # Trying to get the results from output.xml, which is located in outputdir

        if self.result == -2:
            passes = [0, 0, 0]      # first number is critical tests, second one is total tests, the rest are individual tests
            fails = [0, 0, 0]       # more will be added while going through the results
            resultnotes = []        # for test notes, passed tests say PASSED, failed ones give an error message
            names_collected = False
            names = []


            i = 1
            while i <= runTimes:

                outputdir = self.vOutputdir + testCaseName + "/" + str(i) + "/"
                try:
                    outputfile = outputdir + "para_output.xml"
                    tree = ET.parse(outputfile)

                    o = 5
                    xmlpath = "suite/test"
                    foundtests = []
                    while o >= 0:  #instead of looking each path separately, we'll check the first five suites for test results
                        tests = tree.findall(xmlpath)
                        for test in tests:
                            foundtests.append(test)
                        xmlpath = "suite/" + xmlpath
                        o = o - 1

                    for test in foundtests:
                        resultnotes.append([])
                        if names_collected == False:
                            testattr = test.attrib
                            names.append(testattr['name'])
                    names_collected = True

                    # counting total and critical results
                    totalresults = tree.findall("statistics/total/stat")

                    for result in totalresults:
                        if result.text == "Critical Tests":
                            resultattr = result.attrib
                            passes[0] = passes[0] + int(resultattr['pass'])
                            fails[0] = fails[0] + int(resultattr['fail'])

                        elif result.text == "All Tests":
                            resultattr = result.attrib
                            passes[1] = passes[1] + int(resultattr['pass'])
                            fails[1] = fails[1] + int(resultattr['fail'])


                    # looping through all tests
                    j = 0

                    o = 5
                    xmlpath = "suite/test/status"
                    foundtestresults = []
                    while o >= 0:  #instead of looking each path separately, we'll check the first five suites for test results
                        testresults = tree.findall(xmlpath)
                        for test in testresults:
                            foundtestresults.append(test)
                        xmlpath = "suite/" + xmlpath
                        o = o - 1

                    for testresult in foundtestresults:
                        testattrlist = testresult.attrib

                        # counting the results extracted from the XML
                        strstatus = str(testattrlist['status'])

                        if strstatus == "PASS":
                            resultnotes[j].append("PASSED") # test result of the specific runtime and test
                            try:
                                passes[j+2] = passes[j+2] + 1   # adding result to existing place in the list
                            except IndexError:      # if the list doesn't have a place for the result, create a new one
                                passes.append(1)

                        if strstatus == "FAIL":
                            resultnotes[j].append(str(testresult.text))
                            try:
                                fails[j+2] = fails[j+2] + 1
                            except IndexError:
                                fails.append(1)

                        j = j + 1

                    log.msg('Got results from xml-files')

                except Exception, e:
                    # if something goes wrong, the message and blocked result are returned to Testlink
                    self.result = -1
                    self.notes = "\nXML ERROR: " + str(e)
                    log.msg('xml error:', str(e))

                i = i + 1


        if self.result == -2:
            # combining all the notes to be returned
            if fails[0] != 0:
                self.result = 0
                reason = "Not all critical tests were passed"
            else:
                if (passes[1] + fails[1]) != (passes[0] + fails[0]):
                    tests_total = (passes[1] - passes[0]) + (fails[1] - fails[0])
                    tests_passes = (passes[1] - passes[0]) * 100

                    if (tests_passes / tests_total) >= int(tolerance):
                        self.result = 1
                    else:
                        self.result = 0
                        reason = "Not enough tests were passed, only " + str(tests_passes / tests_total) + "% of non critical tests passed"
                else:
                    self.result = 1

            self.notes = "Tests were run " + str(runTimes) + " times\n\n"
            self.notes = self.notes + "Total tests passed: " + str(passes[1]) + ", failed: " + str(fails[1]) + "\n"
            self.notes = self.notes + "Critical tests passed: " + str(passes[0]) + ", failed: " + str(fails[0]) + "\n"
            self.notes = self.notes + "Non critical tests passed: " + str(passes[1] - passes[0]) + ", failed: " + str(fails[1] - fails[0]) + "\n"
            if self.result == 1:
                self.notes = self.notes + "Test set PASSED\n\n"
            else:
                self.notes = self.notes + "Test set FAILED: " + reason + "\n\n"

                if self.conf['log_collecting']['log_collecting_enabled'] == True:
                    # tests failed, so we need to fetch the logs to see what went wrong
                    self.hosts.pop(0)
                    self.logger.collect_logs(self.vOutputdir, testCaseName, self.hosts)
                    log.msg('Logs were fetched to', (self.vOutputdir + testCaseName))
                    
            # results for each test separately
            j = 0
            try:
                for test in resultnotes:
                    i = 1
                    self.notes = self.notes + names[j] + ":\n"
                    for run in test:
                        self.notes = self.notes + str(i) + ". " + str(run) + "\n"
                        i = i + 1
                    self.notes = self.notes + "\n"
                    j = j + 1
            except IndexError:
                pass
            
            if len(self.skippedTests) > 0:
                for t in self.skippedTests:
                    self.notes = self.notes + t + ": SKIPPED\n\n"

        # creating the list of results
        results = []
        results.append(self.result)
        results.append(self.notes)
        return results
