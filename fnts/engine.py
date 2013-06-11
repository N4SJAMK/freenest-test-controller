'''

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

'''

import sys, os, time
import subprocess

from datetime import datetime
from xml.etree import ElementTree as ET
from git_puller import gitpuller

from twisted.python import log

class Engine:

	'''
	    Default test handler engine
	    overwrite methods as needed
	'''

	def __init__(self, conf, scheduled):
		self.conf = conf
		#self.vOutputdir = vOutputdir
		#self.testdir = testdir
		self.scheduled = scheduled

	'''
		used when test case is actually run, gets all arguments given throught API
	'''
	def run_test_case(self,*args):
		pass

	'''
		used when main program requests test results
	'''
	
	def get_test_results(self,*args):
		''' -1 error, 0 fail, 1 pass'''
		return (-1, 'Engine class, not usable', t.strftime("%Y-%m-%d %H:%M:%S"))

	def get_testcases(self,*args):
		pass

	def init_environment(self,*args):
		return 1

	def teardown_environment(self,*args):
		return 1


class robotEngine(Engine):

	def __init__(self, vOutputdir, testdir, vScheduled):
		self.vOutputdir = vOutputdir
		self.testdir = testdir

		self.scheduled = vScheduled
		self.notes = ""
		self.result = ""
		self.timestamp = ""


	def run_test_case(self, testName):
		# using subprocess for running robot, cwd is the working directory
		# stdout is needed for the command to work, use subprocess.PIPE if you don't need the output
		# or f if you want the output to be written in a file.

		# getting testing scripts
		file = self.testdir + testName + ".txt"
		# output directory, each test case has its own folder and if one doesn't exist, it will be created.
		outputdir = self.vOutputdir + testName + "/"
		if not os.path.exists(outputdir):
			os.makedirs(outputdir)
		try:
			robo = subprocess.Popen(["pybot", file],cwd=outputdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			# check and raise an exception if Robot fails to start
			if str(robo[1]) != '':
				raise Exception(str(robo[1]))
			else:
				return "ok"

		except Exception as e:
			# if something goes wrong, the message and blocked result are returned to TestLink
			self.notes = "\nROBOT STARTUP ERROR: " + str(e)
			self.result = "b"
			t = datetime.now()
			self.timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
			return self.notes


	def get_test_results(self, testCaseName):
		# Trying to get the results from output.xml, which is located in outputdir
		outputdir = self.vOutputdir + testCaseName + "/"

		if self.result == "":
			try:
				outputfile = outputdir + "output.xml"
				tree = ET.parse(outputfile)
				messages = tree.findall("suite/test/kw/msg")
				# output messages visible in Testlink
				self.notes = "Output:\n"
				for i in messages:
					self.notes = self.notes + str(i.text) + "\n"
					p = tree.find("suite/test/status")
					resultlist = p.attrib
					# getting results from attributes extracted from XML
					strstatus = str(resultlist['status'])
					if strstatus == "PASS":
						self.result = "p"
					if strstatus == "FAIL":
						self.result = "f"
					self.timestamp = resultlist['endtime']

			except Exception, e:
				# if something goes wrong, the message and blocked result are returned to Testlink
				self.result = "b"
				self.notes = "\nXML ERROR: " + str(e)
				t = datetime.now()
				self.timestamp = t.strftime("%Y-%m-%d %H:%M:%S")

		results = []
		results.append(self.result)
		results.append(self.notes)
		results.append(self.scheduled)
		results.append(self.timestamp)

		self.result = ""
		self.notes = ""
		self.timestamp = ""

		return results


	def get_testcases(self):
		puller = gitpuller()
		gitresult = puller.pull(str(self.testdir))
		if gitresult != "ok":
			self.notes = gitresult
			return False
		else:
			return True
