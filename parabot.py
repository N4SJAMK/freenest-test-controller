# -*- coding: utf-8 -*-
#
# Script to execute test cases from one suite in parallel
# by thomas klein / 2009
# Edited by Niko Korhonen / 2012
#

# imports
from robot.running import TestSuite
from robot import utils
from robot.conf import settings
import os, glob
import subprocess
import time
from datetime import datetime
import sys
import getopt
import yaml
from twisted.python import log
from log_collector import logcollector



class para(): 
	def __init__(self, conf, testCaseName, outputdir, testdir, testlist):	
		# loading config file
                f = open('/home/adminuser/fntc/testlink_client.conf')
                conf = yaml.load(f)
                f.close
		
		self.log = log

		# save current time to calculate execution time at the end of the script
		self.startTime = datetime.now()
		
		# global vars
		self.suite_name = testCaseName 
		self.includeTags = [] 
		self.excludeTags = [] 
		self.para_tag = "parallel"
		self.testlist = testlist
		self.clientCwd = testdir
		self.logFolder = outputdir 
		self.forceSerialExecution = False
		self.baseDir = "./"
		
		self.conf = conf
		
		# reading variables from config
		self.max_parallel_tests = conf['grid']['max_parallel_tests']
		self.min_test_per_block = conf['grid']['min_tests_per_block']
		self.DYN_ARGS = conf['variables']['dyn_args']		

		self.log.msg('Parabot succesfully loaded')
		
	# Methods #####################################################################################################
	
	def splitTestsToBlocks(self, tests):
		""" Splits a list of tests into several small lists (blocks) and returns a list containing these lists.
		'MAX_PARALLEL_TESTS' and 'MIN_TESTS_PER_BLOCK' will be used as criteria for splitting the list. For 
		details see configuration hints in ParabotConfig.py.
		"""
		para_test_blocks = []
		number_of_blocks = -1
		if len(tests) / self.min_test_per_block > self.max_parallel_tests:
			number_of_blocks = self.max_parallel_tests
		else:
			number_of_blocks = len(tests) / self.min_test_per_block
		for i in range(0, number_of_blocks):
			para_test_blocks.append([])	
		current_block = 0
		for test in tests:
			block = current_block%number_of_blocks
			para_test_blocks[block].append(test)
			current_block = current_block+1
		return para_test_blocks
	
	def startPybot(self, name, tests, suite, conf, index, args=[]):
		""" Creates a pybot object, starts it and returns the object
		'name' is the name for the pybot (will be used for log outputs)
		'tests' is a list of tests to be executed by the pybot
		'suite' is the filename of the test suite containing the 'tests'
		'args' (optional) is a list of additional parameters passed to pybot
		"""
		pybot = Pybot(name, self.suite_name, self.logFolder, self.clientCwd)
		pybot.start(tests, suite, conf, index, args)
		return pybot
	
	def generateReportAndLog(self, xmlFiles, outputFile, reportFile, logFile):
		""" Calls RobotFrameworks rebot tool to generate Report and Log files from output.xml files
		'xmlFiles' is a list of output.xml files from jybot / pybot
		'reportFile' is the path+name of the report.html file to be written
		'logFile' is the path+name of the log.html file to be written
		the global variable 'suite_name' will be used a report title
		"""
		rebotCommand = "rebot --noncritical noncrit --log %s --report %s --output %s --reporttitle \"%s\" " % (logFile, reportFile, outputFile, self.suite_name)
		for file in xmlFiles:	
			rebotCommand = rebotCommand + "%s " % file
		rc = os.system(rebotCommand)
		return rc
	
	def getDynArgs(self, index):
		""" Reads the DYN_ARGS variable from the config file and parses it into a list of argument strings
		like --variable name:"value".
		This list can be passed to the Pybot start() method as args[] list.
		"""
		arglist = []
		for row in self.DYN_ARGS:
			valueIndex = index
			#log.msg('args in row:', row)
			if len(row) < 2:
				log.msg("Error reading DYN_ARGS: Row is invalid: %s. Row will be skipped!", row)
			else:
				varName = row[0]
				values = []
				i = 1
				while i < len(row):
					values.append(row[i])
					i = i + 1
				if valueIndex >= len(values):
					valueIndex = (len(values)-1) % valueIndex
				varValue = values[valueIndex]
				arglist.append("--variable %s:%s" % (varName, varValue))
		#log.msg('processed args:', arglist)
		return arglist

	def run(self):
		# generating two lists containing parallel and serial tests
		para_tests = []
		seri_tests = []
		retlist = []

		for file in self.testlist:
			suiteOps = settings.RobotSettings()
			suite = TestSuite(file, suiteOps)
		
			for test in suite.tests:
				# special treatment for tests without tags:
				# include them into serial execution as long as no include tags are defined
				if not test.tags and len(self.includeTags)==0:
			       		seri_tests.append(test.name)
				# tests with tags:
				# filter excluded tests (if any), then filter included tests (if any), then scan for
				# parallel keyword and assign to parallel / serial block	
				elif len(self.excludeTags)==0 or not test._matches_tag(self.excludeTags):
			       		if len(self.includeTags)==0 or test._matches_tag(self.includeTags):
						if test._matches_tag(self.para_tag):
			       	        		para_tests.append(test.name)
						else:
							seri_tests.append(test.name)
				#para_tests.append(test.name)

		
		# output serial test list
		serMessage = "Serial tests: "
		if len(seri_tests) == 0:
			serMessage = serMessage + "NONE"
		else:
			for test in seri_tests:
				serMessage = serMessage + test + " "
		self.log.msg(serMessage)    
		
		# splitting parallel tests into blocks 	
		para_test_blocks = self.splitTestsToBlocks(para_tests)
		
		# output parallel test list
		paraMessage = "Parallel tests: "
		for block in para_test_blocks:
			for test in block:
				paraMessage = paraMessage + test + " "
		if len(para_test_blocks) == 0:
			paraMessage = paraMessage + "NONE"
		self.log.msg(paraMessage)

		
		# starting parallel pybots
		i = 0;
		pybots = []
		for block in para_test_blocks:
			dynArgs = self.getDynArgs(i)
			self.log.msg(self.suite_name)
			pybots.append(self.startPybot("paraBlock_%s" % i, block, self.suite_name, self.conf, i, dynArgs))
			retlist.append(self.conf['general']['slave_user'] + "@" + self.conf['general']['slaves'][i])
			i = i + 1
			# delay start of next pybot
			time.sleep(5)
		
		# waiting for parallel tests to finish
		finished = False
		while not finished:
			time.sleep(10)
			message = "Finished: %s" % finished
			finished = True
			for pybot in pybots:
				message = "%s | %s: " % (message, pybot.name)
				if pybot.isRunning():
					finished = False
				else:	
					message = "%s%s" % (message, "DONE")
		self.log.msg(message)
		        
		self.log.msg("Parallel Tests finished ...")
		
		
		# running serial block	
		pybot = None
		if len(seri_tests) > 0:
			self.log.msg("Starting serial tests...")
			pybot = self.startPybot("serial_block", seri_tests, self.suite_name, self.conf, 0, self.getDynArgs(0))
			while pybot.isRunning():
				time.sleep(5)
		
			self.log.msg("Serial tests finished")
		
		
		# merging outputs to one report and log
		self.log.msg("Generating report and log")
		temp, suiteName = os.path.split(self.suite_name)
		output = self.logFolder + "para_output.xml" 
		report = "%s_Report.html" % os.path.join(self.logFolder, suiteName)
		log = "%s_Log.html" % os.path.join(self.logFolder, suiteName)
		outputXmls = []
		if pybot != None:
			outputXmls.append(os.path.join(self.logFolder, pybot.output))
		for pybot in pybots:
			outputXmls.append(os.path.join(self.logFolder, pybot.output))
		
		reportRC = self.generateReportAndLog(outputXmls, output, report, log)
		
		
		# delete XML output files after generating the report / log (if report generating 
		# returned zero)
		#if reportRC == 0:
		#    for outXML in outputXmls:
		#        os.remove(outXML)
		
		# calculating test execution time
		endTime = datetime.now()
		executionTime = endTime - self.startTime
		self.log.msg("Execution time:", executionTime)

		retlist.insert(0, "ok")

		return retlist

	
