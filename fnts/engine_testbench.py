"""

   Copyright (C) 2000-2012, JAMK University of Applied Sciences

   This program is free software: you can redistribute it and/or modify
   it under the terms of the GNU General Public License as published by
   the Free Software Foundation, version 2.

   This program is distributed in the hope that it will be useful,
   but WITHOUT ANY WARRANTY; without even the implied warranty of
   MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
   GNU General Public License for more details.

   You should have received a copy of the GNU General Public License
   along with this program.  If not, see <http://www.gnu.org/licenses/>

"""

import base64, os, socket, subprocess, time
from datetime import datetime
from xml.etree import ElementTree as ET
from itertools import islice

from twisted.python import log

from engine import Engine
from TestLinkPoller import TestlinkAPIClientFNTS


class testbenchEngine(Engine):

    def __init__(self, conf, vScheduled):
        self.conf = conf
        self.devKey = conf['testlink']['devkey']
        self.dyn_args = conf['variables']['dyn_args']
        self.host = ""
        self.notes = ""
        self.result = -1
        self.robot_cmd = conf['robot']['command']
        self.scheduled = vScheduled
        self.testdir = conf['general']['testingdirectory']
        self.timestamp = ""
        self.vOutputdir = conf['general']['outputdirectory']
        self.SERVER_URL = conf['testlink']['serverURL']
        self.slaves = conf['general']['slaves']
        self.slave_user = conf['general']['slave_user']
        self.testlist = []
        log.msg( __name__ + ' loaded')


    def run_tests(self, testCaseName, testList, runTimes, daemon):
        # using subprocess for running testbench, cwd is the working directory
        # stdout is needed for the command to work, use subprocess.PIPE if you don't need the output
        # or a file object if you want the output to be written in a file.
        # Note that PIPEs can fill up the buffer and deadlock the system if there's too much output.

        log.msg(testCaseName, testList, runTimes)
        self.testlist = testList
        roboresult = ""
        foundtests = []
        listedtests = []
        testbenchresult = ""

        i = 0
        cmd = "mvn -Dtest="
        for test in testList:
            if i == 0:
                cmd = cmd + test
                i = 1
            else:
                cmd = cmd + "," + test    

        cmd = cmd + " test"
        #cmd = "mvn verify"
        cmdlist = cmd.split()

        log.msg('running tests', runTimes, 'times')
        
        i = 1
        if testbenchresult == "":
            while i <= runTimes:
                try:
                    # output directory, each test case has its own folder and if one doesn't exist, it will be created.
                    outputdir = "/home/adminuser/example/" + str(i) + "/" # own folder for each test run, the project name needs to be flexible
                    if not os.path.isdir(outputdir):
                        os.makedirs(outputdir)

                    outputfile = outputdir + "testbench_output.txt"
                    with open(outputfile, 'w') as fo:

                        log.msg('Running command:', cmd)

                        testbench = subprocess.Popen(cmdlist,cwd="/home/adminuser/example/",stdout=fo,stderr=fo).communicate()   #the project name needs to be flexible, maybe the same way as in RF engine?

                    
                    # move output files into different folder for processing
                    cpcmd = "cp TEST-com.vaadin.* " + outputdir
                    moveit = subprocess.Popen(cpcmd,cwd="/home/adminuser/example/target/failsafe-reports/",shell=True,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate() # flexibility needed once again
                    log.msg(str(moveit))

                    # check and raise an exception if testbench cannot be run, needs to be tweaked
                    #if outputfile == '':
                    #    raise Exception(str(testbench[1]))
                    #else:
                    testbenchresult = "ok"

                except Exception, e:
                    testbenchresult = str(e)

                    break   # only if testbench fails to start or something is seriously wrong

                i = i + 1


        return testbenchresult



    def get_test_results(self, testCaseName, runTimes, tolerance):
        # Trying to get the results from the output file
        #return ["1", "tests passed"] # just for testing

        if self.result == -1:
            run = 0
            failed = 0
            blocked = 0                                                                                                
            skipped = 0
            resultnotes = []        # for test notes, passed tests say PASSED, failed ones give an error message
            names = []


            i = 1
            while i <= runTimes:
                try:
                    # project name needs to be flexible, same with the whole path
                    outputdir = "/home/adminuser/example/" + str(i) + "/"
                    resultnotes.append([])
                    for test in self.testlist:
                        log.msg("getting results for " + test)
                        outputfile = outputdir + "TEST-com.vaadin.testbenchexample." + test + ".xml" #the project name needs to be dynamic...
                        tree = ET.parse(outputfile)
                    
                        xmlpath = "testcase"
                        tcases = tree.findall(xmlpath)
                        for tcase in tcases:
                        
                            if names == [] or tcase.get('name') not in names:
                                names.append(tcase.get('name'))

                            #errorpath = xmlpath + "/error"
                            error = tcase.findall("error")
                            #skippath = xmlpath + "/skipped"
                            skip = tcase.findall("skipped")
                            #failpath = xmlpath + "/failed"
                            fail = tcase.findall("failed")

                            if fail != []:
                                resultnotes[i - 1].append(fail[0].get('message'))
                                run = run + 1
                                failed = failed + 1
                            elif error != []:
                                if error[0].get('message'):
                                    resultnotes[i - 1].append(error[0].get('message'))
                                    run = run + 1
                                    blocked = blocked + 1
                            elif skip != []:
                                resultnotes[i - 1].append("SKIPPED")
                                run = run + 1
                                skipped = skipped + 1
                            else:
                                resultnotes[i - 1].append("PASSED")
                                run = run + 1

                except Exception, e:
                    # something went wrong while parsing the XML
                    log.msg("XML-ERROR: " + str(e))
                    log.msg(str(resultnotes))
                    self.result = -1
                    self.notes = "XML-ERROR: " + str(e)
                    return [self.result, self.notes]
                
                i = i + 1
        #log.msg(str(resultnotes))
                        


        if self.result == -1:
            try:
                log.msg(str(names) + "\n" + str(resultnotes))
                reason = " "
                tests_passed = run - (failed + blocked + skipped)

                if (tests_passed / run) * 100 < tolerance:
                    self.result = 0
                    reason = "Not enough tests were passed, only " + str((tests_passed / run) * 100) + "% of tests passed"
                else: 
                    self.result = 1


                self.notes = "The test set was run " + str(runTimes) + " times\n"
                self.notes = self.notes + "Total number of tests run: " + str(run) + "\n"
                self.notes = self.notes + "Failed tests: " + str(failed) + "\n"
                self.notes = self.notes + "Blocked tests: " + str(blocked) + "\n"
                self.notes = self.notes + "Skipped tests: " + str(skipped) + "\n"
                if self.result == 1:
                    self.notes = self.notes + "Test set PASSED\n\n"
                elif self.result == 0:
                    self.notes = self.notes + "Test set FAILED: " + reason + "\n\n"

                if blocked != 0:
                    self.notes = self.notes + "WARNING: Some tests were blocked due to errors!\n"
                if skipped != 0:
                    self.notes = self.notes + "WARNING: Some tests were skipped!\n"
                self.notes = self.notes + "\n"

                i = 0
                #results for each individual test
                for name in names:
                    j = 1
                    self.notes = self.notes + name + ":\n"
                    while j <= runTimes:
                        self.notes = self.notes + str(j) + ". " + resultnotes[j - 1][i] + "\n"
                        j = j + 1
                    self.notes = self.notes + "\n"
                    i = i + 1


            except Exception, e:
                log.msg("ERROR, something went wrong while compiling results: " + str(e))
                self.result = -1
                self.notes = "ERROR, something went wrong while compiling results: " + str(e)

        results = []
        results.append(self.result)
        results.append(self.notes)
        return results



    def upload_results(self, tcID, testCaseName, runTimes):
        # This method is used for packing the reports into one zip-package and uploading that to Testlink
        log.msg("Packaging results...")
        no_problems = 1
        self.tcID = tcID

        try:
            outputdir = self.vOutputdir + testCaseName + "/"

            t = datetime.now()
            time = t.strftime("%Y%m%d%H%M%S")
            filename = "results_" + time
            cmd = "zip -r " + filename + ".zip"

            i = 1
            while i <= runTimes:
                cmd = cmd + " " + str(i)
                i = i + 1

            cmdlist = cmd.split()

            # creating the zip-package
            package = subprocess.Popen(cmdlist,cwd=outputdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg("Files packed, output:", str(package))
        except Exception, e:
            log.msg("PACKAGING ERROR:", str(e))
            no_problems = 0


        if no_problems == 1:
            try:
                # base64 encoding the package so it doesn't get corrupted
                #base64.encode(open(outputdir + filename, 'rb'), open(outputdir + filename, 'w'))
                with open(outputdir + filename + ".zip", 'rb') as fin, open(outputdir + filename + "_b64.zip", 'w') as fout:
                    base64.encode(fin, fout)
            except Exception, e:
                log.msg("ENCODING ERROR:", str(e))
                no_problems = 0


            if no_problems == 1:
                try:
                    # uploading the package
                    client = TestlinkAPIClientFNTS(self.SERVER_URL, self.devKey)
                    up = client.uploadTestCaseAttachment(self.tcID, "results", "Reports from Robot Framework", filename + "_b64.zip", "zip", outputdir + filename + "_b64.zip")
                    log.msg(str(up))

                except Exception, e:
                    log.msg("UPLOADING ERROR:", str(e))
