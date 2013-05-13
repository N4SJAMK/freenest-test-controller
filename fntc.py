#! /usr/bin/python


"""
			Copyright (C) 2000-2012, JAMK University of Applied Sciences

			This program is free software: you can redistribute it and/or modify
			it under the terms of the GNU testlink Public License as published by
			the Free Software Foundation, version 2.

			This program is distributed in the hope that it will be useful,
			but WITHOUT ANY WARRANTY; without even the implied warranty of
			MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
			GNU General Public License for more details.

			You should have received a copy of the GNU General Public License
			along with this program.  If not, see <http://www.gnu.org/licenses/>

"""


#	import xmlrpclib
import TestLinkAPI
import sys, os, time
#	import subprocess
from twisted.python import log
import yaml
#from config import conf
from datetime import datetime
from xml.etree import ElementTree as ET
from git_puller import gitpuller
#from engine_robot import robotEngine
from engine import Engine

class fntc:
	def fntc_main(self, conf, cfengine, cfscripts, cfruntimes, cftolerance, cfoutputdir, cftestdir, cfscheduled, cftestname):

		engine_state = 1
		engine_defined = False
		cls = Engine
		engines = []
		results = []

		#path = "usr/share/fntcservice/engine/"	# will look for classes under the folder where this script is installed and under its subclasses
		path ="./"
		for root, dirs, files in os.walk(path):
			for name in files:
				if name.endswith(".py") and name.startswith("engine_"):
					path = os.path.join(root, name)
					modulename = path.rsplit('.', 1)[0].replace('/', '.')
					modulename = modulename.rsplit('.', 1)[1]
					try:
						log.msg("Checking module:", modulename)
			        		module = __import__(modulename)
			 
			        		# walk the dictionaries to get to the last one
			        		d = module.__dict__
			        		for m in modulename.split('.')[1:]:
			        		    	d = d[m].__dict__
			 
			        		#look through this dictionary for the correct class
			        		for key, entry in d.items():
			        		    	if key == cls.__name__:
			        		        	continue
							try:
								if issubclass(entry, cls):
									log.msg("Found engine:", key)
							    		engines.append(entry)
							except TypeError:
								#this happens when a non-type is passed in to issubclass. Non-types can't be instances, so they will be ignored.
								continue			
					except Exception, e:
						# if something goes wrong while loading modules, loading is aborted
						log.msg('Error while loading modules:', str(e))						

		if engines == []:
			log.msg('No test engines found')

		log.msg('engines found', engines)

		engine = 'none'
		engine_defined = False

		for e in engines:	#scroll through all found engines and find the correct one
			if e.__name__ == cfengine:
				engine = e(conf, cfengine, cfoutputdir, cftestdir, cfscheduled)
				engine_defined = True
				break

		if engine_defined == False:
			engine_state = -1
			t = datetime.now()
			timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
			log.msg('The correct testing engine was not found, tests cannot be run. Check the custom field value')
			#resultstring = "b@@The correct testing engine was not found, tests cannot be run. Check the custom field value.@@" + timestamp + "@@now"
			return (-1, 'Test engine was not found, check custom fields', timestamp)
		else:
			# getting testing scripts
			scriptlist = cfscripts.split()

			engine_state = engine.init_environment()

			if engine_state == 1:
				# if everything is ok, run the tests
				log.msg('Starting Engine')

				engineresult = engine.run_tests(cftestname, scriptlist, cfruntimes)
				if engineresult != "ok":
					t = datetime.now()
					timestamp = t.strftime("%Y-%m-%d %H:%M:%S")
					log.msg('Engine error: ', engineresult)
					return (-1, 'Engine error: ' + engineresult, timestamp)
					engine_state = 0

			if engine_state == 1:
				# Trying to get the results from engine
				log.msg('Trying to get test results')
				results = engine.get_test_results(cftestname, cfruntimes, cftolerance)


			engine_state = engine.teardown_environment()

		if engine_state != 1:
			log.msg('Something went wrong while running engine')
			return (-1, 'Engine error: ' + engineresult, timestamp)
		
		log.msg('Returning results')

		return results



if __name__ == "__main__":

	pass
