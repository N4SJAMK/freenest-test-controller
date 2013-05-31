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
#import shlex
from twisted.python import log

class svnpuller:
    def pull(self, testdir):
        try:
            log.msg('pulling tests')
            svnpull = subprocess.Popen(["sh", "svn_wrapper.sh"],cwd=testdir,stdout=subprocess.PIPE,stderr=subprocess.PIPE).communicate()
            log.msg('SVN output:', str(svnpull))
            # check and raise an exception if errors occur
            if str(svnpull[0]).find == ' ':
                raise Exception(str(svnpull[1]))
            else:
                return "ok"
        except Exception as e:
            # if something weird happens, a message will be returned and old tests are run
            log.msg('SVN process exception: %s', str(e))
            return str(e)
