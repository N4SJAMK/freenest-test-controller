#!/usr/bin/env python

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


import sys, time
import xmlrpclib
import TestLinkAPI
import sys, os, time 
import subprocess
import logging
from git import *

#from config import conf
from datetime import datetime
from xml.etree import ElementTree as ET
from git_puller import gitpuller

from daemon import Daemon

repository = "/var/www/Testlink-Robot/robot_testing_scripts"
sleeptime = 10

class TestlinkDaemon(Daemon):
    def run(self):
	print "Testlink daemon starting"
        logger = logging.getLogger('testlink_daemon')
        logger.setLevel(logging.DEBUG)
        fh = logging.FileHandler('testlink_daemon.log')
        formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        fh.setLevel(logging.DEBUG)
        fh.setFormatter(formatter)
        logger.addHandler(fh)
	
	repo = Repo(repository)
	assert repo.bare == False
	status = repo.iter_commits('master', max_count=1)

	while True:
		time.sleep(sleeptime)
		logging.debug('Daemon heartbeat')
		newstatus = repo.iter_commits('master', max_count=1)
		if newstatus != status:
			logging.debug('repo status changed, tests should be re-run!')
			status = newstatus


if __name__ == "__main__":
    daemon = TestlinkDaemon('/tmp/testlinkdaemon.pid')
    if len(sys.argv) == 2:
            if 'start' == sys.argv[1]:
                    daemon.start()
            elif 'stop' == sys.argv[1]:
                    daemon.stop()
            elif 'restart' == sys.argv[1]:
                    daemon.restart()
            else:
                    print "Unknown command"
                    sys.exit(2)
            sys.exit(0)
    else:
            print "usage: %s start|stop|restart" % sys.argv[0]
            sys.exit(2)


	


