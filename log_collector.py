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

import sys
import os
import subprocess
from twisted.python import log

class logcollector:
        def mark_logs(self, testCaseName, host):
                try:
			# Creating the command for marking the logs on all hosts that are used in the test
			cmd = "fab -f " + os.path.dirname(os.path.realpath(__file__)) + "/fab_log_collector.py mark_log:" + testCaseName + " -H " + host
			#hosts_joined = ""
			#for host in hosts:
			#	if hosts_joined:
			#		hosts_joined = hosts_joined + "," + host
			#	else:
			#		hosts_joined = host

                        #cmd = cmd + hosts_joined
			cmdlist = cmd.split()

                        log.msg('Marking starting time to logs...')
                        fabmark = subprocess.Popen(cmdlist,cwd="./",stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

                        # check and raise an exception if errors occur
                        if str(fabmark[1]).find == ' ':
                                raise Exception(str(fabmark[1]))
                        else:
                                return "ok"

                except Exception as e:
                        # if something weird happens, a message will be returned and old tests are run
                        log.msg('Fabric exception:', str(e))
                        return str(e)


	def mark_logs_end(self, testCaseName, host):
		try:
			# Creating the command for marking the logs on all hosts that are used in the test
			cmd = "fab -f " + os.path.dirname(os.path.realpath(__file__)) + "/fab_log_collector.py mark_log_end:" + testCaseName + " -H " + host
			#hosts_joined = ""
			#for host in hosts:
			#	if hosts_joined:
			#		hosts_joined = hosts_joined + "," + host
			#	else:
			#		hosts_joined = host

			#cmd = cmd + hosts_joined
			cmdlist = cmd.split()

			msg = "Marking ending time to " + host + " logs..."
			log.msg(msg)
			fabmarkend = subprocess.Popen(cmdlist,cwd="./",stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()

			# check and raise an exception if errors occur
			if str(fabmarkend[1]).find == ' ':
				raise Exception(str(fabmarkend[1]))
			else:
				return "ok"

		except Exception as e:
			# if something weird happens, a message will be returned
			log.msg('Fabric exception:', str(e))
			return str(e)


	def collect_logs(self, outputdir, testCaseName, hosts):
		try:
                        # Creating the command for marking the logs on all hosts that are used in the test
			logdir = outputdir + testCaseName + "/"
                        cmd = "fab -w -f " + os.path.dirname(os.path.realpath(__file__)) + "/fab_log_collector.py collect_log:" + logdir + " -H "
			hosts_joined = ""
			for host in hosts:
				if hosts_joined:
					hosts_joined = hosts_joined + "," + host
				else:
					hosts_joined = host

			cmd = cmd + hosts_joined
                        cmdlist = cmd.split()

                        log.msg('Fetching logs from test machines...')
                        fabcollect = subprocess.Popen(cmdlist,cwd="./",stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			#log.msg(fabcollect)

                        # check and raise an exception if errors occur
                        if str(fabcollect[1]).find == ' ':
                                raise Exception(str(fabcollect[1]))
                        else:
				log.msg('Logs succesfully received')
                                return "ok"

                except Exception as e:
                        # if something weird happens, a message will be returned
                        log.msg('Fabric exception:', str(e))
                        return str(e)
		