class Pybot():
	""" Helper class to interact with RobotFramework's pybot script to execute tests / test suites.    
	"""
	name = ""
	tests = []
	suite = ""
	args = []
	output = ""
	process = -1
	running = False
    
	def __init__(self, name, suite_name, logFolder, clientCwd):
		""" Constructor, creates the object and assigns the given 'name'.
		"""

		self.name = name
		self.suite_name = suite_name
		self.logFolder = logFolder
		self.clientCwd = clientCwd
		self.host = ""
		self.logger = logcollector()
		log.msg("Created pybot", name)

    
	def start(self, tests, suite, conf, index, args=[]):
		""" Starts the pybot script from RobotFramework executing the defined 'tests' from the given 'suite'.
		'tests' is a list of tests to be executed by the pybot
		'suite' is the filename of the test suite containing the 'tests'
		'args' (optional) is a list of additional parameters passed to pybot
		"""
		self.conf = conf
		self.tests = tests
		self.suite = suite
		self.args = args
		log.msg(self.suite_name)
		temp, suiteName = os.path.split(self.suite_name)
		self.output = self.suite_name + "_" + self.name + ".xml"

		#creating the command that is passed on for pybot
		pybotCommand = "pybot --name " + self.suite_name + " --noncritical noncrit "
		pybotCommand = pybotCommand + "--outputdir " + self.logFolder + " "  
		pybotCommand = pybotCommand + "--output " + self.output + " " 	#output.xml
                pybotCommand = pybotCommand + "--log NONE "     #logfiles disabled
                pybotCommand = pybotCommand + "--report NONE "  #reports disabled

		for arg in self.args:
                        pybotCommand = pybotCommand + arg + " "
		for test in self.tests:
			pybotCommand = pybotCommand + self.clientCwd + test + ".txt "

		pybotCmdList = pybotCommand.split()

		if conf['log_collecting']['log_collecting_enabled'] == True:
			# marking starting time
			self.host = self.conf['general']['slave_user'] + "@" + self.conf['general']['slaves'][index]
			self.logger.mark_logs(self.suite_name, self.host)
	
		log.msg("Starting pybot", self.name)
		log.msg(pybotCommand)
		self.running = True
		self.process = subprocess.Popen(pybotCmdList,cwd=self.logFolder,stdout=subprocess.PIPE,stderr=subprocess.PIPE)
	
	
	def isRunning(self):
		""" Polls the pybot subprocess to check if it's running. Will return true if the process is running.
		Returns false if the process hasn't been started or has finished already.
		"""
		if not self.running:
			return False
		elif self.process.poll() == 0 or self.process.returncode >= 0:
			if self.conf['log_collecting']['log_collecting_enabled'] == True:
				# marking ending time
				self.logger.mark_logs_end(self.suite_name, self.host)
			self.running = False
			return False
		else:
			return True
	
	
	def stop(self):
		""" Kills the pybot subprocess.
		"""
		os.system("taskkill /T /F /PID %s" % self.process.pid)
		self.running = False


