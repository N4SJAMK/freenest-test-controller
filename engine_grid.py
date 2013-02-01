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

import socket
import base64
import TestLinkAPI
import sys, os, time
import subprocess

from twisted.python import log
import yaml

from datetime import datetime
from xml.etree import ElementTree as ET
from git_puller import gitpuller
from engine import Engine
from parabot import para


class gridEngine(Engine):

	def __init__(self, tcID, vOutputdir, testdir, vScheduled):
        	# loading grid specific configs
		f = open('/home/adminuser/fntc/testlink_client.conf')
        	conf = yaml.load(f)
        	f.close

        	self.robot_version = conf['robot']['version']
		self.devKey = conf['testlink']['devkey']
		self.SERVER_URL = conf['testlink']['serverURL'] + "lib/api/xmlrpc.php"

        	self.vOutputdir = vOutputdir
        	self.testdir = testdir

		self.scheduled = vScheduled
		self.notes = ""
		self.result = -2
		self.timestamp = ""

		self.tcID = tcID

		log.msg('Engine succesfully loaded')


    	def run_tests(self, testCaseName, testList, runTimes):
        	# using subprocess for running robot, cwd is the working directory
        	# stdout is needed for the command to work, use subprocess.PIPE if you don't need the output
        	# or f if you want the output to be written in a file.

		# building the command that is sent to RF
                # name is used so RF doesn't create a huge, nasty looking name for the test suite
		gridresult = ""
		foundtests = []

                tests = ""

		for t in testList: 			# checking that tests exist, so the script doesn't fail because of a missing test
                        if os.path.exists(self.testdir + t):
				if os.path.isdir(self.testdir + t):
					for dirname, dirnames, filenames in os.walk(self.testdir + t):
						# editing the 'dirnames' list will stop os.walk() from recursing into there.
                                                if '.git' in dirnames:
                                                        # don't go into any .git directories.
                                                        dirnames.remove('.git')

						# print path to all filenames.
						for filename in filenames:
							#should match to supported filetypes
							ext = ".txt", ".html", ".htm", ".xhtml", ".tsv", ".robot", ".rst", ".rest"
							if filename.endswith(ext):
								foundtests.append(filename)
							else:
								pass

				else:
					foundtests.append(t)


			else:
				log.msg('Skipping test', t)


		if foundtests != []:
			for ft in foundtests:                      # adding found tests to the command
				tests = tests + " " + self.testdir + ft
		else:	# and if no tests were found...
			log.msg('No runnable tests found!')
			gridresult = "No runnable tests found!"

	
		testlist = tests.split()

		i = 1
		if gridresult == "":
			while i <= runTimes:
        			try:
					# output directory, each test case has its own folder and if one doesn't exist, it will be created.
                			outputdir = self.vOutputdir + testCaseName + "/" + str(i) + "/"	# own folder for each test run

                			if not os.path.exists(outputdir):
                        			os.makedirs(outputdir)

                			log.msg('Sending tests for parabot: "%s"', tests)

                			#robo = subprocess.Popen(cmdlist,cwd=outputdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
					parabot = para(testCaseName, outputdir, self.testdir, testlist)
					grid = parabot.run()

					# check and raise an exception if Robot fails to start
                		        if grid != "ok":
                		               raise Exception(grid)
                		        else:
                		               gridresult = "ok"
						

				except Exception, e:
					gridresult = str(e)
					break	# only if robot fails to start or something is seriously wrong

				i = i + 1

		return gridresult
				


	def get_test_results(self, testCaseName, runTimes, tolerance):
		# Trying to get the results from output.xml, which is located in outputdir
		
		if self.result == -2:
			passes = [0, 0, 0]	# first number is critical tests, second one is total tests, the rest are individual tests
			fails = [0, 0, 0]	# more will be added while going through the results
			resultnotes = []	# for test notes, passed tests say PASSED, failed ones give an error message
			names_collected = False
			names = []


			i = 1
			while i <= runTimes:

				outputdir = self.vOutputdir + testCaseName + "/" + str(i) + "/"
                		try:
					outputfile = outputdir + "para_output.xml"
                        		tree = ET.parse(outputfile)

                        		tests = tree.findall("suite/suite/test")
					if tests == []:	# this happens in the case of single tests, so the path needs to be fixed
						tests = tree.findall("suite/test")
						if tests == []: # when there are more test suites
							tests = tree.findall("suite/suite/suite/test")

                        		for test in tests:
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
                        		testresults = tree.findall("suite/suite/test/status")
					j = 0

					if testresults == []:	# this happens in the case of single tests, so the path needs to be fixed
						testresults = tree.findall("suite/test/status")
						if testresults == []: # when there are more test suites 
							testresults = tree.findall("suite/suite/suite/test/status")

					for testresult in testresults:
                        			testattrlist = testresult.attrib

                        			# counting the results extracted from the XML
                        			strstatus = str(testattrlist['status'])

                        			if strstatus == "PASS":
                        			        resultnotes[j].append("PASSED")	# test result of the specific runtime and test 
							try:
								passes[j+2] = passes[j+2] + 1	# adding result to existing place in the list
							except IndexError:	# if the list doesn't have a place for the result, create a new one
								passes.append(1)
						
                        			if strstatus == "FAIL":
                        			        resultnotes[j].append(str(testresult.text))
							try:
                                                                fails[j+2] = fails[j+2] + 1
                                                        except IndexError:
                                                                fails.append(1)
					
						j = j + 1


                        		t = datetime.now()
                                        self.timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
					
					log.msg('Got results from xml-files')

            			except Exception, e:
                        		# if something goes wrong, the message and blocked result are returned to Testlink
                        		self.result = -1
                        		self.notes = "\nXML ERROR: " + str(e)
                        		t = datetime.now()
                        		self.timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
                        		log.msg('xml error: %s', str(e))
				
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

			# test reports
			# Here the original Robot Framework reports are made visible. A link is generated for each report, so the user only
			# needs to go to the address to see an accurate report about what has happened. 
			noproblems = 1
			"""try:
				#getting the ip from Google
				s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
				s.connect(("8.8.8.8",80))
				ip = s.getsockname()[0]
				s.close()

			except Exception, e:	# if the socket fails for some reason...
				log.msg("SOCKET ERROR: %s", str(e))
				noproblems = 0
				self.notes = self.notes + "Failed to create links for accurate reports. \nCheck the log for details.\n"
 

			if noproblems == 1:
				self.notes = self.notes + "See accurate reports here: \n"
				i = 1
				while i <= runTimes:
					self.notes = self.notes + str(i) + ". http://" + ip + self.vOutputdir.split('www')[1] + testCaseName + "/" + str(i) + "/report.html\n"
					i = i + 1
			"""		

		# creating the list of results
		results = []
        	results.append(self.result)
		results.append(self.notes)
		#results.append(self.scheduled)
		results.append(self.timestamp)

		log.msg('grid returns:', results)

		# pack and upload results
		#self.upload_results(testCaseName, runTimes)
		
        	return results


	def get_testcases(self):
        	puller = gitpuller()
        	gitresult = puller.pull(str(self.testdir))
        	if gitresult != "ok":
            		log.msg('git error:', gitresult)
			self.notes = gitresult
            		return False
		else:
			return True


	def upload_results(self, testCaseName, runTimes):
		# This method is used for packing the reports into one zip-package and uploading that to Testlink
		log.msg("Packaging results...")
		no_problems = 1

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
					client = TestLinkAPI.TestlinkAPIClient(self.SERVER_URL, self.devKey)
					up = client.uploadTestCaseAttachment(self.tcID, "results", "Reports from Robot Framework", filename + "_b64.zip", "zip", outputdir + filename + "_b64.zip")
					log.msg(str(up))

				except Exception, e:
					log.msg("UPLOADING ERROR:", str(e))	
	













