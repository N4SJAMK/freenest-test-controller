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
import logging
#import shlex

module_logger = logging.getLogger('engine_starter.git_puller')

class gitpuller:
	
        def __init__(self):

            self.logger = logging.getLogger('engine_starter.git_puller.git_puller')

	def pull(self, testdir):
		try:
                        self.logger.debug('Starting GIT process')
                	gitpull = subprocess.Popen(["sh", "git_wrapper.sh"],cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
			#self.logger.debug('GIT output list: %s', str(gitpull))
			# check and raise an exception if errors occur
                	if str(gitpull[0]).find == ' ':
                	        raise Exception(str(gitpull[1]))
			else:
				self.logger.debug('GIT output: %s', gitpull[0])
				return "ok"
        	except Exception as e:
			# if something weird happens, a message will be returned and old tests are run
                        self.logger.critical('GIT process exception: %s', str(e))
                	return str(e)
                
                

